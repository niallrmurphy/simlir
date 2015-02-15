#!/usr/bin/env python
# encoding: utf-8
# Niall Richard Murphy <niallm@gmail.com>

"""These are the unit tests for the timeline module, part of the SimLIR
framework.
"""

import sys
sys.path.append(".")
import timeline
import unittest


class ListNodeTest(unittest.TestCase):
  def setUp(self):
    self.ln = timeline.ListNode()

  def testListNodeNew(self):
    self.assert_(self.ln, "List node could not be created")

  def testListNodeAccessors(self):
    date = self.ln.date
    self.assertEqual(date, None)
    data = self.ln.data
    self.assertEqual(data, [])
    next = self.ln.next
    self.assertEqual(next, None)

  def testListNodeAccessorsMutators(self):
    self.ln.date = "19930101"
    self.assertEqual(self.ln.date, "19930101")
    self.ln.data = ["hiya"]
    self.assertEqual(self.ln.data, ["hiya"])
    self.ln.next = self.ln
    self.assertEqual(self.ln.next, self.ln)

  def testListNodeAddEvent(self):
    self.ln.AddData([{"name": "wibbly"}])
    self.assertEqual(self.ln.data, [{"name": "wibbly"}])
    self.ln.AddData([{"name": "wobbly"}])
    self.assertEqual(self.ln.data, [{"name": "wibbly"},
                                    {"name": "wobbly"}])


class LinkedListTest(unittest.TestCase):
  def setUp(self):
    self.ll = timeline.LinkedList()

  def testLinkedListNew(self):
    self.assert_(self.ll, "Linked list could not be created")

  def testLinkedListHeads(self):
    self.assertEqual(self.ll.head, None)
    ln = timeline.ListNode()
    self.ll.head = ln
    self.assertEqual(self.ll.head, ln)

  def testLinkedConstructList(self):
    ln1 = timeline.ListNode()
    ln2 = timeline.ListNode()
    ln3 = timeline.ListNode()
    self.ll.head = ln1
    self.ll.head.next = ln2
    self.ll.head.next.next = ln3
    self.assertEqual(self.ll.ConstructList(self.ll.head),
                     [ln1, ln2, ln3])

class TimeLineTest(unittest.TestCase):
  def setUp(self):
    self.tl = timeline.Timeline()

  def testTimeLineNew(self):
    self.assert_(self.tl, "Timeline could not be created")

  def testTimeLineHeads(self):
    self.assertEqual(self.tl.head, None)
    ln = timeline.ListNode()
    self.tl.head = ln
    self.assertEqual(self.tl.head, ln)

  def testTimeLineCurrent(self):
    ln = timeline.ListNode()
    self.tl.head = ln
    self.assertEqual(self.tl.pointer, None)
    self.tl.SetPointerToHead()
    self.assertEqual(self.tl.pointer, ln)

  def testTimeLineNextPointer(self):
    ln1 = timeline.ListNode()
    ln2 = timeline.ListNode()
    self.tl.head = ln1
    self.assertEqual(self.tl.head, ln1)
    self.assertEqual(self.tl.head.next, None)
    self.tl.head.next = ln2
    self.assertEqual(self.tl.head.next, ln2)
    self.assertEqual(self.tl.head, ln1)
    self.tl.SetPointerToHead()
    self.assertEqual(self.tl.pointer.next, ln2)

  def testTimeLineAddNode(self):
    ln1 = timeline.ListNode(date="19950101")
    ln2 = timeline.ListNode(date="19950303")
    ln3 = timeline.ListNode(date="19950606")
    ln4 = timeline.ListNode(date="19910404")
    self.tl.AddNode(ln1)
    self.assertEqual(self.tl.head, ln1)
    self.tl.AddNode(ln3)
    self.assertEqual(self.tl.head.next, ln3)
    self.tl.AddNode(ln2)
    self.assertEqual(self.tl.head.next, ln2)
    self.tl.AddNode(ln4)
    self.assertEqual(self.tl.head, ln4)
    self.assertEqual(self.tl.head.next, ln1)

  def testtimeLineAddData(self):
    self.tl.Add("19950101", ["1st data"])
    self.assertEqual(self.tl.head.date, "19950101")
    self.assertEqual(self.tl.head.data, ["1st data"])
    self.tl.Add("19950606", ["2nd data"])
    self.assertEqual(self.tl.head.next.data, ["2nd data"])
    self.tl.Add("19950303", ["3rd data"])
    self.assertEqual(self.tl.head.next.data, ["3rd data"])
    self.tl.Add("19950303", ["4th data"])
    self.assertEqual(self.tl.head.next.data,
                     ["3rd data", "4th data"])
    self.tl.Add("19930101", ["5th data"])
    self.assertEqual(self.tl.head.data, ["5th data"])
    self.assertEqual(self.tl.head.next.data, ["1st data"])

  def testTimeLineGenerator(self):
    self.tl.Add("19950101", ["wibb"])
    self.tl.Add("19950606", ["wubb"])
    self.tl.Add("19950303", ["wobb1"])
    self.tl.Add("19950303", ["wobb2"])
    self.tl.Add("19930101", ["wargl"])
    count = 0
    result = [1, 2, 3, 4, 5]
    result[1] = "23"
    self.tl.SetPointerToHead()
    for y in self.tl.WalkAlong():
      result[count] = y
      count += 1
    self.assertEqual(result[0], "wargl")
    self.assertEqual(result[1], "wibb")
    self.assertEqual(result[2], "wobb1")
    self.assertEqual(result[3], "wobb2")
    self.assertEqual(result[4], "wubb")

  def testTimeLineGetAtDate(self):
    self.tl.Add("19950101", ["wabb"])
    result = self.tl.GetAtDate("19950101")
    self.assertEqual(result.data, ["wabb"])
    result = self.tl.GetAtDate("19930101")
    self.assertEqual(result, None)

  def testTimeLineRemove(self):
    self.tl.Add("19950101", ["wibb"])
    self.tl.Add("19950606", ["wubb"])
    self.tl.Add("19950303", ["wobb1"])
    result = self.tl.Remove("19950303")
    self.assertEqual(result, True)
    n = self.tl.GetAtDate("19950101")
    n2 = self.tl.GetAtDate("19950606")
    self.assertEqual(n.next, n2)

  def testTimeLinePrune(self):
    self.tl.Add("19950101", ["wibb"])
    self.tl.Add("19950606", ["wubb", "glimmer"])
    self.tl.Add("19950303", ["wobb1"])
    result = self.tl.Prune("19950606", "glimmer")
    self.assertEqual(result, True)
    result = self.tl.GetAtDate("19950606")
    self.assertEqual(result.data, ["wubb"])

  def testTimeLineGetFirstBefore(self):
    self.tl.Add("19950101", ["wibb"])
    self.tl.Add("19950606", ["wubb", "glimmer"])
    self.tl.Add("19950303", ["wobb1"])
    result = self.tl.GetFirstBefore("19950606")
    self.assertEqual(result, self.tl.GetAtDate("19950303"))

  def testTimeLineGetFirstAfter(self):
    self.tl.Add("19950101", ["wibb"])
    self.tl.Add("19950606", ["wubb", "glimmer"])
    self.tl.Add("19950303", ["wobb1"])
    result = self.tl.GetFirstAfter("19950101")
    self.assertEqual(result, self.tl.GetAtDate("19950303"))

  def testDayDelta(self):
    result = timeline.DayDelta("19950203", "19950201")
    self.assertEqual(result, 2)
    result = timeline.DayDelta("19950201", "19950203")
    self.assertEqual(result, -2)
    self.failUnlessRaises(ValueError,
                          timeline.DayDelta,
                          "00000000", "-1-1-1-1")

  def testCalculatePeriodLater(self):
    result = timeline.CalculatePeriodLater("19950101", delta=20, upperbound=1)
    self.assert_(result == "19950120" or result == "19950121" or
                 result == "19950122")

  def testFilterWithinDate(self):
    result = timeline.FilterWithinDate("20071010", 10, "20071012")
    self.assertEqual(result, True)
    result = timeline.FilterWithinDate("20071212", 2, "20071219")
    self.assertEqual(result, False)
    result = timeline.FilterWithinDate("20071212", 2, "20071214")
    self.assertEqual(result, True)

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(ListNodeTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(LinkedListTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
  suite = unittest.TestLoader().loadTestsFromTestCase(TimeLineTest)
  unittest.TextTestRunner(verbosity=2).run(suite)
