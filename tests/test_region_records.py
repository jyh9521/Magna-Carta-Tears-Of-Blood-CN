import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_region_records import parse_records,context,PROFILES

def fixture(ext):
 p=PROFILES[ext];b=bytearray(struct.pack('<II',1,p['kind'])+bytes(p['stride']))
 for off,size in p['text']:b[8+off:10+off]='한'.encode('cp949')
 return b

class RegionRecordTests(unittest.TestCase):
 def test_all_geometries(self):
  for ext in PROFILES:
   r=parse_records(fixture(ext),ext);self.assertEqual(len(r[0]['text_fields']),2)
 def test_text_after_nonzero_metadata(self):
  b=fixture('.itm');b[335:339]=b'\xff'*4;r=parse_records(b,'.itm');self.assertEqual(r[0]['text_fields'][1]['raw'],'한'.encode('cp949'))
 def test_wrong_kind(self):
  b=fixture('.abi');struct.pack_into('<I',b,4,8)
  with self.assertRaisesRegex(ValueError,'geometry'):parse_records(b,'.abi')
 def test_count_mismatch(self):
  with self.assertRaisesRegex(ValueError,'geometry'):parse_records(fixture('.nod')+b'\0','.nod')
 def test_padding_rejected(self):
  b=fixture('.sgi');b[20]=1
  with self.assertRaisesRegex(ValueError,'padding'):parse_records(b,'.sgi')
 def test_missing_nul(self):
  b=fixture('.dod');b[12:268]=b'A'*256
  with self.assertRaisesRegex(ValueError,'termination'):parse_records(b,'.dod')
 def test_exact_and_partial(self):
  p=parse_records(fixture('.itm'),'.itm');self.assertEqual(context(dict(offset=12,source_bytes=2),p)['classification'],'exact-text-field');self.assertEqual(context(dict(offset=13,source_bytes=1),p)['classification'],'text-subspan')
 def test_opaque_or_crossing(self):
  p=parse_records(fixture('.itm'),'.itm');self.assertEqual(context(dict(offset=335,source_bytes=4),p)['classification'],'opaque-metadata');self.assertEqual(context(dict(offset=337,source_bytes=4),p)['classification'],'boundary-crossing-or-unresolved')
if __name__=='__main__':unittest.main()
