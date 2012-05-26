import sys
sys.path = ["src"] + sys.path

import unittest

import abstract


def get_all_tests():
    all_tests = unittest.TestSuite()

    tests = unittest.TestSuite([])

    all_tests.addTest(tests)

    return all_tests

