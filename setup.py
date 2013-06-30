#!/usr/bin/env python

from setuptools import setup

setup(name="pyinsane",
      version="1.0.3",
      description=("Pure Python implementation of the Sane API (using ctypes) and"
                   " abstration layer"),
      long_description=("Pure Python implementation of the Sane API (using"
                        " ctypes). Include a thread-safe abstration layer"),
      keywords="sane scanner",
      url="https://github.com/jflesch/pyinsane",
      download_url="https://github.com/jflesch/pyinsane/archive/v1.0.1.zip",
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      license="GPLv3+",
      author="Jerome Flesch",
      author_email="jflesch@gmail.com",
      packages=['pyinsane'],
      package_dir={ 'pyinsane': 'src' },
      data_files=[],
      scripts=[],
      install_requires=[
          "Pillow",
      ],
     )

