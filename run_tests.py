#!/usr/bin/env python

import sys
import unittest

from tests import tests_rawapi
from tests import tests_abstract

if __name__ == '__main__':
    print "---"
    print "=== RawAPI: ==="
    unittest.TextTestRunner().run(tests_rawapi.get_all_tests())
    print "---"
    print "=== Abstract: ==="
    unittest.TextTestRunner().run(tests_abstract.get_all_tests())

