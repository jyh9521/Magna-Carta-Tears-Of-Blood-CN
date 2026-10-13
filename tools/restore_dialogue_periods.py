"""Restore explicitly reviewed narrative periods in translated fixed-slot copies.

Offsets, capacities and source identities come from the audited catalog. No
extension-based write selection or global sentence normalization is performed.
"""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
import font_poc as core
from import_audited_fields import fixed_extent
from source_interpretation import source_text, control_policy, encode_target
from localization.text import validate_target


def restore_fields(original, baseline, rows, encoder):
    changed = bytearray(baseline)
    ranges, proofs = [], []
    for entry, review in rows:
        core.require(review.get('status') == 'reviewed' and review.get('role') == 'narrative', 'not reviewed narrative')
        core.require(entry['source_sha256'] == review['source_sha256'], 'source identity mismatch')
        old, target = review['previous_target'], review['target']
        core.require(target == old + '。' and old and old[-1] not in '。！？!?…～', 'not a terminal period restoration')
        at = entry['offset']
        span, _ = fixed_extent(entry)
        core.require(0 <= at and at + span <= len(baseline) == len(original), 'slot outside resource')
        core.require(core.digest(original[at:at + entry['source_bytes']]) == entry['source_sha256'], 'original source mismatch')
        before, after = encode_target(encoder, entry, old), encode_target(encoder, entry, target)
        core.require(len(after) < span, 'field overflow')
        core.require(baseline[at:at + span] == before + bytes(span - len(before)), 'translated baseline mismatch ' + review['id'])
        core.require(not any(at < b and a < at + span for a, b in ranges), 'overlapping fields')
        validate_target(source_text(entry), target, control_policy=control_policy(entry, target))
        changed[at:at + span] = after + bytes(span - len(after))
        ranges.append((at, at + span))
        proofs.append(dict(id=review['id'], offset=at, span=span, old_hex=before.hex(), new_hex=after.hex(), previous_target=old, target=target))
    cursor = 0
    for start, end in sorted(ranges):
        core.require(baseline[cursor:start] == changed[cursor:start], 'unselected bytes changed')
        cursor = end
    core.require(baseline[cursor:] == changed[cursor:], 'unselected tail changed')
    return bytes(changed), proofs
