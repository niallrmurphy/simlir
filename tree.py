#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""tree.py - IPv4 prefix storage with fast lookup and find gap operations.

We use a structure that borrows somewhat from radix trees, patricia tries,
and plain old binary trees. (Think of it as a binary tree of depth 32,
with used portions being marked as such.)

Although the primitive operations of the tree (insert, find) are obviously
necssary to implement, the most important operation from the point of view
of the rest of the program is 'find a free slot of size X'. 

How it works:
Initially the tree is empty, having just a root node with no children.

To insert a route of PREFIX/LEN causes us to travel from the root to the 
appropriate node at depth LEN. We take the corresponding left or right branch 
(0 or 1 respectively) depending on the binary expansion of PREFIX. If there 
are nodes which have not been filled out yet (i.e. have no children) we fill 
them out in the course of descending to the correct place. (We also AND prefix 
and len to get the canonical reference notation for the route, just in case.) 

When we arrive at the right node, we check whether it's 
already been used, and optionally bomb out. (If not, we mark it used, and
check whether or not our peer at the same level is also used, in which case
we mark the parent used.)

To find an unallocated space of LEN X we begin at the root node and proceed 
first down the left branch until we hit either the level associated with the 
LEN in question, or hit a marked-as-used ancestor node on the way, or hit a 
leaf node before LEN depth. If we hit the level associated with the LEN in 
question and we've not encountered a marked as used component on the path, 
hooray! We're done. If we have, then back-track and try the right hand branch 
immediately upwards of the left hand branch that was occupied. Follow again,
retracing our steps upwards as necessary. This amounts to a pre-order traversal.

Created by Niall Murphy on 2007-07-25.
"""

import constants
import fileinput
import IPy
import re
import string
import sys

IPy.check_addr_prefixlen = False

class Node:
  """This is a node on the tree, which stores the address prefix by virtue
  of its position, but must keep track of its children and parent."""

  def __init__(self, supplied_parent = None, supplied_left = None, 
              supplied_right = None, supplied_data = None, 
              supplied_used = False):
    # initializes the data members
    self.left = supplied_left
    self.right = supplied_right
    self.parent = supplied_parent
    self.data = supplied_data
    self.used = supplied_used
    self.level = None

  def GetData(self):
    """Return the per-node 'user data' (essentially anything you could
    want to store) associated with this node."""
    return self.data

  def SetData(self, supplied_data = None):
    """Change the per-node 'user data' to the supplied anything."""
    self.data = supplied_data

  def GetParent(self):
    """What object is my parent? Returns Node or None."""
    return self.parent

  def SetParent(self, supplied_parent = None):
    """Change my parent to be a Node object or None."""
    self.parent = supplied_parent

  def GetLeft(self):
    """What object is to my left? Returns Node or None."""
    return self.left

  def SetLeft(self, supplied_left = None):
    """Change my left-hand object to be Node or None."""
    self.left = supplied_left

  def GetRight(self):
    """What's to my right? Returns Node or None."""
    return self.right

  def SetRight(self, supplied_right = None):
    """Change my right-hand object to be Node or None."""
    self.right = supplied_right

  def _GetLevel(self):
    """Get level caching implementation."""
    current = self.GetParent()
    level = 0
    while current != None:
      current = current.GetParent()
      level += 1
    return level

  def GetLevel(self):
    """What 'level' am I at in the tree? Root level is 0,
    anything after that is +N. Returns integer."""
    if self.level == None:
      self.level = self._GetLevel()
    return self.level

  def AmLeft(self):
    """Am I in the left-hand side of this particular bit of
    the tree where I am? Returns boolean."""
    if self.AmRoot():
      return False
    if self.parent.left == self:
      return True
    return False

  def AmRight(self):
    """Am I in the right-hand side of this particular bit of
    the tree where I am? Returns boolean."""
    if self.AmRoot():
      return False
    if self.parent.right == self:
      return True
    return False

  def HaveChildren(self):
    """Do I have any children? Returns boolean."""
    if self.left != None or self.right != None:
      return True
    else:
      return False

  def AmRoot(self):
    """Am I the root? Returns boolean."""
    if self.parent == None:
      return True
    return False

  def GetBinary(self):
    """Get the binary notation for the side I'm on - 0 for
    left, 1 for right. Returns integer. Don't ask about the root,
    we'll return an exception."""
    if self.AmLeft():
      return 0
    elif self.AmRight():
      return 1
    else:
      raise ValueException

  def GetPath(self):
    """Find the binary path of our current position by starting at
    the node and tracing our steps upwards, appending a 1 or 0 as we
    go depending on our value. Reverse the accumulated value and return
    it as a string."""
    tracelevel = self.GetLevel()
    binary = ""
    current = self
    while tracelevel != 0:
      binary += str(current.GetBinary())
      tracelevel -= 1
      current = current.GetParent()
    return binary[::-1]

  def AboutMe(self):
    """A misc debugging function that prints stuff about the node."""
    if self.AmRoot():
      print "\tI am the root"
    if self.used:
      print "\tMarked Used"
    else:
      print "\tNOT marked used"
    print "\tLevel: ", self.GetLevel()
    print "\tData: ", self.GetData()
    binstr = self.GetPath()
    print "\tPath: ", binstr
    q = len(binstr)
    for count in range(q, 32):
      binstr += "0"
    iphex = hex(int(binstr,2))
    complete_addr = iphex + "/" + str(self.GetLevel())
    print "Prefix: ",IPy.IP(complete_addr).strNormal(1)
    if self.AmLeft():
      print "\tI am left child of ", self.GetParent().GetPath()
    if self.AmRight():
      print "\tI am right child of ", self.GetParent().GetPath()
    if self.GetLeft() != None:
      print "\thave a left child "
    else:
      print "\tDON'T have a left child"
    if self.GetRight() != None:
      print  "\thave a right child "
    else:
      print "\tDON'T have a right child "

class Tree:
  """A Tree consists of nodes and a number of important methods.
  The root node is a root node, obviously. Import methods include
  insert, lookup and FindGap."""

  def __init__(self, supplied_debug = 0):
    # initializes the root member
    self.total_unusable_prefixes = 0
    self.root = Node(supplied_data = "Root")
    self.debug = supplied_debug

  def Insert(self, route, supplied_data, mark_used = True, 
             test_used = False, test_none = False, test_dup = True):
    """Insert route with supplied_data into tree. 
    
    Args:
      mark_used: boolean, mark the node inserted as used
      test_used: boolean, test during insertion path whether any node
        encountered is used, if so bail out (return False)
      test_none: boolean, test during insertion path whether any node
        encountered is not defined (== None), if so bail out (False)
      test_dup: boolean, test whether this new insertion is a duplicate
        of a previous insertion, if so bail out
    
    Otherwise return the node that we just inserted."""
    ip = IPy.IP(route)
    binary = ip.strBin()
    netlen = ip.prefixlen()
    current = self.root
    if self.debug >= 2:
      print "Binary is [%s], [%s] char is [%s]" % (binary, netlen, binary[netlen])
    for x in binary[:netlen]:
      if current.used and test_used == True:
        return False
      if x == '0':
        if current.GetLeft() == None and test_none == False:
          current.SetLeft(Node(current))
          current.GetLeft().used = False
          current.GetLeft().SetData("CREATED BY INSERT")
        elif current.GetLeft() == None and test_none == True:
          return False
        current = current.GetLeft()
      elif x == '1':
        if current.GetRight() == None and test_none == False:
          current.SetRight(Node(current))
          current.GetRight().used = False
          current.GetRight().SetData("CREATED BY INSERT")
        elif current.right == None and test_none == True:
          return False
        current = current.GetRight()
      else:
        """Don't understand how this could come about."""
        raise ValueException
    if test_dup == True and current.GetData() != "CREATED BY INSERT":
      return False
    if mark_used == True:
      current.used = True
    current.SetData(supplied_data)
    return current

  def Lookup(self, route, used_check = False):
    """Look up the route supplied in CIDR format and return it if
    present in the tree. Otherwise return None. used_check returns
    True if we hit a marked_as_used node on the way down to our
    lookup (in other words, a covering subnet has been registered.)"""
    ip = IPy.IP(route)
    binary = ip.strBin()
    netlen = ip.prefixlen()
    level = 0
    current = self.root
    for x in binary[:netlen]:
      if current.used == True and used_check == True:
        return current
      if x == '0':
        current = current.GetLeft()
      elif x == '1':
        current = current.GetRight()
      if current == None:
        return None
    return current

  def Remove(self, route):
    if self.Lookup(route) != None:
      """Mark current node un-used. TODO(niallm): Is this sufficient?"""
      current.used = False
    else:
      raise ValueException


  def IterateNodes(self, return_data = False):
    """Generator for nodes marked used in the current tree."""
    current = self.root
    next_node = self.root
    previous = self.root
    while (current != None):
      if current.used:
        binstr = current.GetPath()
        prefix = self.PathToDotQuad(binstr, current.GetLevel())
        if return_data:
          yield (prefix, current.GetData())
        else:
          yield prefix
      if previous == current.GetParent() or (previous == self.root and current == self.root):
        # Came from parent, therefore try to go left.
        if current.GetLeft() == None:
          if current.GetRight() == None:
            next_node = current.GetParent()
          else:
            next_node = current.GetRight()
        else:
          next_node = current.GetLeft()
      elif previous == current.GetLeft():
        # Came from my left child, therefore try to go right.
        if current.GetRight() == None:
          next_node = current.GetParent()
        else:
          next_node = current.GetRight()
      elif previous == current.GetRight():
        # Came from my right child, therefore try to go up.
        next_node = current.GetParent()
      previous = current
      current = next_node

  def IterateNodesUnder(self, prefix, return_data = False):
    """Generator for nodes marked used in the current tree,
    rooted at the supplied prefix."""
    node = self.Lookup(prefix)
    if node == None:
      raise "Node Not Present"
    else:
      original = node
      current = node
      next_node = node
      previous = node
    while (current != None):
      if self.debug > 2:
        print "Previous path: ", (previous.GetPath(), 
                                  self.PathToDotQuad(previous.GetPath(), 
                                                        previous.GetLevel()))
        print "Current path: ", (current.GetPath(), 
                                 self.PathToDotQuad(current.GetPath(), 
                                                       current.GetLevel()))
        print "ITERATE", current.AboutMe()
      if current.used == True:
        if self.debug >= 2:
          print "*** GET USED OK FOR", current.GetPath()
        binstr = current.GetPath()
        prefix = self.PathToDotQuad(binstr, current.GetLevel())
        if return_data:
          yield (prefix, current.GetData())
        else:
          yield prefix
      if previous == current.GetParent() or (previous == original and current == original):
        if self.debug >= 2:
          print "Came from parent, therefore try to go left."
        if current.GetLeft() == None:
          if current.GetRight() == None:
            next_node = current.GetParent()
          else:
            next_node = current.GetRight()
        else:
          next_node = current.GetLeft()
      elif previous == current.GetLeft():
        if self.debug >= 2:
          print "Came from my left child, therefore try to go right."
        if current.GetRight() == None:
          next_node = current.GetParent()
        else:
          next_node = current.GetRight()
      elif previous == current.GetRight():
        if self.debug >= 2: 
          print "Came from my right child, therefore try to go up."
        next_node = current.GetParent()
      if next_node == original.GetParent():
        return
      previous = current
      current = next_node
    if self.debug >= 2:
      print "FALL OUT BOTTOM"

  def IterateNodesUnderOnlySupernets(self, prefix, return_data = False):
    """Generator for nodes marked used in the current tree,
    rooted at the supplied prefix. Catch only the supernets."""
    node = self.Lookup(prefix)
    if node == None:
      raise "Node Not Present"
    else:
      original = node
      current = node
      next_node = node
      previous = node
    while (current != None):
      if self.debug > 2:
        print "Previous path: ", (previous.GetPath(), 
                                  self.PathToDotQuad(previous.GetPath(), 
                                                        previous.GetLevel()))
        print "Current path: ", (current.GetPath(), 
                                 self.PathToDotQuad(current.GetPath(), 
                                                       current.GetLevel()))
        print "ITERATE", current.AboutMe()
      if current.used:
        if self.debug >= 2:
          print "*** GET USED OK FOR", current.GetPath()
        binstr = current.GetPath()
        prefix = self.PathToDotQuad(binstr, current.GetLevel())
        if return_data:
          yield (prefix, current.GetData())
        else:
          yield prefix
      if current.used:
        next_node = current.GetParent()
      elif previous == current.GetParent() or (previous == original and current == original):
        if self.debug >= 2:
          print "Came from parent, therefore try to go left."
        if current.GetLeft() == None:
          if current.GetRight() == None:
            next_node = current.GetParent()
          else:
            next_node = current.GetRight()
        else:
          next_node = current.GetLeft()
      elif previous == current.GetLeft():
        if self.debug >= 2:
          print "Came from my left child, therefore try to go right."
        if current.GetRight() == None:
          next_node = current.GetParent()
        else:
          next_node = current.GetRight()
      elif previous == current.GetRight():
        if self.debug >= 2: 
          print "Came from my right child, therefore try to go up."
        next_node = current.GetParent()
      if next_node == original.GetParent():
        return
      previous = current
      current = next_node
    if self.debug >= 2:
      print "FALL OUT BOTTOM"


  def PrintIterableNodes(self):
    if self.debug >= 2:
      print "tree PrintIterableNodes has:"
    for prefix_data in self.IterateNodes(True):
      print prefix_data

  def CountUsedNodes(self):
    """Count the inserted nodes in the tree; i.e., the ones marked as
    used."""
    count = 0
    for node in self.IterateNodes():
      count += 1
    return count

  def FindGap(self, size, strict = True, start_from = None,
               test_blank = False):
    """Find a gap of prefixlen size, by following algorithm above. FIXME - move
    that down. strict = True implies we will return a string of exactly the size
    you are looking for - e.g. if 128.0.0.0/1 is free and you ask for first /8,
    you will get 128.0.0.0/8. With strict off you get 128.0.0.0/1. 
    start_from is the node we'll start from.
    test_blank = True implies we will bomb out if at any stage
    we find ourselves heading onto a node which is neither marked used
    or indeed present."""
    if start_from == None:
      current = self.root
      next_node = self.root
      previous = self.root
    else:
      current = start_from
      next_node = None
      previous = current.GetParent()
    if self.debug >= 1:
      print "Called Tree.FindGap(%s)" % size
    while (current != None and current.GetLevel() <= size):
      if self.debug >= 2:
        print "Tree.FindGap examines node (%s)." % \
          (self.PathToDotQuad(current.GetPath(), current.GetLevel()))
      if previous == current.GetParent() or (previous == self.root 
                                              and current == self.root):
        if current.used:
          if self.debug >= 3:
            print "Tree.FindGap finds current node used; ergo go to previous."
          next_node = previous
        elif current.GetLevel() == size and start_from == None:
          if self.debug >= 3:
            print "Tree.FindGap finds current level at size limit; ergo go up."
          next_node = current.GetParent()
        else:
          if self.debug >= 3:
            print "Tree.FindGap goes left from parent..."
          if current.GetLeft() == None and test_blank == False:
            binstr = current.GetPath() + "0"
            if self.debug >= 3:
              print "...and finds a blank."
            if strict:
              return self.PathToDotQuad(binstr, size)
            else:
              return self.PathToDotQuad(binstr, depth)
          elif current.GetLevel() == size and start_from != self.root:
            next_node = current.GetParent()
          elif current.GetLeft() == None and test_blank == True:
            if self.debug >= 3:
              print "Tree.FindGap has a left of None and test_blank of True."
            return None
          else:
            if self.debug >= 3:
              print "Tree.FindGap just goes left."
            next_node = current.GetLeft()
      elif previous == current.GetLeft():
        if self.debug >= 3:
          print "Tree.FindGap came from my left child; ergo go right."
        if current.used:
          if self.debug >= 3:
            print "Tree.FindGap finds current node used; ergo go to previous."
          next_node = previous
        elif current.GetLevel() == size:
          if self.debug >= 3:
            print "Tree.FindGap finds current level at size limit; ergo go up."
          next_node = previous
        else:
          if self.debug >= 3:
            print "Tree.FindGap goes right from left child..."
          if current.GetRight() == None and test_blank == False:
            binstr = current.GetPath() + "1"
            if self.debug >= 3:
              print "...and finds a blank."
            if strict:
              return self.PathToDotQuad(binstr, size)
            else:
              return self.PathToDotQuad(binstr, depth)
          elif current.GetRight() == None and test_blank == True:
            return None
          else:
            next_node = current.GetRight()
      elif previous == current.GetRight():
        if self.debug >= 3:
          print "Tree.FindGap came from my right child; ergo go to parent."
        # I can't go above where I started if I'm in FindGapFrom mode.
        if start_from == None:
          next_node = current.GetParent()
        elif start_from != None:
          if current.GetParent().GetLevel() < start_from.GetLevel():
            return None
          else:
            next_node = current.GetParent()
      previous = current
      current = next_node
      if current != None and previous != None:
        if current.used and previous.used:
          if self.debug >= 2:
            print "Tree.FindGap returns a None because of special used case."
          return None
    if self.debug >= 2:
      print "Tree.FindGap returns a None because of invariant violation."
    return None

  def FindGapGenerator(self, size):
    yield self.FindGap(size)

  def FindGapFrom(self, prefix, size, strict = True, do_test_none = False):
    """Find a gap underneath a particular prefix. 
    First we look up the path to the prefix. If it does not exist, we insert it,
    on the basis that we might be the IANA.
    If we assume we are starting with an empty tree, we can safely 
    build un-used nodes on the way to the prefix.
    TODO(niallm): Fix those docs."""
    result = self.Lookup(prefix)
    if result == False:
      if self.debug >= 2:
        print "Tree.FindGapFrom did not find [%s] via lookup; inserting" % prefix
      result = self.insert(prefix, 'FindGapFrom', mark_used = False, 
                           test_used = True, test_none = True)
      if result == False or result == None:
        return None
    else:
      pass # here for debugging
    if result == None:
      return None
    else:
      return self.FindGap(size, strict = True, start_from = result)

  def GetRoot(self):
    return self.root

  def SetRoot(self, new_root):
    self.root = new_root

  def PathToDotQuad(self, binstr, depth):
    """Given a binary string and a 'depth' (netmask), return the
    dotted quad for it."""
    q = len(binstr)
    for count in range(q, 32):
      binstr += "0"
    iphex = hex(int(binstr,2))
    complete_addr = iphex + "/" + str(depth)
    return IPy.IP(complete_addr).strNormal(1)

  def GenerateForPrefix(self, count, variance = 0):
    """Generate a list of all possible prefixes at depth 'count'.
    For example, 8 provides 0.0.0.0/8, 1.0.0.0/8, 2.0.0.0/8 ... and so on.
    If 'variance' is set to a number, then (randomly) some subset of
    the routes returned will be aggregated or deaggregated to 'variance'
    prefixlengths away. For example, a variance of 1 with a count of
    8 might provide 0.0.0.0/7, 2.0.0.0/9, 2.128.0.0/9, ... and so on."""
    total_span = 2 ** 32
    divisor = 2 ** count
    for x in range(0,total_span,total_span/divisor):
      if variance == 0:
        complete_addr = hex(x)  + "/" + str(count)
        yield IPy.IP(complete_addr).strNormal(1)
      else:
        # (De)aggregation should happen to roughly half the routes.
        if random.randint(0,1) == 0:
          # Should I aggregate or deaggregate?
          aggregation_condition == False
          if random.randint(0,1) == 0 and aggregation_condition:
            # If I aggregate, I produce a route which is the supernet
            # of this and the next, and advance the counter past the
            # space covered. Note - cannot do this safely on the right_half
            # of a route.
            complete_addr = hex(x) + "/" + str(count + 1)
            yield IPy.IP(complete_addr).strNormal(1)
            x += total_span/divisor
          else:
            # If I deaggregate, I produce the two relevant subroutes
            # and yield them twice.
            half_step = 0
            half_step = x + (total_span/divisor)/2
            complete_addr = hex(x) + "/" + str(count - 1)
            yield IPy.IP(complete_addr).strNormal(1)
            complete_addr = hex(x + half_step) + "/" + str(count - 1)
            yield IPy.IP(complete_addr).strNormal(1)
        else: # Route is untouched
          complete_addr = hex(x) + "/" + str(count)
          yield IPy.IP(complete_addr).strNormal(1)


  def SubtractCantUse(self, do_forbidden = True, do_reserved = True):
    """Subtract RFC 1918 spaces and other structurally unusable spaces from the
    current routing table. This means turning off the flag forbidden_allowed,
    and explicitly marking those spaces as used."""
    if do_forbidden:
      for space in _FORBIDDEN_SPACES:
        self.total_unusable_prefixes += 1
        self.insert(space, "IANA FORBIDDEN")
    if do_reserved:
      for space in _RESERVED_SPACES:
        self.total_unusable_prefixes += 1
        self.insert(space, "IANA RESERVED")

  def GetUnusablePrefixCount(self):
    """Return count of how many unusable prefixes we have (both
    reserved and impossible."""
    return self.total_unusable_prefixes
