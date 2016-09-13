from . import _rawapi


def init():
    _rawapi.init()


def open(devid):
    return _rawapi.open(devid)


def exit():
    _rawapi.exit()


def get_devices():
    return _rawapi.get_devices()