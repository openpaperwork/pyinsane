from . import _rawapi


class WIAException(Exception):
    def __init__(self, msg):
        super(WIAException, self).__init__("WIA: {}".format(msg))


def init():
    _rawapi.init()


def open(devid):
    out = _rawapi.open(devid)
    if not out:
        raise WIAException("Failed to open {}".format(devid))
    return out


def get_sources(dev):
    sources = _rawapi.get_sources(dev)
    if not sources:
        raise WIAException("Failed to get sources")
    return sources


def exit():
    _rawapi.exit()


def get_devices():
    devices = _rawapi.get_devices()
    if not devices:
        raise WIAException("Failed to get device list")
    return devices