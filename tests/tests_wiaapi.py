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
        if os.name == "nt":
            rawapi.init()

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_get_devices(self):
        devices = rawapi.get_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        if os.name == "nt":
            rawapi.exit()


class TestOpenDevice(unittest.TestCase):
    def setUp(selfself):
        if os.name == "nt":
            rawapi.init()

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_open_device(self):
        devices = rawapi.get_devices()
        self.assertTrue(len(devices) > 0)
        devid = devices[0][0]
        dev = rawapi.open(devid)
        self.assertNotEqual(dev, None)
        del dev
        dev = None

    def tearDown(self):
        if os.name == "nt":
            rawapi.exit()


class TestGetSources(unittest.TestCase):
    def setUp(selfself):
        if os.name == "nt":
            rawapi.init()

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_get_sources(self):
        devices = rawapi.get_devices()
        self.assertTrue(len(devices) > 0)
        devid = devices[0][0]
        dev = rawapi.open(devid)
        self.assertNotEqual(dev, None)
        sources = rawapi.get_sources(dev)
        self.assertTrue(len(sources) > 0)

    def tearDown(self):
        if os.name == "nt":
            rawapi.exit()