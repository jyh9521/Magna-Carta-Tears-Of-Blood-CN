import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_deferred_decodes import verify_failure, ledger
from font_poc import digest


class DeferredDecodeTests(unittest.TestCase):
    def entry(self,raw=b'\x81'):
        return dict(id='fixture',decode='failed',raw_hex=raw.hex(),source_bytes=len(raw),source_sha256=digest(raw),offset=4)
    def corpus(self,e):return dict(resources=[dict(resource='SHIP/fixture.fpb',entries=[e])])
    def test_actual_failure(self):self.assertEqual(verify_failure(self.entry())['start'],0)
    def test_valid_bytes_not_deferred(self):
        with self.assertRaises(ValueError):verify_failure(self.entry(b'ABC'))
    def test_empty_not_failure(self):
        with self.assertRaises(ValueError):verify_failure(self.entry(b''))
    def test_hash_mismatch(self):
        e=self.entry();e['source_sha256']='bad'
        with self.assertRaises(ValueError):verify_failure(e)
    def test_size_mismatch(self):
        e=self.entry();e['source_bytes']=2
        with self.assertRaises(ValueError):verify_failure(e)
    def test_missing_bytes(self):
        e=self.entry();del e['raw_hex']
        with self.assertRaises(ValueError):verify_failure(e)
    def test_wrong_status(self):
        e=self.entry();e['decode']='strict'
        with self.assertRaises(ValueError):verify_failure(e)
    def test_ledger_preserves(self):
        e=self.entry();rs,s=ledger(self.corpus(e));self.assertEqual(s['fields'],1);self.assertEqual(s['deferred'],1);self.assertEqual(e['decode'],'failed');self.assertFalse(rs[0]['field_deleted'])
    def test_alternative_preserved(self):
        e=self.entry();e['coverage_reviews']=[dict(layer='decode',source_sha256=e['source_sha256'],classification='alternate-codec-candidate')]
        rs,_=ledger(self.corpus(e));self.assertEqual(rs[0]['alternatives'],e['coverage_reviews']);self.assertFalse(rs[0]['all_codecs_failed'])
    def test_alternative_wrong_source(self):
        e=self.entry();e['coverage_reviews']=[dict(layer='decode',source_sha256='wrong')]
        with self.assertRaises(ValueError):ledger(self.corpus(e))
    def test_nonfailures_not_deferred(self):
        e=self.entry(b'ABC');e['decode']='strict';rs,s=ledger(self.corpus(e));self.assertEqual(rs,[]);self.assertEqual(s['fields'],1)
    def test_duplicate_rejected(self):
        e=self.entry();c=self.corpus(e);c['resources'][0]['entries'].append(e.copy())
        with self.assertRaises(ValueError):ledger(c)
    def test_gate_stays_pending(self):
        rs,s=ledger(self.corpus(self.entry()));self.assertFalse(s['coverage_review_complete']);self.assertFalse(rs[0]['backend_eligible'])


if __name__=='__main__':unittest.main()
