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
caps_audio = Gst.Caps.from_string("audio/x-raw,format=S16LE,rate=48000,channels=2,layout=interleaved")
caps_audio_be = Gst.Caps.from_string("audio/x-raw,format=S16BE,rate=48000,channels=2")
caps_rtp = Gst.Caps.from_string("application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2")

# audiotestsrc freq=220 ! audiomixer name=mix ! autoaudiosink
# audiotestsrc freq=440 ! fakesink
##

testsrc1 = Gst.ElementFactory.make("audiotestsrc", "testsrc1")
testsrc1.set_property("is-live", True)
testsrc1.set_property("freq", 220)
pipeline.add(testsrc1)

mixer = Gst.ElementFactory.make("audiomixer")
pipeline.add(mixer)
testsrc1.link_filtered(mixer, caps_audio)

sink = Gst.ElementFactory.make("autoaudiosink")
pipeline.add(sink)
mixer.link(sink)

testsrc2 = Gst.ElementFactory.make("audiotestsrc", "testsrc2")
testsrc2.set_property("is-live", True)
testsrc2.set_property("freq", 440)
pipeline.add(testsrc2)

tee = Gst.ElementFactory.make("tee")
tee.set_property("allow-not-linked", True)
pipeline.add(tee)
testsrc2.link_filtered(tee, caps_audio)


def link_element():
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "link_element_before")

    log.info("Requesting Tee-Pad")
    tee_pad_templ = tee.get_pad_template("src_%u")
    tee_pad = tee.request_pad(tee_pad_templ)
    log.debug(tee_pad)

    log.info("Requesting Mixer-Pad")
    mixer_pad_templ = mixer.get_pad_template("sink_%u")
    mixer_pad = mixer.request_pad(mixer_pad_templ)
    log.debug(mixer_pad)

    log.info("Linking Tee-Pad to Mixer-Pad")
    log.debug(tee_pad.link(mixer_pad))

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "link_element_after")


def unlink_element():
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "link_element_before")

    log.info("Unlinking tee from mixer")
    for tee_pad in tee.srcpads:
        mixer_pad = tee_pad.get_peer()

        log.info("Unlinking pads %s and %s" % (tee_pad, mixer_pad))
        log.debug(tee_pad.unlink(mixer_pad))

        log.info("Releasing pad %s" % tee_pad)
        log.debug(tee.release_request_pad(tee_pad))

        log.info("Releasing pad %s" % mixer_pad)
        log.debug(mixer.release_request_pad(mixer_pad))

    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "link_element_after")


stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")

    while True:
        if stop_event.wait(2): return
        GLib.idle_add(link_element)

        if stop_event.wait(2): return
        GLib.idle_add(unlink_element)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()
