import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_candidate_contexts import SpanIndex,wrapper_record,supplementary_spans
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
class WrapperRecordTests(unittest.TestCase):
 def record(self,name='A.ini',size=7):return name.encode()+bytes(128-len(name))+struct.pack('<I',size)
 def test_exact(self):self.assertEqual(wrapper_record(self.record(),0,'A.ini',7)['end'],132)
 def test_truncation(self):
  with self.assertRaises(ValueError):wrapper_record(self.record()[:-1],0,'A.ini',7)
 def test_name(self):
  with self.assertRaises(ValueError):wrapper_record(self.record(),0,'B.ini',7)
 def test_size(self):
  with self.assertRaises(ValueError):wrapper_record(self.record(),0,'A.ini',8)
 def test_nonzero_padding(self):
  raw=bytearray(self.record());raw[120]=1
  with self.assertRaises(ValueError):wrapper_record(bytes(raw),0,'A.ini',7)
 def test_negative_start(self):
  with self.assertRaises(ValueError):wrapper_record(self.record(),-1,'A.ini',7)
 def test_size_overflow(self):
  with self.assertRaises(ValueError):wrapper_record(self.record(),0,'A.ini',2**32)
 def test_name_too_long(self):
  with self.assertRaises(ValueError):wrapper_record(self.record(),0,'X'*128,7)
 def test_empty_config(self):
  with self.assertRaises(ValueError):supplementary_spans(b'',[],{'A.ini':b''})
 def test_missing_initial_source(self):
  with self.assertRaises(ValueError):supplementary_spans(b'',[],{})

if __name__=='__main__':unittest.main()
