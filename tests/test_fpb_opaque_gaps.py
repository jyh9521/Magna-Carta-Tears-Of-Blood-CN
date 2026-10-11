import sys
import unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('src','lib')]
from localization.text import rewrite_fpb
from translate.fpb import build_fpb,parse_fpb_raw


class Encoder:
    def encode(self,text):return text.encode('ascii')


class GapTests(unittest.TestCase):
    def fixture(self,windows,pool):return build_fpb(bytes(16),windows,pool)
    def test_explicit_zero_leading_prefix_preserved(self):
        b=self.fixture([(5,3,3),(0,6,3)],b'PREabcdef');new,_=rewrite_fpb(b,{5:'long'},Encoder());h,w,p=parse_fpb_raw(new)
        self.assertEqual(p,b'PRElongdef');self.assertEqual(w,[(5,3,4),(0,7,3)]);self.assertEqual(int.from_bytes(h[12:16],'little'),3)
    def test_opaque_internal_gap_and_tail_preserved(self):
        b=self.fixture([(0,0,3),(1,5,3)],b'abc\xff\xfedefTAIL');new,_=rewrite_fpb(b,{0:'LONG',1:'X'},Encoder());_,w,p=parse_fpb_raw(new)
        self.assertEqual(p,b'LONG\xff\xfeXTAIL');self.assertEqual(w,[(0,0,4),(1,6,1)])
    def test_unknown_controls_in_gap_are_opaque(self):
        b=self.fixture([(0,3,3)],b'%q!abc');new,_=rewrite_fpb(b,{0:'X'},Encoder());self.assertEqual(parse_fpb_raw(new)[2],b'%q!X')
    def test_untargeted_view_preserved(self):
        b=self.fixture([(0,2,3),(1,5,3)],b'??abcdef');new,_=rewrite_fpb(b,{1:'LONG'},Encoder());_,w,p=parse_fpb_raw(new);self.assertEqual(p,b'??abcLONG');self.assertEqual(w[0],(0,2,3))
    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):rewrite_fpb(self.fixture([(0,0,4),(1,3,3)],b'abcdef'),{0:'X'},Encoder())
    def test_duplicate_sequence_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):rewrite_fpb(self.fixture([(0,0,3),(0,3,3)],b'abcdef'),{0:'X'},Encoder())
    def test_missing_target_not_inferred_from_gap(self):
        with self.assertRaisesRegex(ValueError,'missing'):rewrite_fpb(self.fixture([(0,2,3)],b'??abc'),{5:'X'},Encoder())


if __name__=='__main__':unittest.main()
