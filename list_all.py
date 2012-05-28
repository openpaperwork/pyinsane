#!/usr/bin/env python

import src.abstract as pyinsane

if __name__ == "__main__":
    for device in pyinsane.get_devices():
        print "%s" % (str(device))

        for opt in device.options.values():
            print "  Option: %s" % (opt.name)
            print "    Title: %s" % (opt.title)
            print "    Desc: %s" % (opt.desc)
            print "    Type: %s" % (str(opt.val_type))
            print "    Unit: %s" % (str(opt.unit))
            print "    Size: %d" % (opt.size)
            print "    Capabilities: %s" % (str(opt.capabilities))
            print "    Constraint type: %s" % (str(opt.constraint_type))
            print "    Constraint: %s" % (str(opt.constraint))
            print "    Value: %s" % (str(opt.value))

        print ""
