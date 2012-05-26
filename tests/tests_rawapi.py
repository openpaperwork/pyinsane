import sys
sys.path = ["src"] + sys.path

import unittest

import rawapi


class TestSaneInit(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        out = rawapi.sane_init()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], rawapi.SaneStatus(rawapi.SaneStatus.GOOD))
        self.assertTrue(out[1].is_current())
        rawapi.sane_exit()

    def tearDown(self):
        pass

class TestSaneGetDevices(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()

    def test_get_devices(self):
        pass

    def tearDown(self):
        rawapi.sane_exit()


def get_all_tests():
    all_tests = unittest.TestSuite()

    tests = unittest.TestSuite([TestSaneInit("test_init")])
    all_tests.addTest(tests)

    tests = unittest.TestSuite([TestSaneGetDevices("test_get_devices")])
    all_tests.addTest(tests)

    return all_tests
