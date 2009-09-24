from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
import doctest
import os
import shutil
import time
import unittest

class EasyTreeManagerTestCase(TestCase):
    """
    Unit test for EasyTreeManager
    """
    def setUp(self):
        pass
    
    def runTest(self):
        pass
        
    def tearDown(self):
        pass

def suite():
    s = unittest.TestSuite()
    s.addTest(EasyTreeManagerTestCase())
    s.addTest(doctest.DocFileSuite(os.path.join('doctests', 'tree_structure.txt')))
    return s
