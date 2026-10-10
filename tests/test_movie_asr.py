import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_asr import wave_identity,segment_record,inventory


def segment(**kw):
    return dict(dict(start=1,end=2,text='source',avg_logprob=-0.2,no_speech_prob=0.1,
                     compression_ratio=1.2,words=[dict(start=1,end=2,word='source',probability=0.9)]),**kw)


class ASRSegmentTests(unittest.TestCase):
    def test_good(self):self.assertEqual(segment_record(segment(),3)['uncertainty_flags'],[])
    def test_low_average(self):self.assertIn('low-average-log-probability',segment_record(segment(avg_logprob=-1),3)['uncertainty_flags'])
    def test_no_speech(self):self.assertIn('high-no-speech-probability',segment_record(segment(no_speech_prob=0.8),3)['uncertainty_flags'])
    def test_compressed(self):self.assertIn('high-compression-ratio',segment_record(segment(compression_ratio=3),3)['uncertainty_flags'])
    def test_word_low(self):
        x=segment();x['words'][0]['probability']=0.2;self.assertIn('low-word-probability',segment_record(x,3)['uncertainty_flags'])
    def test_no_words(self):self.assertEqual(segment_record(segment(words=None),3)['uncertainty_flags'],[])
    def test_no_mutation(self):
        x=segment();before=copy.deepcopy(x);y=segment_record(x,3);self.assertEqual(x,before);self.assertFalse(y['editable']);self.assertFalse(y['original_verbatim_verified'])
    def test_negative(self):
        with self.assertRaises(ValueError):segment_record(segment(start=-1),3)
    def test_reversed(self):
        with self.assertRaises(ValueError):segment_record(segment(start=3),3)
    def test_exceeds_audio(self):
        with self.assertRaises(ValueError):segment_record(segment(end=4),3)
    def test_rounding_tolerance(self):self.assertEqual(segment_record(segment(end=3.05),3)['end'],3.05)
    def test_nan(self):
        for key in ('start','end','avg_logprob','no_speech_prob','compression_ratio'):
            with self.subTest(key=key),self.assertRaises(ValueError):segment_record(segment(**{key:float('nan')}),3)
    def test_probability(self):
        with self.assertRaises(ValueError):segment_record(segment(no_speech_prob=1.1),3)
    def test_text(self):
        with self.assertRaises(ValueError):segment_record(segment(text=3),3)
    def test_negative_compression(self):
        with self.assertRaises(ValueError):segment_record(segment(compression_ratio=-1),3)
    def test_word_nan(self):
        x=segment();x['words'][0]['probability']=float('nan')
        with self.assertRaises(ValueError):segment_record(x,3)
    def test_word_time(self):
        x=segment();x['words'][0]['end']=4
        with self.assertRaises(ValueError):segment_record(x,3)
    def test_word_probability(self):
        x=segment();x['words'][0]['probability']=-0.1
        with self.assertRaises(ValueError):segment_record(x,3)


class AudioIdentityTests(unittest.TestCase):
    def make(self,path,rate=16000,channels=1,width=2,data=b'\0\0'*10):
        with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(data)
    def test_pcm(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'audio.wav';self.make(p);s=wave_identity(p);self.assertEqual(s['samples'],10);self.assertEqual(s['duration_seconds'],10/16000)
    def test_wrong_rate(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'audio.wav';self.make(p,rate=48000)
            with self.assertRaises(ValueError):wave_identity(p)
    def test_stereo(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'audio.wav';self.make(p,channels=2)
            with self.assertRaises(ValueError):wave_identity(p)
    def test_wrong_width(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'audio.wav';self.make(p,width=1)
            with self.assertRaises(ValueError):wave_identity(p)
    def test_empty(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'audio.wav';self.make(p,data=b'')
            with self.assertRaises(ValueError):wave_identity(p)


class MovieInventoryTests(unittest.TestCase):
    def fixture(self):
        s=[dict(path=f'/MOVIE/{i}.SFD;1',source_sha256=str(i)) for i in range(46)]
        p=[dict(x,exit=0,metadata=dict(streams=[dict(codec_type='audio')])) for x in s]
        return s,p
    def run_inventory(self,s,p):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'decoded.json';b=Path(t)/'probe.json';a.write_text(json.dumps(s));b.write_text(json.dumps(p));return inventory(a,b)
    def test_all(self):
        s,p=self.fixture();self.assertEqual(len(self.run_inventory(s,p)),46)
    def test_silent(self):
        s,p=self.fixture();p[0]['metadata']['streams']=[];self.assertEqual(self.run_inventory(s,p)[0]['audio_streams'],0)
    def test_multiple_requires_selection(self):
        s,p=self.fixture();p[0]['metadata']['streams']*=2
        with self.assertRaises(ValueError):self.run_inventory(s,p)
    def test_hash(self):
        s,p=self.fixture();p[0]['source_sha256']='wrong'
        with self.assertRaises(ValueError):self.run_inventory(s,p)
    def test_duplicate(self):
        s,p=self.fixture();p[0]=p[1]
        with self.assertRaises(ValueError):self.run_inventory(s,p)
    def test_bad_exit(self):
        s,p=self.fixture();p[0]['exit']=1
        with self.assertRaises(ValueError):self.run_inventory(s,p)
    def test_count(self):
        s,p=self.fixture()
        with self.assertRaises(ValueError):self.run_inventory(s[:-1],p)


if __name__=='__main__':unittest.main()
