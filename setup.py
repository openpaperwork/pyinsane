#!/usr/bin/env python

import os
import platform

from setuptools import Extension
from setuptools import setup

if platform.architecture()[0] == '32bit':
    DEFAULT_ATL_WINDDK_LIB_DIR = "c:\\winddk\\7600.16385.1\\lib\\ATL\\amd64"
else:
    DEFAULT_ATL_WINDDK_LIB_DIR = "c:\\winddk\\7600.16385.1\\lib\\ATL\\i386"

if os.name == "nt":
    extensions = [
        Extension(
            'pyinsane2.wia._rawapi', [
                'src/pyinsane2/wia/properties.cpp',
                'src/pyinsane2/wia/rawapi.cpp',
                'src/pyinsane2/wia/transfer.cpp',
            ],
            include_dirs=[
                # Yeah, I know.
                os.getenv(
                    "WINDDK_INCLUDE_DIR",
                    "c:\\winddk\\7600.16385.1\\inc\\atl71"
                ),
            ],
            library_dirs=[
                # Yeah, I know.
                os.getenv("WINDDK_LIB_DIR", DEFAULT_ATL_WINDDK_LIB_DIR),
            ],
            libraries=[
                "ole32",
                "wiaguid",
            ],
            # extra_compile_args=['/W4'],
            undef_macros=['NDEBUG'],
        ),
    ]
else:
    extensions = []

setup(
    name="pyinsane2",
    version="2.0.5",
    description=(
        "Python library to access and use image scanners (Linux/Windows/etc)"
    ),
    long_description=(
        "Python library to access and use image scanners (devices)."
        " Works on GNU/Linux (Sane), *BSD (Sane), Windows >= Vista (WIA 2),"
        " MacOSX (Sane), etc."
    ),
    keywords="sane scanner",
    url="https://github.com/jflesch/pyinsane",
    download_url="https://github.com/jflesch/pyinsane/archive/2.0.2.zip",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later"
        " (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="GPLv3+",
    author="Jerome Flesch",
    author_email="jflesch@gmail.com",
    packages=[
        'pyinsane2',
        'pyinsane2.sane',
        'pyinsane2.wia',
    ],
    package_dir={
        'pyinsane2': 'src/pyinsane2',
        'pyinsane2.sane': 'src/pyinsane2/sane',
        'pyinsane2.wia': 'src/pyinsane2/wia',
    },
    data_files=[],
    scripts=[],
    install_requires=[
        "Pillow",
    ],
    ext_modules=extensions,
    setup_requires=['nose>=1.0'],
)
