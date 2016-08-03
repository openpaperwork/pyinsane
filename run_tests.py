#!/usr/bin/env python

import sys
import unittest

from tests import tests_saneapi
from tests import tests_abstract

from src import abstract
from src import abstract_proc
from src import abstract_th


if __name__ == '__main__':
    test_set = ["saneapi", "abstract", "abstract_th", "abstract_proc"]
    if "-h" in sys.argv or "--help" in sys.argv:
        print("%s [tests [tests [...]]]" % sys.argv[0])
        print("")
        print("Available tests: %s" % " ".join(test_set))
        print("By default, all the tests are run")
        sys.exit(1)
    if len(sys.argv) >= 2:
        test_set = sys.argv[1:]

    if "saneapi" in test_set:
        print("=== SaneAPI: ===")
        unittest.TextTestRunner(verbosity=3).run(
           tests_saneapi.get_all_tests())
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
    if "abstract_proc" in test_set:
        print("=== Abstract Separate Process: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(abstract_proc))
