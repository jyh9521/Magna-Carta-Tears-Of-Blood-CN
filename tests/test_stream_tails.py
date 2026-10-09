import sys,struct,zlib
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_tails import prefix_frames,manifest_rows
class StreamTailTests(unittest.TestCase):
    def frame(self,data=b'abc'):
        c=zlib.compress(data);return struct.pack('<II',len(data),len(c))+c
    def test_complete(self):
        data,row=prefix_frames(self.frame());self.assertEqual(data,b'abc');self.assertTrue(row['complete_framing'])
    def test_tail_preserved(self):
        data,row=prefix_frames(self.frame()+b'x');self.assertEqual(data,b'abc');self.assertEqual(row['remaining_bytes'],1)
    def test_overrun(self):self.assertEqual(prefix_frames(struct.pack('<II',10,100)+b'xx')[1]['prefix_end'],0)
    def test_bad_length(self):
        b=self.frame();b=struct.pack('<I',4)+b[4:];self.assertEqual(prefix_frames(b)[0],b'')
    def test_junk_stream(self):self.assertEqual(prefix_frames(struct.pack('<II',1,2)+b'xx')[0],b'')
    def test_manifest(self):self.assertEqual(manifest_rows(b'AFSLINEARFileIndex\r\n0\r\n0001\r\n12\r\n'),{'0001':12})
    def test_duplicate(self):
        with self.assertRaises(ValueError):manifest_rows(b'AFSLINEARFileIndex\r\n0\r\na\r\n1\r\na\r\n2\r\n')
    def test_bad_header(self):
        with self.assertRaises(ValueError):manifest_rows(b'bad\r\n0\r\n')
