#!/usr/bin/env python

from setuptools import setup

setup(
    name="pyinsane",
    version="1.3.8",
    description=("Pure Python implementation of the Sane API (using ctypes)"
                 " and abstration layer"),
    long_description=("Pure Python implementation of the Sane API (using"
                      " ctypes). Include a thread-safe abstraction layer"),
    keywords="sane scanner",
    url="https://github.com/jflesch/pyinsane",
    download_url="https://github.com/jflesch/pyinsane/archive/v1.3.4.zip",
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
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="GPLv3+",
    author="Jerome Flesch",
    author_email="jflesch@gmail.com",
    packages=['pyinsane'],
    package_dir={'pyinsane': 'src'},
    data_files=[],
    scripts=[],
    install_requires=[
        "Pillow",
    ],
)
