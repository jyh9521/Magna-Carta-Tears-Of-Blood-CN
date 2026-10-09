import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from consolidate_config_fields import merge_config_resources


class ConfigConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.original = [{'resource': 'old', 'entries': [{'id': 'old/1', 'references': {'ko': '원본'}}]}]
        self.extra = [{'resource': 'config', 'entries': [{'id': 'config/1', 'editable': False, 'backend_eligible': False, 'semantic_review': 'pending'}]}]

    def test_append(self):
        self.assertEqual(len(merge_config_resources(self.original, self.extra)), 2)

    def test_old_fields_preserved(self):
        self.assertEqual(merge_config_resources(self.original, self.extra)[0], self.original[0])

    def test_deep_copy(self):
        result = merge_config_resources(self.original, self.extra)
        result[0]['entries'][0]['references']['ko'] = 'changed'
        result[1]['entries'][0]['id'] = 'changed'
        self.assertEqual(self.original[0]['entries'][0]['references']['ko'], '원본')
        self.assertEqual(self.extra[0]['entries'][0]['id'], 'config/1')

    def test_resource_collision(self):
        self.extra[0]['resource'] = 'old'
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_source_collision(self):
        self.extra[0]['entries'][0]['id'] = 'old/1'
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_duplicate_extra(self):
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra * 2)

    def test_duplicate_original(self):
        with self.assertRaises(ValueError): merge_config_resources(self.original * 2, self.extra)

    def test_editable_rejected(self):
        self.extra[0]['entries'][0]['editable'] = True
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_backend_rejected(self):
        self.extra[0]['entries'][0]['backend_eligible'] = True
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_missing_guard_rejected(self):
        del self.extra[0]['entries'][0]['editable']
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_review_required(self):
        self.extra[0]['entries'][0]['semantic_review'] = 'verified'
        with self.assertRaises(ValueError): merge_config_resources(self.original, self.extra)

    def test_empty_additions(self):
        self.assertEqual(merge_config_resources(self.original, []), self.original)


if __name__ == '__main__': unittest.main()
