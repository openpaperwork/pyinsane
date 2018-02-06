import ctypes
import functools

from .. import util


__all__ = [
    'SaneCapabilities',
    'SaneConstraint',
    'SaneConstraintType',
    'SaneDevice',
    'SaneException',
    'SaneFrame',
    'SaneInfo',
    'SaneOptionDescriptor',
    'SaneParameters',
    'SaneRange',
    'SaneStatus',
    'SaneUnit',
    'SaneValueType',
    'SaneVersion',

    'is_sane_available',
    'sane_init',
    'sane_exit',
    'sane_get_devices',
    'sane_open',
    'sane_close',
    'sane_get_option_descriptor',
    'sane_get_option_value',
    'sane_set_option_value',
    'sane_set_option_auto',
    'sane_get_parameters',
    'sane_start',
    'sane_read',
    'sane_cancel',
    'sane_set_io_mode',
    'sane_get_select_fd',
    'sane_strstatus',
]


@functools.total_ordering
class SaneEnum(object):
    VALUE_TO_STR = {}

    def __init__(self, value):
        self.__value = value

    def __int__(self):
        return self.__value

    def __eq__(self, other):
        if isinstance(other, int):
            return self.__value == other
        return self.__value == other.__value

    def __lt__(self, other):
        if isinstance(other, int):
            return self.__value < other
        return self.__value < other.__value

    def __str__(self):
        if self.__value not in self.VALUE_TO_STR:
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
        return ((self.__flags & flag) == flag)

    def __hex__(self):
        return hex(self.__flags)

    def __cmp__(self, other):
        return cmp(self.__flags, other.__flags)  # noqa

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
        return ((self.major == self.SANE_CURRENT_MAJOR) and
                (self.minor == self.SANE_CURRENT_MINOR))

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
        GOOD:          "No error",
        UNSUPPORTED:   "Operation is not supported",
        CANCELLED:     "Operation was cancelled",
        DEVICE_BUSY:   "Device is busy. Try again later",
        INVAL:         "Data is invalid",
        EOF:           "End-of-file : no more data available",
        JAMMED:        "Document feeder jammed",
        NO_DOCS:       "Document feeder out of documents",
        COVER_OPEN:    "Scanner cover is open",
        IO_ERROR:      "Error during device I/O",
        NO_MEM:        "Out of memory",
        ACCESS_DENIED: "Access to resource has been denied",
        WARMING_UP:    "Lamp is not ready yet. Try again later",
        HW_LOCKED:     "Scanner mechanism locked for transport",
    }


class SaneException(util.PyinsaneException):
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
        BOOL:      "Boolean",
        INT:       "Integer",
        FIXED:     "Fixed",
        STRING:    "String",
        BUTTON:    "Button",
        GROUP:     "Group",
    }

    VALUE_TO_CLASS = {
        BOOL:      ctypes.c_int,
        INT:       ctypes.c_int,
        FIXED:     ctypes.c_int,
        STRING:    ctypes.c_buffer,
    }

    def can_getset_opt(self):
        return int(self) in self.VALUE_TO_CLASS

    def buf_to_pyobj(self, buf):
        cl = self.VALUE_TO_CLASS[int(self)]
        if cl == ctypes.c_buffer:
            return buf.value
        return cl.from_buffer(buf).value

    def get_ctype_obj(self, pyobj):
        cl = self.VALUE_TO_CLASS[int(self)]
        return cl(pyobj)


class SaneUnit(SaneEnum):
    NONE = 0
    PIXEL = 1
    BIT = 2
    MM = 3
    DPI = 4
    PERCENT = 5
    MICROSECOND = 6

    VALUE_TO_STR = {
        NONE:          "None",
        PIXEL:         "Pixel",
        BIT:           "Bit",
        MM:            "Mm",
        DPI:           "Dpi",
        PERCENT:       "Percent",
        MICROSECOND:   "Microsecond",
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

    SOFT_SELECT = (1 << 0)
    HARD_SELECT = (1 << 1)
    SOFT_DETECT = (1 << 2)
    EMULATED = (1 << 3)
    AUTOMATIC = (1 << 4)
    INACTIVE = (1 << 5)
    ADVANCED = (1 << 6)

    FLAG_TO_STR = {
        SOFT_SELECT:   "Soft_select",
        HARD_SELECT:   "Hard_select",
        SOFT_DETECT:   "Soft_detect",
        EMULATED:      "Emulated",
        AUTOMATIC:     "Automatic",
        INACTIVE:      "Inactive",
        ADVANCED:      "Advanced",
    }

    def is_active(self):
        return self.INACTIVE not in self

    def is_settable(self):
        return self.SOFT_SELECT in self


class SaneInfo(SaneFlags):
    EMPTY = 0

    INEXACT = (1 << 0)
    RELOAD_OPTIONS = (1 << 1)
    RELOAD_PARAMS = (1 << 2)

    FLAG_TO_STR = {
        INEXACT:           "Inexact",
        RELOAD_OPTIONS:    "Reload_options",
        RELOAD_PARAMS:     "Reload_params",
    }


class SaneConstraintType(SaneEnum):
    NONE = 0
    RANGE = 1
    WORD_LIST = 2
    STRING_LIST = 3

    VALUE_TO_STR = {
        NONE:          "None",
        RANGE:         "Range",
        WORD_LIST:     "Word list",
        STRING_LIST:   "String list",
    }

    @staticmethod
    def __constraint_none_to_pyobj(sane_constraint):
        return None

    @staticmethod
    def __constraint_range_to_pyobj(sane_constraint):
        return (sane_constraint.range.contents.min,
                sane_constraint.range.contents.max,
                sane_constraint.range.contents.quant)

    @staticmethod
    def __constraint_word_list_to_pyobj(sane_constraint):
        list_lng = sane_constraint.word_list[0]
        return sane_constraint.word_list[1:list_lng+1]

    @staticmethod
    def __constraint_string_list_to_pyobj(sane_constraint):
        string_list = []
        idx = 0
        while sane_constraint.string_list[idx]:
            string = sane_constraint.string_list[idx]
            if hasattr(string, 'decode'):
                string = string.decode("utf-8")
            string_list.append(string)
            idx += 1
        return string_list

    def get_pyobj_constraint(self, sane_constraint):
        pyobj = {
            self.NONE:         self.__constraint_none_to_pyobj,
            self.RANGE:        self.__constraint_range_to_pyobj,
            self.WORD_LIST:    self.__constraint_word_list_to_pyobj,
            self.STRING_LIST:  self.__constraint_string_list_to_pyobj,
        }[int(self)](sane_constraint)
        return pyobj


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
        # Is actually multi-line ! -> you have to get
        # a pointer on the pointer and use ptr[0], ptr[1], etc to get all the
        # lines
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
        GET_VALUE: "Get value",
        SET_VALUE: "Set value",
        SET_AUTO:  "Set auto",
    }


class SaneFrame(SaneEnum):
    GRAY = 0
    RGB = 1
    RED = 2
    GREEN = 3
    BLUE = 4

    VALUE_TO_STR = {
        GRAY:  "Gray",
        RGB:   "RGB",
        RED:   "Red",
        GREEN: "Green",
        BLUE:  "Blue",
    }

    VALUE_TO_PIL_FORMAT = {
        GRAY: "L",
        RGB: "RGB",
        RED: "L",
        GREEN: "L",
        BLUE: "L",
    }

    def get_pil_format(self):
        return self.VALUE_TO_PIL_FORMAT[int(self)]


class SaneParameters(ctypes.Structure):
    _fields_ = [
        ("format",          ctypes.c_int),  # SaneFrame
        ("last_frame",      ctypes.c_int),  # boolean
        ("bytes_per_line",  ctypes.c_int),
        ("pixels_per_line", ctypes.c_int),
        ("lines",           ctypes.c_int),
        ("depth",           ctypes.c_int),
    ]


def __dummy_auth_callback(sane_ressource_str):
    return (
        "anonymous",  # login
        ""  # password
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
                       min(len(login)+1, self.MAX_USERNAME_LEN))
        ctypes.memmove(passwd_ptr, ctypes.c_char_p(password),
                       min(len(password)+1, self.MAX_USERNAME_LEN))


sane_is_init = 0
sane_version = None

sane_available = False

for libname in ["libsane.so.1", "libsane.1.dylib"]:
    try:
        SANE_LIB = ctypes.cdll.LoadLibrary(libname)
        sane_available = True
        break
    except OSError:
        pass

if sane_available:
    AUTH_CALLBACK_DEF = ctypes.CFUNCTYPE(None, ctypes.c_char_p,
                                         ctypes.c_char_p, ctypes.c_char_p)
    SANE_LIB.sane_init.argtypes = [
        ctypes.POINTER(ctypes.c_int), AUTH_CALLBACK_DEF
    ]
    SANE_LIB.sane_init.restype = ctypes.c_int

    SANE_LIB.sane_exit.argtypes = []
    SANE_LIB.sane_exit.restype = None

    SANE_LIB.sane_get_devices.argtypes = [
        ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(SaneDevice))),
        ctypes.c_int
    ]
    SANE_LIB.sane_get_devices.restype = ctypes.c_int

    SANE_LIB.sane_open.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    SANE_LIB.sane_open.restype = ctypes.c_int

    SANE_LIB.sane_close.argtypes = [ctypes.c_void_p]
    SANE_LIB.sane_close.restype = None

    SANE_LIB.sane_get_option_descriptor.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int
    ]
    SANE_LIB.sane_get_option_descriptor.restype = \
        ctypes.POINTER(SaneOptionDescriptor)

    SANE_LIB.sane_control_option.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int)
    ]
    SANE_LIB.sane_control_option.restype = ctypes.c_int

    SANE_LIB.sane_get_parameters.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(SaneParameters),
    ]
    SANE_LIB.sane_get_parameters.restype = ctypes.c_int

    SANE_LIB.sane_start.argtypes = [ctypes.c_void_p]
    SANE_LIB.sane_start.restype = ctypes.c_int

    SANE_LIB.sane_read.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int)
    ]
    SANE_LIB.sane_read.restype = ctypes.c_int

    SANE_LIB.sane_cancel.argtypes = [ctypes.c_void_p]
    SANE_LIB.sane_cancel.restype = None

    SANE_LIB.sane_set_io_mode.argtypes = [ctypes.c_void_p, ctypes.c_int]
    SANE_LIB.sane_set_io_mode.restype = ctypes.c_int

    SANE_LIB.sane_get_select_fd.argtypes = [ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_int)]
    SANE_LIB.sane_get_select_fd.restype = ctypes.c_int


def is_sane_available():
    global sane_available
    return sane_available


def sane_init(auth_callback=__dummy_auth_callback):
    global sane_available, sane_is_init, sane_version
    assert(sane_available)

    sane_is_init += 1
    if sane_is_init > 1:
        return sane_version

    version_code = ctypes.c_int()
    wrap_func = __AuthCallbackWrapper(auth_callback).wrapper
    auth_callback = AUTH_CALLBACK_DEF(wrap_func)

    status = SANE_LIB.sane_init(ctypes.pointer(version_code), auth_callback)
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))
    version_code = version_code.value
    major = (version_code >> 24) & 0xFF
    minor = (version_code >> 16) & 0xFF
    build = (version_code >> 0) & 0xFFFF
    sane_version = SaneVersion(major, minor, build)
    return sane_version


def sane_exit():
    global sane_available, sane_is_init
    assert(sane_available)

    # TODO(Jflesch): This is a workaround
    # In a multithreaded environment, for some unknown reason,
    # calling sane_exit() will work but the program will crash
    # when stopping. So we simply never call sane_exit() ...

    # sane_is_init -= 1
    # if sane_is_init <= 0:
    #     SANE_LIB.sane_exit()


def sane_get_devices(local_only=False):
    global sane_available
    assert(sane_available)

    devices_ptr = ctypes.POINTER(ctypes.POINTER(SaneDevice))()

    status = SANE_LIB.sane_get_devices(ctypes.pointer(devices_ptr),
                                       ctypes.c_int(local_only))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    devices = []
    i = 0
    while devices_ptr[i]:
        devices.append(devices_ptr[i].contents)
        i += 1
    return devices


def sane_open(dev_name):
    global sane_available
    assert(sane_available)

    if isinstance(dev_name, str):
        dev_name = dev_name.encode('utf-8')

    handle_ptr = ctypes.c_void_p()

    status = SANE_LIB.sane_open(ctypes.c_char_p(dev_name),
                                ctypes.pointer(handle_ptr))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    return handle_ptr


def sane_close(handle):
    global sane_available
    assert(sane_available)

    SANE_LIB.sane_close(handle)


def sane_get_option_descriptor(handle, option_idx):
    global sane_available
    assert(sane_available)

    opt_desc_ptr = SANE_LIB.sane_get_option_descriptor(
        handle, ctypes.c_int(option_idx))
    if not opt_desc_ptr:
        raise SaneException(SaneStatus(SaneStatus.INVAL))
    return opt_desc_ptr.contents


def sane_get_option_value(handle, option_idx):
    global sane_available
    assert(sane_available)

    # we need the descriptor first in order to allocate a buffer of the correct
    # size, then cast it to the correct type
    opt_desc = sane_get_option_descriptor(handle, option_idx)

    buf = ctypes.c_buffer(max(4, opt_desc.size))
    info = ctypes.c_int()

    status = SANE_LIB.sane_control_option(handle, ctypes.c_int(option_idx),
                                          SaneAction.GET_VALUE,
                                          ctypes.pointer(buf),
                                          ctypes.pointer(info))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    return SaneValueType(opt_desc.type).buf_to_pyobj(buf)


def sane_set_option_value(handle, option_idx, new_value):
    global sane_available
    assert(sane_available)

    if isinstance(new_value, str):
        new_value = new_value.encode('utf-8')

    # we need the descriptor first in order to allocate a buffer of the correct
    # size, then cast it to the correct type
    opt_desc = sane_get_option_descriptor(handle, option_idx)

    value = SaneValueType(opt_desc.type).get_ctype_obj(new_value)
    info = ctypes.c_int()

    status = SANE_LIB.sane_control_option(handle, ctypes.c_int(option_idx),
                                          SaneAction.SET_VALUE,
                                          ctypes.pointer(value),
                                          ctypes.pointer(info))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    return SaneInfo(info.value)


def sane_set_option_auto(handle, option_idx):
    global sane_available
    assert(sane_available)

    info = ctypes.c_int()

    status = SANE_LIB.sane_control_option(handle, ctypes.c_int(option_idx),
                                          SaneAction.SET_AUTO,
                                          ctypes.c_void_p(),
                                          ctypes.pointer(info))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    return SaneInfo(info.value)


def sane_get_parameters(handle):
    global sane_available
    assert(sane_available)

    parameters = SaneParameters()

    status = SANE_LIB.sane_get_parameters(handle, ctypes.pointer(parameters))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))

    return parameters


def sane_start(handle):
    global sane_available
    assert(sane_available)

    status = SANE_LIB.sane_start(handle)
    if status == SaneStatus.NO_DOCS:
        raise StopIteration()
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))


def sane_read(handle, nb_bytes):
    global sane_available
    assert(sane_available)

    buf = ctypes.c_buffer(nb_bytes)
    length = ctypes.c_int()

    status = SANE_LIB.sane_read(handle, ctypes.pointer(buf), len(buf),
                                ctypes.pointer(length))
    if status == SaneStatus.NO_DOCS:
        raise StopIteration()
    elif status == SaneStatus.EOF:
        raise EOFError()
    elif status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))
    return buf[:length.value]


def sane_cancel(handle):
    global sane_available
    assert(sane_available)

    SANE_LIB.sane_cancel(handle)


def sane_set_io_mode(handle, non_blocking=False):
    global sane_available
    assert(sane_available)

    status = SANE_LIB.sane_set_io_mode(handle,
                                       ctypes.c_int(int(non_blocking)))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))


def sane_get_select_fd(handle):
    global sane_available
    assert(sane_available)

    fd = ctypes.c_int()
    status = SANE_LIB.sane_get_select_fd(handle, ctypes.pointer(fd))
    if status != SaneStatus.GOOD:
        raise SaneException(SaneStatus(status))
    return fd.value


def sane_strstatus(status):
    global sane_available
    assert(sane_available)

    if status in SaneStatus.__meanings:
        return SaneStatus.__meanings[status]
    return "Unknown error code: %d" % (status)
