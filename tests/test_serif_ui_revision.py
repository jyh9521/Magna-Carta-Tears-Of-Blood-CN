from pathlib import Path
import sys,json,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from apply_ui_layout_copies import same_size_overlay
from localization.text import validate_target,protected_tokens

class RevisionTests(unittest.TestCase):
    def profile(self):return json.loads((ROOT/'locales/zh-CN/proofreading/ui-layout-revision.json').read_text('utf8'))
    def test_same_size_overlay(self):self.assertEqual(same_size_overlay(b'abcdef',[dict(offset=2,original=b'cd',modified=b'XY')]),b'abXYef')
    def test_wrong_source(self):
        with self.assertRaises(ValueError):same_size_overlay(b'abcdef',[dict(offset=2,original=b'ZZ',modified=b'XY')])
    def test_size_change(self):
        with self.assertRaises(ValueError):same_size_overlay(b'abcdef',[dict(offset=2,original=b'cd',modified=b'XYZ')])
    def test_overlap(self):
        with self.assertRaises(ValueError):same_size_overlay(b'abcdef',[dict(offset=2,original=b'cd',modified=b'XY'),dict(offset=3,original=b'de',modified=b'ZZ')])
    def test_negative_offset(self):
        with self.assertRaises(ValueError):same_size_overlay(b'abcdef',[dict(offset=-2,original=b'e',modified=b'X')])
    def test_two_reviewed_fields(self):self.assertEqual(len(self.profile()['fields']),2)
    def test_linebreak_tokens_preserved(self):
        for q in self.profile()['fields']:validate_target(q['previous_target'],q['target']);self.assertEqual(protected_tokens(q['previous_target']),protected_tokens(q['target']))
    def test_care_phrase_not_split(self):
        q=next(q for q in self.profile()['fields'] if '14107' in q['id']);self.assertIn('总得有人照顾他们。',q['target']);self.assertEqual(q['target'].count('$n'),4)
    def test_short_talisman_first_line(self):
        q=next(q for q in self.profile()['fields'] if '06460' in q['id']);self.assertLess(len(q['target'].split('$n')[0]),len(q['previous_target'].split('$n')[0]));self.assertIn('混乱状态',q['target'])
    def test_source_bound_center_operand(self):
        q=self.profile()['operand'];self.assertEqual((q['export_index'],q['offset'],q['old_hex'],q['new_hex']),(12302,3521,'2cf4','2cf1'));self.assertEqual(q['owner_path'],['MrtsWindowStateCharInfo','MrtsFieldCharListBox'])
    def test_font_geometry_and_backup_guards(self):
        p=json.loads((ROOT/'locales/zh-CN/serif-font-profile.json').read_text('utf8'));self.assertEqual(p['font_input']['family'],'Source Han Serif SC Regular')
        for q in p['fonts'].values():self.assertEqual(q['body_top'],0);self.assertEqual(q['original_glyphs'],2667);self.assertEqual(len(q['base_sha256']),64);self.assertEqual(q['advance_overrides']['，'],10)
    def test_ui_texture_labels_and_duplicate(self):
        p=json.loads((ROOT/'locales/zh-CN/images/field-ui-texture-profile.json').read_text('utf8'));self.assertEqual(len(p['streams']),3);self.assertEqual(p['streams']['00001002.lin']['patches'],p['streams']['00065533.lin']['patches']);self.assertEqual([q['text'] for q in p['streams']['00001002.lin']['patches']],['编成','道具','装备','流派','信息','设置','魅力']);self.assertEqual(p['streams']['00001008.lin']['patches'][0]['text'],'整理')

if __name__=='__main__':unittest.main()
