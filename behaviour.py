#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""behaviour.py - Change request/modelling behaviour for LIRs/RIRs/IANA.

Currently each LIR/RIR/IANA instantiation has a behaviour object which is
assigned to a class from here. We indirect requests through that object so
we can change request and response behaviour on the fly.

A typical use case runs something like this:
TODO(niallm): write one here :-)

Created by Niall Murphy on 2007-07-25.
"""

import constants
import datetime
import IPy
import math
import random
import timeline


class Behaviour(object):
  """Change request behaviour for address holders and suppliers.

  This class brings together the various kinds of modifable behaviour
  that LIRs/RIRs/IANA etc can have. This mostly boils down to controlling
  when addresses will be asked for, how much will be given out in response
  to a startup request, and controlling other simulation parameters."""

  def __init__(self, args=None, debug=0):
    self.last_called = None # Date this obj last called
    self.cached_results = None # Place to store results in
    self.debug = debug # Debug level
    self.args = args

  def GetInitialSize(self, date=None):
    """Return the default size for a startup, new LIR allocation.
    Currently a /21, defined in the constants file."""
    return constants.defines._LIR_INITIAL_POLICY

  def GetDefaultSize(self, date=None):
    """For other unsized requests that are (e.g.) not as a result of
    startup operations, what actual size should they be? Use what
    the constants file tells us."""
    return constants.defines._LIR_DEFAULT_POLICY

  def Failed(self, cur_date, timeline, callback):
    """What I do if I asked for a block and got None. Default
    action is to try again 'soon'."""
    #timeline.RegisterCallbackAtDate(timeline.CalculatePeriodLater(cur_date),
    #                                   callback)
    # TODO(niallm): revive this
    pass

class Scaling(Behaviour):
  """Class governing how scaling address requirements works inside an LIR.
  This is the abstract class that new behaviour modules should inherit from.
  (Actual serious number crunching happens in the derived classes.)
  FIXME: explain growth function, 70%, etc."""

  def HowManyNeeded(self):
    """If asked, how many addresses do I say we need?"""
    return constants.defines._DEFAULT_HOWMANYNEEDED

  def CalculateReqs(self):
    """Placeholder for request size calculation."""
    pass

  def ConvertPrefixesToCounts(self, items):
    """Convert supplied prefixes to spans (absolute counts)."""
    array = []
    if self.debug > 1:
      print "(ITEMS) PREFIXES SUPPLIED: ", items
    for prefixes in items:
      for element in items[prefixes]:
        pspan = IPy.IP(element).len()
        array.append(pspan)
    if self.debug > 1:
      print "(ITEMS) SPANS RETURNED: ", array
    return array

  def SumPrefixesSpanCutoff(self, items, supplied_date, cutoff_point):
    """Count the total number of registrations, and the total size of all
    prefixes associated with that registration.
    
    Returns: (number of prefixes, number of addresses)"""
    total_pspan = 0
    total_regs = 0
    plen = 0
    for reg_date in items.keys():
      if timeline.DayDelta(supplied_date, reg_date) < cutoff_point: # Filter FIXME
        for prefix in items[reg_date]:
          pspan = IPy.IP(prefix).len()
          total_pspan += pspan
          total_regs += 1
    return (total_regs, total_pspan)
    

class IANA_Standard(Behaviour):
  """Whatever things IANA needs to decide in a variable fashion
  are controlled here."""
  def CostOfBusiness(self, size=constants.defines._UNSIZED_DEFAULT_REQUEST):
    """ A function determining how attractive this address supplier is
    currently. (The basis of market simulation.) Almost by definition, either
    the IANA is costless to deal with, or you don't care. """
    return constants.defines._COST_BUSINESS_LOW

  def GetInitialSize(self, date=None):
    """ Return the default size for an RIR startup. Currently a /8. """
    return constants.defines._RIR_INITIAL_POLICY

  def GetDefaultSize(self, date=None):
    """ For other unsized requests that are as a result of ongoing operations, 
    this is the supposed size. """
    return constants.defines._RIR_DEFAULT_POLICY

class RIR_Standard(Behaviour):
  """This defines how an RIR will behave as standard."""
  def CostOfBusiness(self, size=constants.defines._UNSIZED_DEFAULT_REQUEST):
    """A function determining how attractive this address supplier is
    for this particular request. Basis of (as yet unimplemented) market 
    simulation."""
    return constants.defines._COST_BUSINESS_LOW

  def FitChunk(self):
    """How should I fit a particular chunk, if I want it to be other
    than the first available slot? Undefined as yet."""
    pass

  def CalculateReqs(self, addr_avail, prefix_items, cur_date):
    """Calculate RIR's address space requirements, given the published
    algorithm at http://www.icann.org/general/allocation-IPv4-rirs.html -
    according to this, we should allocate from IANA to RIR if:
    * RIRs available space of ipv4 addresses is less than 50% of a /8 block,
    * RIRs available space is less than its established necessary space
    for the following nine months,
    limiting to a max of requesting two blocks as per Mar 2007 agreement.
    """
    # Check if RIRs available space of ipv4 addresses is less than 50% of a /8 block.
    if addr_avail < ((constants.defines._RIR_DEFAULT_REQUEST) * 0.5):
      # Instrument this FIXME
      return ([constants.defines._RIR_DEFAULT_REQUEST],
        timeline.CalculatePeriodLater(cur_date))
    # OR
    # RIRs available space is less than its established necessary space
    # for the following nine months.
    #else:
    #  result_set = []
    #  consideration = prefix_items.items()
    #  necessary_space = 0      
    #  for elem in consideration:
    #    if TimeLine.filter_within_date(cur_date, 30 * 6, elem[0]):
    #      for item in elem[1]:
    #        necessary_space += IPy.IP(item).len() 
    #  if available_space < (necessary_space/6) * 9:
    #    return ([constants.defines._RIR_DEFAULT_REQUEST],
    #            timeline.CalculatePeriodLater(cur_date))
    # limit to a max of requesting two blocks as per Mar 2007 agreement.
    # AVAILABLE SPACE = CURRENTLY FREE ADDRESSES + RESERVATIONS EXPIRING DURING
    # THE FOLLOWING 3 MONTHS - FRAGMENTED SPACE
    # FRAGMENTED SPACE is determined as the total amount of available blocks
    # smaller than the RIR's minimum allocation size within the RIR's currently
    # available stock.
    # NECESSARY SPACE = AVERAGE NUMBER OF ADDRESSES ALLOCATED MONTHLY DURING
    # THE PAST 6 MONTHS * LENGTH OF PERIOD IN MONTHS
    # FIXME: properly implement this
    return ([0], timeline.CalculatePeriodLater(cur_date))

  def Failed(self, cur_date, timeline, callback):
    """What I do if I asked for a block and got None. RIRs always
    re-register."""
    timeline.RegisterCallbackAtDate(timeline.CalculatePeriodLater(cur_date),
                                    callback)

class LIR_Static(Scaling):
  """Whenever we're asked, we request a block of the same size;
  primarily used for testing. If a size is not specified, we use
  constants.defines._DEFAULT_LIR_STATIC_SCALING_SIZE."""
  def CalculateReqs(self, items, supplied_date):
    if self.args == None:
      return ([2 ** (32 - constants.defines._DEFAULT_LIR_STATIC_SCALING_SIZE)],
              timeline.CalculatePeriodLater(supplied_date))
    else:
      return ([2 ** (32 - int(self.args))],
              timeline.CalculatePeriodLater(supplied_date))

class LIR_Last_N_Requests(Scaling):
  """Cycle through the last N requests. Testing method. FIXME."""
  pass

class LIR_Weekly_Average(Scaling):
  """Average our entire year's requests into weekly requests."""
  def CalculateReqs(self, items, supplied_date, period = 365):
    if self.cached_results == None:
      (numreg, span) = self.SumPrefixesSpanCutoff(items, supplied_date, period)
      # cached_results is now the daily average.
      self.cached_results = span/365
    weekly = self.cached_results * 7
    return ([weekly], timeline.CalculatePeriodLater(supplied_date, 7))

class LIR_Fortnightly_Average(Scaling):
  """Average our entire year's requests into fortnightly requests."""
  def CalculateReqs(self, items, supplied_date, period = 365):
    if self.cached_results == None:
      numreg = 0
      span = 0
      (numreg, span) = self.SumPrefixesSpanCutoff(items, supplied_date, period)
      # cached_results is now the daily average.
      self.cached_results = span/365
    fortnightly = self.cached_results * 14
    return ([fortnightly], timeline.CalculatePeriodLater(supplied_date, 14))

class LIR_Replay(Scaling):
  """Whatever we ordered in the last N days, order it again, at exactly the
  same 'rate'. N defaults to 30 days."""
  def CalculateReqs(self, items, supplied_date, period = 30):
    if self.cached_results != None:
      (request, next_date) = self.cached_results.pop()
      return (request, next_date)
    else:
      self.cached_results = []
      for reg_date in items.keys(): # younger to older
        span_for = self.ConvertPrefixesToCounts({reg_date: items[reg_date]})
        date_diff = timeline.DayDelta(supplied_date, reg_date)
        next_date = timeline.CalculatePeriodLater(supplied_date, date_diff)
        self.cached_results.append([span_for, next_date])
      (request, next_date) = self.cached_results.pop()
      return (request, next_date)


class LIR_Fortnightly_Gold_Rush(Scaling):
  """Average our entire year's requests into fortnightly requests. Inflate the
  request as we come closer to the current projected exhaustion date."""
  def CalculateReqs(self, items, supplied_date):
    if self.cached_results == None:
      numreg = 0
      span = 0
      (numreg, span) = SumPrefixesSpanCutoff(items, supplied_date, 365)      
      self.cached_results = total_plen/365
    fortnightly = self.cached_results * 14
    # Inflate the request after a certain time. FIXME to be
    # after a certain event, *NOT* hard-coded
    if timeline.DayDelta(supplied_date, "20100101") < 0:
      fortnightly_gold_rush = self.cached_results * 2
    return ([fortnightly_gold_rush],
      timeline.CalculatePeriodLater(supplied_date, 14))


class LIR_Monthly_Exp(Scaling):
  """Whatever we ordered in the last month, order it again, times 1.1,
  or whatever _DEFAULT_LIR_REQUEST_MULTIPLIER is set to. 
  Adjust timing so that we don't just go bonkers and order a /1."""
  def CalculateReqs(self, items, supplied_date):
    month_later = timeline.CalculatePeriodLater(supplied_date)
    if self.cached_results is not None:
      self.cached_results = int(self.cached_results * 
                                constants.defines._DEFAULT_LIR_REQUEST_MULTIPLIER)
      return ([self.cached_results], month_later)
    else:
      items.sort(reverse=True)
      len_bucket = []
      total_regs = 0
      total_plen = 0
      for collection in items:
        reg_date = collection[0]
        if timeline.DayDelta(supplied_date, reg_date) < 30:
          total_plen = 0
          for prefixes in collection[1]:
            plen = IPy.IP(prefixes).len()
            total_plen += plen
            total_regs += 1
      self.cached_results = total_plen
      return ([self.cached_results], month_later)

class LIR_Monthly_Smoothed(Scaling):
  """Whatever we ordered in the last month, order it again, times 1.1,
  or whatever _DEFAULT_LIR_REQUEST_MULTIPLIER is set to.
  Adjust timing so that we don't just go bonkers and order a /1.
  Also, smooth out the peaks a bit."""
  def CalculateReqs(self, items, supplied_date):
    month_later = TimeLine.calculate_month_later(supplied_date)
    if self.cached_results is not None:
      self.cached_results = int(self.cached_results * 1.10)
      if self.cached_results > (2 ** 16):  # If we're ordering more than a /16...
        self.cached_results = self.cached_results / 2  # Flatten it a bit, and halve period
        return ([self.cached_results * 2], 
                self.calculate_period_later(supplied_date, 15))
      return ([self.cached_results], month_later)
    else:
      items.sort(reverse=True)
      len_bucket = []
      total_regs = 0
      total_plen = 0
      for collection in items:
        reg_date = collection[0]
        if self.day_delta(supplied_date, reg_date) < 30:
          total_plen = 0
          for prefixes in collection[1]:
            plen = IPy.IP(prefixes).len()
            total_plen += plen
            total_regs += 1
      self.cached_results = total_plen
      return ([self.cached_results], month_later)

class LIR_Simple_Steady_State(Scaling):
  """Simple average of usage over the last LOOKBACK occasions we requested."""

  def CalculateReqs(self, items, supplied_date):
    """Calculate address requirements."""
    items.sort(reverse=True)
    if self.debug >= 1:
      print "steady_state.calculate_reqs sorted items [%s]" % items
    if self.last_called is None:
      # This is the first time we've been call-backed. 
      # Get difference between today and last date we have in items.
      self.last_called = items[-1][0]
    # If we've only ever registered one thing, we'll just return.
    # Otherwise tailor to what's available.
    lookback_range = 0
    if len(items) == 1:
      return [0]
    elif len(items) > 1 and len(items) < constants.defines._LOOKBACK:
      lookback_range = len(items)
    else:
      lookback_range = constants.defines._LOOKBACK
    # Iterate over all the items we've seen in the past _LOOKBACK, so we know 
    # roughly what our average run rate is.
    # ('20070427', ['77.87.24.0/21', '91.123.224.0/20', '91.193.188.0/22'])
    span = 0
    if self.debug >= 2:
      print "steady_state.calculate_reqs lookback range: [%s]" % lookback_range
    for x in range (0, (lookback_range - 1)):
      if self.debug >= 3:
        print "steady_state.calculate_reqs lookback item: [%s]" % x
      for possible_items in items[x][1]:
        possible_list = items[x][1]
        for prefix in possible_list:
          span += IPy.IP(prefix).len()
    if self.debug >= 2:
      print "steady_state.calculate_reqs total span: [%s]" % span
      print ("steady_state.calculate_reqs first item [%s] last item [%s]" % 
        (items[0][0], items[-1][0]))
    total_days = timeline.DayDelta(items[0][0], items[-1][0])
    if self.debug >= 2:
      print "steady_state.calculate_reqs total days [%s]" % total_days
    daily_run_rate = span/total_days
    # How many days since we were last called?
    day_gap = timeline.DayDelta(supplied_date, self.last_called)
    # These are the addresses required since we last ran.
    return ([day_gap * daily_run_rate], timeline.CalculatePeriodLater(supplied_date))


class LIR_Probability(Scaling):
  """Probability-based scaling method.
  
  We look at the past behaviour of the LIR, stick all the prefixes it has
  requested into a bucket, and then probabilistically select a prefix out
  of that bucket, registering to be asked again at the average gap."""

  def CalculateReqs(self, items, supplied_date):
    """Calculate address requirements."""
    items.sort(reverse=True)
    if self.debug >= 1:
      print "probability.calculate_reqs sorted items [%s]" % items
    if self.last_called is None:
      # This is the first time we've been call-backed. 
      # Get difference between today and last date we have in items.
      self.last_called = items[-1][0]
    # Iterate over all the items we've seen in the past _LOOKBACK_PERIOD.
    # In this model we stick all the prefix lengths we've requested
    # in a bucket, and we pluck a length at random out of that.
    len_bucket = []
    date_bucket = []
    total_regs = 0
    for collection in items:
      reg_date = collection[0]
      if (timeline.DayDelta(supplied_date, reg_date) < 
          constants.defines._LOOKBACK_PERIOD):
        date_bucket.append(reg_date)
        total_plen = 0
        for prefixes in collection[1]:
          plen = IPy.IP(prefixes).len()
          total_plen += plen
          total_regs += 1
        len_bucket.append(int((32 - (math.log(int(total_plen), 2)))))
    if self.debug >= 2:
      print "behave.scaling.lir_prob: total registrations [%s]" % total_regs
      print "behave.scaling.lir_prob: bucket [%s]" % len_bucket
    # Maybe we've never registered anything, in which case we'll just return 0,
    # and 'come back to us in a month'
    if len(len_bucket) == 0:
      return ([0], timeline.CalculatePeriodLater(supplied_date))
    # Now pick a size from the bucket.
    size = random.choice(len_bucket)
    # But when should we register it?
    # We'll use the average gap.
    date_bucket.sort()
    total_days = timeline.DayDelta(date_bucket[0], items[-1][0])
    average_gap = total_days/total_regs
    average_day_gap = int(average_gap)
    #next_date = TimeLine.calculate_date_obj(supplied_date) + \
    #  datetime.timedelta(days = average_day_gap)
    next_date = timeline.CalculatePeriodLater(supplied_date, average_day_gap)
    return ([2 ** (32 - size)], next_date)

class LIR_Histogram(Scaling):
  """Another probabilistic scaling method which caches results."""
  def CalculateReqs(self, items, supplied_date):
    """Calculate address requirements."""
    if self.cached_results == None:
      items.sort(reverse = True)
      len_bucket = []
      date_bucket = []
      grouping_bucket = []
      collections = 0
      total_reqs = 0
      previous_date = supplied_date
      for collection in items:
        reg_date = collection[0]
        collections += 1
        if (timeline.DayDelta(supplied_date, reg_date) < 
            constants.defines._LOOKBACK_PERIOD):
          date_bucket.append(timeline.DayDelta(reg_date, previous_date))
          grouping = 0
          for prefixes in collection[1]:
            plen = IPy.IP(prefixes).len()
            #len_bucket[plen] = len_bucket.get(plen, 0) + 1
            len_bucket.append(plen)
            grouping += 1
            total_reqs += 1
          grouping_bucket.append(grouping)
        previous_date = reg_date
      if len(date_bucket) == 0:
        average_gap = 30  # Keep them in the game
      else:
        average_gap = abs(sum(date_bucket)/len(date_bucket))
      self.cached_results = {'grouping': grouping_bucket,
                             'lengths': len_bucket,
                             'avg_day_gap': int(average_gap)}
    # Pick a grouping cardinality
    plengths = []
    if len(self.cached_results['lengths']) == 0:
      plengths = [0]
    else:
      number = random.choice(self.cached_results['grouping'])
      for x in range(1, number):
        # Now select a prefix length
        plengths.append(random.choice(self.cached_results['lengths']))
    #print "AVGDAYGAP", self.cached_results['avg_day_gap']
    next_date = timeline.CalculatePeriodLater(supplied_date, 
                                              self.cached_results['avg_day_gap'])
    return (plengths, next_date)

class RIR_Static(Behaviour):
  """This defines how an RIR will behave as standard."""
  def CostOfBusiness(self, size=constants.defines._UNSIZED_DEFAULT_REQUEST):
    """A function determining how attractive this address supplier is
    for this particular request. Basis of market simulation."""
    return constants.defines._COST_BUSINESS_LOW

  def FitChunk(self):
    """How should I fit a particular chunk, if I want it to be other
    than the first available slot? FIXME."""
    pass

  def CalculateReqs(self, cur_date):
    """TODO(niallm): fix description."""
    return ([constants.defines._RIR_DEFAULT_REQUEST],
            timeline.CalculatePeriodLater(cur_date))

  def Failed(self, cur_date, timeline, callback):
    """What I do if I asked for a block and got None. RIRs always
    re-register."""
    timeline.RegisterCallbackAtDate(timeline.CalculatePeriodLater(cur_date),
                                    callback)
