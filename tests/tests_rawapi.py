import sys
sys.path = ["src"] + sys.path

import unittest

import rawapi


class TestSaneInit(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        pass

    def tearDown(self):
        pass


def get_all_tests():
    all_tests = unittest.TestSuite()

    tests = unittest.TestSuite(
        [
            TestSaneInit("test_init"),
        ]
    )

    all_tests.addTest(tests)

    return all_tests
