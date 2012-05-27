import ctypes

import rawapi

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
        return opt

    def __get_value(self):
        self.__scanner._open()
        return rawapi.sane_get_option_value(self.__scanner._handle, self.idx)

    def __set_value(self, new_value):
        self.__scanner._open()
        rawapi.sane_set_option_value(self.__scanner._handle, self.idx, new_value)

    value = property(__get_value, __set_value)


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

    def close(self):
        if self._handle == None:
            return
        rawapi.sane_close(self._handle)
        _sane_exit()

    def __del__(self):
        self.close()

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

