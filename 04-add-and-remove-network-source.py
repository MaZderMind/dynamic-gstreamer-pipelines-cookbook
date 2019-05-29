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
caps_audio = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2")
caps_audio_be = Gst.Caps.from_string("audio/x-raw,format=S16BE,rate=48000,channels=2")
caps_rtp = Gst.Caps.from_string("application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2")

testsrc = Gst.ElementFactory.make("audiotestsrc", "testsrc")
testsrc.set_property("is-live", True)
testsrc.set_property("freq", 220)
testsrc.set_property("volume", 0.5)
pipeline.add(testsrc)

mixer = Gst.ElementFactory.make("audiomixer")
mixer.set_property("latency", (rtp_max_jitter_mx * 1_000_000))
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
    rxbin = Gst.Bin.new("rx-bin-%d" % port)  # (1)

    log.info("Creating udpsrc")
    udpsrc = Gst.ElementFactory.make("udpsrc")
    log.debug(udpsrc)
    udpsrc.set_property("port", port)
    udpsrc.set_property("caps", caps_rtp)

    log.info("Adding udpsrc to bin")
    log.debug(rxbin.add(udpsrc))

    log.info("Registering Pad-Probe after udpsrc")
    log.debug(udpsrc.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "udpsrc-%d-output" % port))

    log.info("Creating jitterbuffer")
    jitterbuffer = Gst.ElementFactory.make("rtpjitterbuffer")
    log.debug(jitterbuffer)
    jitterbuffer.set_property("latency", rtp_max_jitter_mx)
    jitterbuffer.set_property("drop-on-latency", True)

    log.info("Adding jitterbuffer to bin")
    log.debug(rxbin.add(jitterbuffer))

    log.info("Linking udpsrc to jitterbuffer")
    log.debug(udpsrc.link(jitterbuffer))

    log.info("Creating depayloader")
    depayload = Gst.ElementFactory.make("rtpL16depay")
    log.debug(depayload)

    log.info("Adding depayloader to bin")
    log.debug(rxbin.add(depayload))

    log.info("Linking jitterbuffer to depayloader")
    log.debug(jitterbuffer.link(depayload))

    log.info("Registering Pad-Probe after depayload")
    log.debug(depayload.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "depayload-%d-output" % port))

    log.info("Creating audioconvert")
    audioconvert = Gst.ElementFactory.make("audioconvert")
    log.debug(audioconvert)

    log.info("Adding audioconvert to bin")
    log.debug(rxbin.add(audioconvert))

    log.info("Linking depayload to audioconvert")
    log.debug(depayload.link_filtered(audioconvert, caps_audio_be))

    log.info("Selecting Output-Pad")
    src_pad = audioconvert.get_static_pad("src")  # (2) ff.
    log.debug(src_pad)

    log.info("Creating Ghost-Pad")
    ghost_pad = Gst.GhostPad.new("src", src_pad)
    log.debug(ghost_pad)

    log.info("Adding Ghost-Pad to Bin")
    log.debug(rxbin.add_pad(ghost_pad))

    return rxbin


def add_bin(port):
    log.info("Adding RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_before" % port)

    log.info("Creating Bin")
    rxbin = create_bin(port)
    log.info("Created Bin")
    log.debug(rxbin)

    log.info("Adding bin to pipeline")
    log.debug(pipeline.add(rxbin))

    log.info("Linking bin to mixer")
    rxbin.link(mixer)  # (3)

    log.info("Syncing Bin-State with Parent")
    log.debug(rxbin.sync_state_with_parent())

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_after" % port)
    log.info("Added RTP-Bin for Port %d to the Pipeline" % port)


def remove_bin(port):
    log.info("Removing RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "remove_bin_%u_before" % port)

    log.info("Selecting Bin")
    rxbin = pipeline.get_by_name("rx-bin-%d" % port)  # (1)
    log.debug(rxbin)

    log.info("Selecting Ghost-Pad")
    ghostpad = rxbin.get_static_pad("src")
    log.debug(ghostpad)

    log.info("Selecting Mixerpad (Peer of Ghost-Pad)")
    mixerpad = ghostpad.get_peer()  # (4)
    log.debug(mixerpad)

    log.info("Stopping Bin")
    log.debug(rxbin.set_state(Gst.State.NULL))  # (5) ff.

    log.info("Removing Bin from Pipeline")
    log.debug(pipeline.remove(rxbin))

    log.info("Releasing mixerpad")
    log.debug(mixer.release_request_pad(mixerpad))

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
            GLib.idle_add(add_bin, 10000 + i)

        for i in range(0, num_ports):
            if stop_event.wait(2): return
            log.info("Scheduling remove_bin for Port %d", 10000 + i)
            GLib.idle_add(remove_bin, 10000 + i)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
