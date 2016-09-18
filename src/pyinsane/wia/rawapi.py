import queue
import sys
import threading

from . import _rawapi
from .. import util


class WIAException(util.PyinsaneException):
    def __init__(self, msg):
        super(WIAException, self).__init__("WIA: {}".format(msg))


class WiaAction(object):
    def __init__(self, func, **kwargs):
        self.func = func
        self.kwargs = kwargs
        self.result = None
        self.exception = None
        self.__sem = threading.Semaphore(0)

    def start(self):
        global wia_thread
        global wia_action_queue

        if wia_thread is None or not wia_thread.is_alive():
            raise WIAException("WIA thread died unexpectidly !")
        wia_action_queue.put(self)

    def wait(self):
        self.start()
        self.__sem.acquire()
        if self.exception is not None:
            raise self.exception
        return self.result

    def do(self):
        try:
            sys.stdout.flush()
            self.result = self.func(**self.kwargs)
        except Exception as exc:
            self.exception = exc
        self.__sem.release()


class WiaWorker(threading.Thread):
    def run(self):
        global wia_action_queue
        while True:
            try:
                action = wia_action_queue.get(block=True, timeout=1)
                action.do()
            except queue.Empty:
                if not parent_thread.is_alive():
                    return


parent_thread = threading.current_thread()
wia_action_queue = queue.Queue()
wia_thread = WiaWorker()
wia_thread.start()


def _init():
    _rawapi.init()


def init():
    return WiaAction(_init).wait()


def _open(devid):
    out = _rawapi.open(devid)
    if out is None:
        raise WIAException("Failed to open {}".format(devid))
    return out


def open(devid):
    return WiaAction(_open, devid=devid).wait()


def _get_devices():
    devices = _rawapi.get_devices()
    if devices is None:
        raise WIAException("Failed to get device list")
    return devices


def get_devices():
    return WiaAction(_get_devices).wait()


def _get_sources(dev):
    sources = _rawapi.get_sources(dev)
    if sources is None:
        raise WIAException("Failed to get sources")
    return sources


def get_sources(dev):
    return WiaAction(_get_sources, dev=dev).wait()


def _get_properties(dev_or_src):
    properties = _rawapi.get_properties(dev_or_src)
    if properties is None:
        raise WIAException("Failed to get scanner properties")
    return properties


def get_properties(dev_or_src):
    return WiaAction(_get_properties, dev_or_src=dev_or_src).wait()


def _set_property(dev_or_src, propname, propvalue):
    ret = _rawapi.set_property(dev_or_src, propname, propvalue)
    if not ret:
        raise WIAException("Failed to set scanner properties")


def set_property(dev_or_src, propname, propvalue):
    return WiaAction(_set_property, dev_or_src=dev_or_src,
                     propname=propname, propvalue=propvalue).wait()


def _start_scan(src):
    ret = _rawapi.start_scan(src)
    if ret is None:
        raise WIAException("Failed to start scan")
    return ret


def _download(scan):
    _rawapi.download(scan)


def start_scan(src):
    r = WiaAction(_start_scan, src=src).wait()
    WiaAction(_download, scan=r).start()  # don't wait
    return r


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