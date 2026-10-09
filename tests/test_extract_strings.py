import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
from extract_strings import field, extract_resource, scan_candidates, seed_targets
from translate.fpb import build_fpb
from font_poc import digest
from build_locale import patch_font
from test_font_resource import fixture


class CatalogTests(unittest.TestCase):
    def test_cp949_strict(self):
        r=field('id','한글'.encode('cp949'),0)
        self.assertEqual(r['references']['ko-KR'],'한글')
        self.assertTrue(r['canonical_encoding'])

    def test_failed_bytes_preserved(self):
        r=field('id',b'\x81',3)
        self.assertEqual((r['decode'],r['raw_hex']),('failed','81'))
        self.assertNotIn('references',r)

    def test_unknown_controls_quarantined(self):
        self.assertEqual(field('id',b'A$unknown',0)['controls'],'quarantined')

    def test_raw_controls_quarantined(self):
        self.assertEqual(field('id',b'A\tB',0)['controls'],'quarantined')

    def test_fpb_implicit_window(self):
        blob=build_fpb(bytes(16),[(1,1,1)],b'AB')
        rows=extract_resource('a.fpb',blob)['entries']
        self.assertEqual([r['seq'] for r in rows],[0,1])
        self.assertTrue(all(r['backend_eligible'] and not r['editable'] for r in rows))

    def test_fpb_stub(self):
        r=extract_resource('a.fpb',bytes(8))
        self.assertEqual(r['audit']['status'],'stub-not-parsed')

    def test_fpb_overlap_readonly(self):
        r=extract_resource('a.fpb',build_fpb(bytes(16),[(0,0,2),(1,1,1)],b'AB'))
        self.assertFalse(any(e['backend_eligible'] for e in r['entries']))

    def test_fpb_bounds_unverified(self):
        blob=bytearray(build_fpb(bytes(16),[(1,1,1)],b'AB'))
        struct.pack_into('<I',blob,24,99)
        self.assertFalse(extract_resource('a.fpb',bytes(blob))['entries'][-1]['bounds_valid'])

    def test_tui_both_fields(self):
        blob=struct.pack('<III',1,2,42)+b'A'+bytes(255)+b'B'+bytes(255)
        rows=extract_resource('a.tui',blob)['entries']
        self.assertEqual([r['references']['ko-KR'] for r in rows],['A','B'])
        self.assertEqual([r['offset'] for r in rows],[12,268])

    def test_tui_padding_not_hidden(self):
        blob=struct.pack('<III',1,2,42)+b'A\0Z'+bytes(253)+bytes(256)
        self.assertFalse(extract_resource('a.tui',blob)['entries'][0]['padding_clean'])

    def test_tui_duplicate_id_unique_catalog_ids(self):
        record=struct.pack('<I',42)+bytes(512)
        r=extract_resource('a.tui',struct.pack('<II',2,2)+record*2)
        self.assertFalse(r['unique_record_ids'])
        self.assertEqual(len({e['id'] for e in r['entries']}),4)

    def test_slot_partial_readonly(self):
        r=extract_resource('a.cha',bytes(12)+b'A\0')
        self.assertFalse(r['entries'][0]['complete_slot'])
        self.assertFalse(r['entries'][0]['editable'])

    def test_heuristic_not_editable(self):
        rows=scan_candidates('한글'.encode('cp949')+b'\0LookupKey\0','x')
        self.assertEqual(len(rows),2)
        self.assertTrue(all(not r['editable'] for r in rows))

    def test_seed_hash_guard(self):
        blob=build_fpb(bytes(16),[],b'A')
        resources=[extract_resource('a.fpb',blob)]
        locale=dict(text_resources=[dict(resource='a.fpb',kind='fpb',expected_sha256=digest(blob),
                         targets=[dict(seq=0,source_sha256=digest(b'A'),target='测')])])
        self.assertEqual(seed_targets(resources,locale)[0]['target'],'测')
        bad=copy.deepcopy(locale);bad['text_resources'][0]['targets'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'seed field'):seed_targets(resources,bad)

    def test_invalid_raster_size(self):
        for size in [True,3,999]:
            with self.assertRaisesRegex(ValueError,'raster size'):
                patch_font(fixture(),None,Path('missing.otf'),'测',1,size)


if __name__=='__main__':unittest.main()
