import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_decode import frame_summary


class MovieDecodeTests(unittest.TestCase):
    def parse(self,rows,header='#tb 0: 1/30\n'):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frames';p.write_text(header+rows,'ascii');return frame_summary(p)
    def row(self,pts=0,duration=1,size=1024,digest='a'*64):return f'0, {pts}, {pts}, {duration}, {size}, {digest}\n'
    def test_frame(self):self.assertEqual(self.parse(self.row())['frames'],1)
    def test_timeline(self):self.assertAlmostEqual(self.parse(self.row()+self.row(1))['timeline_seconds'],2/30)
    def test_offset_pts(self):self.assertAlmostEqual(self.parse(self.row(99))['timeline_seconds'],1/30)
    def test_comment(self):self.assertEqual(self.parse('# comment\n'+self.row())['frames'],1)
    def test_no_timebase(self):
        with self.assertRaises(ValueError):self.parse(self.row(),header='')
    def test_empty(self):
        with self.assertRaises(ValueError):self.parse('')
    def test_bad_digest(self):
        with self.assertRaises(ValueError):self.parse(self.row(digest='bad'))
    def test_nonmonotonic(self):
        with self.assertRaises(ValueError):self.parse(self.row(1)+self.row(0))
    def test_duration(self):
        with self.assertRaises(ValueError):self.parse(self.row(duration=0))
    def test_size(self):
        with self.assertRaises(ValueError):self.parse(self.row(size=0))
    def test_stream(self):
        with self.assertRaises(ValueError):self.parse(self.row().replace('0,','1,',1))
    def test_row_shape(self):
        with self.assertRaises(ValueError):self.parse('0, 1\n')


if __name__=='__main__':unittest.main()
