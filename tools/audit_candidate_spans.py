"""Read-only byte-interval audit of slot discovery candidates.

Coverage means original leading-field byte coverage, not visible-text semantics.
Candidate text and uncovered fragments are retained only in ignored output.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
import font_poc as core
from afs import filename_toc
from cri_afs import Afs
from extract_strings import extract_resource, field
from translate.slot import SLOT_FORMATS, parse_slot_file, split_slot


def span(row: dict, size: int) -> tuple[int, int]:
    start, length = row['offset'], row['source_bytes']
    core.require(type(start) is int and type(length) is int
                 and 0 <= start <= size and 0 <= length <= size-start,
                 'invalid source interval')
    return start, start+length


def classify(candidate: dict, entries: list[dict], size: int) -> dict:
    """Subtract a union of leading-field intervals, never slot capacities."""
    start, end = span(candidate, size)
    overlaps, intervals = [], []
    exact = []
    for entry in entries:
        left, right = span(entry, size)
        if (left, right) == (start, end):
            exact.append(entry['id'])
        left, right = max(left, start), min(right, end)
        if left < right:
            overlaps.append(entry['id'])
            intervals.append((left, right))
    merged = []
    for left, right in sorted(intervals):
        if merged and left <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(right, merged[-1][1]))
        else:
            merged.append((left, right))
    uncovered, cursor = [], start
    for left, right in merged:
        if cursor < left:
            uncovered.append(dict(offset=cursor, source_bytes=left-cursor))
        cursor = right
    if cursor < end:
        uncovered.append(dict(offset=cursor, source_bytes=end-cursor))
    covered = sum(right-left for left, right in merged)
    relation = ('empty' if start == end else 'exact-primary-span' if exact else
                'contained-in-primary-union' if covered == end-start else
                'partially-overlaps-primary' if covered else 'outside-primary')
    return dict(relation=relation, exact_primary_ids=exact,
                overlapping_primary_ids=overlaps, covered_bytes=covered,
                uncovered_bytes=end-start-covered, uncovered_intervals=uncovered)


def placement(start: int, end: int, header: int, slots: list[tuple[bytes, int]],
              stride: int) -> list[dict]:
    """Split uncovered bytes at observed header/leading/padding/trailer bounds."""
    regions = [(0, header, 'header', None)]
    for index, (slot, cap) in enumerate(slots):
        base = header+index*stride
        raw, tail, _ = split_slot(slot, cap)
        regions.extend([(base, base+len(raw), 'leading-field', index),
                        (base+len(raw), base+tail, 'terminator-or-padding', index),
                        (base+tail, base+cap, 'observed-trailer', index)])
    return [dict(offset=max(start, left), source_bytes=min(end, right)-max(start, left),
                 region=kind, slot=index)
            for left, right, kind, index in regions if max(start, left) < min(end, right)]


def audit(catalog_path: Path, ship: Path, out: Path) -> dict:
    source_hash, ship_hash = core.file_digest(catalog_path), core.file_digest(ship)
    manifest = json.loads((catalog_path.parent/'manifest.json').read_text('utf8'))
    catalog = json.loads(catalog_path.read_text('utf8'))
    core.require(ship_hash == manifest['archives']['SHIP.AFS'], 'SHIP identity mismatch')
    core.require(catalog['iso_sha256'] == manifest['iso_sha256'], 'catalog identity mismatch')
    archive = Afs.open(ship)
    names = filename_toc(archive)
    core.require(len(names) == len(set(names)), 'duplicate archive name')
    index = {name:i for i, name in enumerate(names)}
    rows, by_extension, fragments = [], {}, {}
    with ship.open('rb') as stream:
        for resource in catalog['resources']:
            if 'candidates' not in resource:
                continue
            name = resource['resource'].split('/', 1)[1]
            blob = archive.read_entry(index[name], stream)
            core.require(extract_resource(name, blob) == resource, 're-extraction mismatch: '+name)
            ext = Path(name).suffix.lower()
            header, slots = parse_slot_file(blob, ext)
            stride = SLOT_FORMATS[ext][1]
            for entry in resource['entries']:
                left, right = span(entry, len(blob))
                core.require(core.digest(blob[left:right]) == entry['source_sha256'], 'primary identity mismatch')
            for candidate in resource['candidates']:
                left, right = span(candidate, len(blob))
                core.require(core.digest(blob[left:right]) == candidate['source_sha256'], 'candidate identity mismatch')
                relation = classify(candidate, resource['entries'], len(blob))
                for interval in relation['uncovered_intervals']:
                    start, end = span(interval, len(blob))
                    interval['placement'] = placement(start, end, len(header), slots, stride)
                    # Retain full candidate as the authoritative decode unit. A
                    # subtraction boundary can bisect a multibyte character.
                    key = (resource['resource'], start, end)
                    if key not in fragments:
                        fragments[key] = dict(resource=resource['resource'],
                            fragment=field(f"{resource['resource']}/uncovered/{start}/{end-start}",
                                blob[start:end], start, semantic='unverified-byte-fragment', editable=False),
                            placement=interval['placement'], candidate_ids=[])
                    fragments[key]['candidate_ids'].append(candidate['id'])
                rows.append(dict(resource=resource['resource'], candidate=candidate,
                                 **relation, semantic='unverified', editable=False))
                by_extension.setdefault(ext, Counter())[relation['relation']] += 1
    summary = dict(schema=1, source_catalog_sha256=source_hash, ship_sha256=ship_hash,
        candidates=len(rows), relations=dict(sorted(Counter(r['relation'] for r in rows).items())),
        by_extension={ext:dict(sorted(count.items())) for ext,count in sorted(by_extension.items())},
        candidates_with_uncovered_bytes=sum(r['uncovered_bytes'] > 0 for r in rows),
        unique_uncovered_intervals=len(fragments),
        fragment_decode=dict(sorted(Counter(f['fragment']['decode'] for f in fragments.values()).items())),
        fragment_placements=dict(sorted(Counter(p['region'] for f in fragments.values() for p in f['placement']).items())),
        complete_game_text=False, translation_gate='coverage-audit-not-complete',
        result='byte-coverage-classified; visible-text semantics unresolved')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('summary.json', summary), ('candidate-spans.json', rows),
                        ('uncovered-fragments.json', list(fragments.values()))]:
        path = out/name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        core.require(json.loads(path.read_text('utf8')) == value, 'output reopen mismatch')
    core.require(core.file_digest(catalog_path) == source_hash and core.file_digest(ship) == ship_hash,
                 'input changed')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--ship', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.catalog, args.ship, args.out), sort_keys=True))


if __name__ == '__main__':
    main()
