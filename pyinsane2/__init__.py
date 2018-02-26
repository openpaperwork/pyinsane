import logging
import os
import sys

from .util import PyinsaneException

SINGLE_THREAD = bool(int(os.getenv("PYINSANE_SINGLE_THREAD", 0)))

if os.name == "nt":
    from .wia.abstract import *  # noqa
elif sys.platform == "darwin" or SINGLE_THREAD:
    # The dedicated process appear to crash on MacOSX. Don't know why.
    from .sane.abstract import *  # noqa
else:
    from .sane.abstract_proc import *  # noqa


logger = logging.getLogger(__name__)

__all__ = [
    'init',
    'exit',
    'Scanner',
    'ScannerOption',
    'PyinsaneException',
    'get_devices',
    'set_scanner_opt',
    'maximize_scan_area',
    '__version__',
]

__version__ = "2.0.10"


def __normalize_value(value):
    if isinstance(value, str):
        return value.lower()
    return value


def set_scanner_opt(scanner, opt, values):
    """
    Utility function to set most common values easily.

    Examples:
        set_scanner_opt(scanner, "source", ["flatbed"])
        set_scanner_opt(scanner, "source", ["ADF", "feeder"])
    """
    assert(values is not None and values != [])

    if opt not in scanner.options:
        # check it's not just a casing problem
        for key in scanner.options.keys():
            if opt.lower() == key.lower():
                opt = key
                break
        # otherwise just keep going, it will raise a KeyError anyway

    if not scanner.options[opt].capabilities.is_active():
        logger.error(
            "Unable to set scanner option [{}]:"
            " Option is not active".format(opt)
        )
        # this may not be a problem. For instance, 'source' is not active
        # on all scanners, and there is no point in raising an exception
        # when trying to set it to 'FlatBed' or 'Auto'
        return

    last_exc = None
    for value in values:

        # See if we can normalize it first
        if isinstance(scanner.options[opt].constraint, list):
            found = False
            for possible in scanner.options[opt].constraint:
                if __normalize_value(value) == __normalize_value(possible):
                    value = possible
                    found = True
                    break
            if not found:
                # no direct match. See if we have an indirect one
                # for instance, 'feeder' in 'Automatic Document Feeder'
                for possible in scanner.options[opt].constraint:
                    if (isinstance(possible, str) and
                            __normalize_value(value) in
                            __normalize_value(possible)):
                        logger.info(
                            "Value for [{}] changed from [{}] to [{}]".format(
                                opt, value, possible
                            )
                        )
                        value = possible
                        found = True
                        break
            # beware: don't select a source that is not in the constraint,
            # with some drivers (Brother DCP-8025D for instance),
            # it may segfault.
            if not found:
                last_exc = PyinsaneException(
                    "Invalid value [{}] for option [{}]."
                    " Valid values are [{}]".format(
                        value, opt, scanner.options[opt].constraint
                    )
                )
                continue

        # Then try to set it
        try:
            scanner.options[opt].value = value
            logger.info("[{}] set to [{}]".format(opt, value))
            return
        except (KeyError, PyinsaneException) as exc:
            logger.info("Failed to set [{}] to [{}]: [{}]".format(
                opt, str(value), str(exc))
            )
            last_exc = exc
    logger.warning("Failed to set [{}] to [{}]: [{}]".format(
        opt, values, last_exc)
    )
    raise last_exc


def __set_scan_area_pos(options, opt_name, select_value_func, missing_options):
    if opt_name not in options:
        if missing_options:
            missing_options.append(opt_name)
    else:
        if not options[opt_name].capabilities.is_active():
            logger.warning(
                "Unable to set scanner option [{}]:"
                " Option is not active".format(opt_name)
            )
            return
        constraint = options[opt_name].constraint
        if isinstance(constraint, tuple):
            value = select_value_func(constraint[0], constraint[1])
        elif isinstance(constraint, list):
            value = select_value_func(constraint)
        options[opt_name].value = value


def maximize_scan_area(scanner):
    """
    Utility function to make sure the scanner scan the biggest area possible.
    Must be called *after* setting the resolution.
    """
    opts = scanner.options
    missing_opts = []
    __set_scan_area_pos(opts, "tl-x", min, missing_opts)
    __set_scan_area_pos(opts, "tl-y", min, missing_opts)
    __set_scan_area_pos(opts, "br-x", max, missing_opts)
    __set_scan_area_pos(opts, "br-y", max, missing_opts)
    __set_scan_area_pos(opts, "page-height", max, None)
    __set_scan_area_pos(opts, "page-width", max, None)
    if missing_opts:
        logger.warning(
            "Failed to maximize the scan area. Missing options: {}".format(
                ", ".join(missing_opts)
            )
        )


def get_version():
    from . import _version
    return _version.version


__version__ = get_version()
