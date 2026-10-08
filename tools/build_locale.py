"""Build a small mapped-byte locale PoC, reusing upstream containers/writers.

Only version-locked display fields are edited. Runtime acceptance is separate.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "src"), str(ROOT / "lib")]
import font_poc as core
from localization.text import MappedEncoder, protected_tokens, rewrite_fpb, rewrite_fixed_slot
from research_inventory import font_data, package_tables
from translate.celfid import decompress_chunked, recompress_chunked
from afs import rebuild_afs
from iso import patch_iso


def project_json(path: str) -> dict:
    resolved = (ROOT / path).resolve()
    core.require(resolved.is_relative_to(ROOT), "profile must be inside repository")
    return json.loads(resolved.read_text(encoding="utf8"))


def load_config(path: Path) -> tuple[dict, dict, MappedEncoder]:
    locale = json.loads(path.read_text(encoding="utf8"))
    game = project_json(locale["game_profile"])
    mapping = project_json(locale["glyph_map"])
    core.require(mapping["encoding"] == "mapped-double-byte", "unsupported map backend")
    encoder = MappedEncoder(mapping["entries"])
    records = locale["entries"]
    core.require(len({r["id"] for r in records}) == len(records), "duplicate record IDs")
    core.require(len(records) == 3 and sorted(r["kind"] for r in records) == ["fixed-display-slot", "fpb", "fpb"],
                 "this PoC expects two FPB windows and one identified UI field")
    for record in records:
        expected_id = (f"SHIP/{game['fpb_resource']}/seq/{record['seq']}" if record["kind"] == "fpb"
                       else f"SHIP/{game['ui_resource']}/record/{game['ui']['record_id']}")
        core.require(record["id"] == expected_id, "record ID/profile mismatch")
    core.require(len({r["seq"] for r in records if r["kind"] == "fpb"}) == 2, "duplicate FPB sequences")
    encoder.validate_coverage([r["target"] for r in records])
    return locale, game, encoder


def patch_font(serial: bytes, encoder: MappedEncoder, font_path: Path, reference: str, advance: int) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    info = font_data(serial)
    core.require(0 < advance <= info["width"], "advance outside glyph geometry")
    font = ImageFont.truetype(str(font_path), info["height"] - 2)
    ref = font.getbbox(reference)
    origin = ((info["width"] - (ref[2] - ref[0])) // 2 - ref[0],
              (info["height"] - (ref[3] - ref[1])) // 2 - ref[1])
    result = bytearray(serial)
    allowed = set()
    for entry in encoder.entries:
        code = int(entry["bytes"], 16)
        range_index = bisect_right(info["ranges"], code) - 1
        core.require(0 <= range_index < len(info["ranges"]) - 1, "font range mismatch")
        index = info["bases"][range_index] + code - info["ranges"][range_index]
        core.require(index == entry["glyph"] and index < info["glyphs"], "font mapping mismatch")
        char = entry["character"]
        bounds = font.getbbox(char)
        core.require(0 <= origin[0] + bounds[0] and origin[0] + bounds[2] <= info["width"]
                     and 0 <= origin[1] + bounds[1] and origin[1] + bounds[3] <= info["height"],
                     "glyph would clip at common baseline")
        image = Image.new("L", (info["width"], info["height"]))
        ImageDraw.Draw(image).text(origin, char, font=font, fill=255)
        core.require(image.getbbox() is not None, "empty glyph raster")
        packed = bytearray(info["height"] * info["row_stride"])
        for y in range(image.height):
            for x in range(image.width):
                level = (image.getpixel((x, y)) * 3 + 127) // 255
                packed[y * info["row_stride"] + x // 4] |= level << (2 * (x % 4))
        start = info["bitmap_start"] + index * len(packed)
        result[start:start + len(packed)] = packed
        metric = info["metrics_start"] + index
        result[metric] = advance
        allowed.update(range(start, start + len(packed)))
        allowed.add(metric)
    core.require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(serial, result, strict=True))),
                 "untargeted font bytes changed")
    core.require(font_data(result) == info, "font geometry/range/base changed")
    return bytes(result)


def preview_fonts(fonts: dict[str, bytes], encoder: MappedEncoder, out: Path) -> None:
    from PIL import Image, ImageDraw
    cols, tile = 8, 96
    rows = (len(encoder.entries) + cols - 1) // cols
    image = Image.new("L", (cols * tile, len(fonts) * (rows * tile + 24)))
    draw = ImageDraw.Draw(image)
    for group, (name, serial) in enumerate(fonts.items()):
        y0 = group * (rows * tile + 24)
        draw.text((0, y0), name, fill=255)
        for i, entry in enumerate(encoder.entries):
            bitmap = core.glyph_bitmap(serial, entry["glyph"])
            image.paste(bitmap.resize((bitmap.width * 4, bitmap.height * 4), Image.Resampling.NEAREST),
                        ((i % cols) * tile, y0 + 24 + (i // cols) * tile))
    image.save(out / "glyph-preview.png")


def estimate_widths(text: str, encoder: MappedEncoder, serial: bytes) -> list[int]:
    """Candidate-width estimate, not measured runtime layout. Only $n is resolved."""
    core.require(all(token == "$n" for token in protected_tokens(text)), "unresolved placeholder width")
    info = font_data(serial)
    indices = {entry["character"]: entry["glyph"] for entry in encoder.entries}
    widths = []
    for line in text.split("$n"):
        total = 0
        for char in line:
            index = ord(char) if 32 <= ord(char) < 127 else indices.get(char)
            core.require(index is not None and index < info["glyphs"], "width character lacks glyph")
            total += serial[info["metrics_start"] + index]
        widths.append(total)
    return widths


def checked_archive(original: Path, output: Path, overrides: dict[str, bytes]) -> list[dict]:
    archive, before = core.archive_entries(original)
    rebuild_afs(original, output, overrides)
    new_archive, after = core.archive_entries(output)
    core.require(archive.read_toc_metadata() == new_archive.read_toc_metadata(), "AFS metadata changed")
    core.require([n for n, _ in before] == [n for n, _ in after], "AFS order changed")
    changes = []
    for (name, old), (_, new) in zip(before, after, strict=True):
        core.require(new == overrides.get(name.lower(), old), "unexpected AFS entry edit")
        if old != new:
            changes.append({"name": name, "old_size": len(old), "new_size": len(new),
                            "old_sha256": core.digest(old), "new_sha256": core.digest(new)})
    return changes


def build(source: Path, out: Path, font: Path, locale: dict, game: dict, encoder: MappedEncoder) -> None:
    from fontTools.ttLib import TTFont
    if (out / "DIFF_FILE.json").exists():
        previous = json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8"))
        core.require(previous.get("locale", {}).get("milestone") == locale["milestone"],
                     "output directory belongs to a different experiment")
    core.require(core.file_digest(source) == game["expected_iso_sha256"], "original ISO mismatch")
    core.require(core.file_digest(font) == locale["font_input"]["sha256"], "font input mismatch")
    with TTFont(font) as face:
        cmap = face.getBestCmap()
        core.require(all(cmap.get(ord(e["character"])) not in (None, ".notdef") for e in encoder.entries), "missing font glyph")
    original = core.iso_files(source, ["FILE.AFS", "SHIP.AFS"])
    for name, data in original.items():
        (out / ("original-" + name)).write_bytes(data)
    _, file_entries = core.archive_entries(out / "original-FILE.AFS")
    _, ship_entries = core.archive_entries(out / "original-SHIP.AFS")
    files, ship = dict(file_entries), dict(ship_entries)
    engine, bundle = files["MrtsEngine.u"], decompress_chunked(files["celfid.lix"])
    core.require(core.digest(engine) == game["expected_engine_sha256"], "engine source mismatch")
    core.require(core.digest(bundle) == game["expected_bundle_sha256"], "bundle source mismatch")
    ui, fpb = ship[game["ui_resource"]], ship[game["fpb_resource"]]
    core.require(core.digest(ui) == game["expected_ui_sha256"] and core.digest(fpb) == game["expected_fpb_sha256"], "text source mismatch")
    targets = {r["seq"]: r["target"] for r in locale["entries"] if r["kind"] == "fpb"}
    new_fpb, fpb_report = rewrite_fpb(fpb, targets, encoder)
    if locale.get("require_fpb_growth"):
        core.require(len(new_fpb) > len(fpb), "growth test did not grow FPB")
    ui_target = next(r["target"] for r in locale["entries"] if r["kind"] == "fixed-display-slot")
    new_ui, ui_report = rewrite_fixed_slot(ui, game["ui"], ui_target, encoder)
    core.require(bundle.count(ui) == 1, "UI bundle copy not unique")
    ui_bundle_offset = bundle.index(ui)
    new_engine, new_bundle = bytearray(engine), bytearray(bundle)
    patched_fonts, font_report = {}, {}
    for export in package_tables(engine)["exports"]:
        if export["class"] != "Font" or export["name"] not in game["fonts"]:
            continue
        name, offset, size = export["name"], export["offset"], export["size"]
        serial = engine[offset:offset + size]
        core.require(core.digest(serial) == game["fonts"][name] and bundle.count(serial) == 1, "font source identity mismatch")
        new_serial = patch_font(serial, encoder, font, locale["alignment_reference"], locale["advance"])
        start = bundle.index(serial)
        new_engine[offset:offset + size] = new_serial
        new_bundle[start:start + size] = new_serial
        patched_fonts[name] = new_serial
        font_report[name] = {"modified_sha256": core.digest(new_serial), "engine_offset": offset, "bundle_offset": start}
    core.require(len(patched_fonts) == 2, "expected two main fonts")
    width_estimates = {}
    for record in locale["entries"]:
        estimates = {name: estimate_widths(record["target"], encoder, serial)
                     for name, serial in patched_fonts.items()}
        width_estimates[record["id"]] = estimates
        if "max_estimated_pixels" in record:
            core.require(all(max(values) <= record["max_estimated_pixels"] for values in estimates.values()),
                         "PoC static pixel-width budget exceeded")
    new_bundle[ui_bundle_offset:ui_bundle_offset + len(ui)] = new_ui
    preview_fonts(patched_fonts, encoder, out)
    compressed = recompress_chunked(bytes(new_bundle))
    core.require(decompress_chunked(compressed) == new_bundle, "compression round trip mismatch")
    file_overrides = {"mrtsengine.u": bytes(new_engine), "celfid.lix": compressed}
    file_overrides[file_entries[0][0].lower()] = core.manifest_overlay(file_entries[0][1], {k: len(v) for k, v in file_overrides.items()})
    ship_overrides = {game["fpb_resource"].lower(): new_fpb, game["ui_resource"].lower(): new_ui}
    ship_overrides[ship_entries[0][0].lower()] = core.manifest_overlay(ship_entries[0][1], {k: len(v) for k, v in ship_overrides.items()})
    changes = {name: checked_archive(out / ("original-" + name), out / name, overrides)
               for name, overrides in (("FILE.AFS", file_overrides), ("SHIP.AFS", ship_overrides))}
    branches = patch_iso(source, out / "MODIFIED_FILE.iso", {"/FILE.AFS": out / "FILE.AFS", "/SHIP.AFS": out / "SHIP.AFS"})
    core.require(branches == (2, 0), "unexpected ISO relocation for this small PoC")
    core.verify_sparse_iso(source, out / "MODIFIED_FILE.iso")
    report = {"locale": locale, "game": game, "map": encoder.entries, "source_iso": str(source.resolve()),
              "source_sha256": game["expected_iso_sha256"], "modified_sha256": core.file_digest(out / "MODIFIED_FILE.iso"),
              "font_sha256": core.file_digest(font), "fonts": font_report, "afs_changes": changes,
              "fpb_records": fpb_report, "fpb_size": [len(fpb), len(new_fpb)], "ui": ui_report,
              "candidate_width_estimates": width_estimates,
              "ui_bundle_offset": ui_bundle_offset, "engine_diff": core.byte_spans(engine, bytes(new_engine)),
              "bundle_diff": core.byte_spans(bundle, bytes(new_bundle)), "ui_diff": core.byte_spans(ui, new_ui),
              "iso_branches": {"in_place": 2, "relocated": 0}, "runtime": "unverified for text-poc-02"}
    (out / "DIFF_FILE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    core.require(core.file_digest(source) == game["expected_iso_sha256"], "original input changed")
    print(f"BUILD PASS glyphs={len(encoder.entries)} records=3 fpb={len(fpb)}->{len(new_fpb)} ui_bytes={ui_report['encoded_bytes']} in_place=2 relocated=0")


def verify(path: Path, out: Path, locale: dict, game: dict, encoder: MappedEncoder, state: str) -> None:
    if state == "baseline":
        core.verify(path, "baseline", out, {**game, "resource": game["fpb_resource"]})
        return
    report = json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8"))
    core.require(report["locale"] == locale and report["game"] == game and report["map"] == encoder.entries, "verification profiles differ from build")
    core.require(core.file_digest(path) == report["modified_sha256"], "modified ISO hash mismatch")
    source = Path(report["source_iso"])
    core.require(core.file_digest(source) == game["expected_iso_sha256"], "original verification input mismatch")
    core.verify_sparse_iso(source, path)
    contents = core.iso_files(path, ["FILE.AFS", "SHIP.AFS"])
    parsed = {}
    for name, data in contents.items():
        scratch = out / ("verify-" + name)
        scratch.write_bytes(data)
        _, entries = core.archive_entries(scratch)
        parsed[name] = dict(entries)
        original_archive, original_entries = core.archive_entries(out / ("original-" + name))
        actual_archive, _ = core.archive_entries(scratch)
        core.require(core.digest((out / ("original-" + name)).read_bytes()) == core.digest(core.iso_files(source, [name])[name]),
                     "original verification archive mismatch")
        core.require(original_archive.read_toc_metadata() == actual_archive.read_toc_metadata()
                     and [n for n, _ in original_entries] == [n for n, _ in entries], "AFS order/metadata mismatch")
        changed_names = {entry["name"] for entry in report["afs_changes"][name]}
        for entry, old in original_entries:
            if entry not in changed_names:
                core.require(parsed[name][entry] == old, "untargeted AFS bytes changed")
        manifest = entries[0][1].decode("ascii").split("\r\n")
        for change in report["afs_changes"][name]:
            actual = parsed[name][change["name"]]
            core.require(core.digest(actual) == change["new_sha256"], "AFS entry hash mismatch")
            if change["name"] != entries[0][0]:
                core.require(int(manifest[manifest.index(change["name"]) + 1]) == len(actual), "manifest length mismatch")
    files, ship = parsed["FILE.AFS"], parsed["SHIP.AFS"]
    engine, bundle = files["MrtsEngine.u"], decompress_chunked(files["celfid.lix"])
    font_count = 0
    for export in package_tables(engine)["exports"]:
        if export["class"] == "Font" and export["name"] in game["fonts"]:
            serial = engine[export["offset"]:export["offset"] + export["size"]]
            core.require(core.digest(serial) == report["fonts"][export["name"]]["modified_sha256"] and bundle.count(serial) == 1, "font copies differ")
            core.require(all(serial[font_data(serial)["metrics_start"] + e["glyph"]] == locale["advance"] for e in encoder.entries), "advance mismatch")
            for record in locale["entries"]:
                widths = estimate_widths(record["target"], encoder, serial)
                core.require(widths == report["candidate_width_estimates"][record["id"]][export["name"]], "candidate width mismatch")
                if "max_estimated_pixels" in record:
                    core.require(max(widths) <= record["max_estimated_pixels"], "pixel-width budget exceeded")
            font_count += 1
    core.require(font_count == 2 and bundle.count(ship[game["ui_resource"]]) == 1, "font/UI bundle copies missing")
    _, windows, pool = core.parse_fpb_raw(ship[game["fpb_resource"]])
    views = {s: (o, n) for s, o, n in core.synthesize_implicit_seq0(windows, len(pool))}
    for record in locale["entries"]:
        if record["kind"] == "fpb":
            offset, length = views[record["seq"]]
            actual = pool[offset:offset + length]
        else:
            start, capacity = report["ui"]["offset"], report["ui"]["capacity"]
            actual = ship[game["ui_resource"]][start:start + capacity].split(b"\0", 1)[0]
        core.require(actual == encoder.encode(record["target"]), "target byte payload mismatch")
    print(f"VERIFY MODIFIED PASS glyphs={len(encoder.entries)} font_replicas=4 ui_replicas=2 records=3 manifests=PASS sha256={report['modified_sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "rollback"))
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--locale", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "text-poc-02")
    parser.add_argument("--font", type=Path)
    parser.add_argument("--state", choices=("baseline", "modified"), default="baseline")
    args = parser.parse_args()
    locale, game, encoder = load_config(args.locale)
    out = core.output_directory(args.out)
    if args.action == "build":
        core.require(args.font is not None, "--font required")
        build(args.iso, out, args.font, locale, game, encoder)
    elif args.action == "verify":
        verify(args.iso, out, locale, game, encoder, args.state)
    else:
        report = json.loads((out / "DIFF_FILE.json").read_text(encoding="utf8"))
        target, source = args.iso.resolve(), Path(report["source_iso"])
        core.require(target.parent == out and target.name == "ROLLBACK_COPY.iso", "rollback requires isolated output copy")
        core.require(not target.samefile(out / "MODIFIED_FILE.iso") and core.file_digest(target) == report["modified_sha256"], "rollback copy mismatch/alias")
        core.require(core.file_digest(source) == game["expected_iso_sha256"], "rollback source mismatch")
        shutil.copyfile(source, target)
        verify(target, out, locale, game, encoder, "baseline")
        print("ROLLBACK PASS restored=original-Korean-resources modified_preserved=true")


if __name__ == "__main__":
    main()
