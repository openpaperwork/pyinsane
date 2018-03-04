import io
import logging

import PIL.Image
import PIL.ImageFile

from . import rawapi
from .. import util
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
    # WORKAROUND(Jflesch)> When using the ADF with HP drivers, even if there is
    # no paper in the ADF
    # The driver will write about 56 bytes in the stream (BMP headers ?)
    # --> We ignore BMP too small
    MIN_BYTES = 1024

    def __init__(self, session, source, multiple=False):
        self._session = session
        self.source = source
        self._data = b""
        self.is_valid = False
        self.is_complete = False
        self._img_size = None
        logger.info("Starting scan")
        self.scan = rawapi.start_scan(self.source)
        self.multiple = multiple

    def read(self):
        # will raise EOFError at the end of each page
        # will raise StopIteration when all the pages are done
        if self.is_complete:
            if self.multiple:
                return self._session._next().read()
            else:
                raise StopIteration()
        try:
            buf = self.scan.read()
            self._data += buf
        except EOFError:
            # Jflesch> Some drivers (Brother for instance) keep telling us
            # there is still something to scan yet when there is not.
            # They send some data (image headers ?) and only then they
            # realize there is nothing left to scan ...
            logger.info("End of page")
            self.is_complete = True
            if len(self._data) >= self.MIN_BYTES:
                try:
                    self._session._add_image(self._get_current_image())
                    self.is_valid = True
                except Exception as exc:
                    logger.warning(
                        "Got %d bytes, but exception while decoding image."
                        " Assuming no more page are available",
                        len(self._data), exc_info=exc
                    )
                    logger.info("End of scan session")
                    self._session._cancel_current()
                    raise StopIteration()
                raise
            else:
                # --> Too small. Scrap the crap from the drivers and switch
                # back to the last valid data obtained (last page scanned)
                self._session._cancel_current()
                raise StopIteration()

    def _get_current_image(self):
        stream = io.BytesIO(self._data)
        # We get the image as a truncated bitmap.
        # ('rawrgb' is not supported by all drivers ...)
        # BMP headers are annoying.
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True
        try:
            img = PIL.Image.open(stream)
            img.load()
        finally:
            PIL.ImageFile.LOAD_TRUNCATED_IMAGES = False
        self._img_size = img.size
        return img

    def _get_available_lines(self):
        if self._img_size is None:
            try:
                self._get_current_image()
            except:
                # assumes we just got truncated headers for now
                return (0, 0)
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

    def __str__(self):
        return ("Scan instance for session {}".format(self._session))


class ScanSession(object):
    def __init__(self, scanner, srcid, multiple):
        self.scanner = scanner
        self.multiple = multiple
        self.source = scanner.srcs[srcid]
        self.images = []
        self.previous = None
        self.scan = Scan(self, self.source, self.multiple)

    def _add_image(self, img):
        self.images.append(img)

    def _next(self):
        self.scan = Scan(self, self.source, self.multiple)
        return self.scan

    def _cancel_current(self):
        if self.previous is None:
            return
        self.scan = self.previous


class ScannerCapabilities(object):
    def __init__(self, opt):
        self.opt = opt

    def is_active(self):
        return True

    def is_settable(self):
        return self.opt.accessright == "rw"

    def __str__(self):
        return ("Access: {}".format(self.opt.accessright))


class ScannerOption(object):
    idx = -1
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None  # TODO
    constraint = None

    def __init__(self, scanner, objsrc, name, value, possible_values,
                 accessright, constraint):
        self.objsrc = objsrc
        self.scanner = scanner
        self.name = name
        self._value = value
        if constraint:
            self.constraint = constraint
        else:
            self.constraint = possible_values
        self.accessright = accessright
        self.capabilities = ScannerCapabilities(self)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.accessright != 'rw':
            raise rawapi.WIAException("Property {} is read-only".format(
                self.name
            ))
        has_success = False
        exc = None
        for obj in self.objsrc:
            try:
                rawapi.set_property(obj, self.name, new_value)
                has_success = True
            except rawapi.WIAException as _exc:
                logger.warning("Exception while setting {}: {}".format(
                    self.name, _exc
                ))
                logger.exception(_exc)
                exc = _exc
        self._value = new_value
        try:
            self.scanner.reload_options()
        except:
            pass
        if not has_success:
            raise exc

    value = property(_get_value, _set_value)

    def __str__(self):
        return ("Option [{}] (basic)".format(self.name))

    def __eq__(self, other):
        return (self.name == other.name and
                self.constraint == other.constraint)


class SourceOption(ScannerOption):
    idx = -1
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None  # TODO
    constraint = None

    accessright = "rw"

    def __init__(self, sources):
        self.name = "source"
        self.sources = sources
        self.constraint = [srcid for (srcid, src) in sources]
        self._value = self.constraint[0]
        self.capabilities = ScannerCapabilities(self)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if new_value not in self.constraint:
            raise WIAException("Invalid source: {}".format(new_value))
        self._value = new_value

    value = property(_get_value, _set_value)

    def __str__(self):
        return ("Option [{}] (source)".format(self.name))

    def __eq__(self, other):
        return isinstance(other, SourceOption)


class ModeOption(object):
    idx = -1
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None  # TODO
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
        raise WIAException("Unknown value '{}' for option 'mode'".format(
            new_value
        ))

    value = property(_get_value, _set_value)

    def _get_accessright(self):
        opts = self.scanner.options
        return opts['depth'].accessright

    accessright = property(_get_accessright)

    def __str__(self):
        return ("Option [{}] (mode)".format(self.name))


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
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None  # TODO
    constraint = None

    def __init__(self, scanner, name, base_name, options, opt_min, opt_max,
                 opt_res):
        self.name = name
        self.base_name = base_name
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner
        self._options = options
        self.constraint = get_pos_constraint(
            options, opt_min, opt_max, opt_res
        )

    def _get_value(self):
        return self._options[self.base_name + 'pos'].value

    def _set_value(self, new_value):
        diff = self._options[self.base_name + 'pos'].value - self.value
        extent = self._options[self.base_name + 'extent'].value
        self._options[self.base_name + 'pos'].value = new_value
        self._options[self.base_name + 'extent'].value = extent - diff

    value = property(_get_value, _set_value)

    def _get_accessright(self):
        rw = True
        if self._options[self.base_name + 'pos'].accessright != 'rw':
            rw = False
        elif self._options[self.base_name + 'extent'].accessright != 'rw':
            rw = False
        return "rw" if rw else "ro"

    accessright = property(_get_accessright)

    def __str__(self):
        return ("Option [{}] (position for [{}])".format(
            self.name, self.base_name
        ))


class ExtendOption(object):
    idx = -1
    title = ""
    desc = ""
    val_type = None  # TODO
    unit = None  # TODO
    size = 4
    capabilities = None

    constraint_type = None  # TODO
    constraint = None

    def __init__(self, scanner, name, base_name, options, opt_min, opt_max,
                 opt_res):
        self.name = name
        self.base_name = base_name
        self.capabilities = ScannerCapabilities(self)
        self.scanner = scanner
        self._options = options
        self.constraint = get_pos_constraint(
            options, opt_min, opt_max, opt_res
        )

    def _get_value(self):
        return (self._options[self.base_name + 'extent'].value +
                self._options[self.base_name + 'pos'].value)

    def _set_value(self, new_value):
        new_value -= self._options[self.base_name + 'pos'].value
        self._options[self.base_name + 'extent'].value = new_value

    value = property(_get_value, _set_value)

    def _get_accessright(self):
        rw = True
        if self._options[self.base_name + 'pos'].accessright != 'rw':
            rw = False
        elif self._options[self.base_name + 'extent'].accessright != 'rw':
            rw = False
        return "rw" if rw else "ro"

    accessright = property(_get_accessright)

    def __str__(self):
        return ("Option [{}] (extent for [{}])".format(
            self.name, self.base_name
        ))


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

        for (opt, val) in [
            ('current_intent', 'image_type_color,maximize_quality'),
            ('format', 'bmp'),
            ('preferred_format', 'bmp'),
            ('page_size', 'a4'),
            ('depth', 24),
        ]:
            if opt not in self.options:
                continue
            try:
                self.options[opt].value = val
                logger.warning("Option '{}' preset to '{}' on [{}]".format(
                    opt, val, self
                ))
            except:
                logger.warning("Failed to pre-set option '{}' on [{}]".format(
                    opt, self
                ))

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

    @staticmethod
    def _merge_constraints(props, constraints):
        for (propname, constraint) in constraints:
            if propname not in props:
                logger.warning(
                    "Constraint found on property [{}] but property "
                    "not found".format(propname)
                )
                continue
            if isinstance(constraint, list):
                constraint.sort()
            props[propname]['constraint'] = constraint

    def reload_options(self):
        original = self.options

        self.options = {}

        dev_properties = self._convert_prop_list_to_dict(
            rawapi.get_properties(self._dev)
        )
        dev_constraints = rawapi.get_constraints(self._dev)
        self._merge_constraints(dev_properties, dev_constraints)

        src_properties = {}
        for (srcid, src) in self._srcs_list:
            src_properties[srcid] = self._convert_prop_list_to_dict(
                rawapi.get_properties(src)
            )
            src_constraints = rawapi.get_constraints(src)
            self._merge_constraints(src_properties[srcid], src_constraints)

        for (opt_name, opt_infos) in dev_properties.items():
            self.options[opt_name] = ScannerOption(
                self,
                [self._dev],
                opt_name, opt_infos['value'], opt_infos['possible_values'],
                opt_infos['accessright'],
                opt_infos['constraint'] if 'constraint' in opt_infos else None
            )
        # generate list of options from all the sources, and try to apply them
        # on all the sources
        for (srcid, opts) in src_properties.items():
            for (opt_name, opt_infos) in opts.items():
                opt = ScannerOption(
                    self,
                    self.srcs.values(),
                    opt_name, opt_infos['value'], opt_infos['possible_values'],
                    opt_infos['accessright'],
                    opt_infos['constraint']
                    if 'constraint' in opt_infos else None
                )
                if opt_name in self.options:
                    if self.options[opt_name] != opt:
                        logger.warning("Got multiple time the option [{}],"
                                       " but they are not identical".format(
                                           opt_name))
                self.options[opt_name] = opt

        # aliases to match Sane
        if "xpos" in self.options.keys() and "xextent" in self.options.keys():
            self.options['tl-x'] = PosOption(
                self, "tl-x", "x", self.options, "min_horizontal_size",
                "max_horizontal_size", "xres"
            )
            self.options['br-x'] = ExtendOption(
                self, "br-x", "x", self.options, "min_horizontal_size",
                "max_horizontal_size", "xres"
            )
        if "ypos" in self.options.keys() and "yextent" in self.options.keys():
            self.options['tl-y'] = PosOption(
                self, "tl-y", "y", self.options, "min_vertical_size",
                "max_vertical_size", "yres"
            )
            self.options['br-y'] = ExtendOption(
                self, "br-y", "y", self.options, "min_vertical_size",
                "max_vertical_size", "yres"
            )
        res_alias_for = []
        if "xres" in self.options.keys():
            res_alias_for.append("xres")
        if "yres" in self.options.keys():
            res_alias_for.append("yres")
        if res_alias_for != []:
            self.options['resolution'] = util.AliasOption(
                "resolution", res_alias_for, self.options
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
        if (not ('source' in self.options and
                 self.options['source'].capabilities.is_active())):
            value = ""
        else:
            value = self.options['source'].value
        if hasattr(value, 'decode'):
            value = value.decode('utf-8')
        if "adf" not in value.lower() and "feeder" not in value.lower():
            # XXX(Jflesch): If we try to scan multiple pages
            # from a  feeder, we never get WIA_ERROR_PAPER_EMPTY
            # and loop forever
            multiple = False

        if 'pages' in self.options:
            try:
                # Even with an ADF, Pyinsane actually request one page
                # after the other.
                # This is not orthodox at all, but still, it has proven to be
                # the most reliable way.
                self.options['pages'].value = 1
            except:
                logger.exception("Failed to set options [pages]")

        return ScanSession(self, self.options['source'].value, multiple)

    def __str__(self):
        return ("'%s' (%s, %s, %s)"
                % (self.nice_name, self.vendor, self.model, self.dev_type))


def get_devices(local_only=False):
    devs = rawapi.get_devices()
    out = []
    for dev in devs:
        try:
            scanner = Scanner(dev[0])
            out.append(scanner)
        except Exception as exc:
            logger.warning("Failed to access scanner {} : {}".format(dev, exc))
            logger.exception(exc)
    return out
