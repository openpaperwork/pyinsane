#!/usr/bin/env python

import sys
import unittest

from tests import tests_rawapi
from tests import tests_abstract

from src import abstract
from src import abstract_th

if __name__ == '__main__':
    print("Don't forget to turn at least one scanner on !")
    #print("---")
    #print("=== RawAPI: ===")
    #unittest.TextTestRunner(verbosity=3).run(
    #    tests_rawapi.get_all_tests())
    print("---")
    print("=== Abstract: ===")
    unittest.TextTestRunner(verbosity=3).run(
        tests_abstract.get_all_tests(abstract))
    print("---")
    print("=== Abstract Threaded: ===")
    unittest.TextTestRunner(verbosity=3).run(
        tests_abstract.get_all_tests(abstract_th))
