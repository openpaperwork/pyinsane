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


class SaneException(Exception):
    def __init__(self, status):
        Exception.__init__(self, str(status))
        self.status = status

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


class SaneDevice(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("vendor", ctypes.c_char_p),
        ("model", ctypes.c_char_p),
        ("type", ctypes.c_char_p),
    ]

    def __str__(self):
        return ("Device: %s (%s, %s, %d)"
                % (self.name, self.vendor, self.model, self.type))


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


class SaneRange(ctypes.Structure):
    _fields_ = [
        ("min", ctypes.c_int),
        ("max", ctypes.c_int),
        ("quant", ctypes.c_int),
    ]

    def __str__(self):
        return "Range: %d-%d (%d)" % (self.min, self.max, self.quant)


class SaneConstraint(ctypes.Union):
    _fields_ = [
        ("string_list", ctypes.POINTER(ctypes.c_char_p)),
        ("word_list", ctypes.POINTER(ctypes.c_int)),
        ("range", ctypes.POINTER(SaneRange))
    ]


class SaneOptionDescriptor(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("title", ctypes.c_char_p),
        ("desc", ctypes.c_char_p),
        ("type", ctypes.c_int),  # SaneValueType
        ("unit", ctypes.c_int),  # SaneUnit
        ("size", ctypes.c_int),
        ("cap", ctypes.c_int),  # SaneCapabilities

        ("constraint_type", ctypes.c_int),  # SaneConstraintType
        ("constraint", SaneConstraint),
    ]


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


def __dummy_auth_callback(sane_ressource_str):
    return ("anonymous", # login
            "" # password
           )

class __AuthCallbackWrapper(object):
    MAX_USERNAME_LEN = 128
    MAX_PASSWORD_LEN = 128

    def __init__(self, auth_callback):
        self.__auth_callback = auth_callback

    def wrapper(self, ressource_ptr, login_ptr, passwd_ptr):
        (login, password) = self.__auth_callback(ressource_ptr.value)
        # TODO(Jflesch): Make sure the following works
        ctypes.memmove(login_ptr, ctypes.c_char_p(login),
                       min(len(login)+1, MAX_USERNAME_LEN))
        ctypes.memmove(passwd_ptr, ctypes.c_char_p(password),
                       min(len(password)+1, MAX_USERNAME_LEN))


def sane_init(auth_callback=__dummy_auth_callback):
    auth_callback_def = ctypes.CFUNCTYPE(None,
                                         ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_char_p)
    SANE_LIB.sane_init.argtypes = [ctypes.POINTER(ctypes.c_int),
                                   auth_callback_def]
    SANE_LIB.sane_init.restype = ctypes.c_int

    version_code = ctypes.c_int()
    wrap_func = __AuthCallbackWrapper(auth_callback).wrapper
    auth_callback = auth_callback_def(wrap_func)

    status = SANE_LIB.sane_init(ctypes.pointer(version_code), auth_callback)
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))
    version_code = version_code.value
    major = (version_code >> 24) & 0xFF
    minor = (version_code >> 16) & 0xFF
    build = (version_code >> 0) & 0xFFFF
    return SaneVersion(major, minor, build)


def sane_exit():
    SANE_LIB.sane_exit.argtypes = []
    SANE_LIB.sane_exit.restype = None
    SANE_LIB.sane_exit()


def sane_get_devices(remote=True):
    SANE_LIB.sane_get_devices.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_int
    ]
    SANE_LIB.sane_get_devices.restype = ctypes.c_int

    devices = ctypes.c_void_p()
    status = SANE_LIB.sane_get_devices(ctypes.pointer(devices),
                                       ctypes.c_int(remote))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    devices_ptr = ctypes.cast(devices, ctypes.POINTER(ctypes.POINTER(SaneDevice)))
    devices = []
    i = 0
    while devices_ptr[i]:
        devices.append(devices_ptr[i].contents)
        i += 1
    return devices


def sane_strstatus(status):
    if status in SaneStatus.__meanings:
        return SaneStatus.__meanings[status]
    return "Unknown error code: %d" % (status)
