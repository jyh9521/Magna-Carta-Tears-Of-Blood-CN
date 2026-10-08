"""Read-only KR font-slot capacity and FPB collision inventory, not an allocator."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "lib"), str(ROOT / "src")]
import font_poc as core
from build_locale import load_config
from research_inventory import font_data, package_tables
from translate.fpb import parse_fpb_raw, build_fpb, synthesize_implicit_seq0
from localization.text import protected_tokens


def observed_slots(info: dict) -> dict[bytes, int]:
    keys = [0xA1A6] + [(lead << 8) | 0xA1 for lead in range(0xB0, 0xC9)] + [0xC8FF]
    bases = [256] + [317 + row * 94 for row in range(25)] + [2667]
    core.require(info["glyphs"] == 2667 and info["ranges"] == keys and info["bases"] == bases,
                 "font range/base arrays differ from observed KR layout")
    return {bytes((lead, trail)): 317 + (lead - 0xB0) * 94 + trail - 0xA1
            for lead in range(0xB0, 0xC9) for trail in range(0xA1, 0xFF)}


def scan_fpbs(entries: list[tuple[str, bytes]], slots: dict[bytes, int],
              excluded_sequences: dict[str, set[int]]) -> dict:
    usage, remaining, refs, remaining_refs = Counter(), Counter(), defaultdict(set), defaultdict(set)
    statuses, omitted = Counter(), []
    for name, blob in entries:
        if not name.lower().endswith(".fpb"):
            continue
        if len(blob) == 8:
            statuses["stub"] += 1
            continue
        header, windows, pool = parse_fpb_raw(blob)
        core.require(build_fpb(header, windows, pool) == blob, "FPB source roundtrip mismatch")
        try:
            text = pool.decode("cp949", errors="strict")
        except UnicodeDecodeError:
            statuses["decode_failed"] += 1
            omitted.append(name)
            continue
        statuses["decoded"] += 1
        core.require(text.encode("cp949", errors="strict") == pool, "noncanonical CP949 pool bytes")
        skip = excluded_sequences.get(name, set())
        views = synthesize_implicit_seq0(windows, len(pool))
        core.require(skip.issubset({seq for seq, _, _ in views}), "excluded target sequence missing")
        ranges = [(o, o + n) for seq, o, n in views if seq in skip]
        offset = 0
        for char in text:
            code = char.encode("cp949", errors="strict")
            if code in slots:
                key = code.hex()
                usage[key] += 1
                refs[key].add(name)
                if not any(offset < end and offset + len(code) > start for start, end in ranges):
                    remaining[key] += 1
                    remaining_refs[key].add(name)
            offset += len(code)
        core.require(offset == len(pool), "CP949 byte position reconstruction mismatch")
    return {"statuses": dict(sorted(statuses.items())), "omitted_resources": sorted(omitted),
            "slots": {code.hex(): {"glyph": glyph, "original_occurrences": usage[code.hex()],
                       "outside_target_windows_occurrences": remaining[code.hex()],
                       "resources": sorted(refs[code.hex()]),
                       "outside_target_windows_resources": sorted(remaining_refs[code.hex()])}
                      for code, glyph in slots.items()}}


def capacity_summary(inventory: dict, mapping: list[dict], *, scope: str = "decoded_fpb") -> dict:
    rows = inventory["slots"]
    collisions = []
    for entry in mapping:
        code = bytes.fromhex(entry["bytes"]).hex()
        core.require(code in rows and rows[code]["glyph"] == entry["glyph"], "map/font slot mismatch")
        collisions.append({"target_codepoint": f"U+{ord(entry['character']):04X}", "bytes": code,
                           **rows[code]})
    return {"observed_hangul_slots": len(rows),
            f"used_slots_in_{scope}": sum(r["original_occurrences"] > 0 for r in rows.values()),
            f"unobserved_slots_in_{scope}": sum(r["original_occurrences"] == 0 for r in rows.values()),
            "map_slots": len(mapping),
            "map_slots_with_original_occurrences": sum(r["original_occurrences"] > 0 for r in collisions),
            "map_slots_with_outside_target_occurrences": sum(r["outside_target_windows_occurrences"] > 0 for r in collisions),
            "outside_target_occurrences": sum(r["outside_target_windows_occurrences"] for r in collisions),
            "outside_target_resource_count": len({n for r in collisions for n in r["outside_target_windows_resources"]}),
            "mapping_collisions": collisions}


def inspect_tui(blob: bytes) -> tuple[dict, list[tuple[int, bytes]]]:
    """Observed KR 8 + count * 516 geometry, not a universal TUI schema."""
    report = {"sha256": core.digest(blob), "size": len(blob)}
    if len(blob) < 8:
        return {**report, "status": "header-truncated"}, []
    count, kind = struct.unpack_from("<II", blob)
    report.update(count=count, kind=kind)
    if kind != 2 or len(blob) != 8 + count * 516:
        return {**report, "status": "geometry-unsupported"}, []
    ids = [struct.unpack_from("<I", blob, 8 + i * 516)[0] for i in range(count)]
    if len(set(ids)) != count:
        return {**report, "status": "duplicate-record-id"}, []
    fields, decoded = [], []
    for i, record_id in enumerate(ids):
        offset = 12 + i * 516
        slot = blob[offset:offset + 512]
        field = {"index": i, "id": record_id, "offset": offset, "slot_sha256": core.digest(slot)}
        nul = slot.find(b"\0")
        if nul < 0:
            field["status"] = "missing-nul"
        elif any(slot[nul:]):
            field["status"] = "nonzero-padding"
            field["nul_offset_in_slot"] = nul
            field["next_nonzero_offset_in_slot"] = next(j for j in range(nul + 1, 512) if slot[j])
        elif nul == 0:
            field["status"] = "empty"
        else:
            raw = slot[:nul]
            try:
                text = raw.decode("cp949", errors="strict")
                core.require(text.encode("cp949") == raw, "noncanonical TUI CP949 bytes")
            except UnicodeDecodeError:
                field["status"] = "decode-failed"
            else:
                field.update(status="decoded", encoded_bytes=nul)
                try:
                    protected_tokens(text)
                except ValueError:
                    field["protected_structures_known"] = False
                else:
                    field["protected_structures_known"] = True
                field["has_raw_control"] = any(ord(c) < 32 for c in text)
                decoded.append((record_id, raw))
        fields.append(field)
    return {**report, "status": "geometry-verified", "fields": fields}, decoded


def inspect_tui_pairs(blob: bytes) -> tuple[dict, list[tuple[int, int, bytes]]]:
    """Audit both 256-byte halves; layout evidence is not edit permission."""
    geometry, _ = inspect_tui(blob)
    if geometry["status"] != "geometry-verified":
        return geometry, []
    report = {k: v for k, v in geometry.items() if k != "fields"}
    fields, decoded = [], []
    for record in geometry["fields"]:
        for half in range(2):
            offset = record["offset"] + half * 256
            slot = blob[offset:offset + 256]
            field = {"index": record["index"], "id": record["id"], "half": half,
                     "offset": offset, "span_bytes": 256, "sha256": core.digest(slot)}
            nul = slot.find(b"\0")
            if nul < 0:
                field["status"] = "missing-nul"
            elif any(slot[nul:]):
                field["status"] = "nonzero-padding"
            elif nul == 0:
                field["status"] = "empty"
            else:
                raw = slot[:nul]
                try:
                    text = raw.decode("cp949", errors="strict")
                    core.require(text.encode("cp949") == raw, "noncanonical TUI half bytes")
                except UnicodeDecodeError:
                    field["status"] = "decode-failed"
                else:
                    field.update(status="decoded", encoded_bytes=nul)
                    try:
                        protected_tokens(text)
                    except ValueError:
                        field["protected_structures_known"] = False
                    else:
                        field["protected_structures_known"] = True
                    field["has_raw_control"] = any(ord(c) < 32 for c in text)
                    decoded.append((record["id"], half, raw))
            fields.append(field)
    return {**report, "fields": fields}, decoded


def scan_tuis(entries: list[tuple[str, bytes]], slots: dict[bytes, int],
              excluded_records: dict[str, set[int]], bundle: bytes, *, paired: bool = False) -> dict:
    usage, remaining = Counter(), Counter()
    refs, remaining_refs, statuses, resources = defaultdict(set), defaultdict(set), Counter(), {}
    for name, blob in entries:
        if not name.lower().endswith(".tui"):
            continue
        if paired:
            report, fields = inspect_tui_pairs(blob)
        else:
            report, flat_fields = inspect_tui(blob)
            fields = [(record_id, 0, raw) for record_id, raw in flat_fields]
        report["exact_bundle_copy_count"] = bundle.count(blob)
        statuses["file/" + report["status"]] += 1
        for field in report.get("fields", []):
            prefix = f"half{field['half']}" if paired else "field"
            statuses[prefix + "/" + field["status"]] += 1
        excluded = excluded_records.get(name, set())
        core.require(excluded.issubset({record_id for record_id, half, _ in fields if half == 0}), "excluded TUI record not decoded")
        for record_id, half, raw in fields:
            for char in raw.decode("cp949"):
                code = char.encode("cp949")
                if code not in slots:
                    continue
                key = code.hex()
                usage[key] += 1
                refs[key].add(name)
                if half != 0 or record_id not in excluded:
                    remaining[key] += 1
                    remaining_refs[key].add(name)
        resources[name] = report
    return {"statuses": dict(sorted(statuses.items())), "resources": resources,
            "slots": {code.hex(): {"glyph": glyph, "original_occurrences": usage[code.hex()],
                       "outside_target_windows_occurrences": remaining[code.hex()],
                       "resources": sorted(refs[code.hex()]),
                       "outside_target_windows_resources": sorted(remaining_refs[code.hex()])}
                      for code, glyph in slots.items()}}


def combine_inventories(*inventories: dict) -> dict:
    result = {}
    core.require(bool(inventories), "at least one slot inventory required")
    core.require(all(set(i["slots"]) == set(inventories[0]["slots"]) for i in inventories), "slot domains differ")
    for code, row in inventories[0]["slots"].items():
        rows = [i["slots"][code] for i in inventories]
        core.require(all(r["glyph"] == row["glyph"] for r in rows), "slot glyph differs")
        result[code] = {"glyph": row["glyph"]}
        for key in ("original_occurrences", "outside_target_windows_occurrences"):
            result[code][key] = sum(r[key] for r in rows)
        for key in ("resources", "outside_target_windows_resources"):
            result[code][key] = sorted({n for r in rows for n in r[key]})
    return {"slots": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--locale", type=Path, default=ROOT / "locales/zh-CN/poc-text.json")
    parser.add_argument("--out", type=Path, default=ROOT / "work/font-coverage")
    args = parser.parse_args()
    locale, game, encoder = load_config(args.locale)
    before = core.file_digest(args.iso)
    core.require(game["region"] == "kr" and before == game["expected_iso_sha256"], "unknown ISO version/hash")
    out = core.output_directory(args.out)
    iso_data = core.iso_files(args.iso, ["FILE.AFS", "SHIP.AFS"])
    archives = {}
    for name, blob in iso_data.items():
        path = out / name
        path.write_bytes(blob)
        archives[name] = core.archive_entries(path)[1]
    files = dict(archives["FILE.AFS"])
    engine = files["MrtsEngine.u"]
    core.require(core.digest(engine) == game["expected_engine_sha256"], "engine fingerprint mismatch")
    fonts, slots = {}, None
    for export in package_tables(engine)["exports"]:
        if export["class"] != "Font" or export["name"] not in game["fonts"]:
            continue
        serial = engine[export["offset"]:export["offset"] + export["size"]]
        core.require(core.digest(serial) == game["fonts"][export["name"]], "font fingerprint mismatch")
        info = font_data(serial)
        current = observed_slots(info)
        core.require(slots is None or slots == current, "font slot mapping differs")
        slots = current
        size = info["height"] * info["row_stride"]
        empty = [g for g in current.values() if not any(serial[info["bitmap_start"] + g * size:info["bitmap_start"] + (g + 1) * size])]
        fonts[export["name"]] = {"sha256": core.digest(serial), "glyphs": info["glyphs"],
                                 "height": info["height"], "width": info["width"],
                                 "ranges": info["ranges"], "bases": info["bases"],
                                 "zero_bitmap_hangul_slots": len(empty)}
    core.require(len(fonts) == 2 and slots is not None, "expected two observed fonts")
    excluded = {game["fpb_resource"]: {r["seq"] for r in locale["entries"] if r["kind"] == "fpb"}}
    inventory = scan_fpbs(archives["SHIP.AFS"], slots, excluded)
    summary = capacity_summary(inventory, encoder.entries)
    bundle = core.decompress_chunked(files["celfid.lix"])
    core.require(core.digest(bundle) == game["expected_bundle_sha256"], "bundle fingerprint mismatch")
    tui_inventory = scan_tuis(archives["SHIP.AFS"], slots, {game["ui_resource"]: {game["ui"]["record_id"]}}, bundle)
    tui_summary = capacity_summary(tui_inventory, encoder.entries, scope="decoded_tui_fields")
    combined_summary = capacity_summary(combine_inventories(inventory, tui_inventory), encoder.entries, scope="decoded_fpb_and_tui")
    pair_inventory = scan_tuis(archives["SHIP.AFS"], slots, {game["ui_resource"]: {game["ui"]["record_id"]}}, bundle, paired=True)
    pair_summary = capacity_summary(combine_inventories(inventory, pair_inventory), encoder.entries, scope="decoded_fpb_and_tui_halves")
    core.require(core.file_digest(args.iso) == before, "original ISO hash changed")
    report = {"schema": 3, "input_sha256": before, "locale": locale["locale"],
              "fonts": fonts, "inventory": inventory, "summary": summary,
              "tui_inventory": tui_inventory, "tui_summary": tui_summary, "combined_summary": combined_summary,
              "tui_pair_inventory": pair_inventory, "combined_pair_summary": pair_summary,
              "evidence": "static only; decoded FPB and clean TUI fields, not all visible text, a free-slot allocator or runtime proof"}
    (out / "font-coverage.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("FONT COVERAGE PASS " + json.dumps({k: v for k, v in summary.items() if k != "mapping_collisions"}, sort_keys=True))
    print("TUI COVERAGE PASS " + json.dumps(tui_inventory["statuses"], sort_keys=True))
    print("COMBINED COVERAGE PASS " + json.dumps({k: v for k, v in combined_summary.items() if k != "mapping_collisions"}, sort_keys=True))
    print("TUI PAIR PASS " + json.dumps(pair_inventory["statuses"], sort_keys=True))
    print("PAIRED COVERAGE PASS " + json.dumps({k: v for k, v in pair_summary.items() if k != "mapping_collisions"}, sort_keys=True))


if __name__ == "__main__":
    main()
