from . import _rawapi


def init():
    _rawapi.init()


def get_devices():
    return _rawapi.get_devices()