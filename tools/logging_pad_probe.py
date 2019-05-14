import datetime
import logging

from gi.repository import Gst

log = logging.getLogger("Pad-Probe")


def logging_pad_probe(pad, probeinfo, location):
    pts_nanpseconds = probeinfo.get_buffer().pts
    pts_timedelta = datetime.timedelta(microseconds=pts_nanpseconds / 1000)
    log.debug("PTS at %s = %s", '{:>20s}'.format(location), pts_timedelta)
    return Gst.PadProbeReturn.OK
