import sys
sys.path = ["src"] + sys.path

import unittest

import rawapi


class TestSaneInit(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        version = rawapi.sane_init()
        self.assertTrue(version.is_current())
        rawapi.sane_exit()

    def tearDown(self):
        pass

class TestSaneGetDevices(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()

    def test_get_devices(self):
        devices = rawapi.sane_get_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        rawapi.sane_exit()


class TestSaneOpen(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()
        devices = rawapi.sane_get_devices()
        self.assertTrue(len(devices) > 0)
        self.dev_name = devices[0].name

    def test_open_invalid(self):
        self.assertRaises(rawapi.SaneException, rawapi.sane_open, "whatever")

    def test_open_valid(self):
        dev_handle = rawapi.sane_open(self.dev_name)
        rawapi.sane_close(dev_handle)

    def tearDown(self):
        rawapi.sane_exit()



def get_all_tests():
    all_tests = unittest.TestSuite()

    tests = unittest.TestSuite([TestSaneInit("test_init")])
    all_tests.addTest(tests)

    tests = unittest.TestSuite([TestSaneGetDevices("test_get_devices")])
    all_tests.addTest(tests)

    tests = unittest.TestSuite([
        TestSaneOpen("test_open_invalid"),
        TestSaneOpen("test_open_valid"),
    ])
    all_tests.addTest(tests)

    return all_tests
