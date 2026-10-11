import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from apply_term_revision import patch_bound_bytes
from movie_revision import name_only_ass


class TermRevisionTests(unittest.TestCase):
    def record(self, blob=b'aaOLDzz',new=b'aaNEWzz'):
        return dict(baseline_sha256=hashlib.sha256(blob).hexdigest(),modified_sha256=hashlib.sha256(new).hexdigest(),
                    allowed_spans=[[2,5]],edits=[dict(offset=2,old_hex=b'OLD'.hex(),new_hex=b'NEW'.hex())])

    def test_change_and_reverse(self):
        r=self.record();new=patch_bound_bytes(b'aaOLDzz',r);self.assertEqual(new,b'aaNEWzz')
        r['baseline_sha256'],r['modified_sha256']=r['modified_sha256'],r['baseline_sha256']
        r['edits'][0]['old_hex'],r['edits'][0]['new_hex']=r['edits'][0]['new_hex'],r['edits'][0]['old_hex']
        self.assertEqual(patch_bound_bytes(new,r),b'aaOLDzz')

    def test_wrong_source(self):
        with self.assertRaises(ValueError):patch_bound_bytes(b'bbOLDzz',self.record())

    def test_outside_span(self):
        r=self.record();r['allowed_spans']=[[0,2]]
        with self.assertRaises(ValueError):patch_bound_bytes(b'aaOLDzz',r)

    def test_overflow(self):
        r=self.record();r['edits'][0]['new_hex']=b'LONG'.hex()
        with self.assertRaises(ValueError):patch_bound_bytes(b'aaOLDzz',r)

    def test_wrong_old_bytes(self):
        r=self.record();r['edits'][0]['old_hex']=b'BAD'.hex()
        with self.assertRaises(ValueError):patch_bound_bytes(b'aaOLDzz',r)

    def test_overlapping(self):
        r=self.record();r['edits'].append(dict(r['edits'][0]))
        with self.assertRaises(ValueError):patch_bound_bytes(b'aaOLDzz',r)

    def test_wrong_output(self):
        r=self.record();r['modified_sha256']='0'*64
        with self.assertRaises(ValueError):patch_bound_bytes(b'aaOLDzz',r)

    def test_subtitle_revision_exact(self):
        self.assertTrue(name_only_ass('Dialogue: 1,OLD\\Nword','Dialogue: 1,NEW\\Nword',
                                     [dict(previous='OLD',target='NEW')]))

    def test_subtitle_layout_change_rejected(self):
        with self.assertRaises(ValueError):
            name_only_ass('Dialogue: 1,OLD\\Nword','Dialogue: 2,NEWword',[dict(previous='OLD',target='NEW')])

    def test_subtitle_control_injection(self):
        with self.assertRaises(ValueError):
            name_only_ass('OLD','{NEW}',[dict(previous='OLD',target='{NEW}')])

    def profile(self):
        root=Path(__file__).resolve().parents[1]
        return json.loads((root/'locales/zh-CN/proofreading/term-revision-01.json').read_text('utf8'))

    def test_four_user_terms_and_same_encoded_lengths(self):
        terms=self.profile()['terms']
        self.assertEqual({q['previous']:q['target'] for q in terms},
                         {'卡琳兹':'卡林兹','朱丝蒂娜':'朱斯蒂娜','阿蜜拉':'阿米拉','伊佩莉亚':'伊菲利亚'})
        for q in terms:self.assertEqual(len(bytes.fromhex(q['old_hex'])),len(bytes.fromhex(q['new_hex'])))

    def test_all_active_translation_batches_have_no_old_names(self):
        root=Path(__file__).resolve().parents[1]/'locales/zh-CN'
        old=[q['previous'] for q in self.profile()['terms']]
        for path in root.glob('*.json'):
            data=json.loads(path.read_text('utf8'))
            for row in data.get('entries',[]):
                if isinstance(row,dict) and isinstance(row.get('target'),str):
                    for name in old:self.assertNotIn(name,row['target'],str(path)+' '+str(row.get('id')))

    def test_canonical_glossary_has_no_old_names(self):
        text=(Path(__file__).resolve().parents[1]/'GLOSSARY.md').read_text('utf8')
        for q in self.profile()['terms']:
            self.assertNotIn(q['previous'],text);self.assertIn(q['target'],text)

    def test_movie_targets_and_phrase_units_revised(self):
        root=Path(__file__).resolve().parents[1]/'locales/zh-CN'
        for filename in ('movie-dialogue-01.json','movie-dialogue-layout-01.json','movie-story-01.json'):
            text=(root/filename).read_text('utf8')
            for q in self.profile()['terms']:self.assertNotIn(q['previous'],text)
