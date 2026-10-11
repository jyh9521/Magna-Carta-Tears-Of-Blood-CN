"""Language review and source-role authorization are distinct decisions."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from extract_strings import field
from import_audited_fields import require_write_policy, rewrite_fields
from prepare_translation_scope import freeze
from validate_translation_batch import GlossaryTerms, validate


class ReinsertionPolicyTests(unittest.TestCase):
    def fixture(self):
        source = field('id', '테스트'.encode('cp949'), 0)
        corpus = dict(source_locale='ko-KR', resources=[dict(
            resource='SHIP/fixture.sgi', sha256='0' * 64, entries=[source])])
        target = dict(id='id', source_sha256=source['source_sha256'], target='测试',
                      status='reviewed', reinsertion_policy='pending-role-review')
        return corpus, dict(schema=1, locale='zh-CN', entries=[target])

    def test_pending_review_rejected_before_fixed_field_encoding(self):
        _, batch = self.fixture()
        with self.assertRaisesRegex(ValueError, 'reinsertion policy'):
            rewrite_fields(b'\0', [{}], batch['entries'], None)

    def test_original_retention_and_unknown_policy_never_authorize_writes(self):
        for policy in ('retain-original', 'pending-role-review', 'typo'):
            with self.assertRaisesRegex(ValueError, 'reinsertion policy'):
                require_write_policy(dict(status='reviewed', reinsertion_policy=policy))
        require_write_policy(dict(status='reviewed'))
        require_write_policy(dict(status='reviewed', reinsertion_policy='translate'))

    def test_invalid_policy_rejected_by_batch_validator(self):
        corpus, batch = self.fixture()
        batch['entries'][0]['reinsertion_policy'] = 'typo'
        with self.assertRaisesRegex(ValueError, 'invalid reinsertion policy'):
            validate(corpus, batch, GlossaryTerms())

    def test_scope_reports_pending_roles_without_asserting_visibility(self):
        corpus, batch = self.fixture()
        rows, summary = freeze(corpus, [batch])
        self.assertEqual(summary['pending_role_review_translations'], 1)
        self.assertEqual(rows[0]['reinsertion_policy'], 'pending-role-review')
        self.assertFalse(rows[0]['runtime_visibility_verified'])
        self.assertFalse(summary['coverage_review_complete'])
        self.assertFalse(summary['full_iso_ready'])

    def test_style_batch_246_promotions_require_exact_source_target_profile(self):
        batch = json.loads((ROOT / 'locales/zh-CN/style-description-review-01.json').read_text('utf8'))
        profile = json.loads((ROOT / 'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'))
        self.assertEqual(len(batch['entries']), 288)
        self.assertEqual(len({r['id'] for r in batch['entries']}), 288)
        self.assertEqual(len(profile['bindings']),246)
        bound={r['id']:r for r in profile['bindings']}
        for row in batch['entries']:
            self.assertEqual(row['reinsertion_policy'],'translate')
            if row['id'] in bound:self.assertEqual((row['source_sha256'],row['target']),(bound[row['id']]['source_sha256'],bound[row['id']]['target']))
        self.assertTrue(profile['source_name_equality_partition_preserved'])
        self.assertTrue(profile['caption_producer_closed_statically'])
        self.assertFalse(profile['runtime_verified'])


if __name__ == '__main__':
    unittest.main()
