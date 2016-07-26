import logging
import os
import pickle
import tempfile

# import basic elements directly, so the caller
# doesn't have to import rawapi if they need them.
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


def remote_do(command):
    global length_size
    global fifo_s2c
    global fifo_c2s

    cmd = pickle.dumps(cmd)
    length = pickle.pack("i", len(cmd))
    os.write(fifo_c2s, length)
    os.write(fifo_c2s, cmd)

    length = os.read(fifo_s2c, length_size)
    length = pickle.unpack("i", length)[0]
    result = os.read(fifo_s2c, length)
    result = pickle.loads(result)
    return result


class Scan(object):
    def __init__(self, scanner):
        # TODO
        self.scanner = scanner
        self.is_scanning = True

    def read(self):
        # TODO
        pass

    def _get_available_lines(self):
        # TODO
        pass

    available_lines = property(_get_available_lines)

    def _get_expected_size(self):
        # TODO
        pass

    expected_size = property(_get_expected_size)

    def get_image(self, start_line, end_line):
        # TODO
        pass

    def cancel(self):
        # TODO
        pass


class ScanSession(object):
    def __init__(self, scan):
        self.scan = scan
        # TODO
        return

    def get_nb_img(self):
        # TODO
        return

    def get_img(self, idx=0):
        # TODO
        return


class Scanner(object):
    def __init__(self, name, vendor="Unknown", model="Unknown",
                 dev_type="Unknown"):
        # TODO
        return

    def _get_options(self):
        # TODO
        return

    options = property(_get_options)

    def scan(self, multiple=False):
        # TODO
        return

    def __str__(self):
        # TODO
        return


def get_devices(local_only=False):
    # TODO
    return
