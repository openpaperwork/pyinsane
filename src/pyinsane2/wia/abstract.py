import io
import logging
import sys

import PIL.Image
import PIL.ImageFile

from . import rawapi
from .rawapi import WIAException

__all__ = [
    'init',
    'exit',
    'Scanner',
    'ScannerOption',
    'WIAException',
    'get_devices',
]


logger = logging.getLogger(__name__)


def init():
    rawapi.init()


def exit():
    rawapi.exit()


class Scan(object):

    # WORKAROUND(Jflesch)> When using the ADF with HP drivers, even if there is no paper in the ADF
    # The driver will write about 56 bytes in the stream (BMP headers ?)
    # --> We ignore BMP too small
    MIN_BYTES = 1024

    def __init__(self, session):
        self._session = session
        self.scan = session._rawapi_scan
        self._data = b""
        self._img_size = None

    def read(self):
        # will raise EOFError at the end of each page
        # will raise StopIteration when all the pages are done
        try:
            buf = self.scan.read()
            self._data += buf
            self._got_data = True
        except EOFError:
            if len(self._data) >= self.MIN_BYTES:
                self._session._add_image(self._get_current_image())
                self._session._next()
                raise
            else:
                # Too small. Scrap the crap from the drivers.
                self._data = b""

    def _get_current_image(self):
        # We get the image as a truncated bitmap.
        # ('rawrgb' is not supported by all drivers ...)
        # Bitmap headers are annoying.
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True
        stream = io.BytesIO(self._data)
        img = PIL.Image.open(stream)
        self._img_size = img.size
        return img

    def _get_available_lines(self):
        if self._img_size is None:
            try:
                self._get_current_image()
            except:
                return 0
        # estimated
        line_size = self._img_size[0] * 3  # rgb
        data = len(self._data) - 1024  # - headers
        return (0, int(data / line_size))

    available_lines = property(_get_available_lines)

    def _get_expected_size(self):
        if self._img_size:
            return self._img_size
        options = self._session.scanner.options
        return (
            int(options['xextent'].value),
            int(options['yextent'].value)
        )

    expected_size = property(_get_expected_size)

    def get_image(self, start_line=0, end_line=-1):
        img = self._get_current_image()
        img_size = img.size
        if start_line > 0:
            img = img.crop((0, start_line, img_size[0], img_size[1]))
        if end_line >= 0:
            end_line -= start_line
            img = img.crop((0, 0, img_size[0], end_line))
        return img

    def cancel(self):
        # TODO
        raise NotImplementedError()


class ScanSession(object):
    def __init__(self, scanner, srcid):
        self.scanner = scanner
        self.source = scanner.srcs[srcid]
        self._rawapi_scan = rawapi.start_scan(self.source)
        self.images = []
        self.scan = Scan(self)

    def _add_image(self, img):
        self.images.append(img)

    def _next(self):
        self.scan = Scan(self)


class ScannerCapabilities(object):
    def __init__(self, opt):
        self.opt = opt

    def is_active(self):
        return True

    def is_settable(self):
        return self.opt.accessright == "rw"


class ScannerOption(object):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, scanner, objsrc, name, value, possible_values, accessright):
        self.objsrc = objsrc
        self.scanner = scanner
        self.name = name
        self._value = value
        self.constraint = possible_values
        self.accessright = accessright
        self.capabilities = ScannerCapabilities(self)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.accessright != 'rw':
            raise rawapi.WIAException("Property {} is read-only".format(self.name))
        has_success = False
        exc = None
        for obj in self.objsrc:
            try:
                rawapi.set_property(obj, self.name, new_value)
                has_success = True
            except rawapi.WIAException as _exc:
                exc = _exc
        if not has_success:
            raise exc
        self._value = new_value
        self.scanner.reload_options()

    value = property(_get_value, _set_value)


class SourceOption(ScannerOption):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, sources):
        self.name = "source"
        self.sources = sources
        self.constraint = [srcid for (srcid, src) in sources]
        self._value = self.constraint[0]
        self.capabilities = ScannerCapabilities(self)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if not new_value in self.constraint:
            raise WIAException("Invalid source: {}".format(new_value))
        self._value = new_value

    value = property(_get_value, _set_value)


class ModeOption(object):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, scanner):
        self.name = "mode"
        self.scanner = scanner
        self.constraint = ["Color", "Gray", "BW"]
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner

    def _get_value(self):
        opts = self.scanner.options
        if opts['bits_per_channel'].value == 1:
            return 'BW'
        if opts['channels_per_pixel'].value == 1:
            return 'Gray'
        return 'Color'

    def _set_value(self, new_value):
        opts = self.scanner.options
        if new_value == "BW":
            opts['depth'].value = 1
            self.scanner.reload_options()
            return
        if new_value == "Gray":
            opts['depth'].value = 8
            self.scanner.reload_options()
            return
        if new_value == "Color":
            opts['depth'].value = 24
            self.scanner.reload_options()
            return
        raise WIAException("Unknown value '{}' for option 'mode'".format(new_value))

    value = property(_get_value, _set_value)


def get_pos_constraint(options, opt_min, opt_max, opt_res):
    if (opt_min not in options or
            opt_max not in options or
            opt_res not in options):
        return None
    vmax = options[opt_max].value / 1000  # thousandths of inch
    vres = options[opt_res].value
    return (0, int(vmax * vres))


class PosOption(object):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, scanner, name, base_name, options, opt_min, opt_max, opt_res):
        self.name = name
        self.base_name = base_name
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner
        self._options = options
        self.constraint = get_pos_constraint(options, opt_min, opt_max, opt_res)

    def _get_value(self):
        return self._options[self.base_name + 'pos'].value

    def _set_value(self, new_value):
        diff = self._options[self.base_name + 'pos'].value - self.value
        extent = self._options[self.base_name + 'extent'].value
        self._options[self.base_name + 'pos'].value = new_value
        self._options[self.base_name + 'extent'].value = extent - diff

    value = property(_get_value, _set_value)


class ExtendOption(object):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, scanner, name, base_name, options, opt_min, opt_max, opt_res):
        self.name = name
        self.base_name = base_name
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner
        self._options = options
        self.constraint = get_pos_constraint(options, opt_min, opt_max, opt_res)

    def _get_value(self):
        return (self._options[self.base_name + 'extent'].value
                + self._options[self.base_name + 'pos'].value)

    def _set_value(self, new_value):
        new_value -= self._options[self.base_name + 'pos'].value
        self._options[self.base_name + 'extent'].value = new_value

    value = property(_get_value, _set_value)


class MultialiasOption(object):
    idx = -1
    name = ""
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None # TODO
    constraint = None

    def __init__(self, scanner, name, alias_for, options):
        self.name = name
        self.scanner = scanner
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner
        self.alias_for = alias_for
        self._options = options

    def _get_value(self):
        return self._options[self.alias_for[0]].value

    def _set_value(self, new_value):
        for opt_name in self.alias_for:
            self._options[opt_name].value = new_value

    value = property(_get_value, _set_value)



class Scanner(object):
    def __init__(self, name):
        self._dev = rawapi.open(name)
        self._srcs_list = rawapi.get_sources(self._dev)
        self.srcs = {}
        for (srcid, src) in self._srcs_list:
            self.srcs[srcid] = src

        self.options = {}
        self.reload_options()

        self.name = name
        self.nice_name = self.options['dev_name'].value
        self.vendor = self.options['vend_desc'].value
        self.model = self.options['dev_desc'].value
        self.dev_type = self.options['dev_type'].value

    @staticmethod
    def _convert_prop_list_to_dict(props):
        out = {}
        for (propname, propvalue, accessright, possible_values) in props:
            out[propname] = {
                'value': propvalue,
                'accessright': accessright,
                'possible_values': possible_values
            }
        return out

    def reload_options(self):
        original = self.options

        self.options = {}

        dev_properties = self._convert_prop_list_to_dict(
            rawapi.get_properties(self._dev)
        )
        src_properties = {}
        for (srcid, src) in self._srcs_list:
            src_properties[srcid] = self._convert_prop_list_to_dict(
                rawapi.get_properties(src)
            )

        for (opt_name, opt_infos) in dev_properties.items():
            self.options[opt_name] = ScannerOption(
                self,
                [self._dev],
                opt_name, opt_infos['value'], opt_infos['possible_values'],
                opt_infos['accessright']
            )
        # generate list of options from all the sources, and try to apply them on all the sources
        for (srcid, opts) in src_properties.items():
            for (opt_name, opt_infos) in opts.items():
                if opt_name in self.options:
                    continue
                self.options[opt_name] = ScannerOption(
                    self,
                    self.srcs.values(),
                    opt_name, opt_infos['value'], opt_infos['possible_values'],
                    opt_infos['accessright']
                )

        # aliases to match Sane
        if "xpos" in self.options.keys() and "xextent" in self.options.keys():
            self.options['tl-x'] = PosOption(
                self, "tl-x", "x", self.options, "min_horizontal_size", "max_horizontal_size", "xres"
            )
            self.options['br-x'] = ExtendOption(
                self, "br-x", "x", self.options, "min_horizontal_size", "max_horizontal_size", "xres"
            )
        if "ypos" in self.options.keys() and "yextent" in self.options.keys():
            self.options['tl-y'] = PosOption(
                self, "tl-y", "y", self.options, "min_vertical_size", "max_vertical_size", "yres"
            )
            self.options['br-y'] = ExtendOption(
                self, "br-y", "y", self.options, "min_vertical_size", "max_vertical_size", "yres"
            )
        if "xres" in self.options.keys() and "yres" in self.options.keys():
            self.options['resolution'] = MultialiasOption(
                self, "resolution", ["xres", "yres"], self.options
            )

        if 'source' in original:
            self.options['source'] = original['source']
        else:
            self.options['source'] = SourceOption(self._srcs_list)
        if 'mode' in original:
            self.options['mode'] = original['mode']
        else:
            self.options['mode'] = ModeOption(self)

    def scan(self, multiple=False):
        return ScanSession(self, self.options['source'].value)

    def __str__(self):
        return ("'%s' (%s, %s, %s)"
                % (self.nice_name, self.vendor, self.model, self.dev_type))


def get_devices(local_only=False):
    devs = rawapi.get_devices()
    return [Scanner(dev[0]) for dev in devs]
