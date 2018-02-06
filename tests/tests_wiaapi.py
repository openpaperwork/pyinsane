import os
import unittest

if os.name == "nt":
    from pyinsane2.wia import rawapi


class TestInit(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_init(self):
        rawapi.init()
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
    def setUp(self):
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

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_invalid_open_device(self):
        self.assertRaises(rawapi.WIAException, rawapi.open, "randomcraphere")

    def tearDown(self):
        if os.name == "nt":
            rawapi.exit()


class TestGetSources(unittest.TestCase):
    def setUp(self):
        if os.name != "nt":
            return
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

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_invalid_get_sources(self):
        self.assertRaises(
            rawapi.WIAException, rawapi.get_sources, "randomcrappyobject"
        )

    def tearDown(self):
        if os.name != "nt":
            return
        rawapi.exit()


class TestGetProperties(unittest.TestCase):
    def setUp(self):
        if os.name != "nt":
            return
        rawapi.init()
        devices = rawapi.get_devices()
        devid = devices[0][0]
        self.dev = rawapi.open(devid)
        self.sources = rawapi.get_sources(self.dev)
        self.assertTrue(len(self.sources) > 0)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_get_dev_properties(self):
        props = rawapi.get_properties(self.dev)
        self.assertTrue(len(props) > 0)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_get_src_properties(self):
        props = rawapi.get_properties(self.sources[0][1])
        self.assertTrue(len(props) > 0)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_invalid_get_properties(self):
        self.assertRaises(rawapi.WIAException, rawapi.get_properties,
                          "crappy_obj")

    def tearDown(self):
        if os.name != "nt":
            return
        rawapi.exit()


class TestSetProperty(unittest.TestCase):
    def setUp(self):
        if os.name != "nt":
            return
        rawapi.init()
        devices = rawapi.get_devices()
        devid = devices[0][0]
        self.dev = rawapi.open(devid)
        self.sources = rawapi.get_sources(self.dev)
        self.assertTrue(len(self.sources) > 0)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_set_src_property_depth(self):
        rawapi.set_property(self.sources[0][1], "depth", 8)

        props = rawapi.get_properties(self.sources[0][1])
        self.assertTrue(len(props) > 0)
        for (propname, propvalue, accessright, _) in props:
            self.assertTrue(accessright == "ro" or accessright == "rw")
            if (propname == "depth"):
                self.assertEqual(propvalue, 8)
                self.assertEqual(accessright, "rw")

        rawapi.set_property(self.sources[0][1], "depth", 24)

        props = rawapi.get_properties(self.sources[0][1])
        self.assertTrue(len(props) > 0)
        for (propname, propvalue, _a, _b) in props:
            if (propname == "depth"):
                self.assertEqual(propvalue, 24)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_set_src_property_preview(self):
        rawapi.set_property(self.sources[0][1], "preview", "preview_scan")

        props = rawapi.get_properties(self.sources[0][1])
        self.assertTrue(len(props) > 0)
        for (propname, propvalue, accessright, _) in props:
            self.assertTrue(accessright == "ro" or accessright == "rw")
            if (propname == "preview"):
                self.assertEqual(propvalue, "preview_scan")
                self.assertEqual(accessright, "rw")

        rawapi.set_property(self.sources[0][1], "preview", "final_scan")

        props = rawapi.get_properties(self.sources[0][1])
        self.assertTrue(len(props) > 0)
        for (propname, propvalue, _a, _b) in props:
            if (propname == "preview"):
                self.assertEqual(propvalue, "final_scan")

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_invalid_set_src_property_depth(self):
        self.assertRaises(rawapi.WIAException, rawapi.set_property,
                          "crapobj", "depth", 8)
        self.assertRaises(rawapi.WIAException, rawapi.set_property,
                          self.sources[0][1], "crapproperty", 8)
        self.assertRaises(rawapi.WIAException, rawapi.set_property,
                          self.sources[0][1], "depth", "crapvalue")

    def tearDown(self):
        if os.name != "nt":
            return
        rawapi.exit()


class TestScan(unittest.TestCase):
    def setUp(self):
        if os.name != "nt":
            return
        rawapi.init()
        devices = rawapi.get_devices()
        devid = devices[0][0]
        self.dev = rawapi.open(devid)
        self.sources = rawapi.get_sources(self.dev)
        self.assertTrue(len(self.sources) > 0)

    @unittest.skipIf(os.name != "nt", "Windows only")
    def test_scan(self):
        scan = rawapi.start_scan(self.sources[0][1])
        try:
            while True:
                buf = scan.read()
                self.assertTrue(len(buf) > 0)
        except EOFError:
            pass
        # no more than one page expected
        self.assertRaises(StopIteration, scan.read)

    def tearDown(self):
        if os.name != "nt":
            return
        rawapi.exit()
