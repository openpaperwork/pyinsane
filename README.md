# PyInsane


## Description

Python implementation of the Sane API (using ctypes) and abstration layer.

Why Ctype ?
- To have a pure Python implementation (I don't like mixing languages)
- To not lock the other Python threads or other C bindings like
  python-imaging-sane tends to do (for instance it blocks the Gtk/Gobject
  main loop)

## Installation

$ sudo python ./setup.py install

## Licence

GPL v3

