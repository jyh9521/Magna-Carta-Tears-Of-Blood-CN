import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from export_review import export, join_targets, review_row
from extract_strings import field


class ExportReviewTests(unittest.TestCase):
    def setUp(self):
        self.source = field('SHIP/demo/0', '리스$n'.encode('cp949'), 0)
        self.catalog = dict(source_locale='ko-KR', iso_sha256='0'*64,
                            resources=[dict(resource='SHIP/demo', entries=[self.source])],
                            celfid_candidates=[dict(id='candidate')])
        self.batch = dict(schema=1, locale='zh-CN', entries=[dict(
            id=self.source['id'], source_sha256=self.source['source_sha256'],
            target='莉丝$n', status='draft')])

    def test_join(self):
        self.assertEqual(len(join_targets(self.catalog, [self.batch], [('리스','莉丝')])), 1)

    def test_overlapping_batches(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            join_targets(self.catalog, [self.batch, self.batch], [])

    def test_mixed_locales(self):
        with self.assertRaisesRegex(ValueError, 'mixed'):
            join_targets(self.catalog, [self.batch, dict(self.batch, locale='ja-JP')], [])

    def test_locale_neutral(self):
        self.assertEqual(len(join_targets(self.catalog, [dict(self.batch, locale='zh-TW')], [])), 1)

    def test_untranslated_stays_empty(self):
        row = review_row(self.source, {}, 'ko-KR')
        self.assertEqual(row['target'], '')
        self.assertEqual(row['translation_status'], 'untranslated')
        self.assertFalse(row['reinsertion_authorized'])

    def test_all_records_preserved(self):
        self.catalog['resources'][0]['entries'].append(field('bad', b'\xff', 1))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            summary = export(self.catalog, {}, out)
            rows = [json.loads(s) for s in (out/'review.jsonl').read_text('utf8').splitlines()]
            self.assertEqual(summary['records'], 2)
            self.assertEqual(summary['decode_failed'], 1)
            self.assertEqual(summary['untranslated'], 2)
            self.assertEqual(rows[1]['source']['raw_hex'], 'ff')
            self.assertIsNone(rows[1]['source_text'])
            self.assertEqual(summary['celfid_candidates'], 1)

    def test_nonempty_output_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); (out/'keep').write_text('keep')
            with self.assertRaisesRegex(ValueError, 'empty'): export(self.catalog, {}, out)
            self.assertEqual((out/'keep').read_text(), 'keep')

    def test_escaped_html(self):
        self.source['references']['ko-KR'] = '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); export(self.catalog, {}, out)
            html = (out/'resource-0000.html').read_text('utf8')
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)

    def test_counts_not_review_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            summary = export(self.catalog, join_targets(self.catalog, [self.batch], []), out)
            self.assertEqual(summary['draft'], 1)
            self.assertNotIn('reviewed', summary)
            self.assertEqual(summary['reinsertion'], 'not performed')


if __name__ == '__main__': unittest.main()
