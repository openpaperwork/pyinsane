import Image

import rawapi

__all__ = [
    'Scanner',
    'ScannerOption',
    'get_devices',
]

_sane_instances = 0

def _sane_init():
    global _sane_instances
    if _sane_instances == 0:
        rawapi.sane_init()
    _sane_instances += 1


def _sane_exit():
    global _sane_instances
    _sane_instances -= 1
    if _sane_instances == 0:
        rawapi.sane_exit()


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
    def build_from_rawapi(scanner, opt_idx, opt_raw):
        opt = ScannerOption(scanner, opt_idx)
        opt.name = opt_raw.name
        opt.title = opt_raw.title
        opt.desc = opt_raw.desc # TODO : multi-line
        opt.val_type = rawapi.SaneValueType(opt_raw.type)
        opt.unit = rawapi.SaneUnit(opt_raw.unit)
        opt.size = opt_raw.size
        opt.capabilities = rawapi.SaneCapabilities(opt_raw.cap)
        opt.constraint_type = rawapi.SaneConstraintType(opt_raw.constraint_type)
        opt.constraint = opt.constraint_type.get_pyobj_constraint(
                opt_raw.constraint)
        return opt

    def __get_value(self):
        self.__scanner._open()
        return rawapi.sane_get_option_value(self.__scanner._handle, self.idx)

    def __set_value(self, new_value):
        self.__scanner._open()
        rawapi.sane_set_option_value(self.__scanner._handle, self.idx, new_value)

    value = property(__get_value, __set_value)


class ImgUtil(object):
    @staticmethod
    def __raw_1_to_img(raw_packed, mode, pixels_per_line):
        """
        Sane uses 1 bit for each color, whereas PIL uses 1 byte (0x00 or 0xFF)
        """
        raw_unpacked = b""
        for byte in raw_packed:
            byte = ord(byte)
            for bit in range(7, -1, -1):
                if ((byte & (1<<bit)) > 0):
                    raw_unpacked.append(chr(0xFF))
                else:
                    raw_unpacked.append(chr(0x00))
        assert(len(raw_packed) * 8 == len(raw_packed))
        return ImgUtil.__raw_8_to_img(raw_unpacked, mode, pixels_per_line)

    @staticmethod
    def __raw_8_to_img(raw, mode, pixels_per_line):
        """
        Each color is on one byte --> Each pixel takes 3 bytes in RGB
        """
        nb_colors = {
            "L" : 1,
            "RGB" : 3,
        }[mode]
        width = pixels_per_line
        height = (len(raw) / (width * nb_colors)) / nb_colors
        return Image.frombuffer(mode, (width, height), raw, "raw", mode, 0, 1)

    @staticmethod
    def __raw_16_to_img(raw, mode, pixels_per_line):
        """
        Each color is on 2 bytes --> Each pixel takes 6 bytes in RGB
        """
        nb_colors = {
            "L" : 2,
            "RGB" : 6,
        }[mode]
        width = pixels_per_line
        height = (len(raw) / (width*nb_colors)) / nb_colors
        return Image.frombuffer(mode, (width, height), raw, "raw", mode, 0, 1)

    @staticmethod
    def raw_to_img(raw, parameters):
        mode = rawapi.SaneFrame(parameters.format).get_pil_format()

        return {
            1 : ImgUtil.__raw_1_to_img,
            8 : ImgUtil.__raw_8_to_img,
            16 : ImgUtil.__raw_16_to_img,
        }[parameters.depth](raw, mode, parameters.pixels_per_line)


class SimpleScanSession(object):
    def __init__(self, scanner):
        self.__scanner = scanner

        self.__is_scanning = True
        self.__raw_output = b""
        self.__img = None

        self.__scanner._open()
        rawapi.sane_start(self.__scanner._handle)
        try:
            self.__parameters = \
                    rawapi.sane_get_parameters(self.__scanner._handle)
        except Exception, exc:
            rawapi.sane_cancel(self.__scanner._handle)
            raise exc

    def read(self):
        try:
            self.__raw_output += rawapi.sane_read(self.__scanner._handle)
        except EOFError, exc:
            rawapi.sane_cancel(self.__scanner._handle)
            self.__is_scanning = False
            self.__img = ImgUtil.raw_to_img(self.__raw_output,
                                             self.__parameters)
            raise exc

    def get_nb_img(self):
        if self.__is_scanning:
            return 0
        return 1

    def get_img(self, number=0):
        if number != 0:
            raise IndexError("No such image available")
        if self.__is_scanning:
            try:
                while True:
                    self.read()
            except EOFError, exc:
                pass
        return self.__img

    def __del__(self):
        if self.__is_scanning:
            rawapi.sane_cancel(self.__scanner._handle)


class MultiScanSession(object):
    def __init__(self, scanner):
        self.__scanner = scanner

        self.__is_scanning = True
        self.__raw_output = b""
        self.__imgs = []

        self.__scanner._open()
        self.__must_clean = False
        self.__is_scanning = False

    def read(self):
        try:
            if not self.__is_scanning:
                rawapi.sane_start(self.__scanner._handle)
                self.__is_scanning = True
                self.__must_clean = True
                self.__parameters = \
                        rawapi.sane_get_parameters(self.__scanner._handle)
                return
            try:
                self.__raw_output += rawapi.sane_read(self.__scanner._handle)
            except EOFError, exc:
                self.__imgs.append(ImgUtil.raw_to_img(self.__raw_output,
                                                       self.__parameters))
                self.__is_scanning = False
        except StopIteration, exc:
            rawapi.sane_cancel(self.__scanner._handle)
            self.__must_clean = False
            self.__is_scanning = False
            raise EOFError()

    def get_nb_img(self):
        return len(self.__imgs)

    def get_img(self, number):
        if number >= len(self.__imgs) and self.__must_clean:
            try:
                while True:
                    self.read()
            except EOFError, exc:
                pass
        return self.__imgs[number]

    def __del__(self):
        if self.__must_clean:
            rawapi.sane_cancel(self.__scanner._handle)


class Scanner(object):
    def __init__(self, name, vendor="Unknown", model="Unknown",
                 dev_type="Unknown"):
        self.name = name
        self.vendor = vendor
        self.model = model
        self.dev_type = dev_type
        self._handle = None
        self.__options = None  # { "name" : ScannerOption }

    @staticmethod
    def build_from_rawapi(sane_device):
        return Scanner(sane_device.name, sane_device.vendor, sane_device.model,
                       sane_device.type)

    def _open(self):
        if self._handle != None:
            return
        _sane_init()
        self._handle = rawapi.sane_open(self.name)

    def __del__(self):
        if self._handle == None:
            return
        rawapi.sane_close(self._handle)
        _sane_exit()

    def __load_options(self):
        if self.__options != None:
            return
        self._open()
        nb_options = rawapi.sane_get_option_value(self._handle, 0)
        self.__options = {}
        for opt_idx in range(1, nb_options):
            opt_desc = rawapi.sane_get_option_descriptor(self._handle, opt_idx)
            if not rawapi.SaneValueType(opt_desc.type).can_getset_opt():
                continue
            opt = ScannerOption.build_from_rawapi(self, opt_idx, opt_desc)
            self.__options[opt.name] = opt

    def __get_options(self):
        self.__load_options()
        return self.__options

    options = property(__get_options)

    def scan(self, multiple=False):
        if (not multiple) or self.options['source'].value != "ADF":
            # XXX(Jflesch): We cannot use MultiScanSession() with something
            # else than an ADF. If we try, we will never get
            # SANE_STATUS_NO_DOCS from sane_start()/sane_read() and we will
            # loop forever
            return SimpleScanSession(self)
        else:
            return MultiScanSession(self)

    def __str__(self):
        return ("Scanner '%s' (%s, %s, %s)"
                % (self.name, self.vendor, self.model, self.dev_type))


def get_devices():
    _sane_init()
    try:
        return [Scanner.build_from_rawapi(device)
                for device in rawapi.sane_get_devices()]
    finally:
        _sane_exit()

