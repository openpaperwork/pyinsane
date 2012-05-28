# PyInsane

## Description

Python implementation of the Sane API (using ctypes) and abstration layer.

The code is divided in 3 layers:
- rawapi : Ctypes binding to the raw Sane API
- abstract : An Object-Oriented layer that simplifies the use of the Sane API
  and try to avoid possible misuse of the Sane API. When scanning, it also takes
  care of returning a PIL image.
- abstract\_th : The Sane API is absolutely not thread-safe. This layer solves
  this problem but using a fully dedicated thread.

## Dependencies

libsane

## Installation

$ sudo python ./setup.py install

## Usage

### Scanner detection

	import pyinsane.abstract as pyinsane

	devices = pyinsane.get_devices()
	assert(len(devices) > 0)
	device = devices[0]
	print "I'm going to use the following scanner: %s" % (str(device))
	scanner_id = device.name

or if you already know its name/id:

	import pyinsane.abstract as pyinsane

	device = pyinsane.Scanner(name="somethingsomething")
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

### Abstract\_th

	import pyinsane.abstract_th as pyinsane

	# When imported, it will start a new thread, dedicated to Sane.
	# Its API is the same than for pyinsane.abstract. You can use it the
	# same way.
	# Note however that the Sane thread can only do one thing at a time,
	# so some function call may be on hold on a semaphore for some times.

## Licence

GPL v3

