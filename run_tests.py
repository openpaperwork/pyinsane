#!/usr/bin/env python

import sys
import unittest

from tests import tests_saneapi
from tests import tests_abstract

from src.sane import abstract as sane_abstract
from src.sane import abstract_proc as sane_abstract_proc
from src.sane import abstract_th as sane_abstract_th


if __name__ == '__main__':
    test_set = [
        "sane_rawapi",
        "sane_abstract",
        "sane_abstract_th",
        "sane_abstract_proc"
    ]
    if "-h" in sys.argv or "--help" in sys.argv:
        print("%s [tests [tests [...]]]" % sys.argv[0])
        print("")
        print("Available tests: %s" % " ".join(test_set))
        print("By default, all the tests are run")
        sys.exit(1)
    if len(sys.argv) >= 2:
        test_set = sys.argv[1:]

    if "sane_rawapi" in test_set:
        print("=== Sane API: ===")
        unittest.TextTestRunner(verbosity=3).run(
           tests_saneapi.get_all_tests())
        print("---")
    if "sane_abstract" in test_set:
        print("=== Sane Abstract: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(sane_abstract))
        print("---")
    if "sane_abstract_th" in test_set:
        print("=== Sane Abstract Threaded: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(sane_abstract_th))
    if "sane_abstract_proc" in test_set:
        print("=== Sane Abstract Separate Process: ===")
        unittest.TextTestRunner(verbosity=3).run(
            tests_abstract.get_all_tests(sane_abstract_proc))
