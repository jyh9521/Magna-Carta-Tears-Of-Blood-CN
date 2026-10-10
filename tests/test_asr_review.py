import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from review_movie_asr import folded,source_index,overlaps,review


class ASRReviewTests(unittest.TestCase):
    def test_whitespace_only(self):self.assertEqual(folded(' a\n b\t'),'ab')
    def test_controls_not_removed(self):self.assertEqual(folded('a $n b'),'a$nb')
    def test_punctuation_not_removed(self):self.assertNotEqual(folded('a?'),folded('a.'))
    def test_case_not_normalized(self):self.assertNotEqual(folded('$N'),folded('$n'))
    def test_exact_and_folded(self):
        c=dict(resources=[dict(entries=[dict(id='x',source_sha256='h',decode='strict',references={'ko-KR':'a b'})])])
        e,s=source_index(c);self.assertIn('a b',e);self.assertIn('ab',s);self.assertNotIn('ab',e)
    def test_failed_not_invented(self):
        c=dict(resources=[dict(entries=[dict(id='x',decode='failed',references={'ko-KR':'a'})])])
        e,s=source_index(c);self.assertFalse(e);self.assertFalse(s)
    def test_duplicates_rejected(self):
        c=dict(resources=[dict(entries=[dict(id='x',decode='failed')]*2)])
        with self.assertRaises(ValueError):source_index(c)
    def test_touching_not_overlap(self):self.assertFalse(overlaps(1,2,dict(start_centiseconds=200,end_centiseconds=300)))
    def test_overlap(self):self.assertTrue(overlaps(1,2,dict(start_centiseconds=150,end_centiseconds=300)))
    def test_unknown_requires_listen(self):
        r=review(dict(id=1,start=1,end=2,text='a',uncertainty_flags=[]),{}, {},[])
        self.assertTrue(r['listen_review_required']);self.assertFalse(r['targeted_ocr_requested'])
    def test_uncertain_requests_ocr(self):
        r=review(dict(id=1,start=1,end=2,text='a',uncertainty_flags=['low']),{}, {},[])
        self.assertTrue(r['targeted_ocr_requested']);self.assertFalse(r['original_verbatim_verified'])
    def test_exact_is_not_dedup_approval(self):
        r=review(dict(id=1,start=1,end=2,text='a',uncertainty_flags=[]),{'a':[dict(id='source',source_sha256='h')]},{'a':[dict(id='source',source_sha256='h')]},[])
        self.assertFalse(r['source_dedup_verified']);self.assertFalse(r['spoken_equals_displayed_verified']);self.assertFalse(r['editable'])
    def test_ass_is_timeline_only(self):
        cue=dict(id='ASS/korean/x',source_sha256='h',region='korean',start_centiseconds=100,end_centiseconds=200)
        r=review(dict(id=1,start=1,end=2,text='spoken',uncertainty_flags=[]),{}, {},[cue])
        self.assertEqual(len(r['upstream_timeline_links']),1);self.assertFalse(r['spoken_equals_displayed_verified'])


if __name__=='__main__':unittest.main()
