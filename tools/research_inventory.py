"""Read-only ISO/UE2 reconnaissance; reuse upstream AFS and text parsers.

This is an inventory, not a localization builder or runtime acceptance test.
Derived game bytes stay under ignored work/build directories.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from cri_afs import Afs
from afs import filename_toc
from translate.catalog import SUPPORTED_EXTS
from translate.celfid import decompress_chunked
from translate.fpb import parse_fpb_raw, synthesize_implicit_seq0
from translate.slot import SLOT_FORMATS, parse_slot_file, split_slot
from translate.region import REGION_OVERLAY_EXTS


def compact(data: bytes, pos: int) -> tuple[int, int]:
    first = data[pos]
    value, shift, more = first & 63, 6, first & 64
    pos += 1
    while more:
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        shift += 7
        more = byte & 128
        if shift > 34:
            raise ValueError("invalid compact integer")
    return (-value if first & 128 else value), pos


def package_tables(data: bytes) -> dict:
    if data[:4] != bytes.fromhex("c1832a9e"):
        raise ValueError("not a UE2 package")
    _, version, _, nc, no, ec, eo, ic, io = struct.unpack_from("<9I", data)
    names, pos = [], no
    for _ in range(nc):
        length, pos = compact(data, pos)
        end = pos + abs(length) * (2 if length < 0 else 1)
        names.append(data[pos:end].decode("utf-16le" if length < 0 else "latin1").rstrip("\0"))
        pos = end + 4
    imports, pos = [], io
    for _ in range(ic):
        cp, pos = compact(data, pos)
        cl, pos = compact(data, pos)
        outer = struct.unpack_from("<i", data, pos)[0]
        name, pos = compact(data, pos + 4)
        imports.append({"class": names[cl], "name": names[name], "outer": outer})
    exports, pos = [], eo
    for index in range(ec):
        cl, pos = compact(data, pos)
        _, pos = compact(data, pos)
        outer = struct.unpack_from("<i", data, pos)[0]
        name, pos = compact(data, pos + 4)
        pos += 4  # flags
        size, pos = compact(data, pos)
        offset = 0
        if size > 0:
            offset, pos = compact(data, pos)
        if size < 0 or offset < 0 or offset + size > len(data):
            raise ValueError("export outside package")
        exports.append({"index": index + 1, "class_index": cl,
                        "class": imports[-cl - 1]["name"] if cl < 0 else str(cl),
                        "name": names[name], "outer": outer, "size": size, "offset": offset})
    return {"version": version & 65535, "licensee": version >> 16,
            "names": names, "imports": imports, "exports": exports}


def font_data(serial: bytes) -> dict:
    # Observed KR NormalFont/KatakanaFont custom serialization, NOT stock UFont.
    if serial[:3] != b"\0\0\0":
        raise ValueError("not the observed custom font layout")
    flags1, flags2, glyphs, height, width, stride = struct.unpack_from("<6I", serial, 3)
    bitmap_len, bitmap_start = compact(serial, 27)
    bitmap_end = bitmap_start + bitmap_len
    metrics_len, metrics_start = compact(serial, bitmap_end)
    range_count, range_start = compact(serial, metrics_start + metrics_len)
    range_end = range_start + range_count * 2
    base_count, base_start = compact(serial, range_end)
    base_end = base_start + base_count * 2
    if bitmap_len != glyphs * height * stride or metrics_len != glyphs:
        raise ValueError("font array lengths disagree")
    if base_count != range_count or base_end > len(serial):
        raise ValueError("invalid range arrays")
    return {"flags": [flags1, flags2], "glyphs": glyphs, "height": height,
            "width": width, "row_stride": stride, "bitmap_start": bitmap_start,
            "bitmap_bytes": bitmap_len, "metrics_start": metrics_start,
            "metrics_bytes": metrics_len,
            "ranges": list(struct.unpack_from(f"<{range_count}H", serial, range_start)),
            "bases": list(struct.unpack_from(f"<{base_count}H", serial, base_start)),
            "remaining_hex": serial[base_end:].hex()}


def render_font(serial: bytes, info: dict, output: Path) -> None:
    from PIL import Image
    count = min(info["glyphs"], 384)
    tile, cols = 24, 32
    image = Image.new("L", (cols * tile, ((count + cols - 1) // cols) * tile))
    glyph_bytes = info["height"] * info["row_stride"]
    for g in range(count):
        start = info["bitmap_start"] + g * glyph_bytes
        for y in range(info["height"]):
            for x in range(info["width"]):
                byte = serial[start + y * info["row_stride"] + x // 4]
                image.putpixel((g % cols * tile + x, g // cols * tile + y),
                               ((byte >> (2 * (x % 4))) & 3) * 85)
    image.save(output)


def inspect_ship(path: Path, encoding: str) -> dict:
    archive = Afs.open(path)
    names = filename_toc(archive)
    stats = {e: {"files": 0, "units": 0, "decode_failures": 0,
                 "geometry_remainder_files": 0, "parse_failures": []} for e in SUPPORTED_EXTS}
    fpb_details, tokens = Counter(), Counter()
    with path.open("rb") as fh:
        for index, name in enumerate(names):
            ext = Path(name).suffix.lower()
            if ext not in stats:
                continue
            blob = archive.read_entry(index, fh)
            st = stats[ext]
            st["files"] += 1
            strings = []
            if ext == ".fpb":
                try:
                    h, windows, data = parse_fpb_raw(blob)
                except ValueError as error:
                    st["parse_failures"].append({"file": name, "error": str(error)})
                    continue
                full = synthesize_implicit_seq0(windows, len(data))
                strings = [data[o:o+n] for _, o, n in full]
                fpb_details["explicit_windows"] += len(windows)
                fpb_details["implicit_only_files"] += not bool(windows)
                fpb_details["bad_windows"] += sum(o + n > len(data) for _, o, n in windows)
                expected = windows[0][1] if windows else len(data)
                fpb_details["header_0c_matches"] += struct.unpack_from("<I", h, 12)[0] == expected
                fpb_details["size_matches"] += len(blob) == 20 + len(windows) * 12 + len(data)
            elif ext in SLOT_FORMATS:
                try:
                    header, slots = parse_slot_file(blob, ext)
                except ValueError as error:
                    st["parse_failures"].append({"file": name, "error": str(error)})
                    continue
                strings = [split_slot(b, cap)[0] for b, cap in slots]
                hs, stride = SLOT_FORMATS[ext]
                st["geometry_remainder_files"] += (len(blob) - hs) % stride != 0
            else:
                # USA ASCII heuristic does NOT enumerate KR/JP text. Do not invent totals.
                st["units"] = None
                continue
            st["units"] += len(strings)
            for raw in strings:
                try:
                    text = raw.decode(encoding, errors="strict")
                except UnicodeDecodeError:
                    st["decode_failures"] += 1
                    continue
                tokens.update(re.findall(r"\$n|\$D\d+", text))
    return {"entries": len(names), "extensions": dict(Counter(Path(n).suffix for n in names)),
            "supported": stats, "fpb_checks": dict(fpb_details), "tokens": dict(tokens)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True, type=Path)
    ap.add_argument("--out", default=ROOT / "work" / "research", type=Path)
    ap.add_argument("--encoding", default="cp949")
    args = ap.parse_args()
    out = args.out.resolve()
    if not any(out.is_relative_to(ROOT / d) for d in ("work", "build")):
        raise ValueError("output must be under ignored work/ or build/")
    out.mkdir(parents=True, exist_ok=True)
    import pycdlib
    iso = args.iso.resolve()
    with iso.open("rb") as fh:
        digest = hashlib.file_digest(fh, "sha256").hexdigest()
    cd = pycdlib.PyCdlib()
    cd.open(str(iso))
    files = []
    try:
        for parent, _, filenames in cd.walk(iso_path="/"):
            for filename in filenames:
                path = parent.rstrip("/") + "/" + filename
                record = cd.get_record(iso_path=path)
                files.append({"path": path, "size": record.data_length, "lba": record.extent_location()})
        for f in files:
            basename = f["path"].split("/")[-1].split(";")[0]
            if basename in ("SHIP.AFS", "FILE.AFS", "SYSTEM.CNF") or basename.startswith(("SCKA", "SLUS", "SLPM")):
                cd.get_file_from_iso(local_path=str(out / basename), iso_path=f["path"])
    finally:
        cd.close()
    result = {"input": {"file": iso.name, "size": iso.stat().st_size, "sha256": digest},
              "iso_files": files, "ship": inspect_ship(out / "SHIP.AFS", args.encoding)}
    afs = Afs.open(out / "FILE.AFS")
    names = filename_toc(afs)
    result["file_entries"] = [{"name": n, "size": e.size} for n, e in zip(names, afs.entries, strict=True)]
    bundle, engine = b"", b""
    with (out / "FILE.AFS").open("rb") as fh:
        bundle = decompress_chunked(afs.read_entry(names.index("celfid.lix"), fh))
        engine = afs.read_entry(names.index("MrtsEngine.u"), fh)
    tables = package_tables(engine)
    (out / "engine-tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf8")
    result["fonts"] = []
    for e in tables["exports"]:
        if e["class"] != "Font":
            continue
        serial = engine[e["offset"]:e["offset"] + e["size"]]
        info = {**e, "sha256": hashlib.sha256(serial).hexdigest(),
                "bundle_matches": bundle.count(serial)}
        if e["name"] in ("NormalFont", "KatakanaFont"):
            info.update(font_data(serial))
            render_font(serial, info, out / (e["name"] + ".png"))
        result["fonts"].append(info)
    result["bundle_package_magic_count"] = bundle.count(bytes.fromhex("c1832a9e"))
    result["bundle_paths"] = [m.group().decode("ascii") for m in re.finditer(rb"\.\.[/\\][\x20-\x7e]{3,100}(?=\x00)", bundle)]
    result["supported_extensions"] = list(SUPPORTED_EXTS)
    (out / "inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(f"INPUT sha256={digest} size={iso.stat().st_size}")
    print(f"SHIP entries={result['ship']['entries']} supported_files={sum(s['files'] for s in result['ship']['supported'].values())}")
    print("FONTS " + ", ".join(f"{f['name']}:{f.get('glyphs', 'stock')}" for f in result["fonts"]))
    print(f"REPORT {out / 'inventory.json'}")


if __name__ == "__main__":
    main()
