#!/usr/bin/env python

from setuptools import setup

setup(
    name="pyinsane",
    version="2.0.0-git",
    description=("Python library to access and use scanner devices"),
    long_description=("Python library to access and use scanner devices"),
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
    ],
    package_dir={
        'pyinsane': 'src',
        'pyinsane.sane': 'src/sane',
    },
    data_files=[],
    scripts=[],
    install_requires=[
        "Pillow",
    ],
)
