#!/usr/bin/env python

import sys
import unittest

from tests import tests_rawapi
from tests import tests_abstract

from src import abstract
from src import abstract_th

if __name__ == '__main__':
    test_set = ["rawapi", "abstract", "abstract_th"]
    if "-h" in sys.argv or "--help" in sys.argv:
        print("%s [tests [tests [...]]]" % sys.argv[0])
        print("")
        print("Available tests: %s" % " ".join(test_set))
        print("By default, all the tests are run")
        sys.exit(1)
    if len(sys.argv) >= 2:
        test_set = sys.argv[1:]

    if "rawapi" in test_set:
        print("=== RawAPI: ===")
        unittest.TextTestRunner(verbosity=3).run(
           tests_rawapi.get_all_tests())
        print("---")
    if "abstract" in test_set:
        print("=== Abstract: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(abstract))
        print("---")
    if "abstract_th" in test_set:
        print("=== Abstract Threaded: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(abstract_th))
