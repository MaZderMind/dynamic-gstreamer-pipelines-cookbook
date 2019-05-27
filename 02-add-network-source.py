#!/usr/bin/env python
import logging
from threading import Thread, Event

rtp_max_jitter_mx = 30

from tools.application_init import application_init

application_init()

from gi.repository import Gst, GLib
from tools.logging_pad_probe import logging_pad_probe
from tools.runner import Runner

log = logging.getLogger("main")

log.info("building pipeline")
pipeline = Gst.Pipeline.new()
caps_audio = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2")  # (11)
caps_audio_be = Gst.Caps.from_string("audio/x-raw,format=S16BE,rate=48000,channels=2")
caps_rtp = Gst.Caps.from_string("application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2")

testsrc = Gst.ElementFactory.make("audiotestsrc", "testsrc")
testsrc.set_property("is-live", True)  # (2)
testsrc.set_property("freq", 110)
testsrc.set_property("volume", 0.5)
pipeline.add(testsrc)

mixer = Gst.ElementFactory.make("audiomixer")
mixer.set_property("latency", (rtp_max_jitter_mx * 1_000_000))  # (5)
pipeline.add(mixer)
testsrc.link_filtered(mixer, caps_audio)

sink = Gst.ElementFactory.make("autoaudiosink")
pipeline.add(sink)
mixer.link_filtered(sink, caps_audio)

testsrc.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc-output")

mixer.get_static_pad("src").add_probe(
    Gst.PadProbeType.BUFFER, logging_pad_probe, "mixer-output")


# udpsrc port=… ! {rtpcaps} ! rtpjitterbuffer latency=… ! rtpL16depay ! {rawcaps_be} ! audioconvert ! {rawcaps} ! …
def create_bin(port):
    log.info("Creating RTP-Bin for Port %d" % port)
    rxbin = Gst.Bin.new("rx-bin-%d" % port)  # (8)

    udpsrc = Gst.ElementFactory.make("udpsrc")  # (3)
    udpsrc.set_property("port", port)
    rxbin.add(udpsrc)

    udpsrc.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "udpsrc-%d-output" % port)

    jitterbuffer = Gst.ElementFactory.make("rtpjitterbuffer")  # (4)
    jitterbuffer.set_property("latency", rtp_max_jitter_mx)
    jitterbuffer.set_property("drop-on-latency", True)
    rxbin.add(jitterbuffer)
    udpsrc.link_filtered(jitterbuffer, caps_rtp)

    depayload = Gst.ElementFactory.make("rtpL16depay")  # (6)
    rxbin.add(depayload)
    jitterbuffer.link(depayload)

    depayload.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "depayload-%d-output" % port)

    audioconvert = Gst.ElementFactory.make("audioconvert", "out-%d" % port)  # (7)
    rxbin.add(audioconvert)
    depayload.link_filtered(audioconvert, caps_audio_be)

    return rxbin


def add_bin(port):
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_before" % port)
    bin = create_bin(port)

    log.info("Adding RTP-Bin for Port %d to the Pipeline" % port)
    pipeline.add(bin)
    output_element = pipeline.get_by_name("out-%d" % port)  # (9)
    output_element.link_filtered(mixer, caps_audio)
    bin.sync_state_with_parent()  # (10)
    log.info("Added RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_after" % port)


stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")

    if stop_event.wait(2): return
    log.info("Scheduling adding a Bin for Port 10000")
    GLib.idle_add(add_bin, 10000)  # (1)

    if stop_event.wait(2): return
    log.info("Scheduling adding a Bin for Port 10001")
    GLib.idle_add(add_bin, 10001)  # (1)

    if stop_event.wait(2): return
    log.info("Scheduling adding a Bin for Port 10002")
    GLib.idle_add(add_bin, 10002)  # (1)

    log.info("Sequence ended")


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
