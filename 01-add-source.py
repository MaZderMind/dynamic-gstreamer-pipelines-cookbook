#!/usr/bin/env python
import logging
from threading import Thread, Event

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

sink = Gst.ElementFactory.make("autoaudiosink")
pipeline.add(sink)
mixer.link_filtered(sink, caps)

testsrc1.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc1-output")

mixer.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "mixer-output")


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


stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")
    if stop_event.wait(2): return
    GLib.idle_add(add_new_src)  # (1)
    log.info("Sequence ended")


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
