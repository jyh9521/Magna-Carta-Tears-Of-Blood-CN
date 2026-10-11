import struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from audit_native_stack_registration import bind,trace
class Image:
 def __init__(self):
  self.blob=bytearray(4096);self.name='intUFixtureexecJump';name=self.name.encode()+b'\0';self.blob[0x500:0x500+len(name)]=name
  struct.pack_into('<I',self.blob,0x600,0x1500);struct.pack_into('<3I',self.blob,0x700,0,0xffffffff,0x1800)
  self.words=[0x27bdffe0,0x24041700,0x7fa40000,0x24051604,0x7fa50010,0x24040000,0x7ba40000,0x7ba50010,0xc4820000,0xc4810004,0xc4800008,0xe4a20000,0xe4a10004,0xe4a00008]
  for i,w in enumerate(self.words):struct.pack_into('<I',self.blob,i*4,w)
  self.blob=bytes(self.blob)
 def to_offset(self,va):
  if not 0x1000<=va<0x1000+len(self.blob):raise ValueError('outside fixture')
  return va-0x1000
 def to_va(self,at):return at+0x1000
 def replace(self,at,word):b=bytearray(self.blob);struct.pack_into('<I',b,at,word);self.blob=bytes(b)
class StackRegistrationTests(unittest.TestCase):
 def setUp(self):self.i=Image();self.end=0x1000+4*len(self.i.words)
 def bind(self):return bind(self.i,[self.i.name],0x1000,self.end)
 def test_exact_spill_restore_descriptor(self):
  p=self.bind();m=p['methods'][0];self.assertEqual(m['callback'],'0x1800');self.assertEqual(m['source_descriptor'],'0x1700');self.assertEqual(m['descriptor_words'],['0x0','0xffffffff','0x1800']);self.assertEqual(len(m['word_copies']),3)
 def test_no_execution_claim(self):
  p=self.bind();self.assertFalse(p['runtime_verified']);self.assertFalse(p['methods'][0]['initializer_execution_verified']);self.assertFalse(p['methods'][0]['callback_execution_verified'])
 def test_unknown_instruction_rejected(self):
  self.i.replace(4,0xffffffff)
  with self.assertRaises(ValueError):self.bind()
 def test_call_barrier_rejected(self):
  self.i.replace(4,0x0c040000)
  with self.assertRaises(ValueError):self.bind()
 def test_branch_barrier_rejected(self):
  self.i.replace(4,0x10000000)
  with self.assertRaises(ValueError):self.bind()
 def test_short_range_rejected(self):
  with self.assertRaises(ValueError):bind(self.i,[self.i.name],0x1000,self.end-4)
 def test_unknown_stack_load_rejected(self):
  self.i.replace(6*4,0x7ba40020)
  with self.assertRaises(ValueError):self.bind()
 def test_duplicate_identifier_rejected(self):
  with self.assertRaises(ValueError):bind(self.i,[self.i.name,self.i.name],0x1000,self.end)
 def test_invalid_descriptor_rejected(self):
  self.i.replace(0x704,1)
  with self.assertRaises(ValueError):self.bind()
 def test_missing_identifier_rejected(self):
  with self.assertRaises(ValueError):bind(self.i,['intUFixtureexecMissing'],0x1000,self.end)
if __name__=='__main__':unittest.main()
