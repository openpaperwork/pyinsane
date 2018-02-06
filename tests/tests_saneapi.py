import os
import unittest

if os.name != "nt":
    from pyinsane2.sane import rawapi


def get_devices():
    '''Return SANE devices, perhaps after creating a test device.'''
    devices = rawapi.sane_get_devices()
    if len(devices) == 0:
        # if there are no devices found, create a virtual device.
        # see sane-test(5) and /etc/sane.d/test.conf
        rawapi.sane_close(rawapi.sane_open("test"))
        devices = rawapi.sane_get_devices()
    return devices


class TestSaneInit(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_init(self):
        version = rawapi.sane_init()
        self.assertTrue(version.is_current())
        rawapi.sane_exit()

    def tearDown(self):
        pass


class TestSaneGetDevices(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_get_devices(self):
        devices = get_devices()
        self.assertTrue(len(devices) > 0)

    def tearDown(self):
        rawapi.sane_exit()


class TestSaneOpen(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()
        devices = get_devices()
        self.assertTrue(len(devices) > 0)
        self.dev_name = devices[0].name

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_open_invalid(self):
        self.assertRaises(rawapi.SaneException, rawapi.sane_open, "whatever")

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_open_valid(self):
        dev_handle = rawapi.sane_open(self.dev_name)
        rawapi.sane_close(dev_handle)

    def tearDown(self):
        rawapi.sane_exit()


class TestSaneGetOptionDescriptor(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()
        devices = get_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = rawapi.sane_open(dev_name)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_get_option_descriptor_0(self):
        opt_desc = rawapi.sane_get_option_descriptor(self.dev_handle, 0)
        # XXX(Jflesch): The name may vary: sometimes it's empty, sometimes it's
        # "option-cnt"
        # self.assertEqual(opt_desc.name, "")
        self.assertEqual(opt_desc.title, b"Number of options")
        self.assertEqual(opt_desc.type, rawapi.SaneValueType.INT)
        self.assertEqual(opt_desc.unit, rawapi.SaneUnit.NONE)
        self.assertEqual(opt_desc.size, 4)
        self.assertEqual(opt_desc.cap, rawapi.SaneCapabilities.SOFT_DETECT)
        self.assertEqual(opt_desc.constraint_type,
                         rawapi.SaneConstraintType.NONE)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_get_option_descriptor_out_of_bounds(self):
        # XXX(Jflesch): Sane's documentation says get_option_descriptor()
        # should return NULL if the index value is invalid. It seems the actual
        # implementation prefers to segfault.

        # self.assertRaises(rawapi.SaneException,
        #                   rawapi.sane_get_option_descriptor, self.dev_handle,
        #                   999999)
        pass

    def tearDown(self):
        rawapi.sane_close(self.dev_handle)
        rawapi.sane_exit()


class TestSaneControlOption(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()
        devices = get_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = rawapi.sane_open(dev_name)
        self.nb_options = rawapi.sane_get_option_value(self.dev_handle, 0)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_get_option_value(self):
        for opt_idx in range(0, self.nb_options):
            desc = rawapi.sane_get_option_descriptor(self.dev_handle, opt_idx)
            if not rawapi.SaneValueType(desc.type).can_getset_opt():
                continue
            if desc.cap | rawapi.SaneCapabilities.INACTIVE == desc.cap:
                continue
            val = rawapi.sane_get_option_value(self.dev_handle, opt_idx)
            self.assertNotEqual(val, None)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_set_option_value(self):
        for opt_idx in range(0, self.nb_options):
            desc = rawapi.sane_get_option_descriptor(self.dev_handle, opt_idx)
            if (desc.name != "mode"
                    or not rawapi.SaneValueType(desc.type).can_getset_opt()):
                continue
            info = rawapi.sane_set_option_value(self.dev_handle, opt_idx,
                                                "Gray")
            self.assertFalse(rawapi.SaneInfo.INEXACT in info)
            val = rawapi.sane_get_option_value(self.dev_handle, opt_idx)
            self.assertEqual(val, "Gray")

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_set_option_auto(self):
        # TODO(Jflesch)
        pass

    def tearDown(self):
        rawapi.sane_close(self.dev_handle)
        rawapi.sane_exit()


class TestSaneScan(unittest.TestCase):
    def setUp(self):
        rawapi.sane_init()
        devices = get_devices()
        self.assertTrue(len(devices) > 0)
        dev_name = devices[0].name
        self.dev_handle = rawapi.sane_open(dev_name)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_simple_scan(self):
        # XXX(Jflesch): set_io_mode() always return SANE_STATUS_UNSUPPORTED
        # with my scanner
        # rawapi.sane_set_io_mode(self.dev_handle, non_blocking=False)

        try:
            rawapi.sane_start(self.dev_handle)
        except StopIteration:
            self.skipTest("cannot scan, no document loaded")

        # XXX(Jflesch): get_select_fd() always return SANE_STATUS_UNSUPPORTED
        # with my scanner
        # fd = rawapi.sane_get_select_fd(self.dev_handle)
        # self.assertTrue(fd > 0)

        try:
            while True:
                buf = rawapi.sane_read(self.dev_handle, 128*1024)
                self.assertTrue(len(buf) > 0)
        except EOFError:
            pass
        rawapi.sane_cancel(self.dev_handle)

    @unittest.skipIf(os.name == "nt", "sane only")
    def test_cancelled_scan(self):
        try:
            rawapi.sane_start(self.dev_handle)
        except StopIteration:
            self.skipTest("cannot scan, no document loaded")
        buf = rawapi.sane_read(self.dev_handle, 128*1024)
        self.assertTrue(len(buf) > 0)
        rawapi.sane_cancel(self.dev_handle)

    def tearDown(self):
        rawapi.sane_close(self.dev_handle)
        rawapi.sane_exit()
