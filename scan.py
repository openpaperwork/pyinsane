#!/usr/bin/env python

import sys

sys.path += ['src']

import abstract as pyinsane

def set_scanner_opt(scanner, opt, value):
    print("Setting %s to %s" % (opt, str(value)))
    try:
        scanner.options[opt].value = value
    except (KeyError, pyinsane.SaneException) as exc:
        print("Failed to set %s to %s: %s" % (opt, str(value), str(exc)))


if __name__ == "__main__":
    steps = False

    args = sys.argv[1:]
    if len(args) <= 0:
        print("Syntax:")
        print("  %s [-s] <output file (JPG)>" % sys.argv[0])
        print("")
        print("Options:")
        print("  -s : Generate intermediate images (may generate a lot of"
              " images !)")
        sys.exit(1)

    for arg in args[:]:
        if arg == "-s":
            steps = True
            args.remove(arg)

    output_file = args[0]
    print("Output file: %s" % output_file)

    print("Looking for scanners ...")
    devices = pyinsane.get_devices()
    if (len(devices) <= 0):
        print("No scanner detected !")
        sys.exit(1)
    print("Devices detected:")
    print("- " + "\n- ".join([str(d) for d in devices]))

    print("")

    device = devices[0]
    print("Will use: %s" % str(device))

    print("")

    source = 'Auto'
    # beware: don't select a source that is not in the constraint,
    # with some drivers (Brother DCP-8025D for instance), it may segfault.
    if (device.options['source'].constraint_type
        == pyinsane.SaneConstraintType.STRING_LIST):
        if 'Auto' in device.options['source'].constraint:
            source = 'Auto'
        elif 'FlatBed' in device.options['source'].constraint:
            source = 'FlatBed'
    else:
        print("Warning: Unknown constraint type on the source: %d"
              % device.options['source'].constraint_type)

    set_scanner_opt(device, 'resolution', 300)
    set_scanner_opt(device, 'source', source)
    set_scanner_opt(device, 'mode', 'Color')

    print("")

    print("Scanning ...  ")
    scan_session = device.scan(multiple=False)

    if steps:
        last_line = 0

    try:
        PROGRESSION_INDICATOR = ['|', '/', '-', '\\']
        i = -1
        while True:
            i += 1
            i %= len(PROGRESSION_INDICATOR)
            sys.stdout.write("\b%s" % PROGRESSION_INDICATOR[i])
            sys.stdout.flush()

            scan_session.scan.read()

            if steps:
                next_line = scan_session.scan.available_lines[1]
                if (next_line > last_line):
                    img = scan_session.scan.get_image(last_line, next_line)
                last_line = next_line
    except EOFError:
        pass

    print("\b ")
    print("Writing output file ...")
    img = scan_session.images[0]
    img.save(output_file, "JPEG")
    print("Done")
