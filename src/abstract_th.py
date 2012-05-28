import Queue
import sys
import threading

import abstract
import rawapi

__all__ = [
    'Scanner',
    'ScannerOption',
    'get_devices',
]

class SaneAction(object):
    def __init__(self, func, **kwargs):
        self.func = func
        self.args = kwargs
        self.result = None
        self.exception = None
        self.__sem = threading.Semaphore(0)

    def wait(self):
        global sane_thread
        global sane_action_queue

        if sane_thread == None or not sane_thread.is_alive():
            sane_thread = SaneWorker()
            sane_thread.start()

        sane_action_queue.put(self)
        self.__sem.acquire()
        if self.exception != None:
            raise self.exception
        return self.result

    def do(self):
        try:
            print "SANE: Calling function '%s'" % (self.func.func_name)
            self.result = self.func(**self.args)
        except Exception, exc:
            self.exception = exc
        self.__sem.release()


class SaneWorker(threading.Thread):
    def run(self):
        global sane_action_queue
        while True:
            try:
                action = sane_action_queue.get(block=True, timeout=2)
                action.do()
            except Queue.Empty:
                if not parent_thread.is_alive():
                    return


# TODO(Jflesch): Lock for sane_thread*
sane_thread = SaneWorker()
parent_thread = threading.current_thread()
sane_action_queue = Queue.Queue()
sane_thread.start()


def sane_init():
    return SaneAction(abstract.sane_init).wait()


def sane_exit():
    return SaneAction(abstract.sane_exit).wait()


class ScannerOption(object):
    idx = 0
    name = ""
    title = ""
    desc = ""
    val_type = rawapi.SaneValueType(rawapi.SaneValueType.INT)
    unit = rawapi.SaneUnit(rawapi.SaneUnit.NONE)
    size = 4
    capabilities = rawapi.SaneCapabilities(rawapi.SaneCapabilities.NONE)

    constraint_type = rawapi.SaneConstraintType(rawapi.SaneConstraintType.NONE)
    constraint = None

    def __init__(self, scanner, idx):
        self.__scanner = scanner
        self.idx = idx

    @staticmethod
    def build_from_abstract(scanner, opt_idx, opt_abstract):
        opt = ScannerOption(scanner, opt_idx)
        opt.name = opt_abstract.name
        opt.title = opt_abstract.title
        opt.desc = opt_abstract.desc
        opt.val_type = opt_abstract.val_type
        opt.unit = opt_abstract.unit
        opt.size = opt_abstract.size
        opt.capabilities = opt_abstract.capabilities
        opt.constraint_type = opt_abstract.constraint_type
        opt.constraint = opt_abstract.constraint
        return opt

    def __get_value(self):
        # TODO
        pass

    def __set_value(self, new_value):
        # TODO
        pass

    value = property(__get_value, __set_value)


class ScanSession(object):
    def __init__(self):
        # TODO
        pass

    def read(self):
        # TODO
        pass

    def get_nb_img(self):
        # TODO
        pass

    def get_img(self):
        # TODO
        pass

    def __del___(self):
        # TODO
        pass


class Scanner(object):
    def __init__(self, name, vendor="Unknown", model="Unknown",
                 dev_type="Unkwown"):
        self.name = name
        self.vendor = vendor
        self.model = model
        self.dev_type = dev_type
        self.__options = None # { "name" : ScannerOption }

    @staticmethod
    def build_from_abstract(abstract_dev):
        return Scanner(abstract_dev.name, abstract_dev.vendor,
                       abstract_dev.model, abstract_dev.dev_type)

    def _get_options(self):
        # TODO
        pass

    options = property(_get_options)

    def scan(self, multiple=False):
        # TODO
        pass

    def __str__(self):
        return ("Scanner '%s' (%s, %s, %s)"
                % (self.name, self.vendor, self.model, self.dev_type))


def get_devices():
    # TODO
    pass
