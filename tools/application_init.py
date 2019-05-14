import logging
import signal

import sys

log = logging.getLogger('Application Init')

MIN_GST = (1, 10)
MIN_PYTHON = (3, 5)


def application_init():
    import coloredlogs
    coloredlogs.install(
        level='DEBUG',
        fmt="%(asctime)s %(name)s@%(threadName)s %(levelname)s %(message)s")

    log.debug('importing gi')
    import gi

    log.debug('importing gi.Gst, gi.GObject')
    gi.require_version('Gst', '1.0')
    gi.require_version('GstNet', '1.0')

    from gi.repository import Gst, GObject

    log.debug('Gst.init')
    Gst.init([])

    log.debug('version check')
    if Gst.version() < MIN_GST:
        raise Exception('GStreamer version', Gst.version(),
                        'is too old, at least', MIN_GST, 'is required')

    if sys.version_info < MIN_PYTHON:
        raise Exception('Python version', sys.version_info,
                        'is too old, at least', MIN_PYTHON, 'is required')

    log.debug('GObject.threads_init')
    GObject.threads_init()


def set_sigint_handler(sigint_callback):
    logging.debug('setting SIGINT handler')
    from gi.repository import GLib
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, sigint_callback)
