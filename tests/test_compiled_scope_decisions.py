from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from validate_compiled_scope import validate
class CompiledScopeTests(unittest.TestCase):
 def fixture(self):
  source=[dict(id='A',sha256='a'*64,semantic_classification='visible'),dict(id='B',sha256='b'*64,semantic_classification='unresolved')];batch=dict(entries=[dict(id='A',source_sha256='a'*64,status='reviewed')]);profile=dict(schema=1,runtime_visibility_verified=False,decisions=[dict(id=q['id'],source_sha256=q['sha256'],source_classification=q['semantic_classification'],decision='translate' if q['id']=='A' else 'retain-original',retention_kind='support',reason='explicit project decision',runtime_visibility_verified=False) for q in source]);return source,batch,profile
 def test_all_decided_without_visibility_claim(self):self.assertEqual(validate(*self.fixture())['retained_fields'],1)
 def test_missing_decision_rejected(self):
  s,b,p=self.fixture();p['decisions'].pop()
  with self.assertRaises(ValueError):validate(s,b,p)
 def test_source_classification_rewrite_rejected(self):
  s,b,p=self.fixture();p['decisions'][1]['source_classification']='internal'
  with self.assertRaises(ValueError):validate(s,b,p)
 def test_runtime_claim_rejected(self):
  s,b,p=self.fixture();p['decisions'][1]['runtime_visibility_verified']=True
  with self.assertRaises(ValueError):validate(s,b,p)
if __name__=='__main__':unittest.main()
