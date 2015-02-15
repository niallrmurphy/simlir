#!/usr/bin/env python
# encoding: utf-8
"""
instrumentation.py

This file defines the various 'events' that can happen in the simlir system. Every
time an object in the simulation does something significant, it sends a message
to a global instrumentation object, which currently has a mild wrapping around them
for textual display purposes, and for later driving of a GUI.

Typical use case:
  eventp = instrumentation.event_processor()
  eventp.ReceiveEvent("FINISHED_SETUP")

Created by Niall Murphy on 2007-05-08.
"""

# TODO(niallm): do this with env variable passing from make
# at some point.

import constants
import logging
import logging.handlers
import os
import pprint
import sys

_EVENTS = { 'ADD_ROUTE': 'AddRouteEvent',
            'ADD_PREFIX': 'AddPrefixEvent',
            'REMOVE_ROUTE': 'RemoveRouteEvent',
            'REQUEST_SPACE': 'RequestSpaceEvent',
            'NEEDS_SPACE': 'NeedsSpaceEvent',
            'GETS_SPACE': 'GetsSpaceEvent',
            'TRADE_SPACE': 'TradeSpaceEvent',
            'TAKE_STARTUP_SPACE': 'TakeStartupSpaceEvent',
            'GENERATE_NAME': 'GenerateNameEvent',
            'SET_NAME': 'SetNameEvent',
            'SET_DATE': 'SetDateEvent',
            'FIND_UNUSED': 'FindUnusedEvent',
            'UNIT_TEST': 'JustReturnArgs',
            'CREATE_LIR': 'CreateLIREvent',
            'CREATE_RIR': 'CreateRIREvent',
            'CREATE_IANA': 'CreateIANAEvent',
            'LIR_INITIAL' : 'LIRInitialEvent',
            'GET_NEXT_UNUSED' : 'GetNextUnusedEvent',
            'CONSIDER_PREFIX' : 'ConsiderPrefixEvent',
            'FOUND_GAP' : 'FoundGapEvent',
            'CALC_REQS' : 'CalculateReqsEvent',
            'NEXT_TIMELINE' : 'NextTimelineEvent',
            'ADD_TIMELINE' : 'AddTimelineEvent',
            'IANA_FREE_SPACE_CHANGE' : 'LostSpaceEvent',
            'RIR_FREE_SPACE_CHANGE' : 'LostSpaceEvent',
            'IANA_EXHAUSTED' : 'EntityExhaustedEvent',
            'RIR_EXHAUSTED' : 'EntityExhaustedEvent',
            'LIR_EXHAUSTED' : 'EntityExhaustedEvent',
            'LIR_BLOCKED' : 'EntityBlockedEvent',
            'RIR_BLOCKED' : 'EntityBlockedEvent',
            'FINISHED_READIN' : 'FinishedReadinEvent',
            'FINISHED_SETUP' : 'FinishedSetupEvent'}

class EventError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class event_processor:
  """The event_processor class is a way to instrument the internal operations
  of the LIR/tree etc classes in an extendable way. A class holds
  an event_processor object and sends various events to it. These events can
  be processed in a text-based logging fashion or can in turn send events to
  drive a gui, etc."""
  def __init__(self, 
               mode = constants.defines._INSTRUMENTATION_DEFAULT_MODE, 
               verbosity = constants.defines._INSTRUMENTATION_DEFAULT_VERBOSITY):
    progname = os.path.basename(sys.argv[0])
    self.args = {}
    self.mode = mode
    self.proc = None

    if self.mode == constants.defines._INSTRUMENTATION_MODES['stdout']:
      self.proc = text_event_processor(verbosity)
    elif self.mode == constants.defines._INSTRUMENTATION_MODES['syslog']: 
      self.logger = logging.getLogger(progname)
      self.syslog_hndlr = logging.handlers.SysLogHandler(
        facility = logging.handlers.SysLogHandler.LOG_DAEMON)
      self.formatter = logging.Formatter('%(filename)s: %(levelname)s: %(message)s')
      self.syslog_hndlr.setFormatter(self.formatter)
      self.logger.addHandler(self.syslog_hndlr)
      self.proc = syslog_event_processor
    elif self.mode == constants.defines._INSTRUMENTATION_MODES['gui']:
      raise ValueError, "gui mode not implemented yet"
    else:
      raise ValueError, "event_processor without defined mode!"

  def ReceiveEvent(self, event, *varargs):
    """Receive an event from related objects. Check the event is something we know about.
    If so, record it or log it or similar. If not, discard with error. """
    if self.mode == constants.defines._INSTRUMENTATION_MODES['stdout']:
      func = getattr(self.proc, _EVENTS[event])
      return func(varargs)
    elif self.mode == constants.defines._INSTRUMENTATION_MODES['syslog']:
      return getattr(self.proc,_EVENTS[event])(varargs)
    elif self.mode == constants.defines._INSTRUMENTATION_MODES['gui']:
      raise ValueError, "gui mode not implemented yet"
    else:
      raise ValueError, "mode not implemented yet"

class text_event_processor:
  """The default, stdio output class."""
  def __init__(self, supplied_verbosity):
    self.verbosity = supplied_verbosity

  def AddRouteEvent(self, args):
    if self.verbosity > 1:
      print "*** ADD ROUTE EVENT with route '%s', owner '%s' and note '%s'" % \
        (args[0], args[1], args[2])
    return args

  def AddPrefixEvent(self, args):
    if self.verbosity > 1:
      print "*** ADD PREFIX EVENT for '%s' with prefix '%s'" % (args[0], args[1])
    return args
    
  def RemovePrefixEvent(self, args):
    if self.verbosity > 1:
      print "*** REMOVE PREFIX EVENT with route '%s', owner '%s' and note '%s'" % \
        (args[0], args[1], args[2])
    return args
    
  def NeedsSpaceEvent(self, args): # TODO(niallm): implement
    return args
    
  def GetsSpaceEvent(self, args): # TODO(niallm): implement
    return args
    
  def TradeSpaceEvent(self, args): # TODO(niallm): implmenet
    return args
  
  def FindUnusedEvent(self, args): #
    if self.verbosity > 1:
      print "*** FIND UNUSED EVENT called to find a '/%s'" % args[0]
    return args

  def RequestSpaceEvent(self, args): # FIXME
    if self.verbosity > 0:
      print "*** REQUEST SPACE EVENT from '%s' for '/%s' fulfilling via '%s'" % \
        (args[0], args[1], args[2])
    return args

  def GenerateNameEvent(self, args): # FIXME
    if self.verbosity > 1:
      print "*** GENERATE NAME EVENT generated '%s'" % args[0]
    return args

  def SetNameEvent(self, args):
    if self.verbosity > 1:
      print "*** SET NAME EVENT to '%s'" % args[0]
    return args

  def SetDateEvent(self, args):
    if self.verbosity > 1:
      print "*** SET DATE EVENT FOR '%s' TO '%s/%s/%s'" % \
        (args[0], args[1], args[2], args[3])
    return args

  def CreateLIREvent(self, args):
    if self.verbosity > 1:
      print "*** CREATE LIR EVENT generated LIR '%s'" % args[0]
    return args

  def CreateRIREvent(self, args):
    if self.verbosity > 1:
      print "*** CREATE RIR EVENT generated RIR '%s'" % args[0]
    return args

  def CreateIANAEvent(self, args):
    if self.verbosity > 1:
      print "*** CREATE IANA EVENT"
    return args

  def GetNextUnusedEvent(self, args): # TODO(niallm): implement
    return args

  def TakeStartupSpaceEvent(self, args): # TODO(niallm): probably deprecated now
    if self.verbosity > 0:
      print "*** TAKE STARTUP SPACE for '%s' from '%s' gets prefix '%s'" % \
        (args[0], args[1], args[2])
    return args

  def ConsiderPrefixEvent(self, args):
    if self.verbosity > 0:
      print "*** CONSIDER PREFIX looks at '%s' trying to find gap" % args[1]
    return args

  def FoundGapEvent(self, args):
    if self.verbosity > 0:
      print "*** FOUND GAP found a gap at '%s' length '%s'" % (args[0], args[1])
    return args

  def EntityExhaustedEvent(self, args):
    if self.verbosity > 0:
      print "*** ENTITY [%s] IS EXHAUSTED of space of prefix length '%s' on date '%s'" % \
        (args[0], args[1], args[2]) 
    return args

  def EntityBlockedEvent(self, args):
    if self.verbosity > 0:
      print "*** ENTITY [%s] IS BLOCKED: wants space [%s] on '%s'" % \
        (args[0], args[1], args[2])
    return args

  def CalculateReqsEvent(self, args):
    if self.verbosity > 0:
      print "*** ADDRESS REQUIREMENTS CALCULATED to be '%s' for '%s'" % \
        (args[1], args[0])
    return args

  def NextTimelineEvent(self, args):
    if self.verbosity > 0:
      print "*** NEXT TIMELINE EVENT at '%s' is '%s'" % (args[0], args[1])
    return args

  def AddTimelineEvent(self, args):
    if self.verbosity > 0:
      print "*** ADD EVENT TO TIMELINE at date [%s]" % args[0]
    return args

  def LostSpaceEvent(self, args):
    if self.verbosity > 0:
      print "*** ENTITY [%s] FREE SPACE CHANGE to [%s] percent free at date [%s]" % \
        (args[0].name, args[1], args[2])
    return args

  def FinishedReadinEvent(self, args):
    """Issue this when the simulation has finished reading in checkpoint files."""
    if self.verbosity >= 2:
      print "*** SIMULATION FINISHED READIN"
    return args

  def FinishedSetupEvent(self, args):
    """Issue this when the simulation has finished setting up objects."""
    if self.verbosity >= 0:
      print "*** SIMULATION FINISHED SETUP OF OBJECTS"
    return args

  def JustReturnArgs(self, args):
    return args

class syslog_event_processor(text_event_processor):
  """Inherits everything from text; TODO(niallm): implement"""

