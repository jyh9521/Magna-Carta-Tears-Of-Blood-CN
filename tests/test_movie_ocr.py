import io
import sys
import tempfile
import unittest
from pathlib import Path
from fractions import Fraction

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_ocr import frame_reference, read_frame, validate_ocr, consecutive_cues, MovieDecodeFailure


class MovieOcrTests(unittest.TestCase):
    def reference(self, text=None):
        if text is None:text='#tb 0: 1/30\n#dimensions 0: 2x2\n0, 0, 0, 1, 6, '+('a'*64)+'\n'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frames';p.write_text(text,'ascii');return frame_reference(p)
    def test_reference_complete(self):
        tb,dims,rs=self.reference();self.assertEqual((tb,dims,rs[0]['size']),(Fraction(1,30),(2,2),6))
    def test_missing_timebase(self):
        with self.assertRaises(ValueError):self.reference('#dimensions 0: 2x2\n0,0,0,1,6,'+'a'*64)
    def test_no_frames(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n')
    def test_bad_hash(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n0,0,0,1,6,broken')
    def test_bad_shape(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n0,0,0,1,6')
    def test_wrong_pixel_size(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n0,0,0,1,12,'+'a'*64)
    def test_odd_dimensions(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 3x2\n0,0,0,1,9,'+'a'*64)
    def test_zero_dimensions(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 0x2\n0,0,0,1,6,'+'a'*64)
    def test_zero_duration(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n0,0,0,0,6,'+'a'*64)
    def test_nonmonotonic_pts(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n0,1,1,1,6,'+'a'*64+'\n0,0,0,1,6,'+'b'*64)
    def test_other_stream_rejected(self):
        with self.assertRaises(ValueError):self.reference('#tb 0: 1/30\n#dimensions 0: 2x2\n1,0,0,1,6,'+'a'*64)
    def test_full_frame_read(self):self.assertEqual(read_frame(io.BytesIO(b'abcdefx'),6),b'abcdef')
    def test_partial_eof_retained(self):self.assertEqual(read_frame(io.BytesIO(b'ab'),6),b'ab')
    def test_zero_read_size(self):
        with self.assertRaises(ValueError):read_frame(io.BytesIO(b''),0)
    def box(self):return [[0,0],[20,0],[20,10],[0,10]]
    def test_ocr_record(self):
        r=validate_ocr(['text'],[.9],[self.box()],20,10)[0];self.assertFalse(r['editable']);self.assertFalse(r['original_verbatim_verified'])
    def test_empty_ocr_is_not_absence_proof(self):self.assertEqual(validate_ocr(None,None,None,20,10),[])
    def test_length_mismatch(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[],[self.box()],20,10)
    def test_nan_score(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[float('nan')],[self.box()],20,10)
    def test_negative_score(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[-.1],[self.box()],20,10)
    def test_score_above_one(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[1.1],[self.box()],20,10)
    def test_box_bounds(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[.9],[self.box()],10,10)
    def test_non_string(self):
        with self.assertRaises(ValueError):validate_ocr([1],[.9],[self.box()],20,10)
    def test_box_shape(self):
        with self.assertRaises(ValueError):validate_ocr(['x'],[.9],[[[0,0]]],20,10)
    def test_nonfinite_box(self):
        b=self.box();b[0][0]=float('inf')
        with self.assertRaises(ValueError):validate_ocr(['x'],[.9],[b],20,10)
    def row(self,index,text='A',pts=None):
        return dict(index=index,pts=index if pts is None else pts,duration=1,ocr=[dict(text=text)] if text else [],evidence_image='frame.png')
    def test_exact_runs(self):
        cs=consecutive_cues([self.row(0),self.row(1)],Fraction(1,30));self.assertEqual(len(cs),1);self.assertEqual(cs[0]['end_pts'],2)
    def test_text_change_separates(self):self.assertEqual(len(consecutive_cues([self.row(0),self.row(1,'B')],Fraction(1,30))),2)
    def test_fuzzy_similarity_not_merged(self):self.assertEqual(len(consecutive_cues([self.row(0,'word'),self.row(1,'w0rd')],Fraction(1,30))),2)
    def test_empty_separates(self):self.assertEqual(len(consecutive_cues([self.row(0),self.row(1,''),self.row(2)],Fraction(1,30))),2)
    def test_pts_gap_separates(self):self.assertEqual(len(consecutive_cues([self.row(0),self.row(1,pts=3)],Fraction(1,30))),2)
    def test_unverified_cues(self):
        r=consecutive_cues([self.row(0)],Fraction(1,30))[0];self.assertFalse(r['original_verbatim_verified']);self.assertFalse(r['temporal_boundary_reviewed']);self.assertFalse(r['editable'])
    def test_empty_movie_cues(self):self.assertEqual(consecutive_cues([],Fraction(1,30)),[])
    def test_decode_failure_type(self):self.assertIsInstance(MovieDecodeFailure('fixture'),ValueError)


if __name__=='__main__':unittest.main()
