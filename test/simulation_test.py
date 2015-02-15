#!/usr/bin/env python
# encoding: utf-8
"""
SimulationTest.py

Tests data and assumptions pertaining to the simulation, rather than
correctness of the actions of the individual objects (although there
is some overlap).

Created by Niall Murphy on 2007-10-13.
"""
import sys
sys.path.append(".")
import constants
import unittest
import simulation

class SimTestCase(unittest.TestCase):

  name = "SimTestCase" # For Request testing callbacks

  def setUp(self):
    self.s = simulation.timelined()

  def get_name(self):
    """Mock for request method of IANA, tested later."""
    return "SimTestCase"

  def testSimNew(self):
    self.assert_(self.s, "New timelined simulation could not be created.")

  def testSimArithmetic(self):
    result = self.s.iana.SpanNormaliseSlashEight((2 ** 24) * 1.5)
    self.assertEqual(result, 1.5)

  def testSimRIRCreation(self):
    self.assertEqual(self.s.GetRIRByName('WIBBLE'), None)
    self.s.CreateRIRIfNotSeen('WIBBLE')
    self.assertNotEqual(self.s.GetRIRByName('WIBBLE'), None)

  def testSimLIRCreation(self):
    self.assertEqual(self.s.GetLIRByName('WIBBLE'), None)
    self.s.CreateLIRIfNotSeen('WIBBLE')
    self.assertNotEqual(self.s.GetLIRByName('WIBBLE'), None)

  def testSimIANAProcessData(self):
    self.s.FromIANAProcess()
    ie_res_count = self.s.iana.IETFReservedCount() # IETF says no
    ia_res_count = self.s.iana.IANAAssignedCount() # IANA already said yes
    ia_var_count = self.s.iana.IANAVariousCount() # IANA already said maybe
    ie_norm = self.s.iana.SpanNormaliseSlashEight(ie_res_count)
    ia_norm = self.s.iana.SpanNormaliseSlashEight(ia_res_count)
    iv_norm = self.s.iana.SpanNormaliseSlashEight(ia_var_count)
    self.assertAlmostEqual(ie_norm, constants.defines._IETF_RESERVATIONS, 3,
                           "Incorrect IETF reservations; [%s] not [%s]" % 
                          (constants.defines._IETF_RESERVATIONS,ie_norm))
    self.assertAlmostEqual(iv_norm, constants.defines._IANA_VARIOUS, 3,
                           "Incorrect IANA VARIOUS reservations; [%s] not [%s]" % 
                           (constants.defines._IANA_VARIOUS,iv_norm))
    self.assertEqual(ia_norm, constants.defines._IANA_RESERVATIONS,
                     "Incorrect IANA reservations; [%s] not [%s]" % 
                     (constants.defines._IANA_RESERVATIONS, ia_norm))

  def testSimIANAFullPool(self):
    self.s.FromIANAProcess()
    space = True
    count = 0
    while (space != None):
      space = self.s.iana.Request(self, 8)
      count += 1
    self.assertEqual(count, constants.defines._CURRENT_FREE_POOL_COUNT, 
                     "Incorrect free pool count: is [%s] should be [%s]" % 
                     (constants.defines._CURRENT_FREE_POOL_COUNT, count))

  def tesSimIANAViewOfRIRs(self):
    self.s.FromIANAProcess()
    afrinic = self.s.iana.iana_to_rir_count('afrinic')
    apnic = self.s.iana.iana_to_rir_count('apnic')
    arin = self.s.iana.iana_to_rir_count('arin')
    lacnic = self.s.iana.iana_to_rir_count('lacnic')
    ripencc = self.s.iana.iana_to_rir_count('ripencc')
    self.assertEqual(self.s.iana.SpanNormaliseSlashEight(afrinic), 2,
                     "Incorrect afrinic allocation; 2 not [%s]" % afrinic)
    self.assertEqual(self.s.iana.SpanNormaliseSlashEight(apnic), 24,
                     "Incorrect afrinic allocation; 2 not [%s]" % apnic)
    self.assertEqual(self.s.iana.SpanNormaliseSlashEight(arin), 27,
                     "Incorrect afrinic allocation; 2 not [%s]" % arin)
    self.assertEqual(self.s.iana.SpanNormaliseSlashEight(ripencc), 26,
                     "Incorrect afrinic allocation; 2 not [%s]" % ripencc)
    self.assertEqual(self.s.iana.SpanNormaliseSlashEight(lacnic), 6,
                     "Incorrect afrinic allocation; 2 not [%s]" % lacnic)

  def testSimIANAPercentFree(self):
    self.s.FromIANAProcess()
    pl = self.s.iana.AddressPercentageLeft()
    self.assertAlmostEqual(pl, constants.defines._IANA_START_FREE, 3,
                           "IANA should start off [%s] percent free; got [%s] instead" % 
                           (constants.defines._IANA_START_FREE, pl))

  def testSimRIRsViewsOfRIRs(self):
    self.s.FromIANAProcess()
    for r in self.s.GetRIRs():
      if r.name == 'afrinic':
        for prefix in r.tree.IterateNodes(True):
          fail("afrinic should not have used prefixes at this stage")
        reg_pref = self.s.iana.SpanNormaliseSlashEight(r.address_span)
        self.assertEqual(reg_pref, constants.defines._AFRINIC_START_RECV,
                         "afrinic received [%s] prefixes, not [%s]" % 
                         (constants.defines._AFRINIC_START_RECV, reg_pref))
      elif r.name == 'apnic':
        for prefix in r.tree.IterateNodes(True):
          fail("apnic should not have used prefixes at this stage")
        reg_pref = self.s.iana.SpanNormaliseSlashEight(r.address_span)
        self.assertEqual(reg_pref, constants.defines._APNIC_START_RECV,
                         "apnic received [%s] prefixes, not [%s]" % 
                         (constants.defines._APNIC_START_RECV, reg_pref))
      elif r.name == 'arin':
        for prefix in r.tree.IterateNodes(True):
          fail("arin should not have used prefixes at this stage")
        reg_pref = self.s.iana.SpanNormaliseSlashEight(r.address_span)
        self.assertEqual(reg_pref, constants.defines._ARIN_START_RECV,
                         "arin received [%s] prefixes, not [%s]" % 
                         (constants.defines._ARIN_START_RECV, reg_pref))
      elif r.name == 'lacnic':
        for prefix in r.tree.IterateNodes(True):
          fail("lacnic should not have used prefixes at this stage")
        reg_pref = self.s.iana.SpanNormaliseSlashEight(r.address_span)
        self.assertEqual(reg_pref, constants.defines._LACNIC_START_RECV,
                         "lacnic received [%s] prefixes, not [%s]" % 
                         (constants.defines._LACNIC_START_RECV, reg_pref))
      elif r.name == 'ripencc':
        for prefix in r.tree.IterateNodes(True):
          fail("ripencc should not have used prefixes at this stage")
        reg_pref = self.s.iana.SpanNormaliseSlashEight(r.address_span)
        self.assertEqual(reg_pref, constants.defines._RIPE_START_RECV,
                         "ripencc received [%s] prefixes, not [%s]" % 
                         (constants.defines._RIPE_START_RECV, reg_pref))
      else:
        fail("Unrecognised RIR [%s]" % r)

  def testSimRIRPercentFree(self):
    self.s.FromIANAProcess()
    for r in self.s.GetRIRs():
      pl = r.AddressPercentageLeft()
      self.assertAlmostEqual(100, 100, 3,
                           "RIRs are 100 percent free at this point, not [%s]" % pl)

  def testSimAmountToPrefixDecomposition(self):
    arr = []
    arr = self.s.DecomposeAmountToPrefixes(36864)
    self.assertEqual(arr, [17,20], "Decompose reports %s not [17,20]" % arr)
    arr = self.s.DecomposeAmountToPrefixes(3072)
    self.assertEqual(arr, [21,22], "Decompose reports %s not [21,22]" % arr)

  def testSimSerialisePrefixes(self):
    sp = "199.4.16.0"
    lengths = [21, 22]
    result = self.s.ProvideSeriesFromPrefixesAndLengths(sp, lengths)
    self.assertEqual(result, ['199.4.16.0/21', '199.4.24.0/22'],
                     "Serialising prefixes reported %s - incorrect" % result)

  def testSimNaming(self):
    self.s.FromIANAProcess()
    gotten_rirs = []
    gotten_lirs = []
    for rir in self.s.GetRIRs():
      gotten_rirs.append(rir)
    for lir in self.s.GetLIRs():
      gotten_lirs.append(lir)
    self.assertNotEqual(gotten_rirs, None)
    self.assertNotEqual(gotten_lirs, None)
    self.assertEqual(self.s.GetRIRNames(), 
                     ['afrinic','apnic','arin','lacnic','ripencc'])
    self.s.debug = 1
    self.s.FromRIRProcess()
    self.s.debug = 0
    self.assertEqual(self.s.GetLIRNames(),
                     constants.defines._KNOWN_LIR_NAMES)
    self.assertNotEqual(self.s.GetRIRByName('ripencc'), None)
    self.assertNotEqual(self.s.GetLIRByName('IE'), None)

  def testSimPopSize(self):
    self.s.FromIANAProcess()
    self.s.FromRIRProcess()
    self.assertEqual(self.s.GetLIRPopulationSize('arin'), 
                     constants.defines._ARIN_POP_SIZE)

  def testSimCheckpoints(self):
    # TODO(niallm): actually implement this
    pass


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(SimTestCase)
  unittest.TextTestRunner(verbosity=2).run(suite)
