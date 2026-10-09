import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_movie_frames import frame_command, timestamp, reference_cues, validate_evidence


class MovieFrameTests(unittest.TestCase):
    def test_streaming_command(self):
        cmd = frame_command('ffmpeg', Path('fixture'))
        self.assertIn('pipe:0', cmd)
        self.assertIn('fps=1/8,scale=384:-1,tile=6x6', cmd)
        self.assertNotIn('-y', cmd)
    def test_interval_bounds(self):
        for v in (0, 61, 1.5, '8'):
            with self.assertRaises(ValueError): frame_command('ffmpeg', Path('fixture'), v)
    def test_width_bounds(self):
        with self.assertRaises(ValueError): frame_command('ffmpeg', Path('fixture'), width=1)
    def test_timestamp(self):
        self.assertEqual(timestamp('1:02:03.04'), 372304)
    def test_invalid_timestamp(self):
        for t in ('0:60:00.00', '0:00:60.00', '0:0:0.0', 'text'):
            with self.assertRaises(ValueError): timestamp(t)
    def test_reference_is_not_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'fixture.ass'
            p.write_text('Dialogue: 0,0:00:01.00,0:00:02.00,Style,,0,0,0,,{\\pos(1,2)}Hello, world!\n', encoding='utf8')
            r = reference_cues(p, 'korean')[0]
            self.assertEqual(r['text'], '{\\pos(1,2)}Hello, world!')
            self.assertFalse(r['original_verbatim_verified'])
            self.assertFalse(r['editable'])
    def test_reference_duration(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'fixture.ass'
            p.write_text('Dialogue: 0,0:00:02.00,0:00:01.00,Style,,0,0,0,,Text\n', encoding='utf8')
            with self.assertRaises(ValueError): reference_cues(p, 'korean')
    def test_missing_inventory(self):
        with self.assertRaises(ValueError): validate_evidence([], [], [{'path':'/A.SFD;1'}])
    def test_duplicate_index(self):
        with self.assertRaises(ValueError): validate_evidence([{'movie':'A'}, {'movie':'A'}], [], [])
    def test_missing_review(self):
        with self.assertRaises(ValueError): validate_evidence([{'movie':'A'}], [], [{'path':'/A.SFD;1'}])


if __name__ == '__main__': unittest.main()
