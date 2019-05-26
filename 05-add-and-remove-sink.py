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

testsrc = Gst.ElementFactory.make("audiotestsrc", "testsrc1")
testsrc.set_property("is-live", True)  # (3)
testsrc.set_property("freq", 220)
pipeline.add(testsrc)

tee = Gst.ElementFactory.make("tee")
pipeline.add(tee)
testsrc.link_filtered(tee, caps)

sink = Gst.ElementFactory.make("fakesink")
pipeline.add(sink)
tee.link(sink)

testsrc.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc-output")

sink.get_static_pad("sink").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "fakesink-input")


def add_bin(port):
    log.info("Adding RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_before" % port)

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_after" % port)
    log.info("Added RTP-Bin for Port %d to the Pipeline" % port)


def remove_bin(port):
    log.info("Removing RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "remove_bin_%u_before" % port)

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "remove_bin_%u_after" % port)
    log.info("Removed RTP-Bin for Port %d to the Pipeline" % port)


stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")

    num_ports = 3
    while True:
        for i in range(0, num_ports):
            if stop_event.wait(2): return
            log.info("Scheduling add_bin for Port %d", 10000 + i)
            GLib.idle_add(add_bin, 10000 + i)  # (1)

        for i in range(0, num_ports):
            if stop_event.wait(2): return
            log.info("Scheduling remove_bin for Port %d", 10000 + i)
            GLib.idle_add(remove_bin, 10000 + i)  # (1)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
