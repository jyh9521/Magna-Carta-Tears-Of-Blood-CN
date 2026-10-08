import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "lib")]
import font_poc as poc
import iso
from PIL import ImageFont
from translate.fpb import build_fpb, parse_fpb_raw


def compact(n):
    out = bytearray([n & 63])
    n >>= 6
    if n:
        out[0] |= 64
    while n:
        b, n = n & 127, n >> 7
        out.append(b | (128 if n else 0))
    return bytes(out)


class FontPocTests(unittest.TestCase):
    def test_manifest_preserves_external_stub_sizes(self):
        before = b"index\r\n0\r\nexternal.u\r\n2058129\r\ntest.fpb\r\n3\r\n"
        after = poc.manifest_overlay(before, {"test.fpb": 8})
        self.assertEqual(after, before.replace(b"\r\n3\r\n", b"\r\n8\r\n"))

    def test_manifest_missing_reject(self):
        with self.assertRaises(ValueError):
            poc.manifest_overlay(b"index\r\n0\r\n", {"missing": 1})

    def test_manifest_duplicate_reject(self):
        with self.assertRaises(ValueError):
            poc.manifest_overlay(b"index\r\n0\r\na\r\n1\r\na\r\n1\r\n", {"a": 2})

    def test_glyph_changes_only_selected_bitmap(self):
        serial = (bytes(3) + struct.pack("<6I", 1, 1, 318, 21, 19, 5)
                  + compact(318 * 21 * 5) + bytes(318 * 21 * 5)
                  + compact(318) + bytes([19]) * 318 + compact(2)
                  + struct.pack("<2H", 0xB0A1, 0xB0A2) + compact(2)
                  + struct.pack("<2H", 317, 318) + bytes(8))
        font = ImageFont.load_default()
        with patch("PIL.ImageFont.truetype", return_value=font):
            after = poc.replace_glyph(serial, 317, "A", Path("fixture-font"))
        info = poc.font_data(serial)
        start = info["bitmap_start"] + 317 * 105
        self.assertEqual(after[:start], serial[:start])
        self.assertEqual(after[start + 105:], serial[start + 105:])
        self.assertNotEqual(after[start:start + 105], serial[start:start + 105])
        self.assertIsNotNone(poc.glyph_bitmap(after, 317).getbbox())

    def test_fpb_preserves_windows_length_and_tokens(self):
        pool = "헉$n여기".encode("cp949")
        before = build_fpb(bytes(16), [(2, 4, 4)], pool)
        profile = {"expected_fpb_sha256": poc.digest(before), "sequences": [0, 2], "runtime_bytes": "b0a1"}
        after = poc.edit_fpb(before, profile)
        h, windows, data = parse_fpb_raw(after)
        self.assertEqual(len(after), len(before))
        self.assertEqual(windows, [(2, 4, 4)])
        self.assertEqual(data, bytes.fromhex("b0a1") + b"$n" + bytes.fromhex("b0a1") + pool[6:])

    def test_fpb_hash_gate(self):
        with self.assertRaises(ValueError):
            poc.edit_fpb(b"bad", {"expected_fpb_sha256": "unknown"})

    def test_iso_same_path_rejects_without_modification(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "original.iso"
            path.write_bytes(b"fixture")
            with self.assertRaises(ValueError):
                iso.patch_iso(path, path, {}, verbose=False)
            self.assertEqual(path.read_bytes(), b"fixture")

    def test_portable_iso_real_metadata_and_relocation(self):
        import pycdlib
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cd = pycdlib.PyCdlib()
            cd.new()
            cd.add_fp(io.BytesIO(b"old"), 3, iso_path="/TEST.BIN;1")
            cd.write(str(td / "source.iso"))
            cd.close()
            replacement = td / "new.bin"
            replacement.write_bytes(b"Z" * 4097)
            with patch("iso.subprocess.check_output", side_effect=FileNotFoundError):
                branches = iso.patch_iso(td / "source.iso", td / "out.iso", {"/TEST.BIN": replacement}, verbose=False)
            self.assertEqual(branches, (0, 1))
            cd.open(str(td / "out.iso"))
            result = io.BytesIO()
            cd.get_file_from_iso_fp(result, iso_path="/TEST.BIN;1")
            cd.close()
            self.assertEqual(result.getvalue(), replacement.read_bytes())

    def test_spans_reconstruct_exact_bytes(self):
        old, new = b"ABCDE", b"AZCDY"
        data = bytearray(old)
        for span in poc.byte_spans(old, new):
            offset = span["offset"]
            replacement = bytes.fromhex(span["new_hex"])
            data[offset:offset + len(replacement)] = replacement
        self.assertEqual(data, new)

    def test_output_directory_rejects_tracked_tree(self):
        with self.assertRaises(ValueError):
            poc.output_directory(ROOT / "assets")


if __name__ == "__main__":
    unittest.main()
