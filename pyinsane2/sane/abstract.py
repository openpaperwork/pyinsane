import sys

from PIL import Image

from . import rawapi
from .. import util

# import basic elements directly, so the caller
# doesn't have to import rawapi if they need them.
from .rawapi import SaneCapabilities
from .rawapi import SaneConstraint
from .rawapi import SaneConstraintType
from .rawapi import SaneException
from .rawapi import SaneStatus
from .rawapi import SaneUnit
from .rawapi import SaneValueType
from .rawapi import sane_init, sane_exit


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

# We use huge buffers to spend the maximum amount of time in non-Python code
SANE_READ_BUFSIZE = 512 * 1024

# XXX(Jflesch): Never open more than one handle at the same time.
# Some Sane backends don't support it. For instance, I have 2 HP scanners, and
# if I try to access both from the same process, I get I/O errors.
sane_dev_handle = ("", None)


def init():
    sane_init()


def exit():
    sane_exit()


class ScannerOption(object):
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
        self.__scanner = scanner
        self.idx = idx

    @staticmethod
    def build_from_rawapi(scanner, opt_idx, opt_raw):
        opt = ScannerOption(scanner, opt_idx)
        opt.name = opt_raw.name
        if opt.name is not None and hasattr(opt.name, "decode"):
            opt.name = opt.name.decode('utf-8')
        opt.title = opt_raw.title
        if opt.title is not None and hasattr(opt.title, "decode"):
            opt.title = opt.title.decode('utf-8')
        opt.desc = opt_raw.desc
        if opt.desc is not None and hasattr(opt.desc, "decode"):
            opt.desc = opt.desc.decode('utf-8')  # TODO : multi-line
        opt.val_type = SaneValueType(opt_raw.type)
        opt.unit = SaneUnit(opt_raw.unit)
        opt.size = opt_raw.size
        opt.capabilities = SaneCapabilities(opt_raw.cap)
        opt.constraint_type = SaneConstraintType(opt_raw.constraint_type)
        opt.constraint = opt.constraint_type.get_pyobj_constraint(
            opt_raw.constraint)
        return opt

    def _get_value(self):
        self.__scanner._open()
        val = rawapi.sane_get_option_value(sane_dev_handle[1], self.idx)
        if not self.capabilities.is_active():
            # XXX(Jflesch): if the option is not active, some backends still
            # return a value, some don't and return an error instead.
            # To avoid mistakes in user programs, we make the behavior here
            # consistent and always raise an exception.
            raise SaneException("Option '%s' is not active" % self.name)
        if hasattr(val, 'decode'):
            val = val.decode("utf-8")
        return val

    def _set_value(self, new_value):
        self.__scanner._open()
        rawapi.sane_set_option_value(sane_dev_handle[1], self.idx, new_value)

    value = property(_get_value, _set_value)


class ImgUtil(object):
    COLOR_BYTES = {
        1: {  # we expanded the bits to bytes on-the-fly
            "L": 1,
            "RGB": 3,
        },
        8: {
            "L": 1,
            "RGB": 3,
        },
        16: {
            "L": 2,
            "RGB": 6
        }
    }

    @staticmethod
    def unpack_1_to_8(whole_raw_packed, pixels_per_line, bytes_per_line):
        # Each color is on one bit. We unpack immediately so each color
        # is on one byte.
        # We must take care of one thing : the last byte of each line
        # contains unused bits. They must be dropped
        whole_raw_unpacked = b""

        if sys.version_info < (3, ):
            positive_bit = chr(0x00)
            negative_bit = chr(0xFF)
        else:
            positive_bit = bytes([0x00])
            negative_bit = bytes([0xFF])

        for chunk in range(0, len(whole_raw_packed), bytes_per_line):
            raw_packed = whole_raw_packed[:bytes_per_line]
            whole_raw_packed = whole_raw_packed[bytes_per_line:]
            raw_unpacked = b""

            for byte in raw_packed:
                if type(byte) == str:
                    byte = ord(byte)
                for bit in range(7, -1, -1):
                    if ((byte & (1 << bit)) > 0):
                        raw_unpacked += positive_bit
                    else:
                        raw_unpacked += negative_bit
            assert(len(raw_packed) * 8 == len(raw_unpacked))

            raw_unpacked = raw_unpacked[:pixels_per_line]
            whole_raw_unpacked += raw_unpacked

        return whole_raw_unpacked

    @staticmethod
    def raw_to_img(raw, parameters):
        mode = rawapi.SaneFrame(parameters.format).get_pil_format()
        # color_bytes = ImgUtil.COLOR_BYTES[parameters.depth][mode]
        width = parameters.pixels_per_line
        height = (len(raw) / parameters.bytes_per_line)
        if parameters.depth == 1:
            raw = ImgUtil.unpack_1_to_8(raw, width,
                                        parameters.bytes_per_line)
        return Image.frombuffer(mode, (int(width), int(height)), raw, "raw",
                                mode, 0, 1)


class Scan(object):
    def __init__(self, scanner):
        self.scanner = scanner
        self.__session = None
        self.__raw_lines = []
        self.__img_finished = False

    def _set_session(self, session):
        self.__session = session

    def _init(self):
        self.scanner._open()
        rawapi.sane_start(sane_dev_handle[1])
        try:
            self.parameters = \
                rawapi.sane_get_parameters(sane_dev_handle[1])
        except Exception:
            rawapi.sane_cancel(sane_dev_handle[1])
            raise

    def read(self):
        if self.__img_finished:
            # start a new one
            self.__raw_lines = []
            self.__img_finished = False

        try:
            read = rawapi.sane_read(sane_dev_handle[1], SANE_READ_BUFSIZE)
        except EOFError:
            line_size = self.parameters.bytes_per_line
            for line in self.__raw_lines:
                if len(line) != line_size:
                    print(("Pyinsane: Warning: Unexpected line size: %d"
                           " instead of %d") % (len(line), line_size))
            raw = (b'').join(self.__raw_lines)
            # don't do purge the lines here. wait for the next call to read()
            # because, in the meantime, the caller might use get_image()
            self.__img_finished = True
            self.__session.images.append(ImgUtil.raw_to_img(
                raw, self.parameters))
            raise

        # cut what we just read, line by line

        line_size = self.parameters.bytes_per_line

        if (len(self.__raw_lines) > 0):
            cut = line_size - len(self.__raw_lines[-1])
            self.__raw_lines[-1] += read[:cut]
            read = read[cut:]

        range_func = range
        if sys.version_info.major < 3:
            range_func = xrange  # noqa (non-valid in Python 3)

        for _ in range_func(0, len(read), line_size):
            self.__raw_lines.append(read[:line_size])
            read = read[line_size:]

        if len(read) > 0:
            self.__raw_lines.append(read)

    def _get_available_lines(self):
        line_size = self.parameters.bytes_per_line
        r = len(self.__raw_lines)
        if (r > 0 and len(self.__raw_lines[-1]) < line_size):
            r -= 1
        return (0, r)

    available_lines = property(_get_available_lines)

    def _get_expected_size(self):
        """
        Returns the expected size of the image (tuple: (w, h)).
        Note that (afaik) Sane makes it mandatory for the driver
        to indicates the length of the lines. However, it is not mandatory
        for the driver to indicates the expected number of lines (for
        instance, hand-held scanners can't know it before the end of
        the scan). In that case, the expected height of the image
        will -1 here.
        """
        width = self.parameters.pixels_per_line
        height = self.parameters.lines
        return (width, height)

    expected_size = property(_get_expected_size)

    def get_image(self, start_line=0, end_line=-1):
        if end_line < 0:
            end_line = len(self.__raw_lines)
        assert(end_line > start_line)
        lines = self.__raw_lines[start_line:end_line]
        lines = b"".join(lines)
        return ImgUtil.raw_to_img(lines, self.parameters)

    def _cancel(self):
        rawapi.sane_cancel(sane_dev_handle[1])


class SingleScan(Scan):
    def __init__(self, scanner):
        Scan.__init__(self, scanner)

        self.is_scanning = True

        self._init()

    def read(self):
        if not self.is_scanning:
            raise StopIteration()

        try:
            Scan.read(self)
        except (EOFError, StopIteration):
            self._cancel()
            self.is_scanning = False
            raise

    def cancel(self):
        if self.is_scanning:
            self._cancel()
            self.is_scanning = False


class MultipleScan(Scan):
    def __init__(self, scanner):
        Scan.__init__(self, scanner)
        self.is_scanning = False
        self.is_finished = False
        self.must_request_next_frame = False
        self._init()

    def read(self):
        if self.is_finished:
            raise StopIteration()

        if not self.is_scanning:
            self.is_scanning = True
            self.must_request_next_frame = False

        if self.must_request_next_frame:
            try:
                rawapi.sane_start(sane_dev_handle[1])
            except StopIteration:
                self._cancel()
                self.is_finished = True
                self.is_scanning = False
                raise
            self.must_request_next_frame = False

        try:
            Scan.read(self)
        except EOFError:
            self.must_request_next_frame = True
            raise
        except StopIteration:
            self._cancel()
            self.is_finished = True
            self.is_scanning = False
            # signal the last page first
            raise EOFError()

    def cancel(self):
        if self.is_scanning:
            self._cancel()
            self.is_finished = True
            self.is_scanning = False


class ScanSession(object):
    def __init__(self, scan):
        self.images = []
        self.scan = scan
        self.scan._set_session(self)

    def read(self):
        """
        Deprecated. Use scan_session.scan.read()
        """
        return self.scan.read()

    def get_nb_img(self):
        """
        Deprecated. Use len(scan_session.images) directly
        """
        return len(self.images)

    def get_img(self, idx=0):
        """
        Deprecated. Use scan_session.images[idx] directly
        """
        return self.images[idx]


class Scanner(object):
    def __init__(self, name, vendor="Unknown", model="Unknown",
                 dev_type="Unknown"):
        if hasattr(name, "decode"):
            name = name.decode('utf-8')
        if hasattr(vendor, "decode"):
            vendor = vendor.decode('utf-8')
        if hasattr(model, "decode"):
            model = model.decode('utf-8')
        if hasattr(dev_type, "decode"):
            dev_type = dev_type.decode('utf-8')

        self.name = name
        self.vendor = vendor
        self.model = model
        self.dev_type = dev_type
        self.__options = None  # { "name" : ScannerOption }

    @staticmethod
    def build_from_rawapi(sane_device):
        return Scanner(sane_device.name, sane_device.vendor, sane_device.model,
                       sane_device.type)

    def _open(self):
        global sane_dev_handle
        (devid, handle) = sane_dev_handle
        if devid == self.name:
            return
        self._force_close()
        sane_init()
        handle = rawapi.sane_open(self.name)
        sane_dev_handle = (self.name, handle)

    def _force_close(self):
        global sane_dev_handle
        (devid, handle) = sane_dev_handle
        if handle is None:
            return
        rawapi.sane_close(handle)
        sane_exit()
        sane_dev_handle = ("", None)

    def __load_options(self):
        if self.__options is not None:
            return
        self._open()
        nb_options = rawapi.sane_get_option_value(sane_dev_handle[1], 0)
        self.__options = {}
        for opt_idx in range(1, nb_options):
            opt_desc = rawapi.sane_get_option_descriptor(
                sane_dev_handle[1], opt_idx)
            if not SaneValueType(opt_desc.type).can_getset_opt():
                continue
            opt = ScannerOption.build_from_rawapi(self, opt_idx, opt_desc)
            self.__options[opt.name] = opt

        # WORKAROUND(Jflesch):
        # Lexmark MFP CX510de: option 'resolution' has been mistakenly named
        # 'scan-resolution'
        if ('scan-resolution' in self.__options and
                'resolution' not in self.__options):
            self.__options['resolution'] = util.AliasOption(
                'resolution', ['scan-resolution'], self.__options
            )

        # WORKAROUND(Jflesch):
        # Samsung M288x: option 'source' is actually called 'doc-source'
        if ('doc-source' in self.__options and
                'source' not in self.__options):
            self.__options['source'] = util.AliasOption(
                'source', ['doc-source'], self.__options
            )

    def _get_options(self):
        self.__load_options()
        return self.__options

    options = property(_get_options)

    def scan(self, multiple=False):
        if (not ('source' in self.options and
                 self.options['source'].capabilities.is_active())):
            value = ""
        else:
            value = self.options['source'].value
        if hasattr(value, 'decode'):
            value = value.decode('utf-8')
        if (not multiple or
                ("adf" not in value.lower() and
                 "feeder" not in value.lower())):
            # XXX(Jflesch): We cannot use MultipleScan() with something
            # else than an ADF. If we try, we will never get
            # SANE_STATUS_NO_DOCS from sane_start()/sane_read() and we will
            # loop forever
            scan = SingleScan(self)
        else:
            scan = MultipleScan(self)
        return ScanSession(scan)

    def __str__(self):
        return ("Scanner '%s' (%s, %s, %s)"
                % (self.name, self.vendor, self.model, self.dev_type))


def get_devices(local_only=False):
    sane_init()
    try:
        return [Scanner.build_from_rawapi(device)
                for device in rawapi.sane_get_devices(local_only)]
    finally:
        sane_exit()
