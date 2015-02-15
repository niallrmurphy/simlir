#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""These are the unit tests for the behaviour module, part of the SimLIR
framework."""


import sys
sys.path.append(".")
import behaviour
import constants
import timeline
import unittest


class BehaviourTest(unittest.TestCase):
  def setUp(self):
    self.b = behaviour.Behaviour()

  def testBehaviourNew(self):
    self.assert_(self.b, "Behaviour could not be created")

  def testBehaviourInitialValues(self):
    initsize = self.b.GetInitialSize()
    self.assertEqual(initsize, constants.defines._LIR_INITIAL_POLICY)
    defsize = self.b.GetDefaultSize()
    self.assertEqual(defsize, constants.defines._LIR_DEFAULT_POLICY)
    # FIXME test Failed (with timeline registration)

class ScalingTest(unittest.TestCase):
  def setUp(self):
    self.s = behaviour.Scaling()
    self.p = dict()
    self.p['20071010'] = ['137.43.0.0/16', '137.44.0.0/16']

  def testScalingNew(self):
    self.assert_(self.s, "Scaling object could not be created")

  def testScalingInitialValues(self):
    self.assertEqual(self.s.HowManyNeeded(), constants.defines._DEFAULT_HOWMANYNEEDED)
    
  def testConvertPrefixesToCounts(self):
    span = self.s.ConvertPrefixesToCounts(self.p)
    self.assertEqual(span, [2 ** 16, 2 ** 16])

  def testSumPrefixesSpanCutoff(self):
    (num, span) = self.s.SumPrefixesSpanCutoff(self.p, "20080112",
                                               constants.defines._DEFAULT_CUTOFF)
    self.assertEqual(num, 2)
    self.assertEqual(span, 2 * (2 ** (32 - 16)))
    (num, span) = self.s.SumPrefixesSpanCutoff(self.p, "20090112",
                                               constants.defines._DEFAULT_CUTOFF)
    self.assertEqual(num, 0)
    self.assertEqual(span, 0)
    
class LIRScalingTest(unittest.TestCase):
  
  def setUp(self):
    self.s = behaviour.Scaling()
    self.p = dict()
    self.p['20071010'] = ['137.43.0.0/16', '137.44.0.0/16']
    self.q = dict()
    self.q['20071010'] = ['137.43.0.0/16', '137.44.0.0/16']
    self.q['20071001'] = ['194.125.0.0/17']
  
  def testLIRStatic(self):
    self.s = behaviour.LIR_Static()
    (amount, when) = self.s.CalculateReqs(dict(), '20071010')
    self.assertEqual(amount, [2 ** (32 - constants.defines._DEFAULT_LIR_STATIC_SCALING_SIZE)])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20071010'))
    self.s.args = 16
    (amount, when) = self.s.CalculateReqs(dict(), '20071010')
    self.assertEqual(amount, [2 ** (32 - 16)])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20071010'))
    
  def testLIRWeeklyAverage(self):
    self.s = behaviour.LIR_Weekly_Average()
    (amount, when) = self.s.CalculateReqs(self.p, '20071011')
    self.assertEqual(amount, [((2 ** 17)/365)*7])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20071011'))
    # Invalidate cached results
    self.s.cached_results = None
    (amount, when) = self.s.CalculateReqs(self.q, '20071011')
    self.assertEqual(amount, [((2 ** 17 + 2 ** (32 - 17))/365*7)])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20071011'))
    
  def testLIRFortnightlyAverage(self):
    self.s = behaviour.LIR_Fortnightly_Average()
    (amount, when) = self.s.CalculateReqs(self.p, '20071011')
    self.assertEqual(amount, [(2 ** 17)/365*14])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20071011'))
    
  def testLIRReplay(self):
    self.s = behaviour.LIR_Replay()
    (amount, when) = self.s.CalculateReqs(self.p, '20071201')
    self.assertEqual(amount, [2 ** 16, 2 ** 16])
    self.failUnless(timeline.FilterWithinDate(when, 40, '20080123'))

class IANAScalingTest(unittest.TestCase):
  def setUp(self):
    self.i = behaviour.IANA_Standard()

  def testIANADefaults(self):
    self.assertEqual(self.i.CostOfBusiness(), constants.defines._COST_BUSINESS_LOW)
    self.assertEqual(self.i.GetInitialSize(), constants.defines._RIR_INITIAL_POLICY)
    self.assertEqual(self.i.GetDefaultSize(), constants.defines._RIR_DEFAULT_POLICY)

class RIRScalingTest(unittest.TestCase):
  def setUp(self):
    self.i = behaviour.RIR_Standard()

  def testRIRDefaults(self):
    self.assertEqual(self.i.CostOfBusiness(), constants.defines._COST_BUSINESS_LOW)

  def testRIRStandard(self):
    # self, addr_avail, prefix_items, cur_date
    addr_avail = 0
    prefix_items = dict()
    cur_date = "19930101"
    # my_obj.addr_avail = 0
    # Check if RIRs available space of ipv4 addresses is less than 50% of a /8 block
    # giving us ['/8', 'next month']
    self.assertEqual(self.i.CalculateReqs(my_obj, cur_date), 0)

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(BehaviourTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(ScalingTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(IANAScalingTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(RIRScalingTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(LIRScalingTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
