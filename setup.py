#!/usr/bin/env python

import os

from setuptools import Extension
from setuptools import setup

if os.name == "nt":
    extensions = [
        Extension(
            'pyinsane.wia._rawapi', [
                'src/pyinsane/wia/properties.cpp',
                'src/pyinsane/wia/rawapi.cpp',
                'src/pyinsane/wia/transfer.cpp',
            ],
            include_dirs=[],
            libraries=[
                "ole32",
                "wiaguid",
            ],
            extra_compile_args=['/W4'],
            undef_macros=['NDEBUG'],
        ),
    ]

setup(
    name="pyinsane",
    version="2.0.0-git",
    description=("Python library to access and use image scanners"),
    long_description=("Python library to access and use image scanners (devices)"),
    keywords="sane scanner",
    url="https://github.com/jflesch/pyinsane",
    download_url="https://github.com/jflesch/pyinsane/archive/v1.4.0.zip",
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
        'pyinsane',
        'pyinsane.sane',
        'pyinsane.wia',
    ],
    package_dir={
        'pyinsane': 'src/pyinsane',
        'pyinsane.sane': 'src/pyinsane/sane',
        'pyinsane.wia': 'src/pyinsane/wia',
    },
    data_files=[],
    scripts=[],
    install_requires=[
        "Pillow",
    ],
    ext_modules=extensions,
    setup_requires=['nose>=1.0'],
)
