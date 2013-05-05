#!/usr/bin/env python

import sys

import src.abstract as abstract
import src.rawapi as rawapi

def set_scanner_opt(scanner, opt, value):
    print "Setting %s to %s" % (opt, str(value))
    try:
        scanner.options[opt].value = value
    except rawapi.SaneException, exc:
        print "Failed to set %s to %s: %s" % (opt, str(value), str(exc))


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print "Syntax:"
        print "  %s <output file (JPG)>" % sys.argv[0]
        sys.exit(1)

    output_file = sys.argv[1]
    print "Output file: %s" % output_file

    print "Looking for scanners ..."
    devices = abstract.get_devices()
    if (len(devices) <= 0):
        print "No scanner detected !"
        sys.exit(1)
    print "Devices detected:"
    print "- " + "\n- ".join([str(d) for d in devices])

    print ""

    device = devices[0]
    print "Will use: %s" % str(device)

    print ""

    set_scanner_opt(device, 'resolution', 300)
    set_scanner_opt(device, 'source', 'Auto')
    set_scanner_opt(device, 'mode', 'Color')

    print ""

    print "Scanning ...  "
    scan_src = device.scan(multiple=False)
    try:
        PROGRESSION_INDICATOR = ['|', '/', '-', '\\']
        i = -1
        while True:
            i += 1
            i %= len(PROGRESSION_INDICATOR)
            sys.stdout.write("\b%s" % PROGRESSION_INDICATOR[i])
            sys.stdout.flush()

            scan_src.read()
    except EOFError:
        pass

    print "\b "
    print "Writing output file ..."
    img = scan_src.get_img()
    img.save(output_file, "JPEG")
    print "Done"
