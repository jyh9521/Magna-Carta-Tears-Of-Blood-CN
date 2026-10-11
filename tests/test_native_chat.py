import json,sys,struct,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','lib')]
from audit_native_chat import ANCHORS,validate_anchors,source_match
from font_poc import digest
class Image:
 def __init__(self):
  self.base=min(ANCHORS);self.blob=bytearray(max(ANCHORS)-self.base+4)
  for va,w in ANCHORS.items():struct.pack_into('<I',self.blob,va-self.base,w)
 def to_offset(self,va):return va-self.base
class ChatProtocolTests(unittest.TestCase):
 def fixture(self,key=13):
  raw=struct.pack('<7I',2,key,0,3,0,3,3)+struct.pack('<I',6)+b'abcdef';b=dict(id='fixture',source_resource_sha256=digest(raw),source_sha256=digest(b'abc'),source_offset=0,source_bytes=3,native_record_key=key,physical_index=0);return raw,b
 def test_actual_instruction_anchors(self):validate_anchors(Image())
 def test_changed_instruction_rejected(self):
  i=Image();struct.pack_into('<I',i.blob,i.to_offset(0x37cb30),0)
  with self.assertRaisesRegex(ValueError,'anchor'):validate_anchors(i)
 def test_numeric_source_span_unique(self):
  raw,b=self.fixture();self.assertEqual(source_match(raw,b)['native_record_key'],13)
 def test_unknown_original_resource_rejected(self):
  raw,b=self.fixture()
  with self.assertRaisesRegex(ValueError,'fingerprint'):source_match(raw+b'x',b)
 def test_wrong_key_index_or_source_hash_rejected(self):
  raw,b=self.fixture()
  for k,v in [('native_record_key',99),('physical_index',1),('source_sha256','0'*64)]:
   with self.subTest(field=k),self.assertRaises(ValueError):source_match(raw,{**b,k:v})
 def test_duplicate_key_cannot_bind_later_record(self):
  raw,b=self.fixture(0);b.update(source_offset=3,source_sha256=digest(b'def'),physical_index=1)
  with self.assertRaisesRegex(ValueError,'first-key'):source_match(raw,b)
if __name__=='__main__':unittest.main()
