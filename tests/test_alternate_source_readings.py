import copy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from audit_alternate_source_readings import audit, audit_field
from font_poc import digest


class AlternateReadingTests(unittest.TestCase):
    def fixture(self, text='名前は？$n覚えている？'):
        raw = text.encode('cp932')
        resource = dict(resource='SHIP/sample.cht', sha256=digest(raw))
        entry = dict(id='sample', offset=0, source_bytes=len(raw), source_sha256=digest(raw),
                     raw_hex=raw.hex(), decode='failed')
        decision = dict(**entry, resource=resource['resource'], resource_sha256=resource['sha256'],
                        source_encoding='cp932', reading_sha256=digest(text.encode('utf8')),
                        target='你的名字呢？$n还记得吗？', status='reviewed',
                        import_approved=False, runtime_encoding_verified=False)
        return resource, entry, decision, raw

    def test_roundtrip_and_controls_do_not_authorize_import(self):
        result = audit_field(*self.fixture())
        self.assertTrue(result['source_still_quarantined'])
        self.assertFalse(result['import_approved'])
        self.assertEqual(result['protected_tokens'], ['$n'])

    def test_original_resource_change_rejected(self):
        r, e, d, raw = self.fixture()
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            audit_field(r, e, d, raw + b'x')

    def test_source_binding_change_rejected(self):
        for key in ('id', 'offset', 'source_bytes', 'source_sha256'):
            r, e, d, raw = self.fixture()
            d[key] = 'wrong'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'binding'):
                audit_field(r, e, d, raw)

    def test_wrong_interpretation_hash_rejected(self):
        r, e, d, raw = self.fixture(); d['reading_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'reading fingerprint'):
            audit_field(r, e, d, raw)

    def test_import_and_runtime_claims_rejected(self):
        for key in ('import_approved', 'runtime_encoding_verified'):
            r, e, d, raw = self.fixture(); d[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'cannot authorize'):
                audit_field(r, e, d, raw)

    def test_primary_strict_field_cannot_be_reinterpreted(self):
        r, e, d, raw = self.fixture(); e['decode'] = 'strict'
        with self.assertRaisesRegex(ValueError, 'quarantine'):
            audit_field(r, e, d, raw)

    def test_changed_control_rejected(self):
        r, e, d, raw = self.fixture(); d['target'] = '你叫什么名字？'
        with self.assertRaisesRegex(ValueError, 'protected token'):
            audit_field(r, e, d, raw)

    def test_unknown_control_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown control'):
            audit_field(*self.fixture('名前は？$z'))

    def test_unknown_codec_rejected(self):
        r, e, d, raw = self.fixture(); d['source_encoding'] = 'latin-1'
        with self.assertRaisesRegex(ValueError, 'codec'):
            audit_field(r, e, d, raw)

    def test_corrupted_hex_rejected(self):
        r, e, d, raw = self.fixture(); e['raw_hex'] = '00' * len(raw)
        with self.assertRaisesRegex(ValueError, 'hex mismatch'):
            audit_field(r, e, d, raw)

    def test_no_private_use_or_control_bytes(self):
        for text in ('名前\ue000', '名前\n'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'nontext'):
                audit_field(*self.fixture(text))

    def test_no_lexical_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'lexical'):
            audit_field(*self.fixture('^^ﾇﾏﾇ'))

    def test_dash_and_page_leading_punctuation_rejected(self):
        for target in ('名字—$n还记得吗？', '名字？$n，还记得吗？'):
            r, e, d, raw = self.fixture(); d['target'] = target
            with self.subTest(target=target), self.assertRaises(ValueError):
                audit_field(r, e, d, raw)

    def test_fpb_span_and_actual_numeric_key_binding(self):
        r, e, d, raw = self.fixture()
        blob = struct.pack('<4I', 1, 77, 0, len(raw)) + struct.pack('<I', len(raw)) + raw
        r.update(resource='SHIP/sample.fpb', sha256=digest(blob))
        d.update(resource=r['resource'], resource_sha256=r['sha256'])
        d['native_binding'] = dict(id='sample', source_resource=r['resource'],
            source_resource_sha256=r['sha256'], source_offset=0, source_bytes=len(raw),
            source_sha256=digest(raw), physical_index=0, native_record_key=77)
        self.assertEqual(audit_field(r, e, d, blob)['native_source_binding']['native_record_key'], 77)
        d['native_binding']['native_record_key'] = 78
        with self.assertRaisesRegex(ValueError, 'key/index'):
            audit_field(r, e, d, blob)

    def test_full_linguistic_profile_is_separate_and_source_bound(self):
        p = json.loads((ROOT / 'locales/zh-CN/proofreading/alternate-source-readings.json').read_text('utf8'))
        self.assertEqual(len(p['entries']), 154)
        self.assertEqual(len({e['id'] for e in p['entries']}), 154)
        self.assertEqual(sum('native_binding' in e for e in p['entries']), 115)
        for e in p['entries']:
            self.assertFalse(e['import_approved']); self.assertFalse(e['runtime_encoding_verified'])
            self.assertEqual(e['status'], 'reviewed')
            self.assertEqual(len(e['reading_sha256']), 64)
        by = {e['id']: e for e in p['entries']}
        self.assertIn('奥尔哈”的男人', by['SHIP/00004044.cht/slot/18']['target'])
        self.assertIn('儿子', by['SHIP/00004059.cht/slot/18']['target'])
        self.assertIn('丈夫', by['SHIP/00015240.fpb/seq/29']['target'])
        self.assertIn('女人', by['SHIP/00001005.fpb/seq/12']['target'])


if __name__ == '__main__':
    unittest.main()
