import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_dialogue_blocks import parse_block,OFFSETS

def fixture():
 b=bytearray(12328);struct.pack_into('<III',b,0,31,1,0);return b
class DialogueBlockTests(unittest.TestCase):
 def test_all_slots_and_opaque_exhaust_file(self):
  r=parse_block(fixture());self.assertEqual(len(r['text_fields']),24);self.assertEqual(sum(f['slot_bytes'] for f in r['text_fields'])+sum(m['bytes'] for m in r['opaque']),12328)
 def test_prefix_mismatch(self):
  b=fixture();b[0]=32
  with self.assertRaisesRegex(ValueError,'prefix'):parse_block(b)
 def test_size_mismatch(self):
  with self.assertRaisesRegex(ValueError,'size'):parse_block(fixture()[:-1])
 def test_dirty_padding(self):
  b=fixture();b[22]=1
  with self.assertRaisesRegex(ValueError,'padding'):parse_block(b)
 def test_slot_after_nonzero_u32(self):
  b=fixture();b[7704:7708]=b'\xff'*4;b[7708:7710]='한'.encode('cp949');self.assertEqual(parse_block(b)['text_fields'][15]['raw'],'한'.encode('cp949'))
 def test_empty_and_full_capacity(self):
  b=fixture();b[20:531]=b'A'*511;self.assertEqual(len(parse_block(b)['text_fields'][0]['raw']),511)
if __name__=='__main__':unittest.main()
