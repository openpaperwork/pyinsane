import os

if os.name == "nt":
    from .wia.abstract import *
else:
    from .sane.abstract_proc import *
