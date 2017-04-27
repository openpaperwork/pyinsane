import logging
import os
import pickle
import shutil
import struct
import sys
import tempfile

import PIL.Image

# import basic elements directly, so the caller
# doesn't have to import rawapi if they need them.
from . import abstract
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
    'init',
    'exit',
    'Scanner',
    'ScannerOption',
    'get_devices',
]


logger = logging.getLogger(__name__)

length_size = None
fifo_s2c = None
fifo_c2s = None
pipe_path_c2s = None
pipe_path_s2c = None
pipe_dirpath = None


def remote_do(command, *args, **kwargs):
    global length_size
    global fifo_s2c
    global fifo_c2s
    global pipe_path_c2s
    global pipe_path_s2c

    cmd = {
        'command': command,
        'args': args,
        'kwargs': kwargs,
    }

    cmd = pickle.dumps(cmd)
    length = struct.pack("i", len(cmd))
    os.write(fifo_c2s, length)
    os.write(fifo_c2s, cmd)

    length = os.read(fifo_s2c, length_size)
    length = struct.unpack("i", length)[0]
    result = os.read(fifo_s2c, length)
    assert(len(result) == length)
    result = pickle.loads(result)
    if 'exception' in result:
        exc_class = eval(result['exception'])
        raise exc_class(*result['exception_args'])

    if command == 'exit':
        os.close(fifo_c2s)
        os.close(fifo_s2c)
        os.unlink(pipe_path_c2s)
        os.unlink(pipe_path_s2c)
        shutil.rmtree(pipe_dirpath)
        return

    return result['out']


def init():
    global length_size
    global fifo_s2c
    global fifo_c2s
    global pipe_path_c2s
    global pipe_path_s2c
    global pipe_dirpath

    start_daemon = os.getenv('PYINSANE_DAEMON', '1')
    start_daemon = True if int(start_daemon) > 0 else False

    if not start_daemon:
        return

    logger.info("Starting Pyinsane subprocess")

    pipe_dirpath = tempfile.mkdtemp(prefix="pyinsane_")
    pipe_path_c2s = os.path.join(pipe_dirpath, "pipe_c2s")
    os.mkfifo(pipe_path_c2s)
    pipe_path_s2c = os.path.join(pipe_dirpath, "pipe_s2c")
    os.mkfifo(pipe_path_s2c)

    logger.info("Pyinsane pipes: {} | {}".format(pipe_path_c2s, pipe_path_s2c))

    if os.fork() == 0:
        # prevent the daemon from starting itself (due to the way
        # imports behave)
        os.putenv('PYINSANE_DAEMON', '0')
        os.execlp(
            sys.executable, sys.executable,
            "-m", "pyinsane2.sane.daemon",
            pipe_dirpath,
            pipe_path_c2s, pipe_path_s2c
        )

    length_size = len(struct.pack("i", 0))
    fifo_c2s = os.open(pipe_path_c2s, os.O_WRONLY)
    fifo_s2c = os.open(pipe_path_s2c, os.O_RDONLY)

    logger.info("Connected to Pyinsane subprocess")


def exit():
    remote_do('exit')


class ScannerOption(object):
    _abstract_opt = None
    _scanner_name = None

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
        opt._scanner_name = scanner.name
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
        return remote_do('get_option_value', self._scanner_name, self.name)

    def _set_value(self, new_value):
        remote_do('set_option_value', self._scanner_name, self.name, new_value)

    value = property(_get_value, _set_value)


class Scan(object):
    def __init__(self, scanner_name):
        self._scanner_name = scanner_name

    def read(self):
        return remote_do('scan_read', self._scanner_name)

    def _get_available_lines(self):
        return remote_do('scan_get_available_lines', self._scanner_name)

    available_lines = property(_get_available_lines)

    def _get_expected_size(self):
        return remote_do('scan_get_expected_size', self._scanner_name)

    expected_size = property(_get_expected_size)

    def get_image(self, start_line=0, end_line=-1):
        img = remote_do(
            'scan_get_image', self._scanner_name, start_line, end_line
        )
        return PIL.Image.frombytes(*img)

    def cancel(self):
        return remote_do('scan_cancel', self._scanner_name)


class ScanSession(object):
    def __init__(self, scanner, multiple=False):
        self._scanner = scanner.name
        self._remote_session = remote_do('scan', scanner.name, multiple)
        self.scan = Scan(scanner.name)

    def __get_imgs(self):
        imgs = remote_do('get_images', self._scanner)
        imgs = [PIL.Image.frombytes(*img) for img in imgs]
        return imgs

    images = property(__get_imgs)

    def read(self):
        """
        Deprecated
        """
        self.scan.read()

    def get_nb_img(self):
        """
        Deprecated
        """
        return len(self.images)

    def get_img(self, idx=0):
        """
        Deprecated
        """
        return self.images[idx]


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
        self.nice_name = name  # for WIA compatibility
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
        return ("'%s' (%s, %s, %s)"
                % (self.name, self.vendor, self.model, self.dev_type))


def get_devices(local_only=False):
    return [
        Scanner.build_from_abstract(x)
        for x in remote_do('get_devices', local_only)
    ]
