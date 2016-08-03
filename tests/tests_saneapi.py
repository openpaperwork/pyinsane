import sys
sys.path = ["src"] + sys.path

import unittest

import saneapi


def get_test_devices():
    '''Return SANE devices, perhaps after creating a test device.'''
    devices = saneapi.sane_get_devices()
    if len(devices) == 0:
        # if there are no devices found, create a virtual device.
        # see sane-test(5) and /etc/sane.d/test.conf
        saneapi.sane_close(saneapi.sane_open("test"))
        devices = saneapi.sane_get_devices()
    return devices


class TestSaneInit(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        version = saneapi.sane_init()
        self.assertTrue(version.is_current())
        saneapi.sane_exit()

    def tearDown(self):
        pass


class TestSaneGetDevices(unittest.TestCase):
    def setUp(self):
        saneapi.sane_init()

    def test_get_devices(self):
        devices = get_test_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        saneapi.sane_exit()


class TestSaneOpen(unittest.TestCase):
    def setUp(self):
        saneapi.sane_init()
        devices = get_test_devices()
        self.assertTrue(len(devices) > 0)
        self.dev_name = devices[0].name

    def test_open_invalid(self):
        self.assertRaises(saneapi.SaneException, saneapi.sane_open, "whatever")

    def test_open_valid(self):
        dev_handle = saneapi.sane_open(self.dev_name)
        saneapi.sane_close(dev_handle)

    def tearDown(self):
        saneapi.sane_exit()


class TestSaneGetOptionDescriptor(unittest.TestCase):
    def setUp(self):
        saneapi.sane_init()
        devices = get_test_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = saneapi.sane_open(dev_name)

    def test_get_option_descriptor_0(self):
        opt_desc = saneapi.sane_get_option_descriptor(self.dev_handle, 0)
        # XXX(Jflesch): The name may vary: sometimes it's empty, sometimes it's
        # "option-cnt"
        #self.assertEqual(opt_desc.name, "")
        self.assertEqual(opt_desc.title, b"Number of options")
        self.assertEqual(opt_desc.type, saneapi.SaneValueType.INT)
        self.assertEqual(opt_desc.unit, saneapi.SaneUnit.NONE)
        self.assertEqual(opt_desc.size, 4)
        self.assertEqual(opt_desc.cap, saneapi.SaneCapabilities.SOFT_DETECT)
        self.assertEqual(opt_desc.constraint_type,
                         saneapi.SaneConstraintType.NONE)

    def test_get_option_descriptor_out_of_bounds(self):
        # XXX(Jflesch): Sane's documentation says get_option_descriptor()
        # should return NULL if the index value is invalid. It seems the actual
        # implementation prefers to segfault.

        #self.assertRaises(saneapi.SaneException,
        #                  saneapi.sane_get_option_descriptor, self.dev_handle,
        #                  999999)
        pass

    def tearDown(self):
        saneapi.sane_close(self.dev_handle)
        saneapi.sane_exit()


class TestSaneControlOption(unittest.TestCase):
    def setUp(self):
        saneapi.sane_init()
        devices = get_test_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = saneapi.sane_open(dev_name)
        self.nb_options = saneapi.sane_get_option_value(self.dev_handle, 0)

    def test_get_option_value(self):
        for opt_idx in range(0, self.nb_options):
            desc = saneapi.sane_get_option_descriptor(self.dev_handle, opt_idx)
            if not saneapi.SaneValueType(desc.type).can_getset_opt():
                continue
            if desc.cap|saneapi.SaneCapabilities.INACTIVE == desc.cap:
                continue
            val = saneapi.sane_get_option_value(self.dev_handle, opt_idx)
            self.assertNotEqual(val, None)

    def test_set_option_value(self):
        for opt_idx in range(0, self.nb_options):
            desc = saneapi.sane_get_option_descriptor(self.dev_handle, opt_idx)
            if (desc.name != "mode"
                or not saneapi.SaneValueType(desc.type).can_getset_opt()):
                continue
            info = saneapi.sane_set_option_value(self.dev_handle, opt_idx, "Gray")
            self.assertFalse(saneapi.SaneInfo.INEXACT in info)
            val = saneapi.sane_get_option_value(self.dev_handle, opt_idx)
            self.assertEqual(val, "Gray")

    def test_set_option_auto(self):
        # TODO(Jflesch)
        pass

    def tearDown(self):
        saneapi.sane_close(self.dev_handle)
        saneapi.sane_exit()


class TestSaneScan(unittest.TestCase):
    def setUp(self):
        saneapi.sane_init()
        devices = get_test_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = saneapi.sane_open(dev_name)

    def test_simple_scan(self):
        # XXX(Jflesch): set_io_mode() always return SANE_STATUS_UNSUPPORTED
        # with my scanner
        #saneapi.sane_set_io_mode(self.dev_handle, non_blocking=False)

        try:
            saneapi.sane_start(self.dev_handle)
        except StopIteration:
            self.skipTest("cannot scan, no document loaded")

        # XXX(Jflesch): get_select_fd() always return SANE_STATUS_UNSUPPORTED
        # with my scanner
        #fd = saneapi.sane_get_select_fd(self.dev_handle)
        #self.assertTrue(fd > 0)

        try:
            while True:
                buf = saneapi.sane_read(self.dev_handle, 128*1024)
                self.assertTrue(len(buf) > 0)
        except EOFError:
            pass
        saneapi.sane_cancel(self.dev_handle)

    def test_cancelled_scan(self):
        try:
            saneapi.sane_start(self.dev_handle)
        except StopIteration:
            self.skipTest("cannot scan, no document loaded")
        buf = saneapi.sane_read(self.dev_handle, 128*1024)
        self.assertTrue(len(buf) > 0)
        saneapi.sane_cancel(self.dev_handle)

    def tearDown(self):
        saneapi.sane_close(self.dev_handle)
        saneapi.sane_exit()


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

    tests = unittest.TestSuite([
        TestSaneGetOptionDescriptor("test_get_option_descriptor_0"),
        TestSaneGetOptionDescriptor(
            "test_get_option_descriptor_out_of_bounds"),
    ])
    all_tests.addTest(tests)

    tests = unittest.TestSuite([
        TestSaneControlOption("test_get_option_value"),
        TestSaneControlOption("test_set_option_value"),
        TestSaneControlOption("test_set_option_auto"),
    ])
    all_tests.addTest(tests)

    tests = unittest.TestSuite([
        TestSaneScan("test_simple_scan"),
        TestSaneScan("test_cancelled_scan"),
    ])
    all_tests.addTest(tests)

    return all_tests
