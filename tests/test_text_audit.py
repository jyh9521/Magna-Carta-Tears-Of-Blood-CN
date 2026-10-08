"""Synthetic FPB audit checks; original game input is not required."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "lib")]
from audit_text_resources import inspect_fpb, summarize
from translate.fpb import build_fpb


class TextAuditTests(unittest.TestCase):
    def fpb(self, pool, windows=()):
        return build_fpb(bytes(16), list(windows), pool)

    def test_empty_and_stub(self):
        self.assertEqual(inspect_fpb(bytes(8))["status"], "stub-not-parsed")
        self.assertTrue(inspect_fpb(self.fpb(b""))["partition_backend_eligible"])

    def test_truncated_file(self):
        self.assertEqual(inspect_fpb(b"x")["status"], "parse-error")
        r = inspect_fpb(self.fpb(b"AB")[:-1])
        self.assertFalse(r["roundtrip_identical"])

    def test_partition_and_controls(self):
        r = inspect_fpb(self.fpb(b"A$nB$D04C", [(1, 1, 8)]))
        self.assertTrue(r["partition_backend_eligible"])
        self.assertTrue(r["strict_target_validator_eligible"])
        self.assertEqual(r["tokens"], {"$D04": 1, "$n": 1})

    def test_overlap_rejected(self):
        r = inspect_fpb(self.fpb(b"ABCD", [(1, 1, 3), (2, 2, 2)]))
        self.assertIn("overlap-or-backward-order", r["partition_reasons"])

    def test_gap_and_duplicate(self):
        r = inspect_fpb(self.fpb(b"ABCDE", [(1, 1, 1), (1, 3, 2)]))
        self.assertEqual(r["partition_reasons"], ["duplicate-sequence", "gap"])
        self.assertEqual(r["view_gaps"][0]["length"], 1)

    def test_window_splits_control(self):
        r = inspect_fpb(self.fpb(b"A$nB", [(1, 2, 2)]))
        self.assertEqual(r["tokens"], {"$n": 1})
        self.assertEqual(r["window_control_error_sequences"], [0])
        self.assertFalse(r["strict_target_validator_eligible"])

    def test_invalid_encoding_is_not_replaced(self):
        r = inspect_fpb(self.fpb(b"A\xff"))
        self.assertFalse(r["cp949_pool"])
        self.assertEqual(r["decode_error_byte"], 1)

    def test_window_splits_multibyte(self):
        r = inspect_fpb(self.fpb("가".encode("cp949"), [(1, 1, 1)]))
        self.assertTrue(r["cp949_pool"])
        self.assertEqual(r["window_decode_error_sequences"], [0, 1])
        self.assertFalse(r["strict_target_validator_eligible"])

    def test_unknown_markers_and_raw_controls(self):
        r = inspect_fpb(self.fpb(b"$Q\x00"))
        self.assertFalse(r["strict_target_validator_eligible"])
        self.assertEqual(r["unknown_structures"], [{"character_offset": 0, "codepoint": "U+0024"}])
        self.assertEqual(r["raw_control_codepoints"], {"U+0000": 1})

    def test_character_tiers_and_no_dialogue_export(self):
        r = inspect_fpb(self.fpb("A가。<InternalKey>".encode("cp949")))
        self.assertEqual(r["character_tiers"]["observed-hangul-byte-range"], 1)
        self.assertEqual(r["character_tiers"]["other-cp949-not-covered-by-poc-backend"], 1)
        self.assertEqual(r["tokens"], {"markup": 1})
        self.assertNotIn("InternalKey", str(r))

    def test_summary(self):
        result = summarize({"a": inspect_fpb(self.fpb(b"A$n")), "b": inspect_fpb(bytes(8))})
        self.assertEqual(result["files"], 2)
        self.assertEqual(result["counts"]["whole_file_static_preconditions_pass"], 1)
        self.assertEqual(result["tokens"], {"$n": 1})


if __name__ == "__main__":
    unittest.main()
