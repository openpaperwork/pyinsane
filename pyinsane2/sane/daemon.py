#!/usr/bin/env python3

import logging
import os
import pickle
import struct
import sys

import pyinsane2.sane.abstract as pyinsane


logger = logging.getLogger("Pyinsane_daemon")


device_cache = {}
scan_sessions = {}


def get_devices(local_only):
    global device_cache

    devices = pyinsane.get_devices(local_only)
    device_cache = {}
    for device in devices:
        device_cache[device.name] = device
    return devices


def get_device(scanner_name):
    global device_cache
    if scanner_name in device_cache:
        return device_cache[scanner_name]
    scanner = pyinsane.Scanner(scanner_name)
    device_cache[scanner_name] = scanner
    return scanner


def get_options(scanner_name):
    return get_device(scanner_name).options


def get_option_value(scanner_name, option_name):
    return get_device(scanner_name).options[option_name].value


def set_option_value(scanner_name, option_name, option_value):
    get_device(scanner_name).options[option_name].value = option_value


def make_scan_session(scanner_name, multiple=False):
    global scan_sessions

    scan_session = get_device(scanner_name).scan(multiple)
    scan_sessions[scanner_name] = scan_session
    return scan_session


def get_images(scanner_name):
    global scan_sessions
    imgs = scan_sessions[scanner_name].images
    imgs = [(img.mode, img.size, img.tobytes()) for img in imgs]
    return imgs


def scan_read(scanner_name):
    global scan_sessions
    return scan_sessions[scanner_name].scan.read()


def get_available_lines(scanner_name):
    global scan_sessions
    return scan_sessions[scanner_name].scan.available_lines


def get_expected_size(scanner_name):
    global scan_sessions
    return scan_sessions[scanner_name].scan.expected_size


def get_image(scanner_name, start_line, end_line):
    global scan_sessions
    img = scan_sessions[scanner_name].scan.get_image(start_line, end_line)
    return (img.mode, img.size, img.tobytes())


def cancel(scanner_name):
    global scan_sessions
    return scan_sessions[scanner_name].scan.cancel()


def exit():
    pass


COMMANDS = {
    "get_devices": get_devices,
    "get_options": get_options,
    "get_option_value": get_option_value,
    "set_option_value": set_option_value,
    "scan": make_scan_session,
    "get_images": get_images,
    "scan_read": scan_read,
    "scan_get_available_lines": get_available_lines,
    "scan_get_expected_size": get_expected_size,
    "scan_get_image": get_image,
    "scan_cancel": cancel,
    "exit": exit,
}


def main_loop(fifo_dir, fifo_filepaths):
    global COMMANDS

    pyinsane.init()

    length_size = len(struct.pack("i", 0))
    fifo_c2s = os.open(fifo_filepaths[0], os.O_RDONLY)
    fifo_s2c = os.open(fifo_filepaths[1], os.O_WRONLY)

    try:
        logger.info("Ready")

        while True:
            length = os.read(fifo_c2s, length_size)
            if length == b'':
                break
            length = struct.unpack("i", length)[0]
            cmd = os.read(fifo_c2s, length)
            if cmd == b'':
                break
            assert(len(cmd) == length)
            cmd = pickle.loads(cmd)

            logger.debug("> {}".format(cmd['command']))
            f = COMMANDS[cmd['command']]
            result = {}
            try:
                result['out'] = f(*cmd['args'], **cmd['kwargs'])
            except BaseException as exc:
                if (not isinstance(exc, EOFError) and
                        not isinstance(exc, StopIteration)):
                    logger.warning("Exception", exc_info=exc)
                result['exception'] = str(exc.__class__.__name__)
                result['exception_args'] = exc.args
                logger.debug("< {}".format(result))

            result = pickle.dumps(result)
            length = len(result)
            length = struct.pack("i", length)
            os.write(fifo_s2c, length)
            os.write(fifo_s2c, result)

            if cmd['command'] == 'exit':
                break
    finally:
        os.close(fifo_s2c)
        os.close(fifo_c2s)

    logger.info("Daemon stopped")


if __name__ == "__main__":
    formatter = logging.Formatter(
        '%(levelname)-6s %(name)-10s %(message)s'
    )
    l = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    l.addHandler(handler)
    l.setLevel(logging.INFO)

    main_loop(sys.argv[1], sys.argv[2:4])
