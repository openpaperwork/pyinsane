import faulthandler

from . import _rawapi


class WIAException(Exception):
    def __init__(self, msg):
        super(WIAException, self).__init__("WIA: {}".format(msg))


def init():
    _rawapi.init()


def open(devid):
    out = _rawapi.open(devid)
    if out is None:
        raise WIAException("Failed to open {}".format(devid))
    return out


def get_devices():
    devices = _rawapi.get_devices()
    if devices is None:
        raise WIAException("Failed to get device list")
    return devices


def get_sources(dev):
    sources = _rawapi.get_sources(dev)
    if sources is None:
        raise WIAException("Failed to get sources")
    return sources


def get_properties(dev_or_src):
    properties = _rawapi.get_properties(dev_or_src)
    if properties is None:
        raise WIAException("Failed to get scanner properties")
    return properties


def set_property(dev_or_src, propname, propvalue):
    ret = _rawapi.set_property(dev_or_src, propname, propvalue)
    if not ret:
        raise WIAException("Failed to set scanner properties")


def start_scan(src):
    ret = _rawapi.start_scan(src)
    if ret is None:
        raise WIAException("Failed to start scan")
    return ret


def read(scan, buf):
    ret = _rawapi.read(scan, buf)
    if ret is None:
        raise WIAException("Failed to start scan")
    elif ret == 0:
        raise EOFError()
    elif ret == -1:
        raise StopIteration()
    return ret


def exit():
    _rawapi.exit()


