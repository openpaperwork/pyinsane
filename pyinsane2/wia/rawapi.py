from collections import deque
import logging
import os
import queue
import threading

from . import _rawapi
from .. import util

logger = logging.getLogger(__name__)


_rawapi.register_logger(0, logger)


SINGLE_THREAD = bool(int(os.getenv("PYINSANE_SINGLE_THREAD", 0)))


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
        if SINGLE_THREAD:
            return self.do()

        global wia_thread
        global wia_action_queue

        if wia_thread is None or not wia_thread.is_alive():
            raise WIAException("WIA thread died unexpectedly !")
        wia_action_queue.put(self)

    def wait(self):
        ret = self.start()
        if SINGLE_THREAD:
            return ret

        self.__sem.acquire()
        if self.exception is not None:
            raise self.exception
        return self.result

    def do(self):
        if SINGLE_THREAD:
            return self.func(**self.kwargs)

        try:
            self.result = self.func(**self.kwargs)
        except Exception as exc:
            if (not isinstance(exc, EOFError) and
                    not isinstance(exc, StopIteration)):
                logger.error("Unexpected exception", exc_info=exc)
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


if not SINGLE_THREAD:
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


def _get_constraints(dev_or_src):
    constraints = _rawapi.get_constraints(dev_or_src)
    if constraints is None:
        raise WIAException("Failed to get properties constraints")
    return constraints


def get_constraints(dev_or_src):
    return WiaAction(_get_constraints, dev_or_src=dev_or_src).wait()


def _set_property(dev_or_src, propname, propvalue):
    ret = _rawapi.set_property(dev_or_src, propname, propvalue)
    if not ret:
        raise WIAException("Failed to set scanner properties")


def set_property(dev_or_src, propname, propvalue):
    return WiaAction(_set_property, dev_or_src=dev_or_src,
                     propname=propname, propvalue=propvalue).wait()


class WiaCallbacks(object):
    def __init__(self):
        super(WiaCallbacks, self).__init__()
        self.received = deque()
        self.condition = threading.Condition()
        self.buffer = 512000 * b"\0"

    def get_data_cb(self, nb_bytes):
        self.condition.acquire()
        try:
            data = self.buffer[:nb_bytes]
            self.received.append(data)
            self.condition.notify_all()
        finally:
            self.condition.release()

    def end_of_page_cb(self):
        self.condition.acquire()
        try:
            self.received.append(
                EOFError()
            )
            self.condition.notify_all()
        finally:
            self.condition.release()

    def end_of_scan_cb(self):
        self.condition.acquire()
        try:
            self.received.append(
                StopIteration()
            )
            self.condition.notify_all()
        finally:
            self.condition.release()

    def read(self):
        self.condition.acquire()
        try:
            if len(self.received) <= 0:
                self.condition.wait()
            popped = self.received.popleft()
            if isinstance(popped, Exception):
                raise popped
            return popped
        finally:
            self.condition.release()


def _start_scan(src, out):
    ret = _rawapi.download(
        src,
        out.get_data_cb,
        out.end_of_page_cb,
        out.end_of_scan_cb,
        out.buffer,
    )
    if ret is None:  # Brother MFC-7360N
        raise StopIteration()
    if not ret:
        raise WIAException("Failed to scan")
    return ret


def start_scan(src):
    out = WiaCallbacks()
    WiaAction(_start_scan, src=src, out=out).start()  # don't wait
    return out


def exit():
    _rawapi.exit()
