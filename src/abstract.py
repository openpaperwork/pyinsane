from PIL import Image

import rawapi

# import basic elements directly, so the caller
# doesn't have to import rawapi if they need them.
from rawapi import SaneCapabilities
from rawapi import SaneConstraint
from rawapi import SaneConstraintType
from rawapi import SaneException
from rawapi import SaneStatus
from rawapi import SaneUnit
from rawapi import SaneValueType


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

# We use huge buffers to spend the maximum amount of time in non-Python code
SANE_READ_BUFSIZE = 512*1024

sane_is_init = 0
sane_version = None

# XXX(Jflesch): Never open more than one handle at the same time.
# Some Sane backends don't support it. For instance, I have 2 HP scanners, and
# if I try to access both from the same process, I get I/O errors.
sane_dev_handle = ("", None)


def sane_init():
    global sane_is_init
    global sane_version
    if sane_is_init <= 0:
        sane_version = rawapi.sane_init()
    sane_is_init += 1
    return sane_version


def sane_exit():
    global sane_is_init
    sane_is_init -= 1
    if sane_is_init <= 0:
        rawapi.sane_exit()


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
        if opt.name is not None:
            opt.name = opt.name.decode('utf-8')
        opt.title = opt_raw.title
        if opt.title is not None:
            opt.title = opt.title.decode('utf-8')
        opt.desc = opt_raw.desc
        if opt.desc is not None:
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
        return rawapi.sane_get_option_value(sane_dev_handle[1], self.idx)

    def _set_value(self, new_value):
        self.__scanner._open()
        rawapi.sane_set_option_value(sane_dev_handle[1], self.idx, new_value)

    value = property(_get_value, _set_value)


class ImgUtil(object):
    COLOR_BYTES = {
        1 : {  # we expanded the bits to bytes on-the-fly
            "L" : 1,
            "RGB" : 3,
        },
        8 : {
            "L" : 1,
            "RGB" : 3,
        },
        16 : {
            "L" : 2,
            "RGB" : 6
        }
    }

    @staticmethod
    def unpack_1_to_8(raw_packed):
        # Each color is on one bit. We unpack immediately so each color
        # is on one byte.
        # We do this so we can split the image line by line more easily
        raw_unpacked = b""
        for byte in raw_packed:
            byte = ord(byte)
            for bit in range(7, -1, -1):
                if ((byte & (1<<bit)) > 0):
                    raw_unpacked += (chr(0x00))
                else:
                    raw_unpacked += (chr(0xFF))
        assert(len(raw_packed) * 8 == len(raw_unpacked))
        return raw_unpacked

    @staticmethod
    def raw_to_img(raw, parameters):
        mode = rawapi.SaneFrame(parameters.format).get_pil_format()
        color_bytes = ImgUtil.COLOR_BYTES[parameters.depth][mode]
        width = parameters.pixels_per_line
        height = (len(raw) / (width * color_bytes))
        return Image.frombuffer(mode, (int(width), int(height)), raw, "raw", mode, 0, 1)


class Scan(object):
    def __init__(self, scanner):
        self.scanner = scanner
        self.__session = None
        self.__raw_lines = []

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
        try:
            read = rawapi.sane_read(sane_dev_handle[1], SANE_READ_BUFSIZE)
        except EOFError:
            line_size = self.parameters.bytes_per_line
            for line in self.__raw_lines:
                if len(line) != line_size:
                    print ("Pyinsane: Warning: Unexpected line size: %d instead of %d" %
                           (len(line), line_size))
            raw = (b'').join(self.__raw_lines)
            self.__session.images.append(ImgUtil.raw_to_img(
                    raw, self.parameters))
            raise

        if self.parameters.depth == 1:
            read = ImgUtil.unpack_1_to_8(read)

        # cut what we just read, line by line

        line_size = self.parameters.bytes_per_line

        if (len(self.__raw_lines) > 0):
            cut = line_size - len(self.__raw_lines[-1])
            self.__raw_lines[-1] += read[:cut]
            read = read[cut:]

        for _ in xrange(0, len(read), line_size):
            self.__raw_lines.append(read[:line_size])
            read = read[line_size:]

        if len(read) > 0:
            self.__raw_lines.append(read)

    def _get_available_lines(self):
        line_size = self.parameters.bytes_per_line
        r = len(self.__raw_lines)
        if (r > 0 and len(self.__raw_lines[-1]) < line_size):
            r -= 1;
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

    def get_image(self, start_line, end_line):
        assert(end_line > start_line)
        lines = self.__raw_lines[start_line:end_line]
        lines = b"".join(lines)
        return ImgUtil.raw_to_img(lines, self.parameters)

    def _cancel(self):
        rawapi.sane_cancel(sane_dev_handle[1])

    def _del(self):
        # inheriting classes must call self.cancel() if required
        pass

    def __del__(self):
        self._del()


class SingleScan(Scan):
    def __init__(self, scanner):
        Scan.__init__(self, scanner)

        self.is_scanning = True
        self.__raw_lines = []

        self._init()

    def read(self):
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

    def _del(self):
        if self.is_scanning:
            self.is_scanning = False
            self._cancel()
        Scan._del(self)


class MultipleScan(Scan):
    def __init__(self, scanner):
        Scan.__init__(self, scanner)

        self.is_scanning = False
        self.__raw_lines = []

    def read(self):
        if not self.is_scanning:
            self.is_scanning = True
            self._init()

        try:
            Scan.read(self)
        except StopIteration:
            self._cancel()
            self.is_scanning = False
            raise

    def cancel(self):
        if self.is_scanning:
            self._cancel()
            self.is_scanning = False

    def _del(self):
        if self.is_scanning:
            self.is_scanning = False
            self._cancel()
        Scan._del(self)


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

    def _del(self):
        del(self.scan)

    def __del__(self):
        self._del()


class Scanner(object):
    def __init__(self, name, vendor="Unknown", model="Unknown",
                 dev_type="Unknown"):
        self.name = name.decode('utf-8')
        self.vendor = vendor.decode('utf-8')
        self.model = model.decode('utf-8')
        self.dev_type = dev_type.decode('utf-8')
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
        if handle == None:
            return
        rawapi.sane_close(handle)
        sane_exit()
        sane_dev_handle = ("", None)

    def _del(self):
        self._force_close()

    def __del__(self):
        self._del()

    def __load_options(self):
        if self.__options != None:
            return
        self._open()
        nb_options = rawapi.sane_get_option_value(sane_dev_handle[1], 0)
        self.__options = {}
        for opt_idx in range(1, nb_options):
            opt_desc = rawapi.sane_get_option_descriptor(sane_dev_handle[1], opt_idx)
            if not SaneValueType(opt_desc.type).can_getset_opt():
                continue
            opt = ScannerOption.build_from_rawapi(self, opt_idx, opt_desc)
            self.__options[opt.name] = opt

    def _get_options(self):
        self.__load_options()
        return self.__options

    options = property(_get_options)

    def scan(self, multiple=False):
        if (not multiple
            or (not "ADF" in self.options['source'].value
                and not "Feeder" in self.options['source'].value)):
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

