#!/usr/bin/env python3

import pyinsane2


if __name__ == "__main__":
    pyinsane2.init()
    try:
        for device in pyinsane2.get_devices():
            print("%s" % (str(device)))

            for opt in device.options.values():
                print("  Option: %s" % (opt.name))
                print("    Title: %s" % (opt.title))
                print("    Desc: %s" % (opt.desc))
                print("    Type: %s" % (str(opt.val_type)))
                print("    Unit: %s" % (str(opt.unit)))
                print("    Size: %d" % (opt.size))
                print("    Capabilities: %s" % (str(opt.capabilities)))
                print("    Constraint type: %s" % (str(opt.constraint_type)))
                print("    Constraint: %s" % (str(opt.constraint)))
                try:
                    print("    Value: %s" % (str(opt.value)))
                except pyinsane2.PyinsaneException as exc:
                    # Some scanner allow changing a value, but not reading it.
                    # For instance Canon Lide 110 allow setting the resolution,
                    # but not reading it
                    print("    Value: Failed to get the value: %s" % str(exc))

            print("")
    finally:
        pyinsane2.exit()
