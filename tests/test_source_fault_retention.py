import copy,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import digest
from prepare_source_fault_retention import check_decision,derive,verified_retention
from prepare_translation_scope import disposition,freeze
class SourceFaultTests(unittest.TestCase):
 def fixture(self):
  pool='가'.encode('cp949');raw=struct.pack('<5I',1,0,0,1,len(pool))+pool;e=dict(id='SHIP/sample.fpb/seq/0',offset=0,source_bytes=1,source_sha256=digest(pool[:1]),decode='failed',editable=False,backend_eligible=False,seq=0);res=dict(resource='SHIP/sample.fpb',sha256=digest(raw),entries=[e]);d=dict(id=e['id'],resource=res['resource'],resource_sha256=res['sha256'],offset=0,source_bytes=1,source_sha256=e['source_sha256'],status='reviewed',import_approved=False,runtime_visibility_verified=False,disposition='retain-source-fault',reason='Original native byte window splits a character.',raw_hex=pool[:1].hex(),physical_index=0,native_record_key=0,classification='split-multibyte-native-window');return res,e,d,raw
 def test_native_split_byte_window_verified(self):
  r,e,d,raw=self.fixture();proof=check_decision(r,e,d,raw);self.assertTrue(proof['native_source_span_verified']);self.assertEqual(proof['original_decode'],'failed')
 def test_wrong_raw_hash_rejected(self):
  r,e,d,raw=self.fixture();d['source_sha256']='0'*64
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_changed_original_resource_rejected(self):
  r,e,d,raw=self.fixture()
  with self.assertRaises(ValueError):check_decision(r,e,d,raw+b'x')
 def test_wrong_numeric_key_rejected(self):
  r,e,d,raw=self.fixture();d['native_record_key']=1
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_wrong_physical_record_rejected(self):
  r,e,d,raw=self.fixture();d['physical_index']=1
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_raw_hex_mismatch_rejected(self):
  r,e,d,raw=self.fixture();d['raw_hex']='00'
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_runtime_claim_rejected(self):
  r,e,d,raw=self.fixture();d['runtime_visibility_verified']=True
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_import_claim_rejected(self):
  r,e,d,raw=self.fixture();d['import_approved']=True
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_false_empty_classification_rejected(self):
  r,e,d,raw=self.fixture();d['classification']='all-zero-native-window'
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_opaque_fragment_missing_reading_rejected(self):
  r,e,d,raw=self.fixture();d['classification']='opaque-script-fragment'
  with self.assertRaises(ValueError):check_decision(r,e,d,raw)
 def test_derive_keeps_original_decode_and_source(self):
  r,e,d,raw=self.fixture();c={'resources':[r]};new,proof=derive(c,dict(schema=1,entries=[d]),{'sample.fpb':raw});after=new['resources'][0]['entries'][0];self.assertEqual({k:v for k,v in after.items() if k!='source_fault_retention'},e);self.assertNotIn('source_fault_retention',e);self.assertTrue(verified_retention(after))
 def test_duplicate_decision_rejected(self):
  r,e,d,raw=self.fixture()
  with self.assertRaises(ValueError):derive({'resources':[r]},dict(schema=1,entries=[d,d]),{'sample.fpb':raw})
 def test_modified_backend_eligibility_rejected(self):
  r,e,d,raw=self.fixture();e['source_fault_retention']=check_decision(r,e,d,raw);e['editable']=True
  with self.assertRaises(ValueError):verified_retention(e)
 def test_forged_proof_rejected(self):
  r,e,d,raw=self.fixture();e['source_fault_retention']={'schema':1}
  with self.assertRaises(ValueError):disposition(r,e)
 def test_scope_retention_never_counts_as_translation(self):
  r,e,d,raw=self.fixture();e['source_fault_retention']=check_decision(r,e,d,raw);rows,summary=freeze({'resources':[r]},[]);self.assertEqual(rows[0]['disposition'],'retain-source-fault');self.assertTrue(rows[0]['source_retention_required']);self.assertEqual(summary['existing_translations'],0);self.assertFalse(summary['translation_complete'])
 def test_source_fault_cannot_be_translated(self):
  r,e,d,raw=self.fixture();e['source_fault_retention']=check_decision(r,e,d,raw)
  with self.assertRaises(ValueError):freeze({'resources':[r]},[dict(locale='zh-CN',entries=[dict(id=e['id'],source_sha256=e['source_sha256'],target='x',status='reviewed')])])
