import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_field_prefix import compare_piece
class StreamFieldPrefixTests(unittest.TestCase):
 def test_match(self):self.assertTrue(compare_piece(b'abcdef',1,b'bcd')['matched'])
 def test_difference(self):self.assertEqual(compare_piece(b'abXdef',1,b'bcd')['first_difference'],1)
 def test_truncated(self):self.assertEqual(compare_piece(b'ab',1,b'bcd')['reason'],'stream truncated')
 def test_empty(self):self.assertTrue(compare_piece(b'ab',2,b'')['matched'])
 def test_negative(self):
  with self.assertRaises(ValueError):compare_piece(b'ab',-1,b'a')
 def test_start_bounds(self):
  with self.assertRaises(ValueError):compare_piece(b'ab',3,b'a')
 def test_identity(self):self.assertEqual(len(compare_piece(b'ab',0,b'ab')['sha256']),64)
 def test_mismatch_bytes(self):
  row=compare_piece(b'aa',0,b'ab');self.assertEqual((row['expected_byte'],row['observed_byte']),(98,97))
if __name__=='__main__':unittest.main()
