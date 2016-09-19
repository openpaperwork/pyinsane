import os
import sys

__all__ = [
    'init',
    'exit',
    'Scanner',
    'ScannerOption',
    'PyinsaneException',
    'get_devices',
]

from .util import PyinsaneException

if os.name == "nt":
    from .wia.abstract import *
else:
    from .sane.abstract_proc import *