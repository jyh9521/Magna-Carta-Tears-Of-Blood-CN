"""CDG locale data checks; matching labels do not prove runtime cache linkage."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate_translation_batch import glossary_terms


def entries():
    return json.loads((ROOT / 'locales/zh-CN/talisman-encyclopedia-review-01.json').read_text('utf8'))['entries']


class TalismanEncyclopediaTests(unittest.TestCase):
    def test_missing_slot_set_is_complete_without_duplicate_old_translations(self):
        rows = entries()
        self.assertEqual(len(rows), 138)
        self.assertEqual({r['id'] for r in rows}, {
            f'SHIP/00006460.cdg/slot/{slot}' for slot in range(144)
            if slot not in {31, 81, 87, 97, 117, 137}
        })
        self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_all_names_match_registered_exact_source_variants(self):
        terms = glossary_terms(ROOT / 'GLOSSARY.md')
        canonical = dict(terms)
        names = [r for r in entries() if int(r['id'].rsplit('/', 1)[1]) % 2 == 0]
        self.assertEqual(len(names), 72)
        variants = {source: target for source, target in terms
                    if source in terms.exact_only and ',  ' in source}
        self.assertEqual(len(variants), 72)
        self.assertTrue(all(r['target'] in variants.values() for r in names))
        self.assertIn('칸', canonical)

    def test_explicit_control_breaks_and_effect_phrases(self):
        rows = {r['id']: r['target'] for r in entries()}
        def text(slot):
            return rows[f'SHIP/00006460.cdg/slot/{slot}']
        self.assertEqual(text(23).count('$n'), 2)
        self.assertEqual(text(41).count('$n'), 2)
        self.assertIn('我方一人的', text(15))
        self.assertIn('敌方一人', text(95))
        self.assertIn('HP完全恢复', text(47))

    def test_source_effect_inconsistency_is_not_silently_removed(self):
        row = next(r for r in entries() if r['id'].endswith('/slot/119'))
        self.assertIn('防御提升', row['target'])
        self.assertIn('降低其物理攻击力', row['target'])
        self.assertIn('inconsistency remains in source notes', row['context'])


if __name__ == '__main__':
    unittest.main()
