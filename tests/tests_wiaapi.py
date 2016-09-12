import os
import sys
sys.path = ["src"] + sys.path

import unittest

if os.name == "nt":
    from wia import rawapi


class TestInit(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_init(self):
        version = rawapi.init()
        rawapi.exit()

    def tearDown(self):
        pass


class TestGetDevices(unittest.TestCase):
    def setUp(self):
        rawapi.init()

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_get_devices(self):
        devices = rawapi.get_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        rawapi.exit()