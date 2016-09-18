import os

from .util import PyinsaneException

if os.name == "nt":
    from .wia.abstract import *
else:
    from .sane.abstract_proc import *

__all__ = [
    'Scanner',
    'ScannerOption',
    'PyinsaneException',
    'get_devices',
]