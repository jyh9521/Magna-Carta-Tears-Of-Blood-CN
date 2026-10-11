import unittest,struct,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools')]
from audit_native_text_index import expected_words,validate_lookup,run_lookup,characterize
class FakeImage:
 def __init__(self,offset):self.blob=b''.join(struct.pack('<I',w) for w in expected_words(offset))
 def to_offset(self,va):return va
class NativeTextIndexTests(unittest.TestCase):
 def test_five_offset_profiles(self):
  for offset in (0x148,0x160,0x16c,0x190,0x19c):self.assertEqual(validate_lookup(FakeImage(offset),0,offset),expected_words(offset))
 def test_real_instruction_fixtures(self):
  for offset in (0x148,0x160,0x16c,0x190,0x19c):self.assertEqual(characterize(FakeImage(offset),0,offset),120)
 def test_sparse_key_is_not_index(self):self.assertEqual(run_lookup(FakeImage(0x148),0,0x148,[300,7,14],7)['index'],1)
 def test_duplicate_first_match(self):self.assertEqual(run_lookup(FakeImage(0x160),0,0x160,[9,9],9)['index'],0)
 def test_missing_preserves_sentinel(self):self.assertEqual(run_lookup(FakeImage(0x16c),0,0x16c,[17],8)['index'],0xffffffff)
 def test_instruction_mutation_rejected(self):
  image=FakeImage(0x148);image.blob=image.blob[:32]+struct.pack('<I',0x8c420004)+image.blob[36:]
  with self.assertRaisesRegex(ValueError,'instruction mismatch'):validate_lookup(image,0,0x148)
 def test_wrong_array_profile_rejected(self):
  with self.assertRaises(ValueError):validate_lookup(FakeImage(0x148),0,0x160)
 def test_offset_range_rejected(self):
  for offset in (-1,0x7ffc):
   with self.assertRaises(ValueError):expected_words(offset)
if __name__=='__main__':unittest.main()
