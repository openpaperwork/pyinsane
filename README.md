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
- Python 2.7 (GNU/Linux only)
- Python 3.x (GNU/Linux and Windows)

Not tested but should work too:
- Handheld image scanners


## Dependencies

On all platforms:
- [Pillow](https://github.com/python-imaging/Pillow#readme) (if the abstraction layer is used)

Platform specific:
- GNU/Linux, *BSD, MacOSX, etc: [libsane](http://www.sane-project.org/)


## Installation

```sh
# recommanded to get the latest stable version
sudo pip install pyinsane2
```

or

```sh
# for the development version
git clone https://github.com/jflesch/pyinsane.git
cd pyinsane
sudo python3 ./setup.py install
```


## Tests

```sh
python3 ./setup.py nosetests --tests tests.tests_saneapi  # GNU/Linux
python3 ./setup.py nosetests --tests tests.tests_wiaapi  # Windows
python3 ./setup.py nosetests --tests tests.tests_abstract
```

Tests require at least one scanner with a flatbed and an ADF (Automatic
Document Feeder).

If possible, they should be run with at least 2 scanners connected. The first
that appear in "scanimage -L" must be the one with the ADF.

For reference, my current setup is:
- HP Officejet 4620 (Flatbed + ADF)
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
	devices = pyinsane2.get_devices()
	assert(len(devices) > 0)
	device = devices[0]
	print("I'm going to use the following scanner: %s" % (str(device)))

	pyinsane2.set_scanner_opt(device, 'resolution', [300])

# Beware: Some scanners have "Lineart" or "Gray" as default mode
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
	devices = pyinsane2.get_devices()
	assert(len(devices) > 0)
	device = devices[0]
	print("I'm going to use the following scanner: %s" % (str(device)))

	try:
		pyinsane2.set_scanner_opt(device, 'source', ['ADF', 'Feeder'])
	except PyinsaneException:
		print("No document feeder found")
		return

# Beware: Some scanners have "Lineart" or "Gray" as default mode
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


### Scanner's options

The options available depends on the backend and on the specific driver used.

The WIA implementation emulates common Sane options ('tl-x', 'br-x', 'tl-y', 'br-y',
'color', 'mode', 'source'). So you should use Sane options by default.

See [the Sane documentation](http://www.sane-project.org/html/doc014.html) for the
most common options.

Beware options casing can change between WIA and Sane implementation !
You should use ```pyinsane2.set_scanner_opt()``` whenever possible.


You can access the option values with:

```py
device.options['option_name'].value
```

You can set the option values with:

```py
device.options['option_name'].value = new_value
# or use the helper:
pyinsane2.set_scanner_opt(
    device, 'option_name',
    ['possible_new_value_1', 'possible_new_value_2']
)
```

You can get the constraint (accepted values) with:

```py
device.options['option_name'].constraint
```

Constraints are usually:

* None : unknown constraints / no constraint
* tuple : ```(min_value, max_value)```
* list : possible values (Ex: ```['Flatbed', 'Feeder']``` or ```[75, 150, 300]```)


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

When ```pyinsane2.init()``` is called, it will create 2 Unix pipes (FIFO)
in your temporary directory and a dedicated process. To avoid forking
other file descriptors from your program, you should initialize pyinsane2
as soon as possible.

Building requires nothing except Python. Libsane is loaded dynamically using ```ctypes```.


### Note regarding the WIA 2 implementation

Build requires:

* Either Python 3.4 + Windows SDK 7.1 (Visual C++ 2010) + Windows DDK (aka WDK)
* Or Python 3.5 + Visual C++ 2016 (included in Visual Studio 2016)

(see [the Python wiki for more information](https://wiki.python.org/moin/WindowsCompilers))

WIA provides one WiaItem2 by possible source (Flatbed, ADF, etc). And each of
these items has its own properties.

To make the model consistent with Sane, all the properties have been merged in
the same list. When you update a property specific to sources, it is updated
on all the WIAItem2. The update is considered successful if it worked at
least on one.

Some properties are emulated to make the API behavior consistent with the Sane
implementation. The WIA implementation emulates common Sane options
('tl-x', 'br-x', 'tl-y', 'br-y', 'color', 'mode', 'source').
If your program must be cross-platform, you are strongly advised to use
these emulated options instead of the WIA ones ('xpos', 'ypos', 'xextent',
'yextent', etc).


### Other examples

The folder 'examples' contains more detailed examples.
For instance, examples/scan.py shows how to get pieces of a scan as it goes.

To run one of these scripts, run:

	python -m examples.[script] [args]

For instance

	python -m examples.scan toto.png


## Contact

* [Mailing-list](https://github.com/jflesch/paperwork/wiki/Contact#mailing-list)
* [Bug tracker](https://github.com/jflesch/pyinsane/issues/)


## Licence

GPL v3
2012-2016(c) Jerome Flesch (<jflesch@gmail.com>)
