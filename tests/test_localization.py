"""Asset-free checks for mapped encoding, controls, FPB growth and fixed fields."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "lib"), str(ROOT / "tools")]
from localization.text import MappedEncoder, protected_tokens, validate_target, rewrite_fpb, rewrite_fixed_slot
from translate.fpb import build_fpb, parse_fpb_raw
from build_locale import build, estimate_widths, load_config, patch_font
from research_inventory import font_data


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.map = [{"character": "测", "bytes": "b0a1", "glyph": 317},
                    {"character": "试", "bytes": "b0a2", "glyph": 318}]
        self.encoder = MappedEncoder(self.map)

    def test_mixed_ascii_and_mapped(self):
        self.assertEqual(self.encoder.encode("测试$n123ABC"), bytes.fromhex("b0a1b0a2") + b"$n123ABC")

    def test_reordering_map_does_not_remap(self):
        self.assertEqual(self.encoder.encode("测试"), MappedEncoder(self.map[::-1]).encode("测试"))

    def test_missing_character(self):
        with self.assertRaises(ValueError):
            self.encoder.encode("中文")

    def test_duplicate_character(self):
        with self.assertRaises(ValueError):
            MappedEncoder(self.map + [self.map[0]])

    def test_duplicate_code_and_glyph(self):
        with self.assertRaises(ValueError):
            MappedEncoder([self.map[0], {"character": "另", "bytes": "b0a1", "glyph": 317}])

    def test_map_outside_observed_range(self):
        for code in ("b041", "c9a1", "a1a6", "00a1"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                MappedEncoder([{"character": "测", "bytes": code, "glyph": 317}])

    def test_map_index_mismatch(self):
        with self.assertRaises(ValueError):
            MappedEncoder([{"character": "测", "bytes": "b0a1", "glyph": 318}])

    def test_new_row_and_last_slot(self):
        encoder = MappedEncoder([{"character": "测", "bytes": "b1a1", "glyph": 411},
                                 {"character": "试", "bytes": "c8fe", "glyph": 2666}])
        self.assertEqual(encoder.encode("测试"), bytes.fromhex("b1a1c8fe"))

    def test_exact_coverage(self):
        self.encoder.validate_coverage(["测试"])
        for targets in (["测"], ["测试中文"]):
            with self.assertRaises(ValueError):
                self.encoder.validate_coverage(targets)

    def test_token_add_drop_change_and_order_reject(self):
        source = "$D04$n%s{0}<UI>"
        validate_target(source, "测试" + source)
        for target in (source + "$n", source.replace("$n", ""), source.replace("$D04", "$D06"),
                       "$n$D04%s{0}<UI>"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                validate_target(source, target)

    def test_unknown_markers_reject(self):
        for text in ("$X04", "$D004", "$", "%q", "<未确认>", "{name}", ">"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                protected_tokens(text)

    def test_known_printf_and_markup(self):
        text = "%2$s %% %.2f {1} <UI name='x'></UI>$D20$n"
        self.assertEqual(protected_tokens(text), ["%2$s", "%%", "%.2f", "{1}", "<UI name='x'>", "</UI>", "$D20", "$n"])

    def test_nul_newline_and_empty_reject(self):
        for target in ("", "测\0", "测\n试", "\t"):
            with self.assertRaises(ValueError):
                validate_target("A", target)

    def test_fpb_growth_and_untargeted_view(self):
        original = build_fpb(bytes(16), [(1, 1, 4), (2, 5, 1)], b"A" + b"B$nC" + b"D")
        after, report = rewrite_fpb(original, {0: "测试测试", 1: "测$n试"}, self.encoder)
        header, windows, pool = parse_fpb_raw(after)
        self.assertEqual(struct.unpack_from("<I", header, 12)[0], 8)
        self.assertEqual(windows, [(1, 8, 6), (2, 14, 1)])
        self.assertEqual(pool[-1:], b"D")
        self.assertGreater(len(after), len(original))

    def test_fpb_overlap_reject(self):
        original = build_fpb(bytes(16), [(1, 1, 3), (2, 2, 2)], b"ABCD")
        with self.assertRaises(ValueError):
            rewrite_fpb(original, {0: "测"}, self.encoder)

    def test_fpb_missing_sequence_reject(self):
        original = build_fpb(bytes(16), [], b"A")
        with self.assertRaises(ValueError):
            rewrite_fpb(original, {1: "测"}, self.encoder)

    def slot_fixture(self, capacity=8):
        slot = b"A".ljust(capacity, b"\0")
        blob = struct.pack("<III", 1, 2, 176) + slot
        profile = {"record_count": 1, "kind": 2, "header_size": 8,
                   "record_size": 4 + capacity, "text_offset": 4, "text_bytes": capacity,
                   "record_index": 0, "record_id": 176, "expected_slot_sha256": hashlib.sha256(slot).hexdigest()}
        return blob, profile

    def test_fixed_slot_preserves_id_size_and_nul(self):
        blob, profile = self.slot_fixture()
        after, report = rewrite_fixed_slot(blob, profile, "测试", self.encoder)
        self.assertEqual(len(blob), len(after))
        self.assertEqual(blob[:12], after[:12])
        self.assertEqual(after[12:], bytes.fromhex("b0a1b0a2") + bytes(4))

    def test_fixed_slot_overflow_and_nul_budget(self):
        blob, profile = self.slot_fixture(capacity=4)
        with self.assertRaises(ValueError):
            rewrite_fixed_slot(blob, profile, "测试", self.encoder)

    def test_fixed_slot_identity_reject(self):
        blob, profile = self.slot_fixture()
        for key, value in (("record_id", 177), ("expected_slot_sha256", "bad"), ("record_index", 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                rewrite_fixed_slot(blob, {**profile, key: value}, "测", self.encoder)

    def test_locale_schema_and_glyph_count(self):
        locale, game, encoder = load_config(ROOT / "locales/zh-CN/poc-text.json")
        self.assertEqual(len(encoder.entries), 33)
        self.assertEqual(len(locale["entries"]), 3)
        self.assertEqual(game["ui"]["text_bytes"], 512)

    def test_preserves_other_experiment_directory(self):
        locale, game, encoder = load_config(ROOT / "locales/zh-CN/poc-text.json")
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            record = out / "DIFF_FILE.json"
            record.write_text('{"profile": {"milestone": "glyph-poc-01"}}', encoding="utf8")
            before = record.read_bytes()
            with self.assertRaisesRegex(ValueError, "different experiment"):
                build(Path("missing-source"), out, Path("missing-font"), locale, game, encoder)
            self.assertEqual(record.read_bytes(), before)

    def test_common_baseline_font_patch_only_selected_fields(self):
        from PIL import ImageFont
        def compact(n):
            out = bytearray([n & 63]); n >>= 6
            if n: out[0] |= 64
            while n:
                byte, n = n & 127, n >> 7
                out.append(byte | (128 if n else 0))
            return bytes(out)
        serial = (bytes(3) + struct.pack("<6I", 1, 1, 319, 21, 19, 5)
                  + compact(319 * 105) + bytes(319 * 105) + compact(319)
                  + bytes([16]) * 319 + compact(2) + struct.pack("<2H", 0xB0A1, 0xB0A3)
                  + compact(2) + struct.pack("<2H", 317, 319) + bytes(8))
        encoder = MappedEncoder([{"character": "é", "bytes": "b0a1", "glyph": 317}])
        with patch("PIL.ImageFont.truetype", return_value=ImageFont.load_default()):
            after = patch_font(serial, encoder, Path("synthetic-font"), "A", 19)
        info = font_data(serial)
        self.assertEqual(after[info["metrics_start"] + 317], 19)
        self.assertEqual(after[info["metrics_start"] + 318], 16)
        self.assertEqual(after[:info["bitmap_start"] + 317 * 105], serial[:info["bitmap_start"] + 317 * 105])
        self.assertEqual(after[info["metrics_start"] + 319:], serial[info["metrics_start"] + 319:])
        self.assertEqual(estimate_widths("éA$nA", encoder, after), [35, 16])
        with self.assertRaisesRegex(ValueError, "unresolved placeholder"):
            estimate_widths("é%s", encoder, after)


if __name__ == "__main__":
    unittest.main()
