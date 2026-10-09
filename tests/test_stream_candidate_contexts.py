import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_candidate_contexts import SpanIndex
class StreamContainmentTests(unittest.TestCase):
 def row(self,a,b):return dict(start=a,end=b,kind='test')
 def test_empty(self):self.assertIsNone(SpanIndex([]).containing(0,1))
 def test_inside(self):self.assertEqual(SpanIndex([self.row(10,20)]).containing(12,3)['start'],10)
 def test_exact(self):self.assertEqual(SpanIndex([self.row(10,20)]).containing(10,10)['end'],20)
 def test_end_exclusive(self):self.assertIsNone(SpanIndex([self.row(10,20)]).containing(20,1))
 def test_cross_boundary(self):self.assertIsNone(SpanIndex([self.row(0,10),self.row(10,20)]).containing(9,2))
 def test_gap(self):self.assertIsNone(SpanIndex([self.row(0,5),self.row(10,20)]).containing(7,1))
 def test_before(self):self.assertIsNone(SpanIndex([self.row(10,20)]).containing(0,1))
 def test_overlap_rejected(self):
  with self.assertRaises(ValueError):SpanIndex([self.row(0,10),self.row(9,20)])
 def test_zero_span_rejected(self):
  with self.assertRaises(ValueError):SpanIndex([self.row(1,1)])
 def test_bad_candidate(self):
  with self.assertRaises(ValueError):SpanIndex([]).containing(0,0)
 def test_negative(self):
  with self.assertRaises(ValueError):SpanIndex([self.row(-1,10)])
 def test_sorted(self):self.assertEqual(SpanIndex([self.row(10,20),self.row(0,10)]).containing(0,1)['start'],0)
if __name__=='__main__':unittest.main()
