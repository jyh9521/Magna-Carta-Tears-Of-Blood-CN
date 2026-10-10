import sys,unittest,tempfile,hashlib
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_spots import targets,verify_saved_frames


class MovieSpotTests(unittest.TestCase):
    def setUp(self):
        self.frames=[dict(index=i,pts=i) for i in range(10)]
    def test_midpoint(self):
        x=targets([dict(segment_id=1,start=2,end=4,targeted_ocr_requested=True)],self.frames,Fraction(1))
        self.assertEqual(x[0]['frame_index'],3)
    def test_nonrequested_skipped(self):
        self.assertEqual(targets([dict(targeted_ocr_requested=False)],self.frames,Fraction(1)),[])
    def test_fractional_timebase(self):
        x=targets([dict(segment_id=1,start=0.05,end=0.15,targeted_ocr_requested=True)],self.frames,Fraction(1,30))
        self.assertEqual(x[0]['frame_index'],3)
    def test_tie_uses_first(self):
        x=targets([dict(segment_id=1,start=2,end=3,targeted_ocr_requested=True)],self.frames,Fraction(1))
        self.assertEqual(x[0]['frame_index'],2)
    def test_duplicate_pts_preserved(self):
        self.frames[3]['pts']=2
        x=targets([dict(segment_id=1,start=2,end=2,targeted_ocr_requested=True)],self.frames,Fraction(1))
        self.assertEqual(x[0]['frame_index'],2)
    def test_invalid_time(self):
        with self.assertRaises(ValueError):targets([dict(segment_id=1,start=-1,end=2,targeted_ocr_requested=True)],self.frames,Fraction(1))
    def test_missing_frames(self):
        with self.assertRaises(ValueError):targets([],[],Fraction(1))
    def test_bad_timebase(self):
        with self.assertRaises(ValueError):targets([],self.frames,Fraction(0))
    def test_explicit_scope(self):
        x=targets([dict(segment_id=1,start=2,end=4,targeted_ocr_requested=True)],self.frames,Fraction(1))
        self.assertIn('not-subtitle-boundary-proof',x[0]['selection'])


class SavedSpotTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.folder=Path(self.t.name)
        (self.folder/'frame-0.png').write_bytes(b'fixture')
        self.expected=[dict(index=0,pts=0,sha256='a'*64)]
        self.rows=[dict(self.expected[0],image='frame-0.png',image_sha256=hashlib.sha256(b'fixture').hexdigest(),
                        ocr=[],absence_of_text_verified=False,original_verbatim_verified=False)]
    def tearDown(self):self.t.cleanup()
    def test_valid(self):verify_saved_frames(self.rows,self.expected,self.folder,(2,2))
    def test_source_mismatch(self):
        self.rows[0]['sha256']='b'*64
        with self.assertRaises(ValueError):verify_saved_frames(self.rows,self.expected,self.folder,(2,2))
    def test_image_hash(self):
        (self.folder/'frame-0.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):verify_saved_frames(self.rows,self.expected,self.folder,(2,2))
    def test_image_path(self):
        self.rows[0]['image']='../frame.png'
        with self.assertRaises(ValueError):verify_saved_frames(self.rows,self.expected,self.folder,(2,2))
    def test_false_claim(self):
        self.rows[0]['original_verbatim_verified']=True
        with self.assertRaises(ValueError):verify_saved_frames(self.rows,self.expected,self.folder,(2,2))
    def test_count(self):
        with self.assertRaises(ValueError):verify_saved_frames([],self.expected,self.folder,(2,2))


if __name__=='__main__':unittest.main()
