import sys
sys.path = ["src"] + sys.path

import unittest

import rawapi


class TestSaneGetDevices(unittest.TestCase):
    def set_module(self, module):
        self.module = module

    def setUp(self):
        pass

    def test_get_devices(self):
        devices = self.module.get_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        pass


class TestSaneOptions(unittest.TestCase):
    def set_module(self, module):
        self.module = module

    def setUp(self):
        self.devices = self.module.get_devices()
        self.assertTrue(len(self.devices) > 0)

    def test_get_option(self):
        for dev in self.devices:
            val = dev.options['mode'].value
            self.assertNotEqual(val, None)

    def test_set_option(self):
        for dev in self.devices:
            dev.options['mode'].value = "Gray"
            val = dev.options['mode'].value
            self.assertEqual(val, "Gray")

    def __set_opt(self, opt_name, opt_val):
        for dev in self.devices:
            dev.options[opt_name].value = opt_val

    def test_set_inexisting_option(self):
        self.assertRaises(KeyError, self.__set_opt, 'xyz', "Gray")

    def test_set_invalid_value(self):
        self.assertRaises(rawapi.SaneException, self.__set_opt, 'mode', "XYZ")

    def tearDown(self):
        for dev in self.devices:
            del(dev)
        del(self.devices)


class TestSaneScan(unittest.TestCase):
    def set_module(self, module):
        self.module = module

    def setUp(self):
        devices = self.module.get_devices()
        self.assertTrue(len(devices) > 0)
        self.dev = devices[0]

    def test_simple_scan_gray(self):
        self.assertTrue("Gray" in self.dev.options['mode'].constraint)
        self.dev.options['mode'].value = "Gray"
        scan = self.dev.scan(multiple=False)
        try:
            while True:
                scan.read()
        except EOFError:
            pass
        img = scan.get_img()
        self.assertNotEqual(img, None)

    def test_simple_scan_color(self):
        self.assertTrue("Color" in self.dev.options['mode'].constraint)
        self.dev.options['mode'].value = "Color"
        scan = self.dev.scan(multiple=False)
        try:
            while True:
                scan.read()
        except EOFError:
            pass
        img = scan.get_img()
        self.assertNotEqual(img, None)

    def test_multi_scan_on_flatbed(self):
        self.assertTrue("Flatbed" in self.dev.options['source'].constraint)
        self.dev.options['source'].value = "Flatbed"
        self.dev.options['mode'].value = "Color"
        scan = self.dev.scan(multiple=True)
        try:
            while True:
                scan.read()
        except EOFError:
            pass
        self.assertEqual(scan.get_nb_img(), 1)
        self.assertNotEqual(scan.get_img(0), None)

    def test_multi_scan_on_adf(self):
        self.assertTrue("ADF" in self.dev.options['source'].constraint)
        self.dev.options['source'].value = "ADF"
        self.dev.options['mode'].value = "Color"
        scan = self.dev.scan(multiple=True)
        try:
            while True:
                scan.read()
        except EOFError:
            pass
        self.assertEqual(scan.get_nb_img(), 0)

    def tearDown(self):
        del(self.dev)


def get_all_tests(module):
    all_tests = unittest.TestSuite()

    tests = [
        TestSaneGetDevices("test_get_devices")
    ]
    for test in tests:
        test.set_module(module)
    all_tests.addTest(unittest.TestSuite(tests))

    tests = [
        TestSaneOptions("test_get_option"),
        TestSaneOptions("test_set_option"),
        TestSaneOptions("test_set_inexisting_option"),
        TestSaneOptions("test_set_invalid_value"),
    ]
    for test in tests:
        test.set_module(module)
    all_tests.addTest(unittest.TestSuite(tests))

    tests = [
        TestSaneScan("test_simple_scan_gray"),
        TestSaneScan("test_simple_scan_color"),
        TestSaneScan("test_multi_scan_on_flatbed"),
        TestSaneScan("test_multi_scan_on_adf"),
    ]
    for test in tests:
        test.set_module(module)
    all_tests.addTest(unittest.TestSuite(tests))

    return all_tests

