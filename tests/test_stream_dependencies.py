import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_field_prefix import property_target,RAND_RANGE_SOURCE,RAND_RANGE_STREAM
class StreamDependencyTests(unittest.TestCase):
 def test_target(self):self.assertEqual(property_target(b'\0\0\0'+struct.pack('<II',1,0)+b'\0\3',['None']),3)
 def test_two_byte_target(self):self.assertEqual(property_target(b'\0\0\0'+struct.pack('<II',1,0)+b'\0\x7a\x15',['None']),1402)
 def test_tail_rejected(self):
  with self.assertRaises(ValueError):property_target(b'\0\0\0'+struct.pack('<II',1,0)+b'\0\3\0',['None'])
 def test_zero_target(self):
  with self.assertRaises(ValueError):property_target(b'\0\0\0'+struct.pack('<II',1,0)+b'\0\0',['None'])
 def test_truncated_target(self):
  with self.assertRaises(ValueError):property_target(b'\0\0\0'+struct.pack('<II',1,0)+b'\0',['None'])
 def test_variant_size(self):self.assertEqual(len(RAND_RANGE_STREAM),24)
 def test_variant_not_source(self):self.assertEqual(len(RAND_RANGE_SOURCE),64);self.assertNotEqual(RAND_RANGE_STREAM.hex(),'04ae474b07abaf476b0b474b0716c3161616040b')
if __name__=='__main__':unittest.main()

