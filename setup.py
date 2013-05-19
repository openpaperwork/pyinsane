#!/usr/bin/env python

from setuptools import setup

setup(name="pyinsane",
      version="1.0.1-git",
      description=("Python implementation of the Sane API (using ctypes) and"
                   " abstration layer"),
      author="Jerome Flesch",
      author_email="jflesch@gmail.com",
      packages=['pyinsane'],
      package_dir={ 'pyinsane': 'src' },
      data_files=[],
      scripts=[],
      install_requires=[
          "PIL",
      ],
     )

