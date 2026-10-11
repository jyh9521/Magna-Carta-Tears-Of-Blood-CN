import copy
import hashlib
import struct
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'src', 'lib')]
from source_interpretation import source_text, source_codec, decode_source
from prepare_source_interpretations import derive
from localization.text import rewrite_fpb
from font_poc import digest


class AsciiEncoder:
    def encode(self, text):
        return text.encode('ascii')


class SourceInterpretationTests(unittest.TestCase):
    def field(self, text='名前は？'):
        raw = text.encode('cp932')
        entry = dict(source_sha256=digest(raw), source_encoding='cp932', source_locale='ja-JP',
                     references={'ja-JP': text}, source_interpretation=dict(
                         original_decode='failed', raw_sha256=digest(raw),
                         reading_sha256=digest(text.encode('utf8')),
                         native_source_span_verified=True, runtime_encoding_verified=False))
        return raw, entry

    def test_default_primary_locale_and_codec_unchanged(self):
        e = dict(references={'ko-KR': '이름', 'und': 'fallback'})
        self.assertEqual(source_text(e), '이름'); self.assertEqual(source_codec(e), 'cp949')

    def test_und_fallback_unchanged(self):
        self.assertEqual(source_text(dict(references={'und': 'unknown'})), 'unknown')

    def test_explicit_locale_overrides_other_reference(self):
        raw, e = self.field(); e['references']['ko-KR'] = 'not the source'
        self.assertEqual(decode_source(raw, e), '名前は？')

    def test_explicit_locale_missing_rejected(self):
        raw, e = self.field(); e['references'] = {'ko-KR': 'wrong'}
        with self.assertRaisesRegex(ValueError, 'locale reference'):
            source_text(e)

    def test_alternate_codec_without_proof_rejected(self):
        raw, e = self.field(); del e['source_interpretation']
        with self.assertRaisesRegex(ValueError, 'bound interpretation'):
            source_codec(e)

    def test_every_interpretation_proof_field_enforced(self):
        for key, value in [('original_decode', 'strict'), ('raw_sha256', '0' * 64),
                           ('reading_sha256', '0' * 64), ('native_source_span_verified', False),
                           ('runtime_encoding_verified', True)]:
            raw, e = self.field(); e['source_interpretation'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                source_codec(e)

    def test_raw_mutation_rejected(self):
        raw, e = self.field()
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            decode_source(raw + b'x', e)

    def test_mismatched_actual_decoded_source_rejected(self):
        raw, e = self.field(); e['references']['ja-JP'] = '別の名前'
        e['source_interpretation']['reading_sha256'] = digest('別の名前'.encode('utf8'))
        with self.assertRaisesRegex(ValueError, 'text/roundtrip'):
            decode_source(raw, e)

    def test_unknown_codec_rejected(self):
        raw, e = self.field(); e['source_encoding'] = 'latin-1'
        with self.assertRaises(ValueError): source_codec(e)

    def blob(self):
        jp = 'ヤソンじゃないだろうな？'.encode('cp932'); kr = '이름'.encode('cp949')
        return struct.pack('<7I', 2, 9, 0, len(jp), 12, len(jp), len(kr)) + struct.pack('<I', len(jp + kr)) + jp + kr

    def test_per_sequence_codec_and_untargeted_bytes_preserved(self):
        blob = self.blob()
        rewritten, rows = rewrite_fpb(blob, {0: 'Name?'}, AsciiEncoder(), source_encodings={0: 'cp932'})
        self.assertIn('이름'.encode('cp949'), rewritten)
        self.assertEqual(len(rows), 1)

    def test_mixed_source_encodings_in_same_resource(self):
        rewritten, rows = rewrite_fpb(self.blob(), {0: 'Name?', 12: 'Name'}, AsciiEncoder(),
                                      source_encodings={0: 'cp932', 12: 'cp949'})
        self.assertEqual(len(rows), 2)

    def test_unselected_codec_or_unknown_codec_rejected(self):
        for codecs in ({999: 'cp932'}, {0: 'latin-1'}):
            with self.subTest(codecs=codecs), self.assertRaisesRegex(ValueError, 'encoding selection'):
                rewrite_fpb(self.blob(), {0: 'Name?'}, AsciiEncoder(), source_encodings=codecs)

    def test_default_codec_does_not_silently_fallback(self):
        with self.assertRaises(UnicodeDecodeError):
            rewrite_fpb(self.blob(), {0: 'Name?'}, AsciiEncoder())

    def test_derived_catalog_does_not_mutate_primary(self):
        text = '名前は？'; raw = text.encode('cp932')
        blob = struct.pack('<4I', 1, 77, 0, len(raw)) + struct.pack('<I', len(raw)) + raw
        entry = dict(id='test', offset=0, source_bytes=len(raw), source_sha256=digest(raw),
                     raw_hex=raw.hex(), decode='failed', semantic='dialogue-window')
        r = dict(resource='SHIP/sample.fpb', sha256=digest(blob), entries=[entry])
        d = dict(id='test', offset=0, source_bytes=len(raw), source_sha256=digest(raw),
                 resource=r['resource'], resource_sha256=r['sha256'], source_encoding='cp932',
                 reading_sha256=digest(text.encode('utf8')), target='姓名？', status='reviewed',
                 import_approved=False, runtime_encoding_verified=False,
                 native_binding=dict(id='test', source_resource=r['resource'],
                     source_resource_sha256=r['sha256'], source_offset=0, source_bytes=len(raw),
                     source_sha256=digest(raw), physical_index=0, native_record_key=77))
        original = dict(resources=[r]); before = copy.deepcopy(original)
        catalog, batch = derive(original, dict(schema=1, locale='zh-CN', entries=[d]), {'sample.fpb': blob})
        self.assertEqual(original, before)
        e = catalog['resources'][0]['entries'][0]
        self.assertEqual(e['decode'], 'strict'); self.assertEqual(source_codec(e), 'cp932')
        self.assertEqual(batch['entries'][0]['id'], 'test')
        self.assertNotIn('ko-KR', e['references'])


if __name__ == '__main__':
    unittest.main()
