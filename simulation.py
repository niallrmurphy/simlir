#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>
"""
simulation.py - input data processing and main sim instantiation.

This sets up whatever is required for a real simulation; config file
parsing, UI, data structure serialisation, and so on.

The unittests for this perform consistency checks with respect to the last
externally known "state of affairs", hard coded as values in constants.py.
Over time they will require changes to pass.

Created by Niall Murphy on 2007-08-28. 
"""

import behaviour
import constants
import instrumentation
import lir
import timeline


import cPickle
import datetime
import fileinput
import IPy
import getopt
import math
import os
import re
import string
import sys

class simulation:
  """ The simulation class wraps creation of IANA, RIRs and LIRs in an
    extendable way.

  A simulation has a dictionary of RIRs, LIRs, both indexed by name and
  maintaining separate count and object references,
  a debug setting, an instrumentation object, and a timeline.

  The RIRs look like this: rirs{'ripencc': {'count': 20, 'obj': <objectref> }}
  and similarly for the LIRs.
  """
  def __init__(self, supplied_debug = 0, supplied_inst = None):
    self.iana = lir.iana(supplied_inst = supplied_inst)
    self.rirs = dict()
    self.lirs = dict()
    self.debug = supplied_debug
    self.instrument = supplied_inst
    self.timeline = timeline.Timeline(supplied_debug = supplied_debug,
                                      instrumentation = supplied_inst)

  def GetRIRByName(self, supplied_name):
    """Given an RIR name, return a reference to the object."""
    ref = self.rirs.get(supplied_name, None)
    try:
      return ref['obj']
    except:
      return None

  def GetLIRByName(self, supplied_name):
    """Given an LIR name, return a reference to the object."""
    ref = self.lirs.get(supplied_name, None)
    try:
      return ref['obj']
    except:
      return None

  def GetRIRNames(self):
    """Return a sorted list of all RIR names attached to this simulation."""
    tmp = []
    for rir in self.rirs:
      tmp.append(rir)
    tmp.sort()
    return tmp

  def GetLIRNames(self):
    """Return a sorted list of all LIR names attached to this simulation."""
    tmp = []
    for lir in self.lirs:
      tmp.append(lir)
    tmp.sort()
    return tmp

  def GetRIRs(self):
    """Yield all RIR objects attached to this simulation."""
    for rir_props in self.rirs.values():
      rir_obj = rir_props['obj']
      yield rir_obj

  def GetLIRs(self):
    """Yield all LIR objects attached to this simulation."""
    for lir_props in self.lirs.values():
      lir_obj = lir_props['obj']
      yield lir_obj

  def GetLIRPopulationSize(self, name):
    """How many LIRs does RIR <name> have?"""
    population = 0
    r = self.GetRIRByName(name)
    for lir in self.GetLIRs():
      if lir.address_supplier.name == name:
        population += 1
    return population


  def FromIANAProcess(self, filename = "data/delegated-iana-latest",
                        lir_behave = None, rir_behave = None):
    """ Read in the historical data from Geoff/RIR-aggregate file;
    use this to populate our IANA and RIR objects. """
    linecount = 0
    non_v4 = 0
    iana_count = 0
    alloc = dict()
    rolling_total = 0

    for line in fileinput.input(filename):
      if line.startswith("#"):  # Quick way to comment out non-conforming records
        continue
      if self.debug >= 2:
        print "sim.from_iana.line: ", line.rstrip()

      linecount += 1
      elements = line.split('|')
      if line.startswith("2"):  # Ignore status lines
        continue
      if len(elements) == 6:  # Same again
        continue
      else:
        alloc['assigning_entity'] = elements[0]
        alloc['country'] = elements[1]
        alloc['addr_type'] = elements[2]
        alloc['prefix'] = elements[3]
        alloc['size'] = elements[4]
        alloc['date'] = elements[5]
        alloc['status'] = elements[6].rstrip()

      # Handy aliases.
      assigner = alloc['assigning_entity']
      assignee = alloc['status']

      # For the immediate purposes of this routine, we're interested
      # in IANA IPv4 assignments to RIRs or end users only.
      if alloc['addr_type'] != "ipv4" or assigner != 'iana':
        non_v4 += 1
        continue
      else:
        iana_count += 1
        # Convert assignment to CIDR.
        amount = int(alloc['size'])
        array = self.DecomposeAmountToPrefixes(amount)
        if len(array) > 1 and self.debug >= 2:
          print "sim.from_iana_process decomposes to [%s] POWERS FOR [%s]" % (len(array), alloc['prefix'])
        prefixes = self.ProvideSeriesFromPrefixesAndLengths(alloc['prefix'], array)

        if (alloc['status'] not in ['assigned', 'ietf', 'various']):
          # We now have an RIR as assignee. Create it and add the prefix,
          # marked as used in the iana.
          rir = self.CreateRIRIfNotSeen(alloc['status'],
                                        self.instrument,
                                        rir_behave)
          # Insert them as *unused* because we want to allocate from them.
          for elem in prefixes:
            rir._AddTreePrefix(elem, "TO RIR %s" % assignee,
                                 False, alloc['date'])
            self.iana._AddTreePrefix(elem, "TO RIR %s" % assignee,
                                       True, alloc['date'])
          rir.address_supplier = self.iana
        elif (alloc['status'] == 'ietf'):
          # If it's an IETF assignment we have to mark it used (unusable in theory)
          for elem in prefixes:
            self.iana._AddTreePrefix(elem, "IETF RESERVED", True, alloc['date'])
        elif (alloc['status'] == 'assigned'):
          # If it's assigned or various, it could be in one of many actual states,
          # but for the purposes of this simulation we'll declare it used too.
          for elem in prefixes:
            self.iana._AddTreePrefix(elem, "ASSIGNED", True, alloc['date'])
        elif (alloc['status'] == 'various'):
          for elem in prefixes:
            self.iana._AddTreePrefix(elem, "VARIOUS", True, alloc['date'])
        else:
          for elem in prefixes:
            self.iana._AddTreePrefix(elem, "RESERVED", True, alloc['date'])
      # Progress meter
      if linecount % 100 == 0:
        sys.stdout.write(".")
    # We've read all the lines in the file; now tidy-up work
    # Report act
    if self.debug >= 1:
      print "sim.from_iana_process: finished reading file (%s)" % filename
      print "Read (%s) lines, found (%s) non-ipv4 records, (%s) RIRs, and\n\
(%s) IANA-based assignments." % (linecount, non_v4, len(self.rirs.keys()),
                                 iana_count)


  def FromRIRProcess(self, filename = constants.defines._NRO_DATA,
                       lir_behave = None, rir_behave = None):
    """ Read in the historical data from Geoff/RIR-aggregate file;
    use it to populate our LIR objects. The current version of this
    creates "LIRs" by mapping a LIR object to a country.

    RIR|Country|Type|Prefix|Size|Date|Status
    iana|ZZ|ipv4|0.0.0.0|16777216|19830101|ietf
    iana|US|ipv4|3.0.0.0|16777216|19880223|assigned
    iana|ZZ|ipv4|7.0.0.0|16777216|19880223|arin
    iana|ZZ|ipv4|10.0.0.0|16777216|19940301|ietf
    lacnic|MX|ipv4|204.126.140.0|512|19950114|assigned

    """
    # Counters and useful dictionaries.
    non_v4 = 0
    rir_names = dict()
    lir_names = dict()
    iana_activity = dict()
    array = []
    iana_count = 0
    count = 0

    # Info about the individual allocation we're looking at.
    alloc = dict()

    for line in fileinput.input(filename):
      # Progress metre
      if count % 100 == 0:
        sys.stdout.write(".")
        sys.stdout.flush()
      if line.startswith("#"): # Quick way to comment out non-conforming records
        continue
      if self.debug >= 10:
        print "sim.from_rir.line: ", line.rstrip()
      count += 1
      elements = line.split('|')
      if len(elements) == 7:
        alloc['assigning_entity'] = elements[0]
        alloc['country'] = elements[1]
        alloc['addr_type'] = elements[2]
        alloc['prefix'] = elements[3]
        alloc['size'] = elements[4]
        alloc['date'] = elements[5]
        alloc['status'] = elements[6].rstrip()
      else:
        continue

      # Handy aliases.
      assigner = alloc['assigning_entity']
      assignee = alloc['country']

      # If the date is unknown ("00000000") then for the purposes
      # of simulation, we set it to a known constant.
      if alloc['date'] == "00000000":
        alloc['date'] = constants.defines._DEFAULT_NON_ZERO_DATE

      # For the immediate purposes of this simulator, we are
      # interested in IPv4 assignments only.
      if alloc['addr_type'] != "ipv4":
        non_v4 += 1
        continue
      else:
        if self.debug >= 2:
          print "sim.from_rir.line: ", line.rstrip()
        # Take the assignment, convert it into CIDR.
        # It's possible for the amount to be a sum of powers,
        # so decompose it where possible.
        amount = int(alloc['size'])
        array = self.DecomposeAmountToPrefixes(amount)
        if len(array) > 1 and self.debug >= 2:
          print "sim.from_rir_process decomposes to [%s] powers for [%s]" % (len(array), alloc['prefix'])
        prefixes = []
        prefixes = self.ProvideSeriesFromPrefixesAndLengths(alloc['prefix'], array)

        # If we have an assigner of iana, this is from IANA to
        # an RIR, or to legacy-land, or to IETF. These assignments
        # over-ride standard RIR->LIR assignments.
        if assigner == 'iana':
          iana_count += 1
          # Not relevant, done in other routine
          continue
        else: 
          # A non-IANA assigner.
          # Outside scope variables
          the_lir = None
          the_rir = None
          # It's RIR->LIR, LIR being in this case a country.
          the_rir = self.CreateRIRIfNotSeen(assigner,
                                            self.instrument,
                                            rir_behave)
          the_lir = self.CreateLIRIfNotSeen(assignee,
                                            self.instrument,
                                            lir_behave)
          """
          if self.debug >= 2:
            print "sim.from_rir_process rir->assigner: (%s) (%s)" % (the_rir, assigner)
            print "sim.from_rir_process lir->assignee: (%s) (%s)" % (the_lir, assignee) """
          # Register with the relevant entities in any case.
          for prefix in prefixes:
            if self.debug >= 3:
              print "sim.from_rir_process adding prefix [%s]", prefix
            the_lir._AddTreePrefix(prefix, 
                                   "sim.from_rir_process",
                                   True, alloc['date'])
            the_rir._AddTreePrefix(prefix,
                                   "sim.from_rir_process",
                                   True, alloc['date'])
          # We assume that one country has one RIR for this model,
          # and the first one wins.
          the_lir.address_supplier = the_rir
    # Read all lines in file; tidy-up work
    # Activity report
    if self.debug >= 1:
      print "sim.from_rir_process: finished reading file (%s)" % filename
      print "Read (%s) lines, found (%s) non-ipv4 records, (%s) RIRs, \n\
(%s) IANA-based assignments, and (%s) LIR equivalents." % (count, non_v4, len(self.rirs.keys()),
                                                           iana_count, len(self.lirs.keys()))

  def CreateRIRIfNotSeen(self,
                             rir_name,
                             instrument = None,
                             rir_behave = None):
    """Create an RIR and add it to the simulations' list of RIRs,
    but only if we haven't seen it before. Maintain a count of what
    we've been asked to create."""
    # Have we seen the RIR name before?
    if self.rirs.get(rir_name) == None:
      # No, create the object
      if self.debug >= 2:
        print "sim.create_rir: rir (%s) unseen; creating" % rir_name
      new_rir = lir.rir(supplied_name = rir_name, 
                        supplied_debug = self.debug,
                        supplied_inst = instrument,
                        requested_behaviour = rir_behave)
      tmp_binding = {'obj': new_rir, 'count': 1}
      self.rirs[rir_name] = tmp_binding
      return new_rir
    else:
      if self.debug >= 2:
        print "sim.create_rir: rir (%s) has been seen" % rir_name
      # Increase counter
      count = self.rirs[rir_name]['count']
      self.rirs[rir_name]['count'] = count + 1
      return self.GetRIRByName(rir_name)

  def CreateLIRIfNotSeen(self,
                             lir_name,
                             instrument = None,
                             lir_behave = None):
    """Create an LIR and add it to the simulations' list of LIRs,
    but only if we haven't seen it before. The logic is the same as 
    create_rir_if_not_seen."""
    if self.lirs.get(lir_name) == None:
      if self.debug >= 2:
        print "sim.create_lir: lir (%s) unseen; creating" % lir_name
      new_lir = lir.lir(supplied_name = lir_name,
                        supplied_debug = self.debug,
                        supplied_inst = instrument,
                        requested_behaviour = lir_behave)
      tmp_binding = {'obj': new_lir, 'count': 1}
      self.lirs[lir_name] = tmp_binding
      return new_lir
    else:
      if self.debug >= 2:
        print "sim.create_lir: lir (%s) has been seen" % lir_name
      count = self.lirs[lir_name]['count']
      self.lirs[lir_name]['count'] = count + 1
      return self.GetLIRByName(lir_name)

  def DumpCheckpoint(self, output_file):
    if self.debug >= 2:
      print "sim.dump_checkpoint to [%s]" % output_file
    """ Write state of world out to checkpoint file, for later reading. """
    FILE = open(output_file, "w")
    #world_state = [self.lirs, self.rirs, self.timeline, self.global_table, self.debug]
    #Can't pickle radix objects... FIXME
    world_state = [self.iana,  self.rirs, self.lirs, self.timeline]
    sys.stdout.write(".")
    sys.stdout.flush()
    cPickle.dump(world_state, FILE, protocol=-1)  # Warning: selects latest proto!
    sys.stdout.write(".")
    sys.stdout.flush()
    FILE.close()

  def ReadCheckpoint(self, input_file):
    """ Read state of world from checkpoint file, to prevent us having
    to read in initialisation every time. """
    if self.debug >= 2:
      print "sim.read_checkpoint from [%s]" % input_file
    FILE = open(input_file, 'r')
    sys.stdout.write(".")
    sys.stdout.flush()
    world_state = cPickle.load(FILE)
    sys.stdout.write(".")
    sys.stdout.flush()
    self.timeline = world_state.pop()
    sys.stdout.write(".")
    sys.stdout.flush()
    self.lirs = world_state.pop()
    sys.stdout.write(".")
    sys.stdout.flush()
    self.rirs = world_state.pop()
    sys.stdout.write(".")
    sys.stdout.flush()
    self.iana = world_state.pop()
    sys.stdout.write(".")
    sys.stdout.flush()
    FILE.close()

  def DecomposeAmountToPrefixes(self, amount):
    """Decompose supplied number into minimum powers of two. For example, an amount 
    of 36864 can be expressed as into 32768 + 4096."""
    diff = None
    pfxs = []
    while amount != 0:
      power = int(math.floor(math.log(amount)/math.log(2)))
      pfxs.append(32 - power)
      amount -= 2 ** power
    return pfxs

  def ProvideSeriesFromPrefixesAndLengths(self, starting_prefix, lengths):
    """Given a supplied prefix and lengths, we return the right series
    to express that address span starting from the right prefix and
    continuing on for the supplied lengths."""
    current = starting_prefix
    prefixes = []
    for preflen in lengths:
      candidate = str(current) + '/' + str(preflen)
      prefixes.append(candidate)
      candbroad = IPy.IP(candidate).broadcast()
      current = IPy.IP(IPy.IP(candidate).broadcast().int() + 1)
    return prefixes


class timelined(simulation):
  """IPv4 run-out simulation with a timeline."""
  def Begin(self, lir_behave, rir_behave):
    # Useful initial declarations.
    exhaustion_dates = dict()
    # Remove irreleavant LIRs, if they exist.
    try:
      del self.lirs['ZZ']
    except:
      pass
    # Display the state of IANA at the very start.
    self.iana.PrintStats()
    # Lame, please FIXME
    lir_progress_count = 0
    lir_total = len(self.lirs)
    # Go around the LIR population once doing setup.
    for lir in self.GetLIRs():
      lir_progress_count += 1
      if self.debug >= 1:
        print "sim.begin: Examining [%s] of [%s] LIRs" % (lir_progress_count,
                                                          lir_total)
      # Set behaviour as supplied on CLI, which might be different
      # to default behaviour module. Useful to over-ride in case of
      # checkpoint.
      if lir_behave != None:
        # If the class name has arguments, mask them out...
        m = re.compile('(\S+)\((\S+)\)$')
        q = m.match(lir_behave)
        if q != None:
          name = getattr(behaviour, q.group(1))
          self.behaviour = name(q.group(2))
        else:
          name = getattr(behaviour, lir_behave)
          self.behaviour = name()
      # Register each LIR we iterate with on the callback timeline.
      lir.ActivityCallback(self.timeline)
    # We'll do the RIRs as well. Although they don't generally have
    # the immediate requirements that LIRs have, they do need to keep
    # track of their overall availability, and follow policy with respect
    # to asking for more.
    for rir in self.GetRIRs():
      # Setup for RIRs now.
      if self.debug >= 1:
        print "sim.begin: Examining rir [%s]" % rir.name
      rir.UpdateStats()
      rir.PrintStats()
      rir.ActivityCallback(self.timeline)
    # Now this is effectively the main loop, which amounts to iterating
    # along the timeline until we end.
    current_date = self.timeline.GetCurrentDate()
    previous_date = None
    for callback in self.timeline.WalkAlong():
      self.timeline.PrintStatus()
      print exhaustion_dates
      if current_date != previous_date:
        self.iana.SetDate(self.timeline.GetCurrentDate())
      for rir in self.GetRIRs():
        rir.SetDate(self.timeline.GetCurrentDate())
        if rir.GetSpaceExhausted() == True and rir.name not in exhaustion_dates: 
          print "RIR EXHAUSTED", rir.name
          exhaustion_dates[rir.name] = self.timeline.GetCurrentDate()
      if len(exhaustion_dates) == 5:
        print "Game over - RIR exhaustion at [%s]" % self.timeline.GetCurrentDate()
        print exhaustion_dates
        sys.exit()
      self.iana.SetDate(self.timeline.GetCurrentDate())
      current_date = self.timeline.GetCurrentDate()
      print "IANA PERCENT FREE: [%s]" % self.iana.AddressPercentageLeft()
      if self.iana.AddressPercentageLeft() <= 0.0 and 'iana' not in exhaustion_dates:
        exhaustion_dates['iana'] = self.timeline.GetCurrentDate()
      callback(self.timeline)
      previous_date = current_date

def Usage():
  """Instructions for usage."""
  print "Run an address allocation simulation."
  print
  print "--help: this help"
  print "--checkpoint: generate or use a previously generated checkpoint file"
  print "--lir_behave: select a particular kind of LIR behaviour from available classes"
  print "--rir_behave: select a particular kind of RIR behaviour from available classes"
  print "--debug: set integer debug level"

if __name__ == '__main__':
  # CLI argument parsing
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hcl:r:d:", ["help",
                              "checkpoint",
                              "lir_behave=",
                              "rir_behave=",
                              "debug="])
  except getopt.GetoptError:
    # TODO(niallm)
    sys.exit(2)
  # Actually set stuff up as a result of the flags
  cur_debug = 0
  # Checkpoint(ed) flag
  cp = False
  lir_behave = constants.defines._DEFAULT_LIR_BEHAVIOUR
  rir_behave = constants.defines._DEFAULT_RIR_BEHAVIOUR
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      Usage()
      sys.exit()
    if opt in ("-c", "--checkpoint"):
      cp = True
    elif opt in ('-l', '--lir_behave'):
      lir_behave = arg
    elif opt in ('-r', '--rir_behave'):
      rir_behave = arg
    elif opt in ('-d', '--debug'):
      cur_debug = arg
  # Set up the event processor object so that it can cascade
  # through the object tree.
  eventp = instrumentation.event_processor()
  # Initialise the actual simulation. FIXME behaviour mode set by --mode
  sim = timelined(supplied_debug = cur_debug, 
                  supplied_inst = eventp)
  # If we don't have a startup checkpoint file, read in initialisation
  # from the historical table and checkpoint it (so we don't have to do
  # it again for every simulation). We assume this is the right thing
  # to do, since most people aren't interested in a clean-room simulation...
  if not os.path.exists(constants.defines._STARTUP_CHECKPOINT_FILE):
    sim.FromIANAProcess(rir_behave = rir_behave)
    sim.FromRIRProcess(lir_behave = lir_behave,
                       rir_behave = rir_behave)
    eventp.ReceiveEvent("FINISHED_SETUP")
    if cp:
      sim.DumpCheckpoint(constants.defines._STARTUP_CHECKPOINT_FILE)
  elif os.path.exists(constants.defines._STARTUP_CHECKPOINT_FILE) and cp:
    sim.ReadCheckpoint(constants.defines._STARTUP_CHECKPOINT_FILE)
  if not os.path.exists(constants.defines._CHECKPOINT_FILE):
    sim.Begin(lir_behave, rir_behave)
  elif os.path.exists(constants.defines._CHECKPOINT_FILE):
    sim.ReadCheckpoint(constants.defines._CHECKPOINT_FILE)
    sim.Begin(lir_behave, rir_behave)
