import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_decode_quarantine import reading,boundaries,checked_span,reconcile,fields
import font_poc as core

class DecodeQuarantineTests(unittest.TestCase):
    def test_cp949_roundtrip(self):self.assertTrue(reading('한글'.encode('cp949'),'cp949')['roundtrip'])
    def test_cp932_roundtrip(self):self.assertTrue(reading('テスト'.encode('cp932'),'cp932')['roundtrip'])
    def test_strict_rejects_split(self):self.assertFalse(reading('한'.encode('cp949')[:1],'cp949')['strict'])
    def test_byte_not_character_offsets(self):self.assertEqual(boundaries('A한B'.encode('cp949'),'cp949'),{0,1,3,4})
    def test_invalid_pool_has_no_boundaries(self):self.assertIsNone(boundaries(b'\xff','cp949'))
    def test_span_identity(self):self.assertEqual(checked_span(b'ABC',dict(offset=1,source_bytes=1,source_sha256=core.digest(b'B'))),b'B')
    def test_span_hash_mismatch(self):
        with self.assertRaisesRegex(ValueError,'identity'):checked_span(b'ABC',dict(offset=1,source_bytes=1,source_sha256=core.digest(b'C')))
    def test_span_bounds(self):
        with self.assertRaisesRegex(ValueError,'bounds'):checked_span(b'ABC',dict(offset=-1,source_bytes=1,source_sha256=''))
    def test_reconcile_superseded_view(self):
        old=dict(resources=[dict(resource='x',entries=[dict(id='x/1',source_sha256='a',decode='failed'),dict(id='x/2',source_sha256='b',decode='failed')])])
        active=dict(resources=[dict(resource='x',entries=[dict(id='x/1',source_sha256='a',decode='failed')])])
        a,b=reconcile(old,active);self.assertEqual((len(a),len(b)),(1,1));self.assertEqual(b[0]['status'],'superseded-source-view')
    def test_duplicate_id_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):fields(dict(resources=[dict(entries=[dict(id='x'),dict(id='x')])]))
if __name__=='__main__':unittest.main()
