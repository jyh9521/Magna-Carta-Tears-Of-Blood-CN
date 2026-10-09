"""Read-only, version-locked supplementary FDS/GFT/ODD field extraction.

Observed layouts are distinct from upstream USA leading-slot geometry.
Field roles and metadata semantics remain unverified; no writer is supplied.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
import font_poc as core
from afs import filename_toc
from cri_afs import Afs
from extract_strings import field
from audit_candidate_spans import classify


def layout(blob: bytes, ext: str) -> tuple[int, int, str, list[tuple[int, int]], list[tuple[int, int]]]:
    core.require(len(blob) >= 8, 'truncated record header')
    count, kind = struct.unpack_from('<II', blob)
    variants = []
    if ext == '.fds' and kind == 4:
        variants = [(2052, 'four-512-byte-fields', [(4+i*512,512) for i in range(4)], [(0,4)])]
    elif ext == '.gft' and kind == 23:
        for caps, label in [([70]*11, 'eleven-70-byte-fields'),
                            ([1000]*8+[255]+[1000]*2, 'ten-1000-one-255-byte-fields')]:
            pos, text, metadata = 4, [], [(0,4)]
            for cap in caps:
                metadata.append((pos,4));pos += 4
                text.append((pos,cap));pos += cap
            metadata.append((pos,4));pos += 4
            variants.append((pos,label,text,metadata))
    elif ext == '.odd' and kind == 12:
        variants = [(560, '80-240-200-byte-fields', [(8,80),(88,240),(328,200)], [(0,8),(528,32)])]
    elif ext == '.odd' and kind == 4:
        variants = [(20, 'metadata-only-observed-variant', [], [(0,20)])]
    matches = [v for v in variants if len(blob) == 8+count*v[0]]
    # Zero-record files cannot distinguish size-derived variants.
    core.require(count > 0 and len(matches) == 1, 'unsupported or ambiguous record geometry')
    stride, label, text, metadata = matches[0]
    return count, stride, label, text, metadata


def extract(name: str, blob: bytes) -> dict:
    count,stride,label,text,metadata = layout(blob, Path(name).suffix.lower())
    prefix = 'SHIP/'+name
    result = dict(resource=prefix, sha256=core.digest(blob), size=len(blob),
                  header_hex=blob[:8].hex(), record_count=count, stride=stride,
                  layout=label, entries=[], records=[], semantics='unverified', editable=False)
    ids = set()
    for index in range(count):
        base = 8+index*stride
        rid = struct.unpack_from('<I', blob, base)[0]
        core.require(rid not in ids, 'duplicate record id')
        ids.add(rid)
        result['records'].append(dict(index=index, record_id=rid, offset=base,
            source_sha256=core.digest(blob[base:base+stride]),
            metadata=[dict(offset=base+off, length=length,
                           raw_hex=blob[base+off:base+off+length].hex()) for off,length in metadata]))
        # Metadata ranges plus fixed fields must partition the full record.
        cursor = 0
        for off,length in sorted(text+metadata):
            core.require(off == cursor, 'record partition gap or overlap')
            cursor += length
        core.require(cursor == stride, 'record partition does not cover stride')
        for number,(off,cap) in enumerate(text):
            offset = base+off;slot = blob[offset:offset+cap];nul = slot.find(b'\0')
            core.require(nul >= 0 and not any(slot[nul:]), 'unterminated or nonzero field padding')
            result['entries'].append(field(f'{prefix}/record-index/{index}/field/{number}',
                slot[:nul], offset, record_id=rid, record_index=index, field_index=number,
                field_span=cap, field_sha256=core.digest(slot), byte_capacity=cap-1,
                semantic='structured-text-field-unverified-role', editable=False))
    return result


def audit(catalog_path: Path, ship: Path, out: Path) -> dict:
    before = core.file_digest(catalog_path)
    catalog = json.loads(catalog_path.read_text('utf8'))
    manifest = json.loads((catalog_path.parent/'manifest.json').read_text('utf8'))
    ship_hash = core.file_digest(ship)
    core.require(ship_hash == manifest['archives']['SHIP.AFS'], 'SHIP identity mismatch')
    core.require(catalog['iso_sha256'] == manifest['iso_sha256'], 'catalog identity mismatch')
    archive = Afs.open(ship);names = filename_toc(archive)
    core.require(len(set(names)) == len(names), 'duplicate archive name')
    old = {r['resource']:r for r in catalog['resources']}
    resources, coverage, candidate_coverage = [], [], []
    with ship.open('rb') as stream:
        for index,name in enumerate(names):
            if Path(name).suffix.lower() not in ('.fds','.gft','.odd'):
                continue
            blob = archive.read_entry(index,stream)
            prior = old['SHIP/'+name]
            core.require(core.digest(blob) == prior['sha256'], 'resource identity mismatch')
            resource = extract(name,blob)
            for row in resource['entries']:
                relation = classify(row,prior['entries'],len(blob))
                row['prior_primary_coverage'] = relation
                coverage.append(relation['relation'])
            for candidate in prior.get('candidates', []):
                candidate_coverage.append(dict(resource=resource['resource'], id=candidate['id'],
                    **classify(candidate,resource['entries'],len(blob))))
            resources.append(resource)
    rows = [e for r in resources for e in r['entries']]
    summary = dict(schema=1, source_catalog_sha256=before, ship_sha256=ship_hash,
        resources=len(resources), records=sum(r['record_count'] for r in resources),
        fields=len(rows), nonempty_fields=sum(e['source_bytes']>0 for e in rows),
        decode_failed=sum(e['decode']=='failed' for e in rows),
        quarantined_controls=sum(e.get('controls')=='quarantined' for e in rows),
        prior_primary_relations=dict(sorted(Counter(coverage).items())),
        prior_candidate_relations=dict(sorted(Counter(r['relation'] for r in candidate_coverage).items())),
        layouts=[dict(resource=r['resource'], layout=r['layout'], records=r['record_count'],
                      stride=r['stride'], fields=len(r['entries']), size=r['size']) for r in resources],
        complete_game_text=False, translation_gate='coverage-audit-not-complete',
        result='supplementary structured fields exported; visibility and encoding review pending')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name,value in [('summary.json',summary),('record-fields.json',dict(schema=1,resources=resources)),
                       ('candidate-coverage.json',candidate_coverage)]:
        path = out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(path.read_text('utf8')) == value, 'output reopen mismatch')
    core.require(core.file_digest(catalog_path)==before and core.file_digest(ship)==ship_hash,'input changed')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--ship',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.catalog,args.ship,args.out),sort_keys=True))


if __name__ == '__main__':
    main()
