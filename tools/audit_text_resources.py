"""Read-only, version-locked FPB feasibility audit; no source dialogue export."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "lib"), str(ROOT / "tools")]
import font_poc as core
from localization.text import TOKEN, protected_tokens
from translate.fpb import build_fpb, parse_fpb_raw, synthesize_implicit_seq0


def inspect_fpb(blob: bytes) -> dict:
    result = {"sha256": core.digest(blob), "size": len(blob)}
    if len(blob) == 8:
        return {**result, "status": "stub-not-parsed"}
    try:
        header, windows, pool = parse_fpb_raw(blob)
    except (ValueError, struct.error):
        return {**result, "status": "parse-error"}
    result.update(status="parsed", pool_bytes=len(pool), explicit_windows=len(windows),
                  header_implicit_length=struct.unpack_from("<I", header, 12)[0],
                  explicit_sequence_zero=any(seq == 0 for seq, _, _ in windows),
                  roundtrip_identical=build_fpb(header, windows, pool) == blob)
    views = synthesize_implicit_seq0(windows, len(pool))
    reasons, cursor, seen, gaps = set(), 0, set(), []
    for seq, offset, length in views:
        if seq in seen:
            reasons.add("duplicate-sequence")
        if offset < cursor:
            reasons.add("overlap-or-backward-order")
        if offset > cursor:
            reasons.add("gap")
            gaps.append({"offset": cursor, "length": offset - cursor,
                         "sha256": core.digest(pool[cursor:offset])})
        if offset + length > len(pool):
            reasons.add("out-of-bounds")
        cursor = offset + length
        seen.add(seq)
    if cursor != len(pool):
        reasons.add("pool-not-partitioned")
    if not result["roundtrip_identical"]:
        reasons.add("roundtrip-mismatch")
    result.update(view_count=len(views), partition_reasons=sorted(reasons),
                  view_gaps=gaps, partition_backend_eligible=not reasons)
    try:
        text = pool.decode("cp949", errors="strict")
    except UnicodeDecodeError as error:
        result.update(cp949_pool=False, decode_error_byte=error.start,
                      strict_target_validator_eligible=False)
        return result
    boundary_errors, window_control_errors = [], []
    for seq, offset, length in views:
        try:
            view = pool[offset:offset + length].decode("cp949", errors="strict")
        except UnicodeDecodeError:
            boundary_errors.append(seq)
            continue
        try:
            protected_tokens(view)
        except ValueError:
            window_control_errors.append(seq)
    controls = Counter()
    unknown = []
    pos = 0
    while pos < len(text):
        if text[pos] in "$%<>{}":
            match = TOKEN.match(text, pos)
            if match:
                # Unknown tag names/attributes remain protected; do not export source text.
                value = match.group()
                controls["markup" if value.startswith("<") else value] += 1
                pos = match.end()
                continue
            unknown.append({"character_offset": pos, "codepoint": f"U+{ord(text[pos]):04X}"})
        pos += 1
    raw_controls = Counter(f"U+{ord(c):04X}" for c in text if ord(c) < 32)
    tiers = Counter()
    for c in text:
        code = c.encode("cp949")
        if 32 <= ord(c) < 127:
            tiers["printable-ascii"] += 1
        elif len(code) == 2 and 0xB0 <= code[0] <= 0xC8 and 0xA1 <= code[1] <= 0xFE:
            tiers["observed-hangul-byte-range"] += 1
        else:
            tiers["other-cp949-not-covered-by-poc-backend"] += 1
    result.update(cp949_pool=True, window_decode_error_sequences=boundary_errors,
                  window_control_error_sequences=window_control_errors,
                  tokens=dict(sorted(controls.items())), unknown_structures=unknown,
                  raw_control_codepoints=dict(sorted(raw_controls.items())),
                  character_tiers=dict(sorted(tiers.items())),
                  strict_target_validator_eligible=not (boundary_errors or window_control_errors or unknown or raw_controls))
    return result


def summarize(records: dict[str, dict]) -> dict:
    counts, tokens, tiers = Counter(), Counter(), Counter()
    for record in records.values():
        counts[record["status"]] += 1
        for key in ("roundtrip_identical", "partition_backend_eligible", "cp949_pool",
                    "strict_target_validator_eligible"):
            if record.get(key):
                counts[key] += 1
        if record.get("partition_backend_eligible") and record.get("strict_target_validator_eligible"):
            counts["whole_file_static_preconditions_pass"] += 1
        tokens.update(record.get("tokens", {}))
        tiers.update(record.get("character_tiers", {}))
    return {"files": len(records), "counts": dict(sorted(counts.items())),
            "tokens": dict(sorted(tokens.items())), "character_tiers": dict(sorted(tiers.items()))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=ROOT / "profiles/scka-20043.json")
    parser.add_argument("--out", type=Path, default=ROOT / "work/fpb-audit")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf8"))
    core.require(profile["region"] == "kr", "only verified KR decoder profile is supported")
    before = core.file_digest(args.iso)
    core.require(before == profile["expected_iso_sha256"], "unknown ISO version/hash")
    out = core.output_directory(args.out)
    ship = core.iso_files(args.iso, ["SHIP.AFS"])["SHIP.AFS"]
    archive = out / "SHIP.AFS"
    archive.write_bytes(ship)
    _, entries = core.archive_entries(archive)
    records = {name: inspect_fpb(blob) for name, blob in entries if name.lower().endswith(".fpb")}
    core.require(core.file_digest(args.iso) == before, "source ISO hash changed")
    report = {"schema": 1, "input_sha256": before, "ship_sha256": core.digest(ship),
              "decoder": "cp949-strict", "summary": summarize(records), "resources": records,
              "evidence": "static only; eligibility is not runtime acceptance or blanket edit permission"}
    (out / "fpb-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("FPB AUDIT PASS " + json.dumps(report["summary"]["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
