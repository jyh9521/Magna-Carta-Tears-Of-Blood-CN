import io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_streams import probe

class Process:
    def __init__(self,*args,**kwargs):self.stdin=io.BytesIO();self.returncode=0;self.killed=False
    def communicate(self,timeout):return b'{"streams": []}',b''
    def kill(self):self.killed=True
    def wait(self):return self.returncode

class MovieStreamTests(unittest.TestCase):
    def test_stream_exact_bytes(self):
        with patch('audit_movie_streams.subprocess.Popen',Process):result=probe(io.BytesIO(b'abc'),3,Path('fixture'))
        self.assertTrue(result['full_input']);self.assertEqual(result['fed_bytes'],3);self.assertEqual(result['exit'],0)
    def test_stream_bounded(self):
        with patch('audit_movie_streams.subprocess.Popen',Process):result=probe(io.BytesIO(b'abcEXTRA'),3,Path('fixture'))
        self.assertEqual(result['fed_sha256'],'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    def test_truncated_movie_raises(self):
        with patch('audit_movie_streams.subprocess.Popen',Process):
            with self.assertRaisesRegex(ValueError,'truncated'):probe(io.BytesIO(b'a'),3,Path('fixture'))
    def test_command_packet_count_not_transcode(self):
        with patch('audit_movie_streams.subprocess.Popen',Process):result=probe(io.BytesIO(),0,Path('fixture'))
        self.assertIn('-count_packets',result['command']);self.assertNotIn('-c:v',result['command'])
    def test_metadata_reopened(self):
        with patch('audit_movie_streams.subprocess.Popen',Process):result=probe(io.BytesIO(),0,Path('fixture'))
        self.assertEqual(result['metadata'],{'streams':[]})
    def test_early_pipe_not_complete(self):
        class Broken(Process):
            def __init__(self,*args,**kwargs):
                super().__init__();self.stdin=self
            def write(self,data):raise BrokenPipeError()
            def close(self):pass
        with patch('audit_movie_streams.subprocess.Popen',Broken):result=probe(io.BytesIO(b'abc'),3,Path('fixture'))
        self.assertFalse(result['full_input']);self.assertEqual(result['fed_bytes'],0)

if __name__=='__main__':unittest.main()
