# PyInsane 2

## Description

Python library to access and use image scanners.

Support for:
- [Sane](http://www.sane-project.org/) (Scanners on GNU/Linux, *BSD, MacOSX, etc)
- WIA 2 (Windows Image Acquisition ; Scanners on Microsoft Windows >= Vista)

It supports:
- Flatbed
- Automatic Document Feeder
- While scanning, can provide chunks of the image for on-the-fly preview
  (see [Paperwork](https://github.com/jflesch/paperwork/) for instance)
- Python 3.0

Not tested but should work too:
- Handheld image scanners


## Dependencies

On all platforms:
- [Pillow](https://github.com/python-imaging/Pillow#readme) (if the abstraction layer is used)

Platform specific:
- GNU/Linux, *BSD, MacOSX, etc: [libsane](http://www.sane-project.org/)


## Installation

	# recommanded to get the latest stable version
	$ sudo pip install pyinsane2

or

	# for the development version
	$ git clone https://github.com/jflesch/pyinsane.git
	$ cd pyinsane
	$ sudo python3 ./setup.py install


## Unit tests

	$ python3 ./run_tests.py

Unit tests require at least one scanner with a flatbed and an ADF (Automatic
Document Feeder).

If possible, they should be run with at least 2 scanners connected. The first
that appear in "scanimage -L" must be the one with the ADF.

For reference, my current setup is:
- HP Officejet 4500 G510g (Flatbed + ADF)
- HP Deskjet 2050 J510 series (Flatbed)


## Usage

### Scanner detection

```py
import pyinsane2

pyinsane2.init()
try:
	devices = pyinsane2.get_devices()
	assert(len(devices) > 0)
	device = devices[0]

	print("I'm going to use the following scanner: %s" % (str(device)))
	scanner_id = device.name
finally:
	pyinsane2.exit()
```

or if you already know its name/id:

```py
import pyinsane2

pyinsane2.init()
try:
	device = pyinsane2.Scanner(name="somethingsomething")
	print("I'm going to use the following scanner: %s" % (str(device)))
finally:
	pyinsane2.exit()
```


### Simple scan

```py
import pyinsane2

pyinsane2.init()
try:
	pyinsane2.set_scanner_opt(device, 'resolution', [300])

# Beware: Some scanner have "Lineart" or "Gray" as default mode
# better set the mode everytime
	pyinsane2.set_scanner_opt(device, 'mode', ['Color'])

# Beware: by default, some scanners only scan part of the area
# they could scan.
	pyinsane2.maximize_scan_area(device)

	scan_session = device.scan(multiple=False)
	try:
		while True:
			scan_session.scan.read()
	except EOFError:
		pass
	image = scan_session.images[-1]
finally:
	pyinsane2.exit()
```

See examples/scan.py for a more complete example.


### Multiple scans using an automatic document feeder (ADF)

```py
import pyinsane2

pyinsane2.init()
try:
	try:
		pyinsane2.set_scanner_opt(device, 'source', ['ADF', 'Feeder'])
	except PyinsaneException:
		print("No document feeder found")
		return

# Beware: Some scanner have "Lineart" or "Gray" as default mode
# better set the mode everytime
	pyinsane2.set_scanner_opt(device, 'mode', ['Color'])

# Beware: by default, some scanners only scan part of the area
# they could scan.
	pyinsane2.maximize_scan_area(device)

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
finally:
	pyinsane2.exit()
```


### Note regarding the options

The options available depends on the backend and on the specific driver used.

The WIA implementation emulates common Sane option ('tl-x', 'br-x', 'tl-y', 'br-y',
'color', 'mode', 'source'). So you should use Sane options by default.

See [the Sane documentation](http://www.sane-project.org/html/doc014.html) for the
most common options.

Beware options casing can change between WIA and Sane implementation !
You should use ```pyinsane2.set_scanner_opt()``` whenever possible.


### Note regarding the Sane implementation

When using the Sane API as is, some issues with some Sane drivers can become
obvious in complex programs (uninitialized memory bytes, segfault, etc).
You can get corrupted images or even crash your program.

This module works around issues like the following one by using a dedicated
process for scanning:

<table border="0">
	<tr>
		<td>
			<img src="https://raw.githubusercontent.com/jflesch/pyinsane/stable/doc/sane_driver_corrupted_mem.png" alt="corrupted scan" width="359" height="300" />
		</td>
		<td>
			--&gt;
		</td>
		<td>
			<img src="https://raw.githubusercontent.com/jflesch/pyinsane/stable/doc/sane_proc_workaround.png" alt="scan fine" width="352" height="308" />
		</td>
	</tr>
</table>

(see [this comment for details](https://github.com/jflesch/paperwork/issues/486#issuecomment-233925642))

When imported, it will create 2 Unix pipes (FIFO) in your temporary directory
and a dedicated process. To avoid forking useless extra file descriptors, you
should import this module as soon as possible in your program.


### Other examples

The folder 'examples' contains more detailed examples.
For instance, examples/scan.py shows how to get pieces of a scan as it goes.

To run one of these scripts, run:

	python -m examples.[script] [args]

For instance

	python -m examples.scan toto.png


## Details regarding Sane backend

On GNU/Linux, *BSD and MacOSX system, the backend used for scanning is Sane (aka Libsane).
[Sane (part of the Sane)](http://www.sane-project.org/) provides drivers for scanners
under GNU/Linux and *BSD systems.

The code in 'pyinsane.sane' is divided in 2 layers:
- rawapi : Ctypes binding to the raw Sane API
- abstract : An Object-Oriented layer that simplifies the use of the Sane API
  and try to avoid possible misuse of the Sane API. When scanning, it also takes
  care of returning a Pillow image.

Two workaround are provided:
- abstract\_th : The Sane API is not thread-safe and cannot be used in a
  multi-threaded environment easily. This layer solves this problem by using
  a fully dedicated thread. It provides the very same API than 'abstract'
  (deprecated ; use 'abstract\_proc' instead)
- abstract\_proc : Some Sane drivers corrupts memory or return uninitalized bytes.
  (sometimes they even segfault). They usually work well in simple programs but
  can make bugs on more complex ones (see below). This module, when imported,
  fork() + exec() a small daemon in charge of doing the scans and return them
  to the main program using Unix pipes (FIFO). It provides the very same API than
  'abstract'.


## Licence

GPL v3
2012-2016(c) Jerome Flesch (<jflesch@gmail.com>)
