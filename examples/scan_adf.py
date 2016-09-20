#!/usr/bin/env python3

import os
import sys

import pyinsane2


def main(args):
    dstdir = args[0]

    devices = pyinsane2.get_devices()
    assert(len(devices) > 0)
    device = devices[0]

    print("Will use the scanner [%s](%s)"
          % (str(device), device.name))

    pyinsane2.set_scanner_opt(device, "source", ["ADF", "Feeder"])
    # Beware: Some scanner have "Lineart" or "Gray" as default mode
    pyinsane2.set_scanner_opt(device, "mode", ["Color"])
    pyinsane2.maximize_scan_area()

    scan_session = device.scan(multiple=True)

    try:
        print("Scanning ...")
        while True:
            try:
                scan_session.scan.read()
            except EOFError:
                print("Got page %d" % (len(scan_session.images)))
                img = scan_session.images[-1]
                imgpath = os.path.join(dstdir, "%d.jpg" %
                                       (len(scan_session.images)))
                img.save(imgpath)
    except StopIteration:
        print("Got %d pages" % len(scan_session.images))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) <= 0 or args[0][0] == '-':
        print("Usage:")
        print("  %s <dst directory>" % sys.argv[0])
        sys.exit(1)
    main(args)
