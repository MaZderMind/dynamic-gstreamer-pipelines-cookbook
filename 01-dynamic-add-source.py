#!/usr/bin/env python
"""Creates and Manipulates a Pipeline with audiotestsrc and audiomixer

This Example creates a Pipeline like this:

  audiotestsrc ! audiomixer ! alsasink

It installs Pad-Probes after the audiotestsrc and the audiomixer, which log the PTS-Timestamps of the Buffers flowing
through the Element's src-Pads.

After 2 seconds, another audiotestsrc is created with such a Pad-Probe and linked to the audiomixer.

On the Speaker/Headphone you can hear the 220 Hz-Zone from the first audiotestsrc, which after 2 Seconds gets mixed with
the 440 Hz Tone from the second audiotestsrc.

On the Console you can see that the Timestamps from the second audiotestsrc start around the 0:00:02 seconds mark,
because we configured it to be a true live-source.


The most important Lines have been marked as such:
 (1) We schedule the execution on the GLib Event-Loop by using Glib.idle_add. On the Console you can see, that the
     Sequence runs in its own Sequence-Thread but the second testsrc is actually added from the MainThread.

     It seems that this exact example also works without this, because some of the Methods are Thread-Safe by
     Documentation (ie. Bin.add) and some are by luck (ie Gobject.Object.set_property), but not follwing this pattern
     can lead to unexpected and hard to find issues.

     From the console you can also see, that the Pad-Probes are called synchronously from their
     respective Elements' Streaming-Threads (Shown as Dummy-[n]).

 (2) Forcing the audiotestsrc to be a Live-Source makes it produce Buffers with timestamps starting at the current
     Running-Time of the Pipeline. A Non-Live-Source would start ad 0:00:00 and run faster then the other sources,
     until it would have caught up to the current Running-Time.

     Try to comment this line out and look at the Console-Output around the 0:00:02 seconds mark

 (3) Furthermore it is important that all other Sources in the Pipeline are also in Live-Mode, here this is ensured
     by settinf the is-live property of testsrc1. If one or all of the Sources in the Pipeline are not live, they will
     produce as many buffers as the sink allows them to. In a pipeline like the following, where neither source nor
     sink enforce live-behaviour, the timestamp the audiomixer is working with might be way ahead of those produced by
     your newly added live-source: `audiotestsrc ! audiomixer ! wavenc ! filesink …"

     If you are dealing with sources that do not support live behaviour, for example a `filesrc`, you should place an
     `identity`-Element with the `sync`-Property set to True right after it, so that it behaves like a live-source to
     downstream elements like audiomixers.

 (3) An Element does not automatically take over its parent state. Also, not all Elements in a Pipeline have to have the
     same state. In this case the new audiotestsrc-Element starts in NULL state and is added as such to the Pipeline.
     Once it is added, its state is synced to the pipeline (PLAYING) which makes it switch from NULL through
     READY and PAUSED to PLAYING, where it starts generating buffers and sending them downstream to the audiomixer.
"""

import logging
import time
from threading import Thread

from tools.application_init import application_init

application_init()

from gi.repository import Gst, GLib
from tools.logging_pad_probe import logging_pad_probe
from tools.runner import Runner

log = logging.getLogger("main")

log.info("building pipeline")
pipeline = Gst.Pipeline.new()
caps = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2")

testsrc1 = Gst.ElementFactory.make("audiotestsrc", "testsrc1")
testsrc1.set_property("is-live", True)  # (3)
testsrc1.set_property("freq", 220)
pipeline.add(testsrc1)

mixer = Gst.ElementFactory.make("audiomixer")
pipeline.add(mixer)
testsrc1.link_filtered(mixer, caps)

sink = Gst.ElementFactory.make("alsasink")
pipeline.add(sink)
mixer.link(sink)

testsrc1.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc1-output")

mixer.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "mixer-output")


def timed_sequence():
    log.info("Starting Sequence")
    time.sleep(2)

    def add_new_src():
        log.info("Adding testsrc2")
        testsrc2 = Gst.ElementFactory.make("audiotestsrc", "testsrc2")
        testsrc2.set_property("freq", 440)
        testsrc2.set_property("is-live", True)  # (2)

        testsrc2.get_static_pad("src").add_probe(
            Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc2-output")

        pipeline.add(testsrc2)
        testsrc2.link_filtered(mixer, caps)
        testsrc2.sync_state_with_parent()  # (4)
        log.info("Adding testsrc2 done")

    GLib.idle_add(add_new_src)  # (1)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

t.join()
