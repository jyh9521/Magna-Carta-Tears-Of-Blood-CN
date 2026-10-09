import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from consolidate_audited_fields import draft_links

def resource(identity='a',aliases=None):return [dict(resource='r',entries=[dict(id=identity,source_sha256='hash',source_aliases=aliases or [])])]
def draft(identity='a'):return [dict(id=identity,source_sha256='hash')]
class ConsolidateTests(unittest.TestCase):
 def test_direct_link(self):self.assertEqual(draft_links(resource(),resource(),[],draft())[0]['new_id'],'a')
 def test_old_alias_chain(self):self.assertEqual(draft_links(resource('a',['old']),resource('b'),[dict(old_id='a',new_id='b')],draft('old'))[0]['new_id'],'b')
 def test_no_exact_new_source_keeps_draft(self):
  r=draft_links(resource(),resource('b'),[],draft())[0];self.assertIsNone(r['new_id']);self.assertTrue(r['draft_preserved'])
 def test_wrong_hash(self):
  d=draft();d[0]['source_sha256']='other'
  with self.assertRaisesRegex(ValueError,'mismatch'):draft_links(resource(),resource(),[],d)
 def test_duplicate_draft(self):
  with self.assertRaisesRegex(ValueError,'duplicate'):draft_links(resource(),resource(),[],draft()+draft())
 def test_missing_alias(self):
  with self.assertRaisesRegex(ValueError,'missing'):draft_links(resource(),resource(),[],draft('unknown'))
if __name__=='__main__':unittest.main()
