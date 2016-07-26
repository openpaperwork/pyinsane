import logging
import os
import pickle
import tempfile

# import basic elements directly, so the caller
# doesn't have to import rawapi if they need them.
from . import abstract
from .abstract_th import ScannerOption
from .rawapi import SaneCapabilities
from .rawapi import SaneConstraint
from .rawapi import SaneConstraintType
from .rawapi import SaneException
from .rawapi import SaneStatus
from .rawapi import SaneUnit
from .rawapi import SaneValueType


__all__ = [
    'SaneCapabilities',
    'SaneConstraint',
    'SaneConstraintType',
    'SaneException',
    'SaneStatus',
    'SaneValueType',
    'SaneUnit',

    'Scanner',
    'ScannerOption',
    'get_devices',
]


logger = logging.getLogger(__name__)

logger.info("Starting Pyinsane subprocess")

pipe_dirpath = tempfile.mkdtemp(prefix="pyinsane_")
pipe_path_c2s = os.path.join(pipe_dirpath, "pipe_c2s")
os.mkfifo(pipe_path_c2s)
pipe_path_s2c = os.path.join(pipe_dirpath, "pipe_s2c")
os.mkfifo(pipe_path_s2c)

logger.info("Pyinsane pipes: {} | {}".format(pipe_path_c2s, pipe_path_s2c))

if os.fork() == 0:
    os.execlp(
        "pyinsane-daemon", "pyinsane-daemon",
        pipe_dirpath,
        pipe_path_c2s, pipe_path_s2c
    )

length_size = len(pickle.pack("i", 0))
fifo_c2s = os.open(pipe_path_c2s, os.O_WRONLY)
fifo_s2c = os.open(pipe_path_s2c, os.O_RDONLY)

logger.info("Connected to Pyinsane subprocess")


def remote_do(command, *args, **kwargs):
    global length_size
    global fifo_s2c
    global fifo_c2s

    cmd = {
        'command': command,
        'args': args,
        'kwargs': kwargs,
    }

    cmd = pickle.dumps(cmd)
    length = pickle.pack("i", len(cmd))
    os.write(fifo_c2s, length)
    os.write(fifo_c2s, cmd)

    length = os.read(fifo_s2c, length_size)
    length = pickle.unpack("i", length)[0]
    result = os.read(fifo_s2c, length)
    result = pickle.loads(result)
    return result


def sane_init():
    return SaneAction(abstract.sane_init).wait()


def sane_exit():
    return SaneAction(abstract.sane_exit).wait()


class ScannerOption(object):
    _abstract_opt = None

    idx = 0
    name = ""
    title = ""
    desc = ""
    val_type = SaneValueType(SaneValueType.INT)
    unit = SaneUnit(SaneUnit.NONE)
    size = 4
    capabilities = SaneCapabilities(SaneCapabilities.NONE)

    constraint_type = SaneConstraintType(SaneConstraintType.NONE)
    constraint = None

    def __init__(self, scanner, idx):
        self.idx = idx
        self._abstract_opt = abstract.ScannerOption(scanner._abstract_dev, idx)

    @staticmethod
    def build_from_abstract(scanner, abstract_opt):
        opt = ScannerOption(scanner, abstract_opt.idx)
        opt._abstract_opt = abstract_opt
        opt.name = abstract_opt.name
        opt.title = abstract_opt.title
        opt.desc = abstract_opt.desc
        opt.val_type = abstract_opt.val_type
        opt.unit = abstract_opt.unit
        opt.size = abstract_opt.size
        opt.capabilities = abstract_opt.capabilities
        opt.constraint_type = abstract_opt.constraint_type
        opt.constraint = abstract_opt.constraint
        return opt

    def _get_value(self):
        # TODO
        return

    def _set_value(self, new_value):
        # TODO
        return

    value = property(_get_value, _set_value)


class Scan(object):
    def __init__(self, real_scan):
        self._scan = real_scan

    def read(self):
        # TODO
        return

    def _get_available_lines(self):
        # TODO
        return

    available_lines = property(_get_available_lines)

    def _get_expected_size(self):
        # TODO
        return

    expected_size = property(_get_expected_size)

    def get_image(self, start_line, end_line):
        # TODO
        return

    def cancel(self):
        # TODO
        return


class ScanSession(object):
    def __init__(self, scanner, multiple=False):
        # TODO
        pass

    def __get_img(self):
        # TODO
        pass

    images = property(__get_img)

    def read(self):
        """
        Deprecated
        """
        # TODO
        pass

    def get_nb_img(self):
        """
        Deprecated
        """
        # TODO
        pass

    def get_img(self, idx=0):
        """
        Deprecated
        """
        # TODO
        pass


class Scanner(object):
    def __init__(self, name=None,
                 vendor="Unknown", model="Unknown", dev_type="Unknown",
                 abstract_dev=None):
        if abstract_dev is None:
            abstract_dev = abstract.Scanner(name)
        else:
            vendor = abstract_dev.vendor
            model = abstract_dev.model
            dev_type = abstract_dev.dev_type
        self._abstract_dev = abstract_dev
        self.name = name
        self.vendor = vendor
        self.model = model
        self.dev_type = dev_type

    @staticmethod
    def build_from_abstract(abstract_dev):
        return Scanner(abstract_dev.name, abstract_dev=abstract_dev)

    def _get_options(self):
        options = remote_do("get_options", self.name)
        return {
            x.name: ScannerOption.build_from_abstract(self, x)
            for x in options.values()
        }

    options = property(_get_options)

    def scan(self, multiple=False):
        return ScanSession(self, multiple)

    def __str__(self):
        return ("Scanner '%s' (%s, %s, %s)"
                % (self.name, self.vendor, self.model, self.dev_type))


def get_devices(local_only=False):
    return [
        Scanner.build_from_abstract(x)
        for x in remote_do('get_devices', local_only)
    ]
