"""Remove only source-bound reviewed option periods from native PlayBook copies."""
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from audit_native_playbook import native_records
from ui_punctuation import omit_period, single_clause_period
from font_poc import require, digest


def patch_options(original, baseline, reviews, encoder):
    source_rows, source_pool = native_records(original)
    rows, pool = native_records(baseline)
    require([q[0] for q in rows] == [q[0] for q in source_rows], 'native keys changed')
    replacements = {}
    for review in reviews:
        require(review['status'] == 'reviewed' and review['role'] in ('option', 'shop-status'), 'not reviewed option/status')
        require(omit_period(review['previous_target']) == review['target']
                and single_clause_period(review['previous_target'])
                and review['target'] != review['previous_target'], 'not a single option period removal')
        key = review['native_key']
        matches = [j for j, row in enumerate(source_rows) if row[0] == key]
        require(len(matches) == 1, 'ambiguous native option key')
        j = matches[0]
        _, start, size = source_rows[j]
        require(digest(source_pool[start:start+size]) == review['source_sha256'], 'source option mismatch')
        _, start, size = rows[j]
        require(pool[start:start+size] == encoder.encode_characters(review['previous_target']), 'option baseline mismatch')
        require(j not in replacements, 'duplicate option')
        replacements[j] = encoder.encode_characters(review['target'])
    result_pool = bytearray()
    result_rows = []
    cursor = 0
    for j, (key, start, size) in enumerate(rows):
        require(cursor <= start <= start+size <= len(pool), 'overlapping native windows')
        result_pool.extend(pool[cursor:start])
        raw = replacements.get(j, pool[start:start+size])
        result_rows.append((key, len(result_pool), len(raw)))
        result_pool.extend(raw)
        cursor = start+size
    result_pool.extend(pool[cursor:])
    pool_end = 8+12*len(rows)+len(pool)
    output = (struct.pack('<I', len(rows)) + b''.join(struct.pack('<III', *row) for row in result_rows)
              + struct.pack('<I', len(result_pool)) + result_pool + baseline[pool_end:])
    check_rows, check_pool = native_records(output)
    for j, (_, start, size) in enumerate(check_rows):
        _, old_start, old_size = rows[j]
        require(check_pool[start:start+size] == replacements.get(j, pool[old_start:old_start+old_size]), 'option readback mismatch')
    return bytes(output)


def main():
    import argparse
    import collections
    import json
    from font_poc import file_digest, archive_entries, manifest_overlay
    from build_locale import checked_archive
    from localization.text import MappedEncoder
    from research_inventory import font_data
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original-ship', 'base-ship', 'review', 'map', 'font', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--base-sha256', required=True)
    p.add_argument('--original-sha256', required=True)
    a = p.parse_args()
    require(file_digest(a.original_ship) == a.original_sha256, 'original archive mismatch')
    require(file_digest(a.base_ship) == a.base_sha256, 'translated archive mismatch')
    require(not a.out.exists(), 'output already exists')
    source = dict(archive_entries(a.original_ship)[1])
    entries = archive_entries(a.base_ship)[1]
    base = dict(entries)
    encoder = MappedEncoder(json.loads(a.map.read_text('utf8'))['entries'], font_tables=font_data(a.font.read_bytes()))
    groups = collections.defaultdict(list)
    for q in json.loads(a.review.read_text('utf8'))['entries']:
        require(q['id'].startswith('SHIP/'), 'unsupported archive')
        groups[q['id'].split('/')[1]].append(q)
    overrides = {name.lower(): patch_options(source[name], base[name], rows, encoder) for name, rows in groups.items()}
    overrides[entries[0][0].lower()] = manifest_overlay(entries[0][1], {n: len(raw) for n, raw in overrides.items()})
    checked_archive(a.base_ship, a.out, overrides)
    print('OPTION_ARCHIVE_PASS resources='+str(len(groups))+' unselected_members_unchanged=true')


if __name__ == '__main__': main()
