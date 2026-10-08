"""Version-locked KR single-glyph experiment. Reuse upstream AFS/FPB/ISO code.

No complete original assets or font files belong in Git. This is not a general
Chinese encoder: the original Korean character at this slot also changes.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT / "tools")]
from cri_afs import Afs
from afs import filename_toc, rebuild_afs
from iso import patch_iso
from translate.celfid import decompress_chunked, recompress_chunked
from translate.fpb import parse_fpb_raw, build_fpb, synthesize_implicit_seq0
from research_inventory import package_tables, font_data

PROFILE = ROOT / "locales" / "zh-CN" / "poc.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def output_directory(path: Path) -> Path:
    path = path.resolve()
    require(any(path.is_relative_to(ROOT / d) for d in ("work", "build")),
            "output must be under ignored work/ or build/")
    path.mkdir(parents=True, exist_ok=True)
    return path


def iso_files(path: Path, names: list[str]) -> dict[str, bytes]:
    import pycdlib
    cd = pycdlib.PyCdlib()
    cd.open(str(path))
    result = {}
    try:
        for name in names:
            out = io.BytesIO()
            cd.get_file_from_iso_fp(out, iso_path="/" + name + ";1")
            result[name] = out.getvalue()
    finally:
        cd.close()
    return result


def archive_entries(path: Path) -> tuple[Afs, list[tuple[str, bytes]]]:
    archive = Afs.open(path)
    with path.open("rb") as stream:
        entries = [(name, archive.read_entry(i, stream))
                   for i, name in enumerate(filename_toc(archive))]
    return archive, entries


def manifest_overlay(original: bytes, sizes: dict[str, int]) -> bytes:
    """Preserve external-package stub sizes and all untargeted manifest rows."""
    lines = original.decode("ascii").split("\r\n")
    require(lines[-1] == "" and len(lines[:-1]) % 2 == 0, "manifest geometry mismatch")
    found = set()
    for i in range(2, len(lines) - 1, 2):
        name = lines[i].lower()
        if name in sizes:
            require(name not in found, "duplicate manifest target")
            lines[i + 1] = str(sizes[name])
            found.add(name)
    require(found == set(sizes), "manifest target missing")
    return "\r\n".join(lines).encode("ascii")


def glyph_bitmap(serial: bytes, index: int):
    from PIL import Image
    info = font_data(serial)
    image = Image.new("L", (info["width"], info["height"]))
    start = info["bitmap_start"] + index * info["height"] * info["row_stride"]
    for y in range(image.height):
        for x in range(image.width):
            value = (serial[start + y * info["row_stride"] + x // 4] >> (2 * (x % 4))) & 3
            image.putpixel((x, y), value * 85)
    return image


def replace_glyph(serial: bytes, index: int, glyph: str, font_path: Path) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    info = font_data(serial)
    require(0 <= index < info["glyphs"], "glyph index outside font")
    # Fit only one glyph; preserve baseline/advance assumptions of the source slot.
    size = info["height"] - 2
    while size > 4:
        font = ImageFont.truetype(str(font_path), size)
        box = font.getbbox(glyph)
        if box[2] - box[0] <= info["width"] and box[3] - box[1] <= info["height"] - 2:
            break
        size -= 1
    require(size > 4, "glyph cannot fit source geometry")
    image = Image.new("L", (info["width"], info["height"]))
    x = (image.width - (box[2] - box[0])) // 2 - box[0]
    y = (image.height - (box[3] - box[1])) // 2 - box[1]
    ImageDraw.Draw(image).text((x, y), glyph, font=font, fill=255)
    require(image.getbbox() is not None, "empty rendered glyph")
    packed = bytearray(info["height"] * info["row_stride"])
    for y in range(image.height):
        for x in range(image.width):
            level = (image.getpixel((x, y)) * 3 + 127) // 255
            packed[y * info["row_stride"] + x // 4] |= level << (2 * (x % 4))
    start = info["bitmap_start"] + index * len(packed)
    result = serial[:start] + packed + serial[start + len(packed):]
    require(result != serial and len(result) == len(serial), "glyph edit did not change bitmap")
    require(font_data(result) == info, "font geometry/metrics/ranges changed")
    return result


def edit_fpb(blob: bytes, profile: dict) -> bytes:
    require(digest(blob) == profile["expected_fpb_sha256"], "unsupported FPB source")
    header, windows, pool = parse_fpb_raw(blob)
    require(build_fpb(header, windows, pool) == blob, "FPB baseline round trip failed")
    modified = bytearray(pool)
    views = {s: (o, n) for s, o, n in synthesize_implicit_seq0(windows, len(pool))}
    for sequence in profile["sequences"]:
        offset, size = views[sequence]
        require(size >= 2 and pool[offset:offset + 2].decode("cp949").isascii() is False,
                "test window does not start with a double-byte character")
        modified[offset:offset + 2] = bytes.fromhex(profile["runtime_bytes"])
    token_pattern = rb"\$[A-Za-z0-9]+|%[A-Za-z0-9]+|<[^>]*>"
    require(re.findall(token_pattern, pool) == re.findall(token_pattern, modified), "protected tokens changed")
    result = build_fpb(header, windows, bytes(modified))
    require(len(result) == len(blob), "fixed-byte PoC unexpectedly grew FPB")
    return result


def byte_spans(old: bytes, new: bytes) -> list[dict]:
    require(len(old) == len(new), "span comparison requires equal lengths")
    spans, start = [], None
    for i in range(len(old) + 1):
        changed = i < len(old) and old[i] != new[i]
        if changed and start is None:
            start = i
        elif not changed and start is not None:
            spans.append({"offset": start, "old_hex": old[start:i].hex(), "new_hex": new[start:i].hex()})
            start = None
    return spans


def verify_sparse_iso(source: Path, modified: Path) -> None:
    """Prove no ISO bytes changed outside the two archives and FILE size field."""
    from iso import _portable_metadata, SECTOR
    require(source.stat().st_size == modified.stat().st_size, "unexpected ISO growth")
    files, directories = _portable_metadata(source)
    allowed = [(files[name][0] * SECTOR, files[name][0] * SECTOR + files[name][1])
               for name in ("/FILE.AFS", "/SHIP.AFS")]
    lba, size = directories["/"]
    with source.open("rb") as stream:
        stream.seek(lba * SECTOR)
        directory = stream.read(size)
    pos, found = 0, False
    while pos < len(directory):
        length = directory[pos]
        if not length:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        name_length = directory[pos + 32]
        if directory[pos + 33:pos + 33 + name_length] == b"FILE.AFS;1":
            start = lba * SECTOR + pos + 10
            allowed.append((start, start + 8))
            found = True
        pos += length
    require(found, "FILE directory record missing")
    with source.open("rb") as before, modified.open("rb") as after:
        offset = 0
        while original := before.read(8 * 1024 * 1024):
            edited = bytearray(after.read(len(original)))
            for start, end in allowed:
                lo, hi = max(start, offset) - offset, min(end, offset + len(original)) - offset
                if lo < hi:
                    edited[lo:hi] = original[lo:hi]
            require(edited == original, f"untargeted ISO bytes changed near {offset}")
            offset += len(original)


def build(source: Path, out: Path, font: Path, profile: dict) -> None:
    require(file_digest(source) == profile["expected_iso_sha256"], "unsupported original ISO")
    require(font.is_file(), "font input missing")
    from PIL import Image
    from fontTools.ttLib import TTFont
    font_hash = file_digest(font)
    require(font_hash == profile["font_input"]["sha256"],
            "PoC font profile mismatch; add and test a new explicit font profile first")
    with TTFont(font) as source_font:
        mapped = source_font.getBestCmap().get(ord(profile["glyph"]))
        require(mapped is not None and mapped != ".notdef", "source font lacks requested glyph")
    original = iso_files(source, ["SHIP.AFS", "FILE.AFS"])
    for name, data in original.items():
        (out / ("original-" + name)).write_bytes(data)
    _, file_entries = archive_entries(out / "original-FILE.AFS")
    files = dict(file_entries)
    engine = files["MrtsEngine.u"]
    require(digest(engine) == profile["expected_engine_sha256"], "unsupported engine package")
    bundle = decompress_chunked(files["celfid.lix"])
    new_engine, new_bundle = bytearray(engine), bytearray(bundle)
    fonts = {}
    preview = Image.new("L", (19 * 8 * 2, 21 * 8 * 2))
    for row, export in enumerate(e for e in package_tables(engine)["exports"] if e["class"] == "Font" and e["name"] in profile["fonts"]):
        offset, size = export["offset"], export["size"]
        serial = engine[offset:offset + size]
        require(digest(serial) == profile["fonts"][export["name"]], "font serial mismatch")
        require(bundle.count(serial) == 1, "bundle font is not unique")
        edited = replace_glyph(serial, profile["glyph_index"], profile["glyph"], font)
        bundle_offset = bundle.index(serial)
        new_engine[offset:offset + size] = edited
        new_bundle[bundle_offset:bundle_offset + size] = edited
        fonts[export["name"]] = {"original_sha256": digest(serial), "modified_sha256": digest(edited),
                                 "engine_offset": offset, "bundle_offset": bundle_offset,
                                 "advance_byte": serial[font_data(serial)["metrics_start"] + profile["glyph_index"]]}
        for column, data in enumerate((serial, edited)):
            image = glyph_bitmap(data, profile["glyph_index"]).resize((19 * 8, font_data(data)["height"] * 8), Image.Resampling.NEAREST)
            preview.paste(image, (column * 19 * 8, row * 21 * 8))
    require(len(fonts) == 2, "expected both runtime fonts")
    preview.save(out / "glyph-preview.png")
    compressed = recompress_chunked(bytes(new_bundle))
    require(decompress_chunked(compressed) == bytes(new_bundle), "bundle recompression failed")
    file_overrides = {"mrtsengine.u": bytes(new_engine), "celfid.lix": compressed}
    file_overrides[file_entries[0][0].lower()] = manifest_overlay(file_entries[0][1], {k: len(v) for k, v in file_overrides.items()})
    rebuild_afs(out / "original-FILE.AFS", out / "FILE.AFS", file_overrides)
    _, ship_entries = archive_entries(out / "original-SHIP.AFS")
    old_fpb = dict(ship_entries)[profile["resource"]]
    new_fpb = edit_fpb(old_fpb, profile)
    ship_overrides = {profile["resource"].lower(): new_fpb}
    ship_overrides[ship_entries[0][0].lower()] = manifest_overlay(ship_entries[0][1], {profile["resource"].lower(): len(new_fpb)})
    rebuild_afs(out / "original-SHIP.AFS", out / "SHIP.AFS", ship_overrides)
    changed = {}
    for name, overrides in (("FILE.AFS", file_overrides), ("SHIP.AFS", ship_overrides)):
        original_archive, before = archive_entries(out / ("original-" + name))
        modified_archive, after = archive_entries(out / name)
        require(original_archive.read_toc_metadata() == modified_archive.read_toc_metadata(), "AFS metadata changed")
        require([n for n, _ in before] == [n for n, _ in after], "AFS order changed")
        changed[name] = []
        for (entry, old), (_, new) in zip(before, after, strict=True):
            require(new == overrides.get(entry.lower(), old), "untargeted entry changed")
            if old != new:
                changed[name].append({"name": entry, "old_size": len(old), "new_size": len(new), "old_sha256": digest(old), "new_sha256": digest(new)})
    branches = patch_iso(source, out / "MODIFIED_FILE.iso", {"/FILE.AFS": out / "FILE.AFS", "/SHIP.AFS": out / "SHIP.AFS"})
    verify_sparse_iso(source, out / "MODIFIED_FILE.iso")
    report = {"profile": profile, "source_iso": str(source.resolve()), "source_sha256": profile["expected_iso_sha256"],
              "modified_sha256": file_digest(out / "MODIFIED_FILE.iso"), "font_source": str(font.resolve()), "font_sha256": font_hash,
              "font_license": profile["font_input"]["license"],
              "fonts": fonts, "afs_changes": changed, "iso_branches": {"in_place": branches[0], "relocated": branches[1]},
              "engine_diff": byte_spans(engine, bytes(new_engine)), "bundle_decompressed_diff": byte_spans(bundle, bytes(new_bundle)),
              "fpb_diff": byte_spans(old_fpb, new_fpb), "untargeted_iso_bytes": "byte-identical including ELF, LINEAR, MUSIC and movies",
              "runtime": "pending user BIOS and PCSX2 visual acceptance"}
    (out / "DIFF_FILE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    require(file_digest(source) == profile["expected_iso_sha256"], "original input changed")
    print(f"BUILD PASS in_place={branches[0]} relocated={branches[1]} original_unchanged=true")


def verify(path: Path, state: str, out: Path, profile: dict) -> None:
    report = json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8")) if state == "modified" else None
    expected = report["modified_sha256"] if report else profile["expected_iso_sha256"]
    require(file_digest(path) == expected, "ISO hash mismatch")
    if report:
        verify_sparse_iso(Path(report["source_iso"]), path)
    data = iso_files(path, ["FILE.AFS", "SHIP.AFS", "SYSTEM.CNF"])
    require(b"SCKA_200.43" in data["SYSTEM.CNF"], "wrong game boot identity")
    for name in ("FILE.AFS", "SHIP.AFS"):
        scratch = out / ("verify-" + name)
        scratch.write_bytes(data[name])
        _, entries = archive_entries(scratch)
        files = dict(entries)
        if name == "FILE.AFS":
            engine = files["MrtsEngine.u"]
            bundle = decompress_chunked(files["celfid.lix"])
            for export in package_tables(engine)["exports"]:
                if export["class"] != "Font" or export["name"] not in profile["fonts"]:
                    continue
                serial = engine[export["offset"]:export["offset"] + export["size"]]
                wanted = report["fonts"][export["name"]]["modified_sha256"] if report else profile["fonts"][export["name"]]
                require(digest(serial) == wanted and bundle.count(serial) == 1, "font replicas differ")
            manifest = entries[0][1].decode("ascii").split("\r\n")
            for entry in ("MrtsEngine.u", "celfid.lix"):
                require(int(manifest[manifest.index(entry) + 1]) == len(files[entry]), "FILE manifest size mismatch")
        else:
            fpb = files[profile["resource"]]
            h, windows, pool = parse_fpb_raw(fpb)
            require(build_fpb(h, windows, pool) == fpb, "FPB round trip mismatch")
            if report:
                for seq, offset, _ in synthesize_implicit_seq0(windows, len(pool)):
                    if seq in profile["sequences"]:
                        require(pool[offset:offset + 2].hex() == profile["runtime_bytes"], "FPB marker missing")
            else:
                require(digest(fpb) == profile["expected_fpb_sha256"], "original FPB mismatch")
    print(f"VERIFY {state.upper()} PASS fonts=2 replicas=2 fpb=1 manifests=PASS sha256={expected}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "rollback"))
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "poc")
    parser.add_argument("--font", type=Path)
    parser.add_argument("--state", choices=("baseline", "modified"), default="baseline")
    parser.add_argument("--profile", type=Path, default=PROFILE)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf8"))
    out = output_directory(args.out)
    if args.action == "build":
        require(args.font is not None, "--font is required")
        build(args.iso, out, args.font, profile)
    elif args.action == "verify":
        verify(args.iso, args.state, out, profile)
    else:
        source = Path(json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8"))["source_iso"])
        target = args.iso.resolve()
        require(target.parent == out and target != source.resolve() and target.name != "MODIFIED_FILE.iso", "rollback only on isolated output copy")
        require(not target.exists() or not target.samefile(out / "MODIFIED_FILE.iso"), "rollback copy must not alias modified artifact")
        require(target.is_file() and file_digest(target) == json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8"))["modified_sha256"], "rollback target is not modified output")
        require(file_digest(source) == profile["expected_iso_sha256"], "original rollback input mismatch")
        shutil.copyfile(source, target)
        verify(target, "baseline", out, profile)
        print("ROLLBACK PASS restored=original-Korean-font-and-dialogue modified_artifact_preserved=true")


if __name__ == "__main__":
    main()
