import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_name_records import records,classify_candidate

def fixture(ext):
 stride,kind=(299,11) if ext=='.cha' else (526,5)
 b=bytearray(struct.pack('<II',1,kind)+bytes(stride))
 if ext=='.cha':b[12:14]='한'.encode('cp949')
 else:b[16:18]='한'.encode('cp949');b[279:281]='글'.encode('cp949')
 return b

class NameRecordTests(unittest.TestCase):
 def test_cha_layout(self):
  r=records(fixture('.cha'),'.cha')[0];self.assertEqual(len(r['metadata']),11);self.assertEqual(r['text_fields'][0]['offset'],12)
 def test_mdg_two_fields(self):self.assertEqual([f['offset'] for f in records(fixture('.mdg'),'.mdg')[0]['text_fields']],[16,279])
 def test_wrong_kind(self):
  b=fixture('.cha');struct.pack_into('<I',b,4,12)
  with self.assertRaisesRegex(ValueError,'geometry'):records(b,'.cha')
 def test_short_record(self):
  with self.assertRaisesRegex(ValueError,'geometry'):records(fixture('.cha')[:-1],'.cha')
 def test_dirty_text_padding(self):
  b=fixture('.cha');b[20]=1
  with self.assertRaisesRegex(ValueError,'padding'):records(b,'.cha')
 def test_unterminated(self):
  b=fixture('.cha');b[12:267]=b'A'*255
  with self.assertRaisesRegex(ValueError,'terminator'):records(b,'.cha')
 def test_metadata_not_text(self):
  b=fixture('.cha');struct.pack_into('<I',b,283,16816)
  result=classify_candidate(dict(offset=283,source_bytes=2),records(b,'.cha'))
  self.assertEqual(result['classification'],'inside-u32-metadata');self.assertEqual(result['metadata_value'],16816)
 def test_partial_overlap_stays_unresolved(self):self.assertEqual(classify_candidate(dict(offset=266,source_bytes=2),records(fixture('.cha'),'.cha'))['classification'],'unresolved')
if __name__=='__main__':unittest.main()
