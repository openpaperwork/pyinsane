#!/usr/bin/env python

import os
import sys

import pyinsane.abstract as pyinsane

def main(args):
    dstdir = args[0]

    devices = pyinsane.get_devices()
    assert(len(devices) > 0)
    device = devices[0]

    print("Will use the scanner [%s]" % (str(device)))
    scanner_id = device.name

    possible_srcs = device.options['source'].constraint
    adf_src = None
    for src in possible_srcs:
        if "ADF" in src or "Feeder" in src:
            adf_src = src
            break

    if adf_src is None:
        print("No document feeder found")
        sys.exit(1)

    print("Will use the source [%s]" % adf_src)

    device.options['source'].value = "ADF"
    # Beware: Some scanner have "Lineart" or "Gray" as default mode
    device.options['mode'].value = 'Color'
    scan_session = device.scan(multiple=True)

    try:
        while True:
            try:
                scan_session.scan.read()
            except EOFError:
                print ("Got a page ! (current number of pages read: %d)"  %
                       (len(scan_session.images)))
                img = scan_session.images[-1]
                imgpath = os.path.join(dstdir, "%d.jpg" %
                                       (len(scan_session.images)))
                img.save(imgpath)
    except StopIteration:
        print("Document feeder is now empty")
        print("Got %d pages" % len(scan_session.images))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) <= 0 or args[0][0] == '-':
        print("Usage:")
        print("  %s <dst directory>" % sys.argv[0])
        sys.exit(1)
    main(args)
