"""Synthetic regression checks; optional real-input checks are separate."""
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
from research_inventory import compact, font_data, package_tables
from afs import build_manifest, filename_toc, finalize_hybrid_afs
from cri_afs import Afs, write_afs
from translate._common import encode_en
from translate.audit import _token_drop_warning
from translate.celfid import decompress_chunked, recompress_chunked, _detect_linked_groups
from translate.fpb import build_fpb, parse_fpb_raw, translated_fpb_bytes
from translate.region import translated_region_bytes
from translate.slot import build_slot_file, split_slot
import iso as iso_patcher


class ResearchTests(unittest.TestCase):
    def test_compact(self):
        self.assertEqual(compact(bytes.fromhex("6b29"), 0), (2667, 2))
        self.assertEqual(compact(b"\x85", 0), (-5, 1))

    def test_package_reject(self):
        with self.assertRaises(ValueError):
            package_tables(b"not a package")

    def test_font_reject(self):
        with self.assertRaises(ValueError):
            font_data(b"stock")

    def test_latin1_rejects_chinese(self):
        self.assertEqual(encode_en("ABC123"), b"ABC123")
        with self.assertRaises(ValueError):
            encode_en("测试中文")

    def test_fpb_growth_bytes(self):
        data = b"A" + "测试中文$n，。".encode("utf8")
        b = build_fpb(bytes(16), [(1, 1, len(data) - 1)], data)
        h, windows, pool = parse_fpb_raw(b)
        self.assertEqual(struct.unpack_from("<I", h, 12)[0], 1)
        self.assertEqual(windows, [(1, 1, len(data) - 1)])
        self.assertEqual(pool, data)  # byte layout test only; NOT runtime UTF-8 support

    def test_fpb_catalog_noedit_and_ascii_edit(self):
        b = build_fpb(bytes(16), [(1, 1, 1)], b"AB")
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as td:
            p = Path(td) / "sample.json"
            cat = {"records": [{"seq": 0, "en": "A"}, {"seq": 1, "en": "B"}]}
            p.write_text(json.dumps(cat))
            self.assertIsNone(translated_fpb_bytes("sample.fpb", b, Path(td)))
            cat["records"][0]["en"] = "LONG"
            p.write_text(json.dumps(cat))
            h, w, d = parse_fpb_raw(translated_fpb_bytes("sample.fpb", b, Path(td)))
            self.assertEqual((w, d), ([(1, 4, 1)], b"LONGB"))
            self.assertEqual(struct.unpack_from("<I", h, 12)[0], 4)

    def test_slot_trailer(self):
        slot = b"ABC\0\0\0\x01\x02"
        s, at, tail = split_slot(slot, len(slot))
        self.assertEqual((s, at, tail), (b"ABC", 6, b"\x01\x02"))
        result = build_slot_file(b"H", [(b"XYZ", 8, at, tail)], ".cht")
        self.assertEqual(result, b"HXYZ\0\0\0\x01\x02")
        with self.assertRaises(ValueError):
            build_slot_file(b"H", [(b"TOOLONG", 8, at, tail)], ".cht")

    def test_region_noedit_and_cap_edge(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as td:
            p = Path(td) / "sample.json"
            p.write_text(json.dumps({"ext": ".tui", "regions": [{"en": "WORD"}]}))
            self.assertIsNone(translated_region_bytes(".tui", "sample.tui", b"WORD\0\0\x01", Path(td)))
            p.write_text(json.dumps({"ext": ".tui", "regions": [{"en": "ABCDEF"}]}))
            # Upstream accepts cap bytes with no remaining NUL: evidence of a validation gap.
            self.assertEqual(translated_region_bytes(".tui", "sample.tui", b"WORD\0\0\x01", Path(td)), b"ABCDEF\x01")

    def test_token_warning(self):
        self.assertIsNotNone(_token_drop_warning("A$n$D04", "A$n"))
        self.assertIsNone(_token_drop_warning("A$n", "A$n$n"))  # only detects drops

    def test_linked_heuristic(self):
        slots = [{"marker": str(i), "max_bytes": 32, "en": s}
                 for i, s in enumerate(["Roxy", "T.Roxy", "Other"])]
        groups, leaves = _detect_linked_groups(slots)
        self.assertEqual(groups[0]["base"], "Roxy")
        self.assertEqual([s["template"] for s in groups[0]["slots"]], ["{base}", "T.{base}"])
        self.assertEqual(len(leaves), 1)

    def test_chunk_roundtrip(self):
        b = bytes(range(256)) * 301
        self.assertEqual(decompress_chunked(recompress_chunked(b)), b)

    def test_afs_manifest(self):
        entries = [("AFSShipFileIndex.idx", b"old"), ("sample.fpb", b"long data")]
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as td:
            src, dst = Path(td) / "src.afs", Path(td) / "dst.afs"
            write_afs(src, entries)
            finalize_hybrid_afs(dst, Afs.open(src), entries, manifest_name=entries[0][0], header=entries[0][0], verbose=False)
            a = Afs.open(dst)
            self.assertEqual(filename_toc(a), [n for n, _ in entries])
            with dst.open("rb") as f:
                self.assertIn(b"sample.fpb\r\n9\r\n", a.read_entry(0, f))
                self.assertEqual(a.read_entry(1, f), b"long data")

    def test_linear_manifest(self):
        m = build_manifest([("AFSLINEARFileIndex.idx", b""), ("00000001.lin", b"123")], manifest_name="AFSLINEARFileIndex.idx", header="AFSLINEARFileIndex", strip_ext=".lin")
        self.assertEqual(m, b"AFSLINEARFileIndex\r\n0\r\n00000001\r\n3\r\n")

    def test_iso_inplace_and_relocation(self):
        import pycdlib
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as td:
            src, dst, small, large = [Path(td) / n for n in ["src.iso", "dst.iso", "small.dat", "large.dat"]]
            cd = pycdlib.PyCdlib(); cd.new()
            cd.add_fp(io.BytesIO(b"OLD"), 3, iso_path="/SMALL.DAT;1")
            cd.add_fp(io.BytesIO(b"OLD"), 3, iso_path="/LARGE.DAT;1")
            cd.write(str(src)); cd.close()
            cd = pycdlib.PyCdlib(); cd.open(str(src))
            table = {"/"+n: (cd.get_record(iso_path="/"+n+";1").extent_location(), 3) for n in ["SMALL.DAT", "LARGE.DAT"]}
            r = cd.get_record(iso_path="/"); directory = (r.extent_location(), r.data_length); cd.close()
            small.write_bytes(b"OK"); large.write_bytes(b"X"*4097)
            # Test existing patch algorithm; inject metadata to isolate absent isoinfo on Windows.
            with patch.object(iso_patcher, "_read_iso_lbas", return_value=table), patch.object(iso_patcher, "_dir_lba_size", return_value=directory):
                self.assertEqual(iso_patcher.patch_iso(src, dst, {"/SMALL.DAT": small, "/LARGE.DAT": large}, verbose=False), (1, 1))
            cd = pycdlib.PyCdlib(); cd.open(str(dst))
            for name, expected in [("SMALL.DAT", b"OK"), ("LARGE.DAT", b"X"*4097)]:
                buf=io.BytesIO();cd.get_file_from_iso_fp(buf, iso_path="/"+name+";1");self.assertEqual(buf.getvalue(),expected)
            self.assertEqual(cd.pvd.space_size * 2048, dst.stat().st_size)
            cd.close()


if __name__ == "__main__":
    unittest.main()
