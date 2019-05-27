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
testsrc1.set_property("is-live", True)
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

testsrc2 = None  # (2)
capsfilter2 = None
mixerpad = None


def add_new_src():
    global testsrc2, capsfilter2, mixerpad
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "adding-testsrc2-before")
    log.info("Adding testsrc2")

    log.info("Creating testsrc2")
    testsrc2 = Gst.ElementFactory.make("audiotestsrc", "testsrc2")
    testsrc2.set_property("freq", 440)
    testsrc2.set_property("is-live", True)

    testsrc2.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc2-output")

    log.info("Adding testsrc2")
    log.debug(pipeline.add(testsrc2))

    log.info("Creating capsfilter")
    capsfilter2 = Gst.ElementFactory.make("capsfilter", "capsfilter2")  # (3)
    capsfilter2.set_property("caps", caps)

    log.info("Adding capsfilter")
    log.debug(pipeline.add(capsfilter2))

    log.info("Linking testsrc2 to capsfilter2")
    log.debug(testsrc2.link(capsfilter2))

    log.info("Requesting Pad from Mixer")
    mixerpad = mixer.get_request_pad("sink_%u")
    log.debug(mixerpad)

    log.info("Linking capsfilter2 to mixerpad")
    log.debug(capsfilter2.get_static_pad("src").link(mixerpad))

    log.info("Syncing Element-States with Pipeline")
    log.debug(capsfilter2.sync_state_with_parent())
    log.debug(testsrc2.sync_state_with_parent())

    log.info("Adding testsrc2 done")
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "adding-testsrc2-after")  # (4)


def remove_src():
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "removing-testsrc2-before")
    log.info("Removing testsrc2")

    log.info("Stopping testsrc2")
    log.debug(testsrc2.set_state(Gst.State.NULL))  # (5)

    log.info("Stopping capsfilter2")
    log.debug(capsfilter2.set_state(Gst.State.NULL))

    log.info("Removing testsrc2")
    log.debug(pipeline.remove(testsrc2))

    log.info("Removing capsfilter2")
    log.debug(pipeline.remove(capsfilter2))

    log.info("Releasing mixerpad")
    log.debug(mixer.release_request_pad(mixerpad))  # (6)

    log.info("Removing testsrc2 done")
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "removing-testsrc2-after")


stop_event = Event()  # (1)


def timed_sequence():
    log.info("Starting Sequence")
    while True:
        if stop_event.wait(2): return
        log.info("Schedule Add Source")
        GLib.idle_add(add_new_src)

        if stop_event.wait(2): return
        log.info("Schedule Remove Source")
        GLib.idle_add(remove_src)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
