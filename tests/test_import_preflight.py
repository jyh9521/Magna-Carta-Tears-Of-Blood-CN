import sys
import unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','lib','src')]
from preflight_resource_import import preflight
import font_poc as core


class Encoder:
    def encode(self,text):return text.encode('ascii')


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'abc'+bytes(5)+b'def'+bytes(5)
        self.entries=[dict(id='id/'+str(i),source_sha256=core.digest(text),source_bytes=3,offset=i*8,
                           slot_bytes=8,slot_sha256=core.digest(self.raw[i*8:i*8+8]),decode='strict',controls='recognized',references={'ko-KR':text.decode('ascii')})
                      for i,text in enumerate((b'abc',b'def'))]
        self.corpus=dict(resources=[dict(resource='SHIP/sample.cha',sha256=core.digest(self.raw),entries=self.entries)])
        self.targets=[dict(id=e['id'],source_sha256=e['source_sha256'],target='XYZ',status='reviewed') for e in self.entries]
    def run_plan(self):
        return preflight(self.corpus,[dict(schema=1,locale='sample',entries=self.targets)],{'sample.cha':self.raw},Encoder())
    def test_all_accounted(self):
        b,r=self.run_plan();self.assertEqual(len(b['entries']),2);self.assertEqual(r['targets'],2);self.assertFalse(r['final_iso_authorized'])
    def test_policy_deferred_is_not_silently_removed(self):
        self.targets[0]['reinsertion_policy']='pending-role-review';b,r=self.run_plan();self.assertEqual(len(b['entries']),1);self.assertEqual(r['policy_deferred_fields'],1);self.assertEqual(r['deferred'][0]['id'],'id/0')
    def test_overflow_holds_entire_resource(self):
        self.targets[0]['target']='12345678';b,r=self.run_plan();self.assertFalse(b['entries']);self.assertEqual(r['capacity_overflow_fields'],1);self.assertEqual(r['whole_resource_held_fields'],2)
    def test_unknown_policy_rejected(self):
        self.targets[0]['reinsertion_policy']='ignore'
        with self.assertRaisesRegex(ValueError,'policy'):self.run_plan()
    def test_unreviewed_rejected(self):
        self.targets[0]['status']='draft'
        with self.assertRaisesRegex(ValueError,'unreviewed'):self.run_plan()
    def test_resource_hash_rejected(self):
        self.corpus['resources'][0]['sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.run_plan()
    def test_backend_error_is_explicit(self):
        self.entries[0]['slot_sha256']='bad';b,r=self.run_plan();self.assertFalse(b['entries']);self.assertIn('fingerprint',r['resources'][0]['backend_error']);self.assertEqual(r['whole_resource_held_fields'],2)
    def test_alias_and_canonical_duplicate_rejected(self):
        self.entries[0]['source_aliases']=['old/0'];self.targets[1]=dict(self.targets[0],id='old/0')
        with self.assertRaisesRegex(ValueError,'duplicate canonical'):self.run_plan()
    def test_internal_role_cannot_be_promoted_by_preflight(self):
        self.entries[0]['semantic']='internal-configuration'
        with self.assertRaisesRegex(ValueError,'non-display'):self.run_plan()


if __name__=='__main__':unittest.main()
