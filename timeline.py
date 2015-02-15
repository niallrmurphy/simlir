#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""timeline.py - Support for date-based discrete event simulation.

Provide a timeline object, the purpose of which is to do discrete event-based
simulation. Objects register callbacks in a linked list structure; various
methods provide insertion and traversal capabilities. This is part of the
SimLIR framework, which models the exhaustion of the remaining IPv4 address
space.

A typical use case is for a simulation to instantiate a TimeLine object, and
add callback events on particular dates using the add() method. Within the
existing simulation, there is no requirement for the events (callbacks) to
be processed in any particular order within their date grouping, so we just
follow the order of insertion into the list.

Created by Niall Murphy on 2007-07-25.
"""

__author__ = "niallm@gmail.com (Niall Murphy)"

import constants
import datetime
import logging
import random
import types


class ListNode(object):
  """A node in the timeline structure.

  Has 'data', a 'date' (in YYYYMMDD format) and a next pointer.
  """

  def __init__(self, data=[], next=None, date=None):
    """Make a new list node, with data, a next pointer, and a date."""
    self.data = data
    self.next = next
    self.date = date

  def AddData(self, new_data):
    """Add to the data list for this node.

    Args:
      new_data: data to be appended to the list, which should itself
      be a list.

    Raises:
      TypeError: You supplied a non-List.

    If the self.data component doesn't exist, then we just replace it
    with a single element list, otherwise we append to the list.
    """
    if type(new_data) != types.ListType:
        raise TypeError()

    if not self.data:
      self.data = new_data
    else:
      for element in new_data:
        self.data.append(element)

  def ClearData(self):
    """Clear all data from node."""
    self.data = None


class LinkedList(object):
  """A singly-linked list class that ListNode is a subcomponent of.

  We use a linked list rather than collection.dequeue because of the
  non-iterable behaviour of modified collection objects, and we don't
  use a reverse list because the same poor behaviour at scale holds when
  we are initialising.
  """
  def __init__(self):
    self.head = None

  def PrintForward(self, listnode=None):
    """Print the linked list in forward order from supplied node.

    By default, we assume 'listnode' to be the head.
    """
    if listnode is None:
      listnode = self.head
    while listnode:
      print listnode, listnode.data
      listnode = listnode.next

  def PrintBackward(self, listnode=None):
    """Print list backward from supplied node.

    By default, we assume 'listnode' to be the head.
    """
    if listnode is None:
      listnode = self.head
    seq = self.ConstructList(listnode)
    seq.reverse()
    for item in seq:
      print item, item.data

  def ConstructList(self, listnode=None):
    """Construct a list of the nodes following 'listnode'.

    By default, we assume 'listnode' to be the head.

    Returns:
      A list, composed of the following elements of the linked list from
      the nominated node.
    """
    if listnode is None:
      listnode = self.head
    seq = []
    while listnode is not None:
      seq.append(listnode)
      listnode = listnode.next
    return seq


class Timeline(object):
  """High-level object for manipulating timelines.

  The Timeline object glues together collection and
  list node objects to provide a (time-index accessible)
  sequence of items.
  """

  def __init__(self,
               supplied_debug=0,
               instrumentation=None):
    self.head = None
    self.pointer = None  # Our notion of 'the current date'.
    self.debug = supplied_debug
    self.instrument = instrumentation

  def SetPointerToHead(self):
    """Set the current pointer to the head of the list."""
    self.pointer = self.head

  def SetDebug(self, value):
    """Set the debugging value (increase verbosity generally)."""
    self.debug = value

  def PrintStatus(self):
    """Print out some general information about what's going on."""
    print "Timeline status: "
    print "Current pointer date: [%s]" % self.pointer.date
    print "Current pointer data count: [%s]" % len(self.pointer.data)
    print "Next item date: [%s]" % self.pointer.next.date
    print "Next item data count: [%s]" % len(self.pointer.next.data)

  def GetAtDate(self, date):
    """Return whatever node is to be found at this precise date, or None."""
    preserve = self.pointer
    self.pointer = self.head
    while self.pointer is not None and self.pointer.date < date:
      self.pointer = self.pointer.next
    if self.pointer is None:
      return None
    elif self.pointer.date == date:
      ephemeral = self.pointer
      self.pointer = preserve
      return ephemeral
    else:
      self.pointer = preserve
      return None

  def GetFirstBefore(self, supplied_date):
    """Return the first node before this date, or None."""
    preserve = self.pointer
    self.pointer = self.head
    previous = None
    while self.pointer is not None and self.pointer.date < supplied_date:
      previous = self.pointer
      self.pointer = self.pointer.next
    if previous.date < supplied_date:
      self.pointer = preserve
      return previous
    else:
      self.pointer = preserve
      return None

  def GetFirstAfter(self, date):
    """Return the first node after this date, or None."""
    preserve = self.pointer
    self.pointer = self.head
    while self.pointer is not None and self.pointer.date < date:
      self.pointer = self.pointer.next
    if self.pointer.next.date >= date:
      self.pointer = preserve
      return self.pointer.next
    else:
      self.pointer = preserve
      return None

  def GetCurrentDate(self):
    """Get the date of the current node.

    Return the head node if no pointer yet.
    """
    if self.pointer is None:
      return self.head.date
    else:
      return self.pointer.date

  def RegisterCallbackAtDate(self, date, callback_event):
    """This wraps the add() action to add a callback for this specific date."""
    if self.debug >= 2:
      print ("timeline.RegisterCallbackAtDate at [%s] with [%s]" %
             (date, callback_event))
    self.Add(date, callback_event)

  def Add(self, date, event):
    """Add an event to the supplied date.

    If the relevant node with date is missing, create it. Otherwise,
    add it to what is already present. If the date is invalid,
    raise an exception.
    """
    # Event process this if we're not in a test.
    if self.instrument is not None:
      self.instrument.ReceiveEvent("ADD_TIMELINE", date, event)
    # Simple date sanity checking.
    try:
      year = int(date[0:4])
      month = int(date[4:6])
      day = int(date[6:8])
    except ValueError:
      raise ValueError("Date %s out of range for timeline.add" % date)
    preserve = self.pointer
    self.pointer = self.head
    if (year < constants.defines._YEAR_MIN_BEGIN or
        year > constants.defines._YEAR_MAX_END):
      raise ValueError("Supplied year [%s] out of bounds" % year)
    elif month < 1 or month > 12:
      raise ValueError("Supplied month [%s] out of bounds" % month)
    elif day < 1 or day > 31:
      raise ValueError("Supplied day [%s] out of bounds" % day)
    # If we're starting out with a null collection, then we can legitimately
    # special case this.
    if self.head is None:
      logging.info("*** INSERT AT HEAD OF LIST")
      # Insert at head of list (when head is none)
      self.head = ListNode(data=event, next=None, date=date)
      # SIDE EFFECT - WARNING WARNING - we set our pointer to the head now.
      self.SetPointerToHead()
      return
    # If we've got a list, we find the best place to put the new node.
    previous = None
    while self.pointer is not None and self.pointer.date < date:
      previous = self.pointer
      self.pointer = self.pointer.next
    if self.pointer == None:
      logging.info("*** REPLACE AT TAIL OF LIST")
      n = ListNode(next=None, date=date)
      n.data = event
      previous.next = n
    elif self.pointer.date == date:
      logging.info("*** ADD TO CURRENT NODE")
      self.pointer.AddData(event)
    elif self.pointer.date > date and previous is not None:
      logging.info("*** INSERT BETWEEN PREVIOUS AND CURRENT")
      n = ListNode(data=event, next=self.pointer, date=date)
      previous.next = n
      n.next = self.pointer
    elif self.pointer.date > date and previous is None:
      logging.info("*** INSERT AT VERY HEAD OF LIST")
      self.head = (ListNode(data=event, next=self.pointer,
                   date=date))
    self.pointer = preserve

  def AddNode(self, node):
    """Add an already constructed node with existing date specification."""
    preserve = self.pointer
    self.pointer = self.head
    if self.head == None:
      if self.debug >= 2:
        print "*** INSERT AT HEAD OF LIST"
      self.head = node
      return
    previous = None
    while self.pointer is not None and self.pointer.date < node.date:
      previous = self.pointer
      self.pointer = self.pointer.next
    if self.pointer == None:
      if self.debug >= 2:
        print "*** REPLACE AT TAIL OF LIST"
      previous.next = node
    elif self.pointer.date == node.date:
      if self.debug >= 2:
        print "*** ADD TO CURRENT NODE"
      # Add it to current node; brokenly merges data.
      merge1 = node.data
      merge2 = self.pointer.data
      m = dict([(x, 1) for x in merge1 + merge2])
      self.pointer.ClearData()
      self.pointer.data = m.keys
    elif self.pointer.date > node.date and previous is not None:
      if self.debug >= 2:
        print "*** INSERT BETWEEN PREVIOUS AND CURRENT"
      previous.next = node
      node.next = self.pointer
    elif self.pointer.date > node.date and previous is None:
      if self.debug >= 2:
        print "*** INSERT AT VERY HEAD OF LIST"
      self.head = node
      node.next = self.pointer
    self.pointer = preserve

  def Remove(self, supplied_date):
    """Remove node at supplied_date.

    Such nodes as might exist on either side get joined. If no node exists
    at that precise date, we return False."""
    preserve = self.pointer
    self.pointer = self.head
    while self.pointer is not None and self.pointer.date < supplied_date:
      previous = self.pointer
      self.pointer = self.pointer.next
    if self.pointer.date == supplied_date:
      previous.next = self.pointer.next
      self.pointer = preserve
      return True
    else:
      self.pointer = preserve
      return False

  def Prune(self, supplied_date, target):
    """Prune the specified item from the data array at the specified date.

    If no node or matching data exists, return False."""
    preserve = self.pointer
    self.pointer = self.head
    while self.pointer is not None and self.pointer.date < supplied_date:
      self.pointer = self.pointer.next
    if self.pointer.date == supplied_date:
      try:
        self.pointer.data.remove(target)
        self.pointer = preserve
        return True
      except ValueError:
        # A list existed at the given date, but we didn't find the item.
        return False
    else:
      # A node with that date did not exist.
      self.pointer = preserve
      return False

  def WalkAlong(self):
    """A generator for the timeline object.

    The walk_along() method for this class yields the members of the data 
    array for the current node, then moves the pointer to the next node
    and does the same thing there, and so on. (Note that the existence of
    a global pointer member means multiple walkers cannot co-exist.)
    """
    self.pointer = self.head
    while self.pointer is not None:
      for x in self.pointer.data:
        yield x
      self.pointer = self.pointer.next

# And now for general functions to do with date manipulations
# that we'd like to be accessible outside of a TimeLine instance.

def DayDelta(later_date, earlier_date):
  """Provide delta in integer days between two YYYYMMDD dates.

  Args:
    later_date, earlier_date: string representations of the dates
    in question.

  Raises:
    ValueError in the case of unparsable dates being supplied.
  """
  later_datetime = CalculateDateObj(later_date)
  earlier_datetime = CalculateDateObj(earlier_date)
  delta = later_datetime - earlier_datetime
  return delta.days

def CalculatePeriodLater(cur_date=None, delta=27, upperbound=6):
  """Calculate the YYYYMMDD successor of cur_date and delta.

  Default is to assume one month, with a variability of 1-6 days
  (jittering is useful against thundering herd.)

  Raises:
    ValueError if unparsable data is supplied.
  """
  cur_datetime = CalculateDateObj(cur_date)
  reply = (cur_datetime + datetime.timedelta(days=delta) +
           datetime.timedelta(days=random.randint(1,upperbound)))
  return reply.strftime("%Y%m%d")

def FilterWithinDate(cur_date, days, other_date):
  """Return true if other_date unstrictly within <days> days of cur_date.

  Args:
    cur_date and other_date are string representations of the current and
    other date in YYYYMMDD format. days is an integer number of days.

  Raises:
    ValueError in the case of unparsable dates.
  """
  cur_datetime = CalculateDateObj(cur_date)
  other_datetime = CalculateDateObj(other_date)
  if abs(cur_datetime - other_datetime) <= datetime.timedelta(days=days):
    return True
  else:
    return False

def CalculateDateObj(cur_date):
  """Just return a date object for the specified date.

  Args:
    cur_date is a string representation of the specified date in YYYYMMDD
    format.

  Raises:
    ValueError in the case of bad data.
  """
  cur_year = int(cur_date[0:4])
  cur_month = int(cur_date[4:6])
  cur_day = int(cur_date[6:8])
  cur_datetime = datetime.date(cur_year, cur_month, cur_day)
  return cur_datetime
