import json
from pathlib import Path
import struct
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from ui_punctuation import single_clause_period
from patch_option_periods import patch_options
from repair_detection_state import restore_memory, BYPASS
from font_poc import digest


class OptionPeriodTests(unittest.TestCase):
    def test_current_review_targets(self):
        profile = json.loads((ROOT/'locales/zh-CN/proofreading/option-punctuation-review.json').read_text('utf8'))
        self.assertEqual(len(profile['entries']), 43)
        for q in profile['entries']:
            batch = json.loads((ROOT/q['batch']).read_text('utf8'))
            actual = next(e for e in batch['entries'] if e['id'] == q['id'])
            self.assertEqual(actual['target'], q['target'])
            self.assertTrue(single_clause_period(q['previous_target']))
            self.assertEqual(q['previous_target'][:-1], q['target'])

    def test_other_punctuation_retained(self):
        for text in ['不，不乘坐。', '说明：保存。', '选择、确定。', '获得“流派”。', '物品(PS2)。', '好。再来。', '稍等……。']:
            self.assertFalse(single_clause_period(text), text)

    def test_controls_and_decimal(self):
        self.assertTrue(single_clause_period('增加$n1.25倍。'))

    def test_no_empty_suffix(self):
        self.assertFalse(single_clause_period('。'))

    def test_native_records_preserved(self):
        class Encoder:
            def encode_characters(self, text): return text.encode('utf8')
        def fpb(a, b):
            return struct.pack('<8I', 2, 7, 0, len(a), 9, len(a), len(b), len(a+b))+a+b+b'TAIL'
        original = fpb(b'a', b'b')
        baseline = fpb('购买。'.encode(), '你好。'.encode())
        review = dict(status='reviewed', role='option', native_key=7, source_sha256=digest(b'a'), previous_target='购买。', target='购买')
        output = patch_options(original, baseline, [review], Encoder())
        self.assertEqual(output, fpb('购买'.encode(), '你好。'.encode()))
        review['source_sha256'] = '0'*64
        with self.assertRaises(ValueError): patch_options(original, baseline, [review], Encoder())


class DetectionStateTests(unittest.TestCase):
    def fixture(self):
        memory = bytearray(0x400000)
        originals = b''.join(struct.pack('<I', q) for q in [0x8e240268,0x8c830220,0x8c900268,0x8f868258])
        offsets = {a: j*4 for j, a in enumerate(BYPASS)}
        image = SimpleNamespace(blob=originals, to_offset=offsets.__getitem__)
        for a, word in BYPASS.items(): struct.pack_into('<I', memory, a, word)
        return memory, image

    def test_latch_off_does_not_imply_code_restored(self):
        memory, image = self.fixture()
        result, proof = restore_memory(memory, image)
        self.assertEqual(sum(q['bypass'] for q in proof), 4)
        allowed = {a+i for a in BYPASS for i in range(4)}
        self.assertTrue(all(a == b or j in allowed for j, (a, b) in enumerate(zip(memory, result))))
        self.assertEqual(restore_memory(result, image)[0], result)

    def test_unknown_instruction_rejected(self):
        memory, image = self.fixture()
        struct.pack_into('<I', memory, next(iter(BYPASS)), 0xdeadbeef)
        with self.assertRaises(ValueError): restore_memory(memory, image)


if __name__ == '__main__': unittest.main()
