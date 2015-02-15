#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>
"""Test the instrumentation module."""

import sys
sys.path.append('.')
import constants
import instrumentation
import unittest

from instrumentation import _EVENTS as _EVENTS

class InstrumentationTest(unittest.TestCase):

  def testNewInstrumentation(self):
    self.x = instrumentation.event_processor()
    methods = dir(self.x)
    self.failUnless('ReceiveEvent' in methods)

  def testInstrumentationSimple(self):
    self.eventp = instrumentation.event_processor()
    result = self.eventp.ReceiveEvent('UNIT_TEST', 
                                       {'invoker': 'IANA', 
                                        'action': 'add_route_event', 
                                        'route': '137.43.4.16/32', 
                                        'date': '19930101'})
    print result
    self.failUnless(result == ({'invoker': 'IANA', 
      'action': 'add_route_event', 'route': '137.43.4.16/32', 'date': '19930101'},))
    
if __name__ == '__main__':
  unittest.main()
