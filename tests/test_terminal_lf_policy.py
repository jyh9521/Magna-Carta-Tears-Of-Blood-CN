import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from localization.text import TERMINAL_LF_POLICY,terminal_lf_body,protected_tokens,validate_target,MappedEncoder
from source_interpretation import control_policy
from font_poc import digest
from prepare_terminal_lf_interpretations import derive

class TerminalLFTests(unittest.TestCase):
 def test_terminal_body(self):self.assertEqual(terminal_lf_body('Body\n'),'Body')
 def test_default_target_still_rejects_lf(self):
  with self.assertRaises(ValueError):validate_target('Body\n','Body\n')
 def test_explicit_target_accepts_exact_lf(self):validate_target('Body$n2\n','Text$n2\n',control_policy=TERMINAL_LF_POLICY)
 def test_bad_controls_rejected(self):
  for s in ('','\n','Body','Body\n\n','Bo\ndy\n','Body\t\n','Body\r\n','Body\0\n'):
   with self.subTest(s=repr(s)),self.assertRaises(ValueError):terminal_lf_body(s)
 def test_removed_lf_rejected(self):
  with self.assertRaises(ValueError):validate_target('Body\n','Text',control_policy=TERMINAL_LF_POLICY)
 def test_missing_source_lf_rejected(self):
  with self.assertRaises(ValueError):validate_target('Body','Text\n',control_policy=TERMINAL_LF_POLICY)
 def test_known_tokens_retained(self):self.assertEqual(protected_tokens('Body$n%D\n'.replace('%D','%d'),control_policy=TERMINAL_LF_POLICY),['$n','%d','\n'])
 def test_unknown_markup_still_rejected(self):
  with self.assertRaises(ValueError):protected_tokens('Body%\n',control_policy=TERMINAL_LF_POLICY)
 def test_numeric_changes_rejected(self):
  with self.assertRaises(ValueError):validate_target('Body2\n','Text3\n',control_policy=TERMINAL_LF_POLICY)
 def test_encoder_exact_terminal_byte(self):self.assertEqual(MappedEncoder([]).encode('Body\n',control_policy=TERMINAL_LF_POLICY),b'Body\x0a')
 def test_default_encoder_rejects_control(self):
  with self.assertRaises(ValueError):MappedEncoder([]).encode('Body\n')
 def fixture(self):
  s='Hello\n';raw=b'H'*28+s.encode()+bytes(512-len(s))+b'TAIL';identity='SHIP/sample.cht/slot/0';entry=dict(id=identity,slot=0,offset=28,source_bytes=len(s),source_sha256=digest(s.encode()),slot_sha256=digest(raw[28:]),observed_byte_capacity=515,decode='strict',controls='quarantined',references={'ko-KR':s});res=dict(resource='SHIP/sample.cht',sha256=digest(raw),entries=[entry]);binding=dict(id=identity,resource=res['resource'],resource_sha256=res['sha256'],offset=28,source_bytes=len(s),source_sha256=entry['source_sha256'],native_read_bytes=512,runtime_verified=False,record_index=0,numeric_metadata_hex=raw[12:28].hex());import struct;raw=bytearray(raw);struct.pack_into('<I',raw,4,1);raw=bytes(raw);res['sha256']=binding['resource_sha256']=digest(raw);d=dict(id=identity,resource=res['resource'],resource_sha256=res['sha256'],offset=28,source_bytes=len(s),source_sha256=entry['source_sha256'],source=s,reading_sha256=digest(s.encode()),target='Target\n',status='reviewed',binding=binding);return dict(resources=[res]),dict(schema=1,locale='zh-CN',entries=[d]),{'sample.cht':raw}
 def test_native512_derivation_keeps_tail(self):
  c,p,m=self.fixture();new,b,proof=derive(c,p,m,None);e=new['resources'][0]['entries'][0];self.assertEqual(e['observed_byte_capacity'],511);self.assertEqual(proof[0]['geometry']['preserved_tail_bytes'],4);self.assertEqual(c['resources'][0]['entries'][0]['controls'],'quarantined');self.assertEqual(control_policy(e,'Target\n'),TERMINAL_LF_POLICY)
 def test_target_hash_mismatch_rejected(self):
  c,p,m=self.fixture();new,b,proof=derive(c,p,m,None)
  with self.assertRaises(ValueError):control_policy(new['resources'][0]['entries'][0],'Other\n')
 def test_source_binding_mismatch_rejected(self):
  c,p,m=self.fixture();p['entries'][0]['offset']=29
  with self.assertRaises(ValueError):derive(c,p,m,None)
 def test_source_reading_mismatch_rejected(self):
  c,p,m=self.fixture();p['entries'][0]['source']='Other\n'
  with self.assertRaises(ValueError):derive(c,p,m,None)
 def test_native_metadata_mismatch_rejected(self):
  c,p,m=self.fixture();p['entries'][0]['binding']['numeric_metadata_hex']='00'
  with self.assertRaises(ValueError):derive(c,p,m,None)
