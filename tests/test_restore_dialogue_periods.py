import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from restore_dialogue_periods import restore_fields
import font_poc as core


class Encoder:
    def encode_characters(self, text):
        return text.encode('utf8')


class RestorePeriodsTests(unittest.TestCase):
    def setUp(self):
        self.original = b'a' + bytes(15)
        self.baseline = b'x' + bytes(15)
        self.entry = dict(offset=0, slot_bytes=16, slot_sha256=core.digest(self.original), source_sha256=core.digest(b'a'), source_bytes=1)
        self.review = dict(id='sample', status='reviewed', role='narrative', source_sha256=core.digest(b'a'), previous_target='x', target='x。')

    def run_restore(self):
        with patch('restore_dialogue_periods.source_text', return_value='a'), patch('restore_dialogue_periods.control_policy', return_value=None), patch('restore_dialogue_periods.encode_target', side_effect=lambda enc, e, t: enc.encode_characters(t)):
            return restore_fields(self.original, self.baseline, [(self.entry, self.review)], Encoder())

    def test_restore_and_preserve_tail(self):
        result, proof = self.run_restore()
        self.assertEqual(result, 'x。'.encode() + bytes(12))
        self.assertEqual(len(proof), 1)

    def test_reject_ui(self):
        self.review['role'] = 'ui'
        with self.assertRaises(ValueError): self.run_restore()

    def test_reject_wrong_baseline(self):
        self.baseline = b'y' + bytes(15)
        with self.assertRaises(ValueError): self.run_restore()

    def test_reject_other_content_change(self):
        self.review['target'] = 'y。'
        with self.assertRaises(ValueError): self.run_restore()

    def test_reject_overflow(self):
        self.entry['slot_bytes'] = 3
        with self.assertRaises(ValueError): self.run_restore()
