import ctypes


SANE_LIB = ctypes.cdll.LoadLibrary("libsane.so.1")


class SaneEnum(object):
    VALUE_TO_STR = {}

    def __init__(self, value):
        self.__value = value

    def __int__(self):
        return self.__value

    def __cmp__(self, other):
        return cmp(self.__value, other.__value)

    def __str__(self):
        if not self.__value in self.VALUE_TO_STR:
            txt = "Unknown value (%d)" % (self.__value)
        else:
            txt = "%s (%d)" % (self.VALUE_TO_STR[self.__value], self.__value)
        return "%s : %s" % (type(self), txt)


class SaneFlags(object):
    FLAG_TO_STR = {}

    def __init__(self, flags=0):
        self.__flags = flags

    def __int__(self):
        return self.__flags

    def __add__(self, new_flag):
        return (self.__flags | new_flag)

    def __sub__(self, old_flag):
        return (self.flags & ~(old_flag))

    def __contains__(self, flag):
        return ((self.flags & flag) == flag)

    def __hex__(self):
        return hex(self.__flags)

    def __str__(self):
        txt = "%s :" % (type(self))
        txt += "["
        for flag in self.FLAG_TO_STR:
            if flag in self:
                txt += " %s," % (self.FLAG_TO_STR[flag])
        txt += "]"
        return txt


class SaneVersion(object):
    SANE_CURRENT_MAJOR = 1
    SANE_CURRENT_MINOR = 0

    def __init__(self, major, minor, build=0):
        self.major = major
        self.minor = minor
        self.build = build

    def is_current(self):
        return ((self.major == self.SANE_CURRENT_MAJOR)
                and (self.minor == self.SANE_CURRENT_MINOR))

    def __str__(self):
        return "Sane version: %d.%d.%d" % (self.major, self.minor, self.build)


class SaneStatus(SaneEnum):
    GOOD = 0
    UNSUPPORTED = 1
    CANCELLED = 2
    DEVICE_BUSY = 3
    INVAL = 4
    EOF = 5
    JAMMED = 6
    NO_DOCS = 7
    COVER_OPEN = 8
    IO_ERROR = 9
    NO_MEM = 10
    ACCESS_DENIED = 11
    WARMING_UP = 12
    HW_LOCKED = 13

    VALUE_TO_STR = {
        GOOD :          "No error",
        UNSUPPORTED :   "Operation is not supported",
        CANCELLED :     "Operation was cancelled",
        DEVICE_BUSY :   "Device is busy. Try again later",
        INVAL :         "Data is invalid",
        EOF :           "End-of-file : no more data available",
        JAMMED :        "Document feeder jammed",
        NO_DOCS :       "Document feeder out of documents",
        COVER_OPEN :    "Scanner cover is open",
        IO_ERROR :      "Error during device I/O",
        NO_MEM :        "Out of memory",
        ACCESS_DENIED : "Access to resource has been denied",
        WARMING_UP :    "Lamp is not ready yet. Try again later",
        HW_LOCKED :     "Scanner mechanism locked for transport",
    }


class SaneValueType(SaneEnum):
    BOOL = 0
    INT = 1
    FIXED = 2
    STRING = 3
    BUTTON = 4
    GROUP = 5

    VALUE_TO_STR = {
        BOOL :      "Boolean",
        INT :       "Integer",
        FIXED :     "Fixed",
        STRING :    "String",
        BUTTON :    "Button",
        GROUP :     "Group",
    }


class SaneUnit(SaneEnum):
    NONE = 0
    PIXEL = 1
    BIT = 2
    MM = 3
    DPI = 4
    PERCENT = 5
    MICROSECOND = 6

    VALUE_TO_STR = {
        NONE :          "None",
        PIXEL :         "Pixel",
        BIT :           "Bit",
        MM :            "Mm",
        DPI :           "Dpi",
        PERCENT :       "Percent",
        MICROSECOND :   "Microsecond",
    }


class SaneDevice(object):
    def __init__(self, name, vendor, model, dev_type):
        self.name = name
        self.vendor = vendor
        self.model = model
        self.dev_type = dev_type

    def __str__(self):
        return "%s (%s, %s, %d)" % (self.name, self.vendor, self.model,
                                    self.dev_type)


class SaneCapabilities(SaneFlags):
    NONE = 0

    SOFT_SELECT = (1<<0)
    HARD_SELECT = (1<<1)
    SOFT_DETECT = (1<<2)
    EMULATED = (1<<3)
    AUTOMATIC = (1<<4)
    INACTIVE = (1<<5)
    ADVANCED = (1<<6)

    FLAG_TO_STR = {
        SOFT_SELECT :   "Soft_select",
        HARD_SELECT :   "Hard_select",
        SOFT_DETECT :   "Soft_detect",
        EMULATED :      "Emulated",
        AUTOMATIC :     "Automatic",
        INACTIVE :      "Inactive",
        ADVANCED :      "Advanced",
    }

    def is_active(self):
        return not self.INACTIVE in self

    def is_settable(self):
        return self.SOFT_SELECT in self


class SaneInfo(SaneFlags):
    EMPTY = 0

    INEXACT = (1<<0)
    RELOAD_OPTIONS = (1<<1)
    RELOAD_PARAMS = (1<<2)

    FLAG_TO_STR = {
        INEXACT :           "Inexact",
        RELOAD_OPTIONS :    "Reload_options",
        RELOAD_PARAMS :     "Reload_params",
    }


class SaneConstraintType(SaneEnum):
    NONE = 0
    RANGE = 1
    WORD_LIST = 2
    STRING_LIST = 3

    VALUE_TO_STR = {
        NONE :          "None",
        RANGE :         "Range",
        WORD_LIST :     "Word list",
        STRING_LIST :   "String list",
    }


class SaneRange(object):
    def __init__(self, min_val, max_val, quant):
        self.min_val = min_val
        self.max_val = max_val
        self.quant = quant

    def __str__(self):
        return "Range: %d-%d (%s)" % (self.min_val, self.max_val,
                                      str(self.quant))


class SaneOptionDescriptor(object):
    name = ""
    title = ""
    desc = ""
    value_type = SaneValueType(SaneValueType.INT)
    unit = SaneUnit(SaneUnit.NONE)
    size = 0
    capabilities = SaneCapabilities()

    constraint_type = SaneConstraintType(SaneConstraintType.NONE)
    contraint = None


class SaneAction(SaneEnum):
    GET_VALUE = 0
    SET_VALUE = 1
    SET_AUTO = 3

    VALUE_TO_STR = {
        GET_VALUE : "Get value",
        SET_VALUE : "Set value",
        SET_AUTO :  "Set auto",
    }


class SaneFrame(SaneEnum):
    GRAY = 0
    RGB = 1
    RED = 2
    GREEN = 3
    BLUE = 4

    VALUE_TO_STR = {
        GRAY :  "Gray",
        RGB :   "RGB",
        RED :   "Red",
        GREEN : "Green",
        BLUE :  "Blue",
    }


class SaneParameters(object):
    frame_format = SaneFrame(SaneFrame.RGB)
    last_frame = True
    bytes_per_line = 0
    pixels_per_line = 0
    lines = 0
    depth = 0


def __dummy_auth_callback(ressource, username, password):
    pass

def sane_init(auth_callback=__dummy_auth_callback):
    version_code = ctypes.c_int32()
    status = SANE_LIB.sane_init(ctypes.pointer(version_code),
                                ctypes.c_voidp())
    if status != SaneStatus.GOOD:
        return (SaneStatus(status),)
    version_code = version_code.value
    major = (version_code >> 24) & 0xFF
    minor = (version_code >> 16) & 0xFF
    build = (version_code >> 0) & 0xFFFF
    return (SaneStatus(status), SaneVersion(major, minor, build))

def sane_exit():
    SANE_LIB.sane_exit()

def sane_strstatus(status):
    if status in SaneStatus.__meanings:
        return SaneStatus.__meanings[status]
    return "Unknown error code: %d" % (status)
