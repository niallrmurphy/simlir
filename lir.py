#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>
"""
lir.py - model address holders and address suppliers.

Instead of modelling only concrete LIR and RIR objects, we abstract
out address holder and address supplier base objects. These are inherited-from
by the concrete objects you'd expect, but it preserves the flexibility for
an address holder to later mutate into provided address supplier methods;
useful for modelling trading.

Created by Niall Murphy on 2007-02-22.
"""

# Must occur at beginning due to integer division "feature"
from __future__ import division

import os
import sys
sys.path.append("")
import random
import re
import time

import behaviour
import constants
import datetime
import IPy
import instrumentation
import math
import tree

from instrumentation import _EVENTS as _EVENTS

class address_holder:
  """An address holder is the abstract base class for LIRs, RIRs, etc.
  Address holders hold addresses in Trees, have names, IDs, and
  a current date. Internal methods allow adding, removing and
  finding spaces."""

  def __init__(self,
               supplied_name = None,
               supplied_date = None,
               supplied_inst = None,
               supplied_debug = 0):
    """Initialise an address holder.

    Args:
      supplied_name (default None, means autogenerate)
      supplied_name (default None, means today) 
      supplied_debug (level 0 up)"""
    # Sub object initialisation
    self.table = None  # We expect this to be initialised later
    self.address_supplier = None  # Remains true only for IANA
    self.tree = tree.Tree(supplied_debug = supplied_debug)  # Cascade debug lvl
    self.behaviour = None  # This is where behaviour is indirected through
    self.registered_prefixes_by_date = dict()  # Things I've been given...
    self.registered_prefixes_by_prefix = dict()  # maintained by prefix.
    self.fulfilled_requests_by_date = dict()  # Things I've been asked for...
    self.fulfilled_requests_by_prefix = dict()  # maintained by prefix.
    # Assume reasonable defaults if caller hasn't been specific.
    if supplied_inst != None:
      self.instrument = supplied_inst
    else:
      self.instrument = \
        instrumentation.event_processor(verbosity = 
                                        constants.defines._INSTRUMENTATION_DEFAULT_VERBOSITY)
    if supplied_name == None:
      self.GenerateRandomName()
    else:
      self.name = supplied_name
    if supplied_date == None:
      self.date = datetime.date.today()
    else:
      self.date = self.SetDate(supplied_date) 
    # Address spans and utilisation counters.
    self.space_exhausted = False
    self.address_span = 0
    self.addresses_used = 0
    self.debug = supplied_debug
   
  # Functions related to the global routing table model.

  def InjectPrefix(self, prefix):
    """Inject the relevant prefix into the 'global' routing table"""
    try:
      self.table.add_route(prefix)
    except:
      raise

  # The boolean for whether or not our current space is exhausted.
  # This means TOTAL exhaustion, not just all prefixes of a size X
  # filled; that's a separate function. I want getters and setters
  # for this because I will put in extra stuff later.

  def GetSpaceExhausted(self, size = 0):
    """Return boolean describing whether all locally allocatable
    space has been in fact allocated."""
    # TODO(niallm): return true if all _contiguous_ space of size
    # X has been used. i.e we've asked for a /24, but we have dis-contiguous
    # /25's only - that would return false.
    return self.space_exhausted

  def _SetSpaceExhausted(self, value = True):
    """Set boolean describing whether all locally allocatable
    space has been in fact allocated."""
    self.space_exhausted = value

  # Methods related to naming.

  def GenerateRandomName(self):
    """Generate a random name in RIPE LIR format (country.blah)."""
    # TODO(niallm): make this do something useful.
    self.name = constants.defines._DEFAULT_GENERATE_ME
    self.instrument.ReceiveEvent('GENERATE_NAME', self.name)

  def SetName(self, supplied_name):
    """Set the name for this object."""
    # Getters/Setters because of instrumentation.
    self.name = supplied_name
    self.instrument.ReceiveEvent('SET_NAME', supplied_name)

  def GetName(self):
    """Return name for this object"""
    return self.name

  # Methods related to dating.

  def SetDate(self, supplied_date):
    """Set the internal clock (in YYYYMMDD format).
    We maintain internal clock as datetime object. Set and gets impose
    and expect the YYYYMMDD formatting standard used in RIR data files.

    Args:
      supplied_date: date in YYYYMMDD (string) format.

    Raises:
      ValueError if date out of bounds defined in constants.py."""
    year = int(supplied_date[0:4])
    month = int(supplied_date[4:6])
    day = int(supplied_date[6:8])
    # Sanity checking.
    if (year < constants.defines._YEAR_MIN_BEGIN or 
        year > constants.defines._YEAR_MAX_END):
      raise ValueError, "Supplied year %s out of bounds" % year
    elif (month < 1 or month > 12):
      raise ValueError, "Supplied month %s out of bounds" % month
    elif (day < 1 or day > 31):
      raise ValueError, "Supplied day %s out of bounds" % day
    self.date = datetime.date(year, month, day)
    self.instrument.ReceiveEvent('SET_DATE', self.name, year, month, day)
    return self.date

  def GetDate(self):
    """Return the internal clock."""
    # TODO(niallm): fix this output. I think.
    return self.date.strftime("%Y%m%d")

  def IncrementDate(self):
    """Increase the internal clock by the 'unit' of time measurement,
    which is one day."""
    oneday = datetime.timedelta(days=1)
    self.date = self.date + oneday

  # Methods related to obtaining prefixes for this holder from other sources.

  def _AddTreePrefix(self, 
                     prefix, 
                     note, 
                     used = False, 
                     supplied_date = None,
                     test_dup = True):
    """This is an internal method used to attempt to add a prefix
    to that which an address holder holds, and also to 'register' it;
    in other words record that we received it. These things are done in
    separate structures; so the prefix is stored in a Tree object, but
    is 'registered' in a list. This makes it easier to cope with the
    different use cases of an LIR vs an RIR, and also cope properly with
    self-induced deaggregation.

    Args:
      prefix: CIDR string
      note: plain text note you want stored with the prefix
      used: boolean; a holder can get address space that is intended
        for use solely for the holder, and should not be further allocated
        from. i.e. LIRs typically have this set, RIRs typically do not.
      supplied_date: the date on which this event takes place.
      test_dup: enforce duplicate checking on insert.

    Raises:
      Whatever the insert method of Tree.tree() can raise on failure.
    """
    if self.debug >= 2:
      print "lir._add_tree_prefix prefix (%s) note (%s) used (%s) supplied \
date (%s)" % (prefix, note, used, supplied_date)
    result = self.tree.Insert(prefix, 
                              self.GetName() + " " + note, 
                              mark_used = used,
                              test_none = False,
                              test_dup = test_dup)
    if result == False:
      return False
    if self.debug >= 3:
      self.tree.PrintIterableNodes()
    # If it's marked used on reception, we increase both the
    # address span and the used addresses.
    self.address_span += IPy.IP(prefix).len()
    if used == True:
      self.addresses_used += IPy.IP(prefix).len()
    if supplied_date == None:
      self._RegisterPrefix(prefix, self.GetDate())
    else:
      self._RegisterPrefix(prefix, supplied_date)
    self.instrument.ReceiveEvent('ADD_PREFIX', self.GetName(), prefix, supplied_date)
    return True

  def _RemoveTreePrefix(self, prefix):
    """Attempt to remove the prefix supplied from registered prefixes.

    Args:
      prefix: in CIDR (string) format.

    Raises:
      Pass up a KeyError in case of failure."""
    try:
      self.tree.Remove(prefix)
      self._RemovePrefix(prefix)
    except:
      raise
    else:
      return True

  def _IterateTreePrefixes(self):
    """Semi-private method for iterating over the underlying tree nodes."""
    for node in self.tree.IterateNodes():
      yield node

  def _CountTreePrefixes(self):
    """Semi-private method for counting the prefixes we've inserted into 
    the tree."""
    return self.tree.CountUsedNodes()

  # Registered prefixes are those we've gotten (or been given) from other sources,
  # but tracked separately because we want to keep prefix acquisition history
  # disjoint from current-state-of-tree, due to deaggregation.

  def _RegisterPrefix(self, prefix, date):
    """Register a prefix as having been allocated. The below
    is from the python cookbook as a 'map lists to single
    dict key' recipe, in case we receive two prefixes on
    the same date. We store both prefix index and date index
    in the same dict for ease of access."""
    self.registered_prefixes_by_date.setdefault(date, []).append(prefix)
    self.registered_prefixes_by_prefix.setdefault(prefix, []).append(date)

  def _CountRegisteredPrefixes(self):
    """How many prefixes have we registered?"""
    return len(self.registered_prefixes_by_prefix)

  def _RetrieveRegisteredPrefixes(self):
    """What exact prefixes did we receive?"""
    result_set = []
    for item in self.registered_prefixes_by_prefix:
      result_set.append(item)
    return result_set

  def _HaveRegistered(self, prefix):
    """Have I seen this prefix in our list? """
    for x in self.registered_prefixes_by_prefix:
      if prefix in x:
        return True
    return False

  def _RemoveRegisteredPrefix(self, prefix):
    """Never happens... except when it does. FIXME remove _by_date """
    return self.registered_prefixes.remove(prefix)

  def _RegisteredPrefixesByCountSorted(self):
    items = self.registered_prefixes_by_prefix.items()
    items.sort()
    for prefix in items:
      yield prefix[0]

  def _RegisteredPrefixesByDateSorted(self):
    items = self.registered_prefixes_by_date.items()
    items.sort()
    for prefix in items:
      yield prefix[1]

  def AddressesUsed(self):
    return self.addresses_used

  def AddressesAvailable(self):
    return self.address_span - self.addresses_used

  def AddressPercentageLeft(self):
    if self.addresses_used == 0:
      return 100
    else:
      return 100 - 1/(self.address_span/self.addresses_used) * 100.0/1

  def AddressPercentageUsed(self):
    return 1/(self.address_span/self.addresses_used) * 100.0/1

  def AddressCIDRUsed(self, divisor = 8):
    return self.addresses_used/2**(32 - divisor)

  def AddressCIDRLeft(self, divisor = 8):
    return self.addresses_available() / 2 ** (32 - divisor)

  def SpanForSize(self, size):
    return 2 ** (32 - size)

  def PrefixToSpan(self, new_prefix):
    span = IPy.IP(new_prefix).len()
    return 32 - int(math.ceil(math.log(span)/math.log(2)))

  def SpanNormaliseSlashEight(self, span):
    slash = 2 ** 24
    return span/slash

  def SpanByUsedPrefix(self):
    """A consistency check function. This minus addresses_used
    should be zero, unless prefixes overlap"""
    span = 0
    for prefix in self.tree.IterateNodesUnderOnlySupernets():
      span += IPy.IP(prefix).len()
    return span

  def IETFReservedCount(self):
    span = 0
    for prefix in self.tree.IterateNodes(True):
      if prefix[1] == 'IANA IETF RESERVED':
        span += IPy.IP(prefix[0]).len()
    return span

  def IANAAssignedCount(self):
    span = 0
    for prefix in self.tree.IterateNodes(True):
      if prefix[1] == 'IANA ASSIGNED':
        span += IPy.IP(prefix[0]).len()
    return span

  def IANAVariousCount(self):
    span = 0
    for prefix in self.tree.IterateNodes(True):
      if prefix[1] == 'IANA VARIOUS':
        span += IPy.IP(prefix[0]).len()
    return span

  def IANAAssignedCount(self):
    span = 0
    for prefix in self.tree.IterateNodes(True):
      if prefix[1] == 'IANA ASSIGNED':
        span += IPy.IP(prefix[0]).len()
    return span

  def IANAToRIRCount(self, rir):
    span = 0
    for prefix in self.tree.IterateNodes(True):
      if prefix[1] == 'IANA TO RIR ' + str(rir):
        span += IPy.IP(prefix[0]).len()
    return span

class address_supplier(address_holder):
  """Just to make the point that address holders are extensible.."""

  def _FulfillRequest(self, prefix, date):
    """Record that we have fulfilled a request for this prefix on this date.
    """
    self.fulfilled_requests_by_date.setdefault(date, []).append(prefix)
    self.fulfilled_requests_by_prefix.setdefault(prefix, []).append(date)

  # Fulfilled prefixes are those we've given out to others asking.

  def _CountFulfilledRequests(self):
    """How many requests have we fulfilled? """
    return self.fulfilled_requests_by_prefix.len()

  def _RetrieveFulfilledRequests(self):
    """Return what prefixes we've given out"""
    return self.fulfilled_requests_by_prefix

  def _HaveGivenOut(self, prefix):
    """Have we given this particular prefix out? """
    for x in self.fulfilled_requests_by_prefix:
      if prefix in x:
        return True
    return False

  # Making a request of us, from <entity> for <size>.

  def Request(self, entity, size):
    """Process request *from* entity for a block of size size. If we receive
    a request of _UNSIZED_INIT_REQUEST, we substitute the default initial
    allocation size. If we receive a request of _UNSIZED_DEFAULT_REQUEST, we
    substitute our 'default' size. All of these are defined in behaviour object"""
    name = entity.name
    space = None
    if size == constants.defines._UNSIZED_INIT_REQUEST:
      size = self.behaviour.GetInitialSize(self.GetDate())
    elif size == constants.defines._UNSIZED_DEFAULT_REQUEST:
      size = self.behaviour.GetDefaultSize(self.GetDate())
    self.instrument.ReceiveEvent('REQUEST_SPACE', name, size, self.name)
    # Important to sort these for principle of least surprise.
    for prefix in self.iana_prefixes:
      if self.debug >= 2:
        print "lir.addr_supp.request finds gap from (%s)" % prefix
      space = self.tree.FindGapFrom(prefix, size)
      if space != None:
        self._FulfillRequest(space, self.GetDate())
        self.tree.Insert(space, name + self.GetDate())
        self.address_span += self.SpanForSize(size)
        self.addresses_used += self.SpanForSize(size)
        self.instrument.ReceiveEvent('RIR_FREE_SPACE_CHANGE', self,
                                      self.AddressPercentageLeft(),
                                      self.GetDate())
        self.space_exhausted = False
        return space
    # We've not found free space... so we're exhausted
    if space == None:
      if self.debug >= 1:
        print "lir.addr_supp.request is exhausted at size (%s)" % size
      self._SetSpaceExhausted(True)
      # Try to get some more space FIXME
      if self.address_supplier == None:
        # Error condition I don't fully understand
        print "NO ADDRESS SUPPLIER!!"
        print "I AM ", self.name
        sys.exit(2)
      if self.address_supplier.GetSpaceExhausted() != True:
        new_prefix = self.address_supplier.Request(self, 
                                                   constants.defines._UNSIZED_DEFAULT_REQUEST)
        if new_prefix != None:
          if self.debug >= 1:
            print "*** New prefix", new_prefix
          self._AddTreePrefix(new_prefix, 
                                "OBTAINED FROM [%s] ON [%s]" % (self.address_supplier.GetName(), 
                                                              self.GetDate()))
          self.address_span += self.PrefixToSpan(new_prefix)
          self.space_exhausted = False
      else:
        # FIXME raise something here?
        # Can't get space from upstream. So just...
        self._SetSpaceExhausted(True)
        self.instrument.ReceiveEvent('RIR_EXHAUSTED', 
                                      self.name,
                                      size,
                                      self.GetDate())
        return None
    # Hand back the prefix
    if self.debug >= 2:
      print "lir.addr_supp.request finds space (%s)" % space
    return space

class iana(address_supplier):
  """IANA is the top level registrar. It has a requesting RIR population - 
  albeit a small one."""
  def __init__( self,
                supplied_name = "IANA",
                supplied_date = None, 
                supplied_debug = 0,
                supplied_inst = None):
    """Initialise the IANA according to supplied parameters. (Ah, if only.)
    debug is an debugging level integer; expect to see more output if this
    is set > 0. If you want to call it something other than IANA, set 
    supplied_name to whatever is desired. Finally 'date' is a YYYYMMDD
    date specification for the current date that this object thinks it is."""
    # Calling the init of the subclass
    address_holder.__init__(self,
                            supplied_name,
                            supplied_date,
                            supplied_inst,
                            supplied_debug)
    # IANA-specific initialisation
    self.rir_population = []
    self.behaviour = behaviour.IANA_Standard()
    # Adding the allocatable space
    self._AddTreePrefix('0.0.0.0/1', "IANA left")
    self._AddTreePrefix('128.0.0.0/1', "IANA right")
    # Addressing percentages - need to correct after the /1 registrations
    self.address_span = 2 ** 32
    self.addresses_used = 0
    # self.subtract_reserved() # Not done by default; rely on unicast 
    # assignments table
    self.instrument.ReceiveEvent('CREATE_IANA')

  # Methods related to obtaining prefixes for this holder from other sources.

  def _AddTreePrefix(self, 
                     prefix, 
                     note, 
                     used = False, 
                     supplied_date = None,
                     test_dup = True):
    """IANA-specific method for adding tree prefix."""
    result  =self.tree.Insert(prefix, self.name + " " + note, mark_used = used,
                              test_none = False, test_dup = test_dup)
    if result == False:
      return False
    # Only increase addresses used.
    if used == True:
      self.addresses_used += IPy.IP(prefix).len()
    if supplied_date == None:
      self._RegisterPrefix(prefix, self.GetDate())
    else:
      self._RegisterPrefix(prefix, supplied_date)
    self.instrument.ReceiveEvent('ADD_PREFIX', self.name, prefix, supplied_date)
    return True

  def PrintStats(self):
    """Print out a snapshot of our address consumption, etc."""
    # TODO(niallm): should be moved to instrumental model with GUI.
    print "+++ IANA percentage free: [%s]" % self.AddressPercentageLeft()

  def Request(self, entity, size):
    """Process request *from* entity for a block of size size. If we receive
    a request of _UNSIZED_INIT_REQUEST, we substitute the default initial
    allocation size. If we receive a request of _UNSIZED_DEFAULT_REQUEST, we
    substitute our 'default' size. All of these are defined in behaviour object. 
    Since our assignments come from essentially the whole V4 address space,
    we can use unvarnished find_gap"""
    name = entity.name
    space = None
    if size == constants.defines._UNSIZED_INIT_REQUEST:
      size = self.behaviour.GetInitialSize(self.GetDate())
    elif size == constants.defines._UNSIZED_DEFAULT_REQUEST:
      size = self.behaviour.GetDefaultSize(self.GetDate())
    self.instrument.ReceiveEvent('REQUEST_SPACE', name, size, self.name)
    # Important to sort these for principle of least surprise.
    if self.space_exhausted != True:
      space = self.tree.FindGap(size)
    else:
      self.instrument.ReceiveEvent('RIR_BLOCKED',
                                      entity.name,
                                      size,
                                      self.GetDate())
    if self.debug >= 2:
      print "addr_supp.request looking for space size (%s)" % size
    if space != None:
      # We got it! Hooray.
      self._FulfillRequest(space, self.GetDate())
      self.tree.Insert(space, name + self.GetDate())
      self.addresses_used += self.SpanForSize(size)
      self.instrument.ReceiveEvent('IANA_FREE_SPACE_CHANGE', self,
                                    self.AddressPercentageLeft(), 
                                    self.GetDate())
      return space
    else:
      # That's it. For the IANA, more or less we only accept /8 requests,
      # and only give /8s out. So when we can't service /8, we're gone.
      self._SetSpaceExhausted(True)
      self.instrument.ReceiveEvent('IANA_EXHAUSTED', "IANA", size, self.GetDate())
      return None 
    # Hand back the prefix
    if self.debug >= 2:
      print "lir.iana.request finds space (%s)" % space
    return space

class rir(address_supplier):
  """An RIR has an address assignment that it allocates out of, and has
      a requesting LIR population. The spaces received from the IANA and
      the requests made of the RIR by the attaching LIR population are 
      stored in a radix tree. When an RIR is within some determinable 
      limit of running close to exhaustion, this triggers
      a replenishment event with the upstream"""
  def __init__(self,
               supplied_name = constants.defines._DEFAULT_RIR_NAME,
               supplied_date = None,
               supplied_inst = None,
               supplied_debug = 0,
               requested_behaviour = None): # FIXME make this do something
    # Calling the init of the superclass
    address_holder.__init__(self,
                            supplied_name,
                            supplied_date,
                            supplied_inst,
                            supplied_debug)
    # RIR specific initialisation
    self.iana_prefixes = [] # Prefixes we can allocate from, via IANA
    self.util = dict() # Utilisation percentages per IANA prefix
    self.left = dict() # Addresses left per IANA prefix
    if requested_behaviour != None:
      name = getattr(behaviour, requested_behaviour)
      self.behaviour = name()
    # Notifications
    self.instrument.ReceiveEvent('CREATE_RIR', self.name)

  def ActivityCallback(self, timeline):
    """RIR callback for deciding what to do. See the LIR version for comparison."""
    try:
      current_date = timeline.GetCurrentDate()
    except:
      current_date = self.GetDate()
    if self.debug >= 2:
      print "rir.ActivityCallback called at: [%s]" % current_date
    # Set our clock
    self.SetDate(current_date)
    # For testing purposes, let's print out our stats if the debug level's high enough.
    if self.debug >= 1:
      self.PrintStats()
    avail = self.AddressesAvailable()
    # Now invoke behaviour object. 
    (reqsz, ask_again_date) = \
      self.behaviour.CalculateReqs(avail, self.iana_prefixes, current_date)
    # reqsz can be a list in the new world order
    for elem in reqsz:
      # If reqsz non-zero, request from supplier
      if self.space_exhausted == False and elem > 0:
        # What is the closest larger power of two to this?
        len = 32 - int(math.ceil(math.log(elem)/math.log(2)))
        # Make that the request
        space = self.address_supplier.Request(self, len)
        # Success or failure?
        if space == None:
          self.instrument.ReceiveEvent('LIR_BLOCKED',
                                        self.name,
                                        elem,
                                        current_date)
          # I've failed; whether I try again or not is up to the behaviour
          # module.
          self.behaviour.Failed(current_date, timeline, [self.ActivityCallback])
        else:
          self._AddTreePrefix(space, "note FIXME", True, self.GetDate())
    # Register our callback
    timeline.RegisterCallbackAtDate(ask_again_date, [self.ActivityCallback])

  def UpdateStats(self):
    """Update the free versus held per-prefix stats, and the
    total addresses_used versus spanned, etc."""
    self.address_span = 0
    self.addresses_used = 0
    for prefix in self.iana_prefixes:
      block_size = IPy.IP(prefix).len()
      span = 0
      for thing in self.tree.IterateNodesUnderOnlySupernets(prefix):
        span += IPy.IP(thing).len()
      putil = span/block_size * 100/1
      self.util[prefix] = putil
      self.left[prefix] = block_size - span
      self.address_span += block_size
      self.addresses_used += span

  def PrintStats(self):
    """Print out a snapshot of our address consumption, etc"""
    print "RIR name: [%s] Current date: [%s]" % (self.name, 
                                                 self.GetDate())
    for pref in self.iana_prefixes:
      util = self.util[pref]
      print "Prefix [%s] utilised [%2d]" % (pref, util)
      print "Addresses left [%s]" % self.left[pref]

  def _AddTreePrefix(self, prefix, note, used = True, supplied_date = None):
    """This is an internal method used to attempt to add a prefix
    to that which an address holder holds, and also to 'register' it;
    in other words record that we received it. These things are done in
    separate structures; so the prefix is stored in a Tree object, but
    is 'registered' in a list. This makes it easier to cope with the
    different use cases of an LIR vs an RIR, and also cope properly with
    self-induced deaggregation."""
    if self.debug >= 2:
      print "rir._add_tree_prefix prefix (%s) note (%s) used (%s) supplied \
date (%s)" % (prefix, note, used, supplied_date)
    if self.tree.Insert(prefix, self.name + " " + note, mark_used = used,
                       test_used = True, test_none = False) != False:
      # If it's marked used on reception, we increase both the
      # address span and the used addresses.
      self.address_span += IPy.IP(prefix).len()
      if used == True:
        self.addresses_used += IPy.IP(prefix).len()
      else: # If marked un-used, coming from IANA equiv for allocation
        self.iana_prefixes.append(prefix)
      if supplied_date == None:
        self._RegisterPrefix(prefix, self.GetDate())
      else:
        self._RegisterPrefix(prefix, supplied_date)
    else:
      print "*** Unable to add prefix [%s]; conflict" % prefix
      return False
    self.instrument.ReceiveEvent('ADD_PREFIX', self.name, prefix, supplied_date)
    return True

class lir(address_supplier):
  """Local Internet Registry (in RIPE terminology.) The folks who deal with
  the customers. LIRs have a customer base, a scaling model (which determines
  how that customer base grows), an internal clock in YYYYMMDD format, and a
  way of keeping track which allocations they have received over time.
  """
  def __init__( self, 
                supplied_name = constants.defines._DEFAULT_LIR_NAME, 
                supplied_date = None,
                supplied_inst = None,
                supplied_debug = False,
                requested_behaviour = None): # Should be over-ridden
    # Calling the init of the superclass
    try:
      result = getattr(address_supplier, '__init__')
    except AttributeError: pass
    else:
      result(self, supplied_name, supplied_date, supplied_inst, supplied_debug)
    # LIR-specific initialisation
    if requested_behaviour != None:
      # If the class name has arguments, get them out... (officially lame)
      m = re.compile('(\S+)\((\S+)\)$')
      q = m.match(requested_behaviour)
      if q != None:
        name = getattr(behaviour, q.group(1))
        self.behaviour = name(q.group(2))
      else:
        name = getattr(behaviour, requested_behaviour)
        self.behaviour = name()
    # Notifications
    self.instrument.ReceiveEvent('CREATE_LIR', self.name)

  def ActivityCallback(self, timeline):
    """This routine is referenced and placed as a callback into the Timeline
    object kept by the main simulation. It should be instantiated for every RIR 
    and LIR simulated by the system. It's job, when called, is to work out what
    has happened since the last time it was called, and ask for addresses if
    necessary."""
    try:
      current_date = timeline.GetCurrentDate()
    except:
      current_date = self.GetDate()
    if self.debug >= 2:
      print "lir.ActivityCallback called at: [%s]" % current_date
    # Pip our clock just to be safe
    self.SetDate(current_date)
    # Get our request size and callback re-registration date.
    (reqsz, ask_again_date) = \
      self.behaviour.CalculateReqs(self.registered_prefixes_by_date.items(), 
                                   self.GetDate())
    if self.debug >= 2:
        print "lir.ActivityCallback ask_again_day [%s]" % ask_again_day
        print "lir.ActivityCallback len reqsz is [%s]" % len(reqsz)
    # req_sz could be a list in the new world order.
    for elem in reqsz:
      self.instrument.ReceiveEvent('CALC_REQS', self.name, reqsz)
      if elem > 2 ** 8: # FIXME DEFINE AS STATIC
        # What is the closest larger power of two to this?
        len = 32 - int(math.ceil(math.log(elem)/math.log(2)))
        # Make that the request
        space = self.address_supplier.Request(self, len)
        # Success or failure?
        if space == None:
          self.instrument.ReceiveEvent('LIR_BLOCKED',
                                        self.name,
                                        elem,
                                        current_date)
          # I've failed; whether I try again or not is up to the behaviour
          # module.
          self.behaviour.Failed(current_date, timeline, [self.ActivityCallback])
        else:
          self._AddTreePrefix(space, "note FIXME", True, self.GetDate())
          # Register our callback
          timeline.RegisterCallbackAtDate(ask_again_date, [self.ActivityCallback])
      else:
        # You won't get a /24 or shorter from an RIR. Let's wait until the next
        # time.
        continue
    # Register our callback
    timeline.RegisterCallbackAtDate(ask_again_date, [self.ActivityCallback])
