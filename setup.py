#!/usr/bin/env python

import os
import platform
import sys

from setuptools import Extension
from setuptools import setup, find_packages

if platform.architecture()[0] == '32bit':
    DEFAULT_ATL_WINDDK_LIB_DIR = "c:\\winddk\\7600.16385.1\\lib\\ATL\\amd64"
else:
    DEFAULT_ATL_WINDDK_LIB_DIR = "c:\\winddk\\7600.16385.1\\lib\\ATL\\i386"


try:
    with open("pyinsane2/_version.py", "r") as file_descriptor:
        version = file_descriptor.read().strip()
        version = version.split(" ")[2][1:-1]
    print("Pyinsane version: {}".format(version))
    if "-" in version:
        version = version.split("-")[0]
except FileNotFoundError:
    print("ERROR: _version.py file is missing")
    print("ERROR: Please run 'make version' first")
    sys.exit(1)


if os.name == "nt":
    extensions = [
        Extension(
            'pyinsane2.wia._rawapi', [
                'pyinsane2/wia/properties.cpp',
                'pyinsane2/wia/rawapi.cpp',
                'pyinsane2/wia/trace.cpp',
                'pyinsane2/wia/transfer.cpp',
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
    version=version,
    description=(
        "Python library to access and use image scanners (Linux/Windows/etc)"
    ),
    long_description=(
        "Python library to access and use image scanners (devices)."
        " Works on GNU/Linux (Sane), *BSD (Sane), Windows >= Vista (WIA 2),"
        " MacOSX (Sane), etc."
    ),
    keywords="sane scanner",
    url="https://github.com/openpaperwork/pyinsane",
    download_url=(
        "https://github.com/openpaperwork/pyinsane/archive/"
        "{}.zip".format(version)
    ),
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
    author_email="jflesch@openpaper.work",
    packages=find_packages(exclude=['examples', 'tests']),
    data_files=[],
    scripts=[],
    install_requires=[
        "Pillow",
    ],
    ext_modules=extensions,
    zip_safe=(os.name != "nt"),
    setup_requires=['nose>=1.0'],
)
