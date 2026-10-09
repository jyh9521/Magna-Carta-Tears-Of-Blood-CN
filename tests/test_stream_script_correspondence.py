import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_script_correspondence import align_prefix,repetition_sites,header_positions

class ScriptCorrespondenceTests(unittest.TestCase):
 def fixture(self,code=b'\x04\x0b',tokens=None):
  raw=b'H'*21+code
  if tokens is None:tokens=[(21,4,0),(22,11,1)]
  script=dict(start=21,end=len(raw),tokens=[dict(offset=p,opcode=o,depth=d) for p,o,d in tokens])
  return raw,script
 def test_exact(self):
  raw,s=self.fixture();r=align_prefix(raw,0,raw,s);self.assertTrue(r['matched']);self.assertEqual(r['ends'][0]['extra_bytes'],0)
 def test_opcode_duplicate(self):
  raw,s=self.fixture();r=align_prefix(b'H'*21+b'\x04\x04\x0b',0,raw,s);self.assertTrue(r['matched']);self.assertEqual(r['ends'][0]['extra_bytes'],1)
 def test_operand_not_repeated(self):
  raw,s=self.fixture(b'\x47\x2d\x01',[(21,0x47,0)])
  self.assertFalse(align_prefix(b'H'*21+b'\x47\x2d\x2d\x01',0,raw,s)['matched'])
 def test_literal_not_repeated(self):
  raw,s=self.fixture(b'\x1fABC\0',[(21,0x1f,0)])
  self.assertFalse(align_prefix(b'H'*21+b'\x1fAABC\0',0,raw,s)['matched'])
 def test_iterator_word_site(self):
  raw,s=self.fixture(b'\x2f\x25\x03\0\x04\x0b',[(21,0x2f,0),(22,0x25,1),(25,4,0),(26,11,1)])
  self.assertEqual(repetition_sites(raw,s)[23],'iterator-word-low-byte')
  self.assertTrue(align_prefix(b'H'*21+b'\x2f\x25\x03\x03\0\x04\x0b',0,raw,s)['matched'])
 def test_context_word_site(self):
  raw,s=self.fixture(b'\x19\x25\x02\0\1\x25',[(21,0x19,0),(22,0x25,1),(26,0x25,1)])
  self.assertEqual(repetition_sites(raw,s)[23],'context-word-low-byte')
  self.assertTrue(align_prefix(b'H'*21+b'\x19\x25\x02\x02\0\1\x25',0,raw,s)['matched'])
 def test_ambiguous_paths_retained(self):
  raw,s=self.fixture(b'\x16\x16\x04\x0b',[(21,0x16,0),(22,0x16,0),(23,4,0),(24,11,1)])
  r=align_prefix(b'H'*21+b'\x16'*3+b'\x04\x0b',0,raw,s)
  self.assertTrue(r['unique_end']);self.assertEqual(r['ends'][0]['alignment_paths'],'at-least-two')
 def test_multiple_ends_retained(self):
  raw,s=self.fixture(b'\x16',[(21,0x16,0)]);r=align_prefix(b'H'*21+b'\x16\x16',0,raw,s)
  self.assertFalse(r['unique_end']);self.assertEqual(len(r['ends']),2)
 def test_truncation(self):
  raw,s=self.fixture();self.assertFalse(align_prefix(raw[:-1],0,raw,s)['matched'])
 def test_bad_header(self):
  raw,s=self.fixture()
  with self.assertRaises(ValueError):align_prefix(b'X'+raw[1:],0,raw,s)
 def test_bad_token(self):
  raw,s=self.fixture();s['tokens'][0]['opcode']=3
  with self.assertRaises(ValueError):repetition_sites(raw,s)
 def test_bad_depth(self):
  raw,s=self.fixture();s['tokens'][0]['depth']=1
  with self.assertRaises(ValueError):repetition_sites(raw,s)
 def test_header_ambiguity(self):self.assertEqual(header_positions(b'H'*22,b'H'*21),[0,1])
 def test_header_short(self):
  with self.assertRaises(ValueError):header_positions(b'H'*20,b'H'*20)

if __name__=='__main__':unittest.main()
