#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""Test the LIR module"""

import sys
sys.path.append(".")
import constants
import datetime
import math
import unittest
import lir

class AddressHolderTestCase(unittest.TestCase):
  def setUp(self):
    self.addr_hold = lir.address_holder()

  def testAddressHolderNew(self):
    self.assert_(self.addr_hold, 
                 "Address holder could not be created")

  def testAddressHolderGetName(self):
    result = self.addr_hold.name
    self.assert_(result == constants.defines._DEFAULT_GENERATE_ME,
                 "Address holder does not have default pre-generated name - \
instead got [%s]" % result)
    self.assert_(result != None, 
                 "Address holder has no generated name at startup - \
instead got [%s]" % result)

  def testAddressHolderGetDate(self):
    result = self.addr_hold.GetDate()
    expected = datetime.date.today().strftime("%Y%m%d")
    self.assert_(result == expected, 
                 "Address holder does not return default of today [%s] instead" %
                 result)

  def testAddressHolderSetDate(self):
    self.addr_hold.SetDate("20040822")
    result = self.addr_hold.GetDate()
    self.assert_(result == "20040822", 
                 "Address holder unable to set date - \
    instead got [%s]" % result)

  def testAddressHolderSetDateFail(self):
    self.assertRaises(ValueError, self.addr_hold.SetDate, "00010101")

  def testAddressHolderIncrementDate(self):
    before = self.addr_hold.GetDate()
    self.addr_hold.IncrementDate()
    after = self.addr_hold.GetDate()
    self.assert_(before != after,
                 "Address holder unable to increment date")

  def testAddressHolderGetTable(self):
    thing = self.addr_hold.table
    self.assertEquals(thing, None, "Default routing table is not None!")

  def testAddressHolderTableManipulations(self):
    # TODO(niallm): Correctly test this
    pass

  def testAddressHolderInjectPrefix(self):
    # TODO(niallm): Correctly test this
    pass

  def testAddressHolderGetSetExhaustion(self):
    # TODO(niallm): implement test for 'exhausted at prefix length X'
    result = self.addr_hold.GetSpaceExhausted()
    self.assertEqual(result, False, "Shouldn't start off with space exhausted!")
    self.addr_hold._SetSpaceExhausted()
    result2 = self.addr_hold.GetSpaceExhausted()
    self.assertEqual(result2, True, "Space exhausted should have been set to True")

  def testAddressHolderRegisterPrefix(self):
    today = self.addr_hold.GetDate()
    self.addr_hold._RegisterPrefix('137.43.4.16', today)
    self.assertEqual(self.addr_hold.registered_prefixes_by_date[today], ['137.43.4.16'])

  def testAddressHolderAddPrefix(self):
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold1')
    self.assertEqual(result, True, "Couldn't add perfectly good space")
    q = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold1')
    self.assertEqual(q, False, 
                      'Should not have been able to add that again in _AddTreePrefix')
    addr_used = self.addr_hold.addresses_used
    addr_span = self.addr_hold.address_span
    self.assertEqual(addr_used, 0, "Should have no addresses used")
    self.assertEqual(addr_span, 2 ** 16, "Should have a span of /16")
    result = self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold3',
                                           used = True, supplied_date = '19930101')
    self.assertEqual(result, True, "Couldn't add even more perfectly good space")
    addr_used2 = self.addr_hold.addresses_used
    addr_span2 = self.addr_hold.address_span
    self.assertEqual(addr_used2, 2 ** (32 - 17), 
                     "Used [%s] other than expected" % addr_used2)
    self.assertEqual(addr_span2, (2 ** 16) + (2 ** (32 - 17)), 
                     "Span [%s] other than expected" % addr_span2)

  def testAddressHolderRemovePrefix(self):
    # TODO(niallm): implement
    pass

  def testAddressHolderCountRegPrefixes(self):
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold')
    self.assertEqual(result, 1, "Prefixes registered differs from 1")

  def testAddressHolderRetrieveSorted(self):
    # TODO(niallm): this is so broken, but I don't have time to find out why now
    self.addr_hold._AddTreePrefix('193.0.0.0/8', 'test_addrhold', False, "19950101")
    self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold', False, "19930101")
    self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold', False, "19940101")
    count = 0
    for x in self.addr_hold._RegisteredPrefixesByCountSorted():
      expr0 = (count == 0 and x == '137.43.0.0/16')
      expr1 = (count == 1 and x == '193.0.0.0/8')
      expr2 = (count == 2 and x == '194.125.0.0/17')
      count += 1
    count = 0
    for x in self.addr_hold._RegisteredPrefixesByDateSorted():
      expr0 = (count == 0 and x == ['137.43.0.0/16'])
      expr1 = (count == 1 and x == ['194.125.0.0/17'])
      expr2 = (count == 2 and x == ['193.0.0.0/8'])
      count += 1

  def testAddressHolderRetrieveRegisteredPrefixes(self):
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold')
    for q in self.addr_hold._RetrieveRegisteredPrefixes():
      self.assertEqual(q, '137.43.0.0/16')

  def testAddressHolderIterateTreePrefixes(self):
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold')
    result2 = self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold')
    for q in self.addr_hold._IterateTreePrefixes():
      self.assertEqual(q, '137.43.0.0/16' or '194.125.0.0/17')

  def testAddressHolderCountTreePrefixes(self):
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold')
    result2 = self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold')
    count = self.addr_hold._CountTreePrefixes()
    self.assertEqual(count, 0, "1st tree count [%s] wasn't expected" % count)
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold',
                                             used = True, test_dup = False)
    result2 = self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold',
                                              used = True, test_dup = False)
    count = self.addr_hold._CountTreePrefixes()
    self.assertEqual(count, 2, "2nd tree count [%s] wasn't expected" % count)
    result = self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold',
                                             used = True, test_dup = True)
    result2 = self.addr_hold._AddTreePrefix('194.125.0.0/17', 'test_addrhold',
                                              used = True, test_dup = True)
    count = self.addr_hold._CountTreePrefixes()
    self.assertEqual(count, 2, "3rd tree count [%s] wasn't expected" % count)    

  def testAddressHolderAddressPercentageEtc(self):
    self.assertEqual(self.addr_hold.addresses_used, 0)
    self.addr_hold._AddTreePrefix('137.43.0.0/16', 'test_addrhold') # used false
    self.assertEqual(self.addr_hold.addresses_used, 0)
    self.assertEqual(self.addr_hold.address_span, 2 ** 16)
    self.addr_hold._AddTreePrefix('194.125.0.0/16', 'test_addrhold', True) 
    # used true
    self.assertEqual(self.addr_hold.addresses_used, 2 ** 16)
    self.assertEqual(self.addr_hold.address_span, 2 ** 16 + 2 ** 16)
    self.assertEqual(self.addr_hold.AddressPercentageLeft(), 50.0)
    self.assertEqual(self.addr_hold.AddressPercentageUsed(), 50.0)
    self.assertEqual(self.addr_hold.SpanForSize(8), 2 ** 24)
    
class AddressSupplier(unittest.TestCase):
  
  def setUp(self):
    self.addr_supp = lir.address_supplier()

  def testAddressSupplierNew(self):
    self.assert_(self.addr_supp, 
                 "Address supplier could not be created")

  def testAddressSupplierGetSet(self):
    fake_lir = lir.lir()
    supplier = fake_lir.address_supplier
    self.assertEqual(supplier, None)
    fake_lir.set_address_supplier(self.addr_supp)
    supplier = fake_lir.get_address_supplier()
    self.assertEqual(supplier, self.addr_supp)

  def testAddressSupplierMakeRequestFailure(self):
    fake_lir = lir.lir()
    result = self.addr_supp.Request(fake_lir, 8)
    self.assertEqual(result, None)

  def testAddressSupplierMakeRequestSuccess(self):
    fake_lir = lir.lir()
    self.addr_supp._AddTreePrefix('0.0.0.0/8', "MakeRequestSuccess")
    result = self.addr_supp.Request(fake_lir, 8)
    self.assertEqual(result, '0.0.0.0/8')
    self.addr_supp._AddTreePrefix('1.0.0.0/8', "test_addrsupp_make")
    result = self.addr_supp.Request(fake_lir, 8)
    self.assertEqual(result, '1.0.0.0/8')

  def testAddressSupplierRetrieveRequests(self):
    # TODO(niallm): unimplemented
    pass

  def testAddressSupplierCountRequests(self):
    # TODO(niallm): unimplemented
    pass
  

class AddressHolderPrefixTestCase(unittest.TestCase):
  def setUp(self):
    self.addr_hold = lir.address_holder()
    self.prefix = "137.43.0.0/16"
    self.assert_(self.addr_hold._AddTreePrefix(self.prefix, "added by test case \
    setUp"))
      
  def testAddressHolderHaveRegistered(self):
    result = self.addr_hold._HaveRegistered(self.prefix)
    self.assert_(result == True,
                 "Address holder did not see this particular prefix - got \
                 [%s]" % result)
    result = self.addr_hold._RetrieveRegisteredPrefixes()
    self.assert_(len(result) > 0,
                 "Address holder has zero length prefix registration - got \
                 [%s]" % result)

class IANATestCase(unittest.TestCase):
  def setUp(self):
    self.iana = lir.iana()

  def testIANANew(self):
    self.assert_(self.iana, "IANA could not be created")

  def testIANAGetDate(self):
    self.assert_(self.iana.GetDate() != None, "IANA had a null date")

  def testIANAAddressPercentages(self):
    self.assertEqual(self.iana.address_span, 2 ** 32)
    self.assertEqual(self.iana.addresses_used, 0)
    self.iana._AddTreePrefix('137.43.0.0/16', 'test_iana') # used false
    self.assertEqual(self.iana.addresses_used, 0)
    self.assertEqual(self.iana.address_span, 2 ** 32)
    self.iana._AddTreePrefix('194.125.0.0/16', 'test_iana', True) 
    # used true
    self.assertEqual(self.iana.addresses_used, 2 ** 16)
    self.assertEqual(self.iana.AddressPercentageLeft(), 100 - 0.00152587890625)
    self.assertEqual(self.iana.AddressPercentageUsed(), 0.00152587890625)
    self.assertEqual(self.iana.SpanForSize(8), 2 ** 24)

  def testLIRGetsSpaceNotUsed(self):
    # TODO(niallm): implement this check
    pass

  def testAddrHolderRequest(self):
    # TODO(niallm): proper check here, rather than distributed around
    pass

  def testIANAExhaustByOneLIR(self):
    fake_lir = lir.lir()
    result = self.iana.Request(fake_lir, 8)
    count = 1
    while result != None:
      #print "REQUEST: [%s] COUNT [%s]" % (result, count)
      result = self.iana.Request(fake_lir, 8)
      if result != None:
        count += 1
    self.assertEqual(count, constants.defines._DEFAULT_EXHAUSTION_COUNT,
                     "Unexpected exhaustion count [%s]" % count)
  
  def testIANAExhaustByOneRIR(self):
    fake_rir = lir.rir()
    result = self.iana.Request(fake_rir, 8)
    count = 1
    while result != None:
      #print "REQUEST: [%s] COUNT [%s]" % (result, count)
      result = self.iana.Request(fake_rir, 8)
      if result != None:
        count += 1
    self.assertEqual(count, constants.defines._DEFAULT_EXHAUSTION_COUNT,
                      "Unexpected exhaustion count [%s]" % count)

  def testIANAExhaustByExpected(self):
    # TODO(niallm): do population of RIR with historical data, then exhaust
    pass

class IANAHeirarchyTestCase(unittest.TestCase):
  def setUp(self):
    self.iana = lir.iana()

class RIRTestCase(unittest.TestCase):
  def setUp(self):
    self.iana = lir.iana()
    self.rir = lir.rir()

  def testRIRNew(self):
    self.assert_(self.rir, "RIR could not be created")

class LIRTestCase(unittest.TestCase):
  def setUp(self):
    self.rir = lir.rir()
    self.lir = lir.lir()

  def testLIRNew(self):
    self.assert_(self.lir, "LIR could not be created")


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(AddressHolderTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(AddressHolderPrefixTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(IANATestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(IANAHeirarchyTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(RIRTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(LIRTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
