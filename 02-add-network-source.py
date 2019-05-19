#!/usr/bin/env python
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
caps_audio = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2")
caps_audio_be = Gst.Caps.from_string("audio/x-raw,format=S16BE,rate=48000,channels=2")
caps_rtp = Gst.Caps.from_string("application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2")

testsrc = Gst.ElementFactory.make("audiotestsrc", "testsrc")
testsrc.set_property("is-live", True)
testsrc.set_property("freq", 220)
pipeline.add(testsrc)

mixer = Gst.ElementFactory.make("audiomixer")
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
    bin = Gst.Bin.new("rx-bin-%d" % port)

    udpsrc = Gst.ElementFactory.make("udpsrc")
    udpsrc.set_property("port", port)
    bin.add(udpsrc)

    udpsrc.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "udpsrc-%d-output" % port)

    jitterbuffer = Gst.ElementFactory.make("rtpjitterbuffer")
    jitterbuffer.set_property("latency", 100)
    bin.add(jitterbuffer)
    udpsrc.link_filtered(jitterbuffer, caps_rtp)

    depayload = Gst.ElementFactory.make("rtpL16depay")
    bin.add(depayload)
    jitterbuffer.link_filtered(depayload, caps_rtp)

    depayload.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "depayload-%d-output" % port)

    audioconvert = Gst.ElementFactory.make("audioconvert", "out-%d" % port)
    bin.add(audioconvert)
    depayload.link_filtered(audioconvert, caps_audio_be)

    return bin


def add_bin(port):
    bin = create_bin(port)

    log.info("Adding RTP-Bin for Port %d to the Pipeline" % port)
    pipeline.add(bin)
    output_element = pipeline.get_by_name("out-%d" % port)
    output_element.link_filtered(mixer, caps_audio)
    bin.sync_state_with_parent()
    log.info("Added RTP-Bin for Port %d to the Pipeline" % port)


def timed_sequence():
    log.info("Starting Sequence")
    time.sleep(2)
    GLib.idle_add(add_bin, 10000)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "02-add-network-source")
    # time.sleep(2)
    # GLib.idle_add(add_bin, 10001)
    # Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "02-add-network-source")


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

t.join()
