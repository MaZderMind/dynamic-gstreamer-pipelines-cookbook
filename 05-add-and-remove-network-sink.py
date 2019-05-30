#!/usr/bin/env python
import logging
from threading import Thread, Event

from tools.application_init import application_init

application_init()

from gi.repository import Gst, GLib
from tools.runner import Runner

log = logging.getLogger("main")

log.info("building pipeline")
pipeline = Gst.Pipeline.new()
caps_audio = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2")
caps_audio_be = Gst.Caps.from_string("audio/x-raw,format=S16BE,rate=48000,channels=2")
caps_rtp = Gst.Caps.from_string("application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2")

testsrc = Gst.ElementFactory.make("audiotestsrc", "testsrc1")
testsrc.set_property("is-live", True)
testsrc.set_property("freq", 220)
pipeline.add(testsrc)

tee = Gst.ElementFactory.make("tee")  # (1)
tee.set_property("allow-not-linked", True)
pipeline.add(tee)
testsrc.link_filtered(tee, caps_audio)

playback_internal = False  # (2)
if playback_internal:
    sink = Gst.ElementFactory.make("autoaudiosink")
    pipeline.add(sink)
    tee.link(sink)


# audioconvert ! {rawcaps_be} ! rtpL16depay ! udpsink port=…
def create_bin(port):
    log.info("Creating RTP-Bin for Port %d" % port)
    txbin = Gst.Bin.new("tx-bin-%d" % port)
    log.debug(txbin)

    log.info("Creating queue")
    queue = Gst.ElementFactory.make("queue")  # (3)
    log.debug(queue)

    log.info("Adding queue to bin")
    log.debug(txbin.add(queue))

    log.info("Creating audioconvert")
    audioconvert = Gst.ElementFactory.make("audioconvert")
    log.debug(audioconvert)

    log.info("Adding audioconvert to bin")
    log.debug(txbin.add(audioconvert))

    log.info("Linking queue to audioconvert")
    log.debug(queue.link(audioconvert))

    log.info("Creating payloader")
    payloader = Gst.ElementFactory.make("rtpL16pay")
    log.debug(payloader)

    log.info("Adding payloader to bin")
    log.debug(txbin.add(payloader))

    log.info("Linking audioconvert to payloader")
    log.debug(audioconvert.link_filtered(payloader, caps_audio_be))

    log.info("Creating udpsink")
    udpsink = Gst.ElementFactory.make("udpsink")
    log.debug(payloader)
    udpsink.set_property("host", "127.0.0.1")  # (4)
    udpsink.set_property("port", port)

    log.info("Adding udpsink to bin")
    log.debug(txbin.add(udpsink))

    log.info("Linking payloader to udpsink")
    log.debug(payloader.link(udpsink))

    log.info("Selecting Input-Pad")
    sink_pad = queue.get_static_pad("sink")
    log.debug(sink_pad)

    log.info("Creating Ghost-Pad")
    ghost_pad = Gst.GhostPad.new("sink", sink_pad)
    log.debug(ghost_pad)

    log.info("Adding Ghost-Pad to Bin")
    log.debug(txbin.add_pad(ghost_pad))

    return txbin


def add_bin(port):
    log.info("Adding RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_before" % port)

    log.info("Creating Bin")
    txbin = create_bin(port)
    log.info("Created Bin")
    log.debug(txbin)

    log.info("Adding bin to pipeline")
    log.debug(pipeline.add(txbin))

    log.info("Syncing Bin-State with Parent")
    log.debug(txbin.sync_state_with_parent())

    log.info("Linking bin to mixer")
    tee.link(txbin)

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "add_bin_%u_after" % port)
    log.info("Added RTP-Bin for Port %d to the Pipeline" % port)


def remove_bin(port):
    log.info("Removing RTP-Bin for Port %d to the Pipeline" % port)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "remove_bin_%u_before" % port)

    log.info("Selecting Bin")
    txbin = pipeline.get_by_name("tx-bin-%d" % port)
    log.debug(txbin)

    log.info("Selecting Ghost-Pad")
    ghostpad = txbin.get_static_pad("sink")
    log.debug(ghostpad)

    log.info("Selecting Tee-Pad (Peer of Ghost-Pad)")
    teepad = ghostpad.get_peer()
    log.debug(teepad)

    def blocking_pad_probe(pad, info):
        log.info("Stopping Bin")
        log.debug(txbin.set_state(Gst.State.NULL))

        log.info("Removing Bin from Pipeline")
        log.debug(pipeline.remove(txbin))

        log.info("Releasing Tee-Pad")
        log.debug(tee.release_request_pad(teepad))

        Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "remove_bin_%u_after" % port)
        log.info("Removed RTP-Bin for Port %d to the Pipeline" % port)

        return Gst.PadProbeReturn.REMOVE

    log.info("Configuring Blocking Probe on teepad")
    teepad.add_probe(Gst.PadProbeType.BLOCK, blocking_pad_probe)  # (5)


stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")

    num_ports = 3
    timeout = 0.2
    while True:
        for i in range(0, num_ports):
            if stop_event.wait(timeout): return
            log.info("Scheduling add_bin for Port %d", 15000 + i)
            GLib.idle_add(add_bin, 15000 + i)

        for i in range(0, num_ports):
            if stop_event.wait(timeout): return
            log.info("Scheduling remove_bin for Port %d", 15000 + i)
            GLib.idle_add(remove_bin, 15000 + i)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
