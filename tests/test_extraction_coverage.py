import hashlib
import sys
from pathlib import Path
import unittest
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_extraction_coverage import compare_inventory, alternate_candidate, subtitle_inventory


class ExtractionCoverageTests(unittest.TestCase):
    def test_missing_supported_is_reported(self):
        r = compare_inventory(['a.fpb', 'b.tui', 'c.utx'], [{'resource':'SHIP/a.fpb'}])
        self.assertEqual(r['missing_supported'], ['b.tui'])
        self.assertEqual(r['outside_supported_formats'], {'.utx':1})

    def test_unexpected_resource(self):
        self.assertEqual(compare_inventory(['a.fpb'], [{'resource':'SHIP/b.fpb'}])['unexpected_catalog'], ['b.fpb'])

    def test_duplicate_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate archive'):
            compare_inventory(['a.fpb', 'a.fpb'], [])

    def test_duplicate_catalog_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate catalog'):
            compare_inventory(['a.fpb'], [{'resource':'SHIP/a.fpb'}]*2)

    def test_candidate_is_not_verified_encoding(self):
        raw = 'テスト'.encode('cp932')
        row = dict(id='fixture', source_bytes=len(raw), source_sha256=hashlib.sha256(raw).hexdigest(), decode='failed')
        r = alternate_candidate(row, raw)
        self.assertFalse(r['editable'])
        self.assertEqual(r['semantic'], 'unverified')
        self.assertEqual(r['references']['ja-JP'], 'テスト')

    def test_raw_identity_required(self):
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            alternate_candidate(dict(source_bytes=1, source_sha256='bad'), b'a')

    def test_ascii_not_encoding_candidate(self):
        raw = b'identifier'
        row = dict(id='fixture', source_bytes=len(raw), source_sha256=hashlib.sha256(raw).hexdigest(), decode='strict')
        self.assertIsNone(alternate_candidate(row, raw))

    def test_subtitle_inventory_reports_missing_and_preserves_comma(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'korean').mkdir()
            (root/'korean/a.ass').write_text('Dialogue: 0,0:00:01,0:00:02,Default,,0,0,0,,text,with comma\n', encoding='utf8')
            report, rows = subtitle_inventory({'files':[{'path':'/MOVIE/a.SFD;1'}, {'path':'/MOVIE/b.SFD;1'}]}, root)
            self.assertEqual(report['korean']['movies_without_ass'], ['b'])
            self.assertEqual(report['korean']['dialogue_cues'], 1)
            self.assertEqual(rows[0]['fields'][9], 'text,with comma')
            self.assertEqual(report['japanese']['movies_without_ass'], ['a', 'b'])

    def test_malformed_ass_is_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'korean').mkdir()
            (root/'korean/a.ass').write_text('Dialogue: broken\n', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'malformed ASS'):
                subtitle_inventory({'files':[]}, root)
