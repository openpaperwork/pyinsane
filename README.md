# PyInsane

## Description

Pure python implementation of the libsane (using ctypes) and abstration layers.

[Libsane (part of the Sane)](http://www.sane-project.org/) provides drivers for scanners under GNU/Linux and *BSD systems.

The code is divided in 3 layers:
- rawapi : Ctypes binding to the raw Sane API
- abstract : An Object-Oriented layer that simplifies the use of the Sane API
  and try to avoid possible misuse of the Sane API. When scanning, it also takes
  care of returning a Pillow image.
- abstract\_th : The Sane API is not thread-safe and cannot be used in a
  multi-threaded environment easily. This layer solves this problem by using
  a fully dedicated thread.

## Dependencies

libsane
[Pillow](https://github.com/python-imaging/Pillow#readme) (if the abstraction layer is used)

## Installation

	$ sudo pip install pyinsane

or

	$ git clone https://github.com/jflesch/pyinsane.git
	$ cd pyinsane
	$ sudo python ./setup.py install


## Unit tests

	$ python ./run_tests.py

Unit tests require at least one scanner with a flatbed and an ADF (Automatic
Document Feeder).

If possible, they should be run with at least 2 scanners connected. The first that appear in "scanimage -L" must be the one with the ADF.

My current setup:
- HP Officejet 4500 G510g (Flatbed + ADF)
- HP Deskjet 2050 J510 series (Flatbed)

## Usage

### Scanner detection

```py
import pyinsane.abstract as pyinsane

devices = pyinsane.get_devices()
assert(len(devices) > 0)
device = devices[0]

print("I'm going to use the following scanner: %s" % (str(device)))
scanner_id = device.name
```

or if you already know its name/id:

```py
import pyinsane.abstract as pyinsane

device = pyinsane.Scanner(name="somethingsomething")
print("I'm going to use the following scanner: %s" % (str(device)))
```

### Simple scan

```py
device.options['resolution'].value = 300
# Beware: Some scanner have "Lineart" or "Gray" as default mode
device.options['mode'].value = 'Color'
scan_session = device.scan(multiple=False)
try:
	while True:
		scan_session.scan.read()
except EOFError:
	pass
image = scan_session.images[0]
```

### Multiple scans using an automatic document feeder (ADF)

```py
if not "ADF" in device.options['source'].constraint:
	print("No document feeder found")
	return

device.options['source'].value = "ADF"
# Beware: Some scanner have "Lineart" or "Gray" as default mode
device.options['mode'].value = 'Color'
scan_session = device.scan(multiple=True)
try:
	while True:
		try:
			scan_session.scan.read()
		except EOFError:
			print ("Got a page ! (current number of pages read: %d)"
				   % (len(scan_session.images)))
except StopIteration:
	print("Document feeder is now empty. Got %d pages"
	      % len(scan_session.images))
for idx in range(0, len(scan_session.images)):
	image = scan_session.images[idx]
```

### Abstract\_th

```py
import pyinsane.abstract_th as pyinsane

# When imported, it will start a new thread, dedicated to Sane.
# Its API is the same than for pyinsane.abstract. You can use it the
# same way.
# Note however that the Sane thread can only do one thing at a time,
# so some function call may be on hold on a semaphore for some times.
```

### Other examples

The folder 'examples' contains more detailed examples.
For instance, examples/scan.py shows how to get pieces of a scan as it goes.

To run one of these scripts, run:

	python -m examples.[script] [args]

For instance

	python -m examples.scan toto.png

## Licence

GPL v3
2012(c) Jerome Flesch (<jflesch@gmail.com>)

