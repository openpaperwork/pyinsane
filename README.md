# PyInsane


## Description

Python implementation of the Sane API (using ctypes) and abstration layer.

Why Ctype ?
- To have a pure Python implementation (I don't like mixing languages)
- To not lock the other Python threads or other C bindings like
  python-imaging-sane tends to do (for instance it blocks the Gtk/Gobject
  main loop)

Beware: This implementation is not thread safe !

## Dependencies

libsane

## Installation

$ sudo python ./setup.py install

## Usage

### Scanner detection

	import pyinsane.abstract

	devices = pyinsance.abstract.get\_devices()
	assert(len(devices) > 0)
	device = devices[0]
	print "I'm going to use the following scanner: %s" % (str(device))
	scanner_id = device.name

or if you already know its name/id:

	import pyinsane.abstract

	device = pyinsane.abstract.Scanner(name="somethingsomething")
	print "I'm going to use the following scanner: %s" % (str(device))

### Simple scan

	device.options['resolution'].value = 300
	scan_instance = device.scan(multi=False)
	try:
		while True:
			scan_instance.read()
	except EOFError:
		pass
	image = scan_instance.get_img()

### Multiple scans using an automatic document feeder (ADF)

	if not "ADF" in device.options['source'].constraint:
		print "No document feeder found"
		return

	device.options['source'].value = "ADF"
	try:
		while True:
			scan_instance.read()
	except EOFError:
		pass
	for idx in range(0, scan_instance.get_nb_img())
		image = scan_instance.get_img(idx)

## Licence

GPL v3

