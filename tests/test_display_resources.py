from pathlib import Path
import copy
import struct
import sys
import unittest
import tempfile
import json
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'src'), str(ROOT/'lib')]
from display_resources import apply_display_resources, display_cases, character_entries
from font_resource import code_chunks, expanded_entries, append_slots, verify_slots, append_font, parts
from test_font_resource import fixture, sha
from translate.fpb import build_fpb, parse_fpb_raw
from build_poc_pipeline import write_qa
from validate_poc_qa import validate_receipt
from localization.text import MappedEncoder


class DisplayResourceTests(unittest.TestCase):
    def setUp(self):
        self.encoder = MappedEncoder([dict(character='测', bytes='b0a1', glyph=317)])
        self.fpb = build_fpb(bytes(16), [(1, 1, 4), (2, 5, 1)], b'AB$nCD')
        self.plan = dict(resource='a.fpb', kind='fpb', expected_sha256=sha(self.fpb), cached_copies=1,
                         targets=[dict(seq=1, target='测$n测', source_sha256=sha(b'B$nC'))])

    def apply(self):
        return apply_display_resources({'a.fpb': self.fpb}, b'prefix'+self.fpb+b'suffix', self.encoder, [self.plan])

    def test_fpb_cache_and_unselected(self):
        overrides, bundle, report = self.apply()
        self.assertEqual(bundle, b'prefix'+overrides['a.fpb']+b'suffix')
        self.assertEqual(parse_fpb_raw(overrides['a.fpb'])[2], b'A'+bytes.fromhex('b0a1')+b'$n'+bytes.fromhex('b0a1')+b'D')
        self.assertEqual(report[0]['cached_offset'], 6)

    def test_source_hash(self):
        self.plan['targets'][0]['source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'window mismatch'): self.apply()

    def test_resource_hash(self):
        self.plan['expected_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'fingerprint'): self.apply()

    def test_unknown_resource(self):
        self.plan['resource'] = 'b.fpb'
        with self.assertRaisesRegex(ValueError, 'unknown'): self.apply()

    def test_duplicate_resource(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            apply_display_resources({'a.fpb':self.fpb}, self.fpb, self.encoder, [self.plan,self.plan])

    def test_duplicate_sequence(self):
        self.plan['targets'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.apply()

    def test_token_drop(self):
        self.plan['targets'][0]['target'] = '测'
        with self.assertRaisesRegex(ValueError, 'token'): self.apply()

    def test_cache_mismatch(self):
        self.plan['cached_copies'] = 0
        with self.assertRaisesRegex(ValueError, 'cached'): self.apply()

    def test_no_cached_copy(self):
        self.plan['cached_copies'] = 0
        _, bundle, report = apply_display_resources({'a.fpb': self.fpb}, b'other', self.encoder, [self.plan])
        self.assertEqual(bundle, b'other'); self.assertIsNone(report[0]['cached_offset'])

    def test_fixed_preserves_second_field(self):
        old = struct.pack('<III',1,2,42)+b'Name'+bytes(252)+b'Description'+bytes(245)
        profile = dict(header_size=8, record_size=516, record_count=1, kind=2, record_index=0,
                       record_id=42, text_offset=4, text_bytes=256, expected_slot_sha256=sha(old[12:268]))
        plan = dict(resource='a.tui',kind='fixed-display-slot',expected_sha256=sha(old),cached_copies=1,
                    targets=[dict(profile=profile,target='测',max_estimated_pixels=20)])
        result,bundle,_ = apply_display_resources({'a.tui':old},old,self.encoder,[plan],{'font':b''},lambda *args:[19])
        self.assertEqual(result['a.tui'][268:],old[268:]); self.assertEqual(bundle,result['a.tui'])
        with self.assertRaisesRegex(ValueError,'width'):
            apply_display_resources({'a.tui':old},old,self.encoder,[plan],{'font':b''},lambda *args:[21])
        plan['targets'][0]['target']='测'*128
        with self.assertRaisesRegex(ValueError,'overflow'):
            apply_display_resources({'a.tui':old},old,self.encoder,[plan])
        plan['targets'][0]['profile']['text_bytes']=512
        with self.assertRaisesRegex(ValueError,'bounded'):
            apply_display_resources({'a.tui':old},old,self.encoder,[plan])

    def test_trial_qa_inventory(self):
        config = dict(locale='xx',milestone='trial',text_resources=[self.plan])
        config['text_resources'].append(dict(resource='a.tui',kind='fixed-display-slot',targets=[dict(profile=dict(record_id=176),target='测')]))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);write_qa(path,config,dict(candidate_sha256='a'*64))
            receipt=json.loads((path/'QA_CHECKLIST.json').read_text('utf8'))
            result=validate_receipt(receipt,config,'a'*64,path/'QA_CHECKLIST.json')
            self.assertEqual(len(result['cases']),8);self.assertEqual(result['record_state'],'pending')

    def test_character_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'chars.json').write_text(json.dumps(dict(characters=['测','试'])))
            self.assertEqual(character_entries(dict(font_characters='chars.json'),root),[dict(character='测'),dict(character='试')])
            (root/'chars.json').write_text(json.dumps(dict(characters=['测','测'])))
            with self.assertRaisesRegex(ValueError,'inventory'):character_entries(dict(font_characters='chars.json'),root)


class MultiBandFontTests(unittest.TestCase):
    def test_old_band_identical(self):
        original=fixture();a=append_slots(original,33,0xD0A1,expected_sha256=sha(original))
        b=append_font(original,bytes(66),bytes(33),0xD0A1,expected_sha256=sha(original))
        self.assertEqual(a,b)

    def test_bands_and_preservation(self):
        original=fixture();expanded=append_slots(original,317,0xD0A1,expected_sha256=sha(original))
        self.assertEqual(code_chunks(317,0xD0A1),[(0xD0A1,94),(0xD1A1,94),(0xD2A1,94),(0xD3A1,35)])
        self.assertEqual(verify_slots(original,expanded,317,0xD0A1)['expanded_glyphs'],319)
        entries=expanded_entries([dict(character=chr(0x4E00+i)) for i in range(317)],2,0xD0A1)
        enc=MappedEncoder(entries,font_tables=parts(expanded)[0])
        self.assertEqual(enc.encode(entries[94]['character']),bytes.fromhex('d1a1'))
        self.assertTrue(all(0xA1<=int(row['bytes'],16)&255<=0xFE for row in entries))

    def test_invalid_bands(self):
        for count,start in [(0,0xD0A1),(True,0xD0A1),(1,0xD000),(1,0xD0FF),(95,0xFFA1)]:
            with self.assertRaises(ValueError):code_chunks(count,start)

    def test_original_tampering(self):
        original=fixture();expanded=bytearray(append_slots(original,95,0xD0A1,expected_sha256=sha(original)))
        expanded[parts(expanded)[0]['metrics_start']]=0
        with self.assertRaisesRegex(ValueError,'original'):verify_slots(original,bytes(expanded),95,0xD0A1)
