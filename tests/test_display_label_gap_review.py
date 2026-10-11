import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from validate_translation_batch import glossary_terms
class DisplayLabelGapReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'locales/zh-CN/display-label-gap-review-01.json').read_text('utf8'))['entries'];cls.terms=dict(glossary_terms(ROOT/'GLOSSARY.md'))
 def test_all54_source_bound_reviewed(self):
  self.assertEqual(len(self.rows),54);self.assertEqual(len({e['id'] for e in self.rows}),54)
  for e in self.rows:self.assertEqual(e['status'],'reviewed');self.assertTrue(e['target']);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
 def test_original_editor_markers_retained(self):
  self.assertEqual(sum(e['target'].startswith('[未校审]') for e in self.rows),23)
  self.assertEqual(self.terms['불의 조각 (보류?)'],'火之碎片（暂缓？）')
 def test_suffix_letters_and_numeric_recipe_references(self):
  targets=[e['target'] for e in self.rows]
  self.assertIn('[未校审]羽翼弓F',targets);self.assertIn('猎人弓S _ 35',targets);self.assertIn('白色法杖+2 _ 40',targets)
 def test_character_labels_not_untranslated_or_new_sex(self):
  expected=['卡琳兹_状态说明','莉丝_状态说明','阿泽尔_说明','哈伦_说明','艾欧妮丝_说明','玛雅_说明','朱丝蒂娜_说明','莉安娜_说明','克里斯_说明','缪恩_说明','劳尔_说明']
  labels=[e['target'] for e in self.rows if e['id'].startswith('SHIP/00001240.tui/')];self.assertEqual(labels,expected)
 def test_complete_terms_canonical(self):
  self.assertEqual(self.terms['[미감수]메가톤글러브'],'[未校审]巨吨手套');self.assertEqual(self.terms['멋진법의 _ 38'],'华丽法衣 _ 38');self.assertEqual(self.terms['아밀라_지팡이'],'阿蜜拉_法杖')
 def test_no_line_controls_or_dash(self):
  for e in self.rows:
   for c in ('—','\0','\r','\n'):self.assertNotIn(c,e['target'])
if __name__=='__main__':unittest.main()
