import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_ocr import decoder_outcome
from reconcile_movie_ocr import verify_frames

DTS='[rawvideo @ 000001b5bad16900] Application provided invalid, non monotonically increasing dts to muxer in stream 0: 159 >= 159\n'


class MovieOutcomeTests(unittest.TestCase):
    def test_clean(self):self.assertTrue(decoder_outcome(0,'',3,3)['complete'])
    def test_exact_muxer(self):
        x=decoder_outcome(0,DTS,3,3);self.assertTrue(x['complete']);self.assertTrue(x['diagnostic_retained']);self.assertFalse(x['timestamps_rewritten'])
    def test_multiple(self):self.assertTrue(decoder_outcome(0,DTS+DTS.replace('159','2913'),3,3)['complete'])
    def test_nonzero(self):self.assertFalse(decoder_outcome(1,DTS,3,3)['complete'])
    def test_short(self):self.assertFalse(decoder_outcome(0,DTS,2,3)['complete'])
    def test_extra(self):self.assertFalse(decoder_outcome(0,DTS,4,3)['complete'])
    def test_empty(self):self.assertFalse(decoder_outcome(0,'',0,0)['complete'])
    def test_decoder_error(self):self.assertFalse(decoder_outcome(0,DTS+'[mpeg2video @ 123] corrupt frame\n',3,3)['complete'])
    def test_other_muxer(self):self.assertFalse(decoder_outcome(0,DTS.replace('rawvideo','framehash'),3,3)['complete'])
    def test_other_stream(self):self.assertFalse(decoder_outcome(0,DTS.replace('stream 0','stream 1'),3,3)['complete'])
    def test_other_message(self):self.assertFalse(decoder_outcome(0,'warning: duplicate timestamp',3,3)['complete'])
    def test_contradictory_values(self):self.assertFalse(decoder_outcome(0,DTS.replace('159 >= 159','158 >= 159'),3,3)['complete'])


class FrameReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.expected=[dict(index=i,dts=i,pts=i,duration=1,size=6,sha256='a'*64) for i in range(2)]
        self.rows=[dict(x,ocr=[],frame_identity_verified=True,absence_of_text_verified=False,
                        ocr_reused_from_previous=i>0) for i,x in enumerate(self.expected)]
    def test_complete(self):
        s=verify_frames(self.rows,self.expected,(2,2));self.assertEqual(s['native_frame_hash_matches'],2);self.assertEqual(s['ocr_calls'],1)
    def test_no_mutation(self):
        old=copy.deepcopy(self.rows);verify_frames(self.rows,self.expected,(2,2));self.assertEqual(self.rows,old)
    def test_short(self):
        with self.assertRaises(ValueError):verify_frames(self.rows[:1],self.expected,(2,2))
    def test_hash(self):
        self.rows[1]['sha256']='b'*64
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_time(self):
        self.rows[1]['pts']=99
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_false_identity(self):
        self.rows[0]['frame_identity_verified']=False
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_false_absence_claim(self):
        self.rows[0]['absence_of_text_verified']=True
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_reuse_first(self):
        self.rows[0]['ocr_reused_from_previous']=True
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_reuse_different_frame(self):
        self.rows[1]['sha256']=self.expected[1]['sha256']='b'*64
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))
    def test_nonverbatim_flag(self):
        self.rows[0]['ocr']=[dict(text='a',confidence=1,box=[[0,0],[1,0],[1,1],[0,1]],original_verbatim_verified=True,editable=False)]
        with self.assertRaises(ValueError):verify_frames(self.rows,self.expected,(2,2))


if __name__=='__main__':unittest.main()
