"""Version-locked source catalog; structural fields and heuristic candidates stay separate.

Reuses upstream parsers. This exporter never writes game resources and does not
grant reinsertion permission to decoded strings or heuristic byte runs.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'src'), str(ROOT/'lib')]
import font_poc as core
from audit_text_resources import inspect_fpb
from localization.text import protected_tokens
from translate.catalog import SUPPORTED_EXTS
from translate.fpb import parse_fpb_raw, synthesize_implicit_seq0
from translate.slot import SLOT_FORMATS, parse_slot_file, split_slot
from translate.region import find_text_regions
from translate.celfid import decompress_chunked


def field(identity: str, raw: bytes, offset: int, **metadata) -> dict:
    row = dict(id=identity, offset=offset, source_sha256=core.digest(raw),
               source_bytes=len(raw), **metadata)
    try:
        text = raw.decode('cp949', errors='strict')
    except UnicodeDecodeError as error:
        return dict(row, decode='failed', error_byte=error.start, raw_hex=raw.hex())
    row.update(decode='strict', references={'ko-KR': text},
               canonical_encoding=text.encode('cp949') == raw)
    try:
        row['protected_tokens'] = protected_tokens(text)
        row['controls'] = 'recognized'
    except ValueError as error:
        row.update(controls='quarantined', control_reason=str(error))
    if any(ord(ch) < 32 for ch in text):
        row['controls'] = 'quarantined'
    return row


def scan_candidates(blob: bytes, prefix: str) -> list[dict]:
    """NUL-delimited CP949 runs and upstream ASCII runs; all read-only.

    This is a discovery inventory, not a format parser. Binary noise can be
    valid CP949; Korean-containing runs also need semantic confirmation.
    """
    rows, spans = [], set()
    for match in re.finditer(rb'[^\x00]+\x00', blob):
        raw = match.group()[:-1]
        if len(raw) > 8192:
            continue
        try:
            text = raw.decode('cp949', errors='strict')
        except UnicodeDecodeError:
            continue
        if (not any('\uac00' <= ch <= '\ud7a3' for ch in text)
                or any(ord(ch) < 32 for ch in text)):
            continue
        offset = match.start()
        rows.append(field(f'{prefix}/candidate/{offset}', raw, offset,
                          semantic='unverified', editable=False,
                          detection='nul-cp949-hangul-heuristic'))
        spans.add((offset, len(raw)))
    for offset, length in find_text_regions(blob):
        if (offset, length) not in spans:
            rows.append(field(f'{prefix}/ascii/{offset}', blob[offset:offset+length], offset,
                              semantic='identifier-or-text-unverified', editable=False,
                              detection='upstream-ascii-heuristic'))
    return sorted(rows, key=lambda r: (r['offset'], r['id']))


def extract_resource(name: str, blob: bytes) -> dict:
    prefix = 'SHIP/'+name
    ext = Path(name).suffix.lower()
    result = dict(resource=prefix, sha256=core.digest(blob), size=len(blob), entries=[])
    rows = result['entries']
    if ext == '.fpb':
        audit = inspect_fpb(blob)
        result['audit'] = audit
        if audit['status'] != 'parsed':
            return result
        _, windows, pool = parse_fpb_raw(blob)
        # Export the entire pool as reference to preserve uncovered prefix/gaps.
        result['pool'] = field(prefix+'/pool', pool, 0, editable=False,
                               semantic='reference-only')
        seen = Counter(seq for seq, _, _ in synthesize_implicit_seq0(windows, len(pool)))
        for index, (seq, offset, length) in enumerate(synthesize_implicit_seq0(windows, len(pool))):
            valid = offset + length <= len(pool)
            row = field(f'{prefix}/seq/{seq}', pool[offset:offset+length], offset,
                        seq=seq, view_index=index, requested_length=length,
                        bounds_valid=valid, semantic='dialogue-window',
                        editable=False)
            if seen[seq] > 1:
                row['id'] += f'/view/{index}'
            row['backend_eligible'] = bool(valid and audit['partition_backend_eligible']
                and row['decode']=='strict' and row.get('controls')=='recognized')
            rows.append(row)
    elif ext == '.tui':
        if len(blob) < 8:
            result['error'] = 'truncated-header'
            return result
        count, kind = struct.unpack_from('<II', blob)
        result.update(record_count=count, kind=kind)
        if kind != 2 or len(blob) != 8+count*516:
            result['error'] = 'unsupported-geometry'
            return result
        ids = [struct.unpack_from('<I', blob, 8+i*516)[0] for i in range(count)]
        result['unique_record_ids'] = len(set(ids)) == count
        for index, rid in enumerate(ids):
            for half in range(2):
                offset = 12+index*516+half*256
                slot = blob[offset:offset+256]
                nul = slot.find(b'\0')
                raw = slot if nul < 0 else slot[:nul]
                rows.append(field(f'{prefix}/record/{rid}/field/{half}/index/{index}', raw, offset,
                    record_id=rid, record_index=index, half=half, slot_sha256=core.digest(slot),
                    terminated=nul>=0, padding_clean=nul>=0 and not any(slot[nul:]),
                    byte_capacity=255, semantic='display-or-identifier-unverified', editable=False))
    elif ext in SLOT_FORMATS:
        try:
            header, slots = parse_slot_file(blob, ext)
        except ValueError as error:
            result['error'] = str(error)
            return result
        stride = SLOT_FORMATS[ext][1]
        result.update(header_bytes=len(header), stride=stride,
                      geometry='upstream-USA-profile; KR-semantics-unverified')
        for index, (slot, cap) in enumerate(slots):
            raw, tail, trailer = split_slot(slot, cap)
            rows.append(field(f'{prefix}/slot/{index}', raw, len(header)+index*stride,
                slot=index, slot_sha256=core.digest(slot), complete_slot=cap==stride,
                terminated=b'\0' in slot, observed_byte_capacity=tail-1,
                trailer_sha256=core.digest(trailer), trailer_bytes=len(trailer),
                semantic='leading-field-unverified', editable=False))
        # Other strings inside trailers are discovery candidates, not extra slots.
        result['candidates'] = scan_candidates(blob, prefix)
    else:
        result['entries'] = scan_candidates(blob, prefix)
        result['geometry'] = 'heuristic-only'
    return result


def seed_targets(resources: list[dict], locale: dict) -> list[dict]:
    """Join known drafts only by stable geometry and matching source hash."""
    index = {r['resource']:r for r in resources}
    targets = []
    for plan in locale.get('text_resources', []):
        resource = index['SHIP/'+plan['resource']]
        core.require(resource['sha256']==plan['expected_sha256'], 'seed resource mismatch')
        for entry in plan['targets']:
            if plan['kind']=='fpb':
                candidates = [r for r in resource['entries'] if r.get('seq')==entry['seq']]
                expected = entry['source_sha256']
                hash_key = 'source_sha256'
            else:
                profile = entry['profile']
                candidates = [r for r in resource['entries'] if r.get('record_index')==profile['record_index']
                              and r.get('record_id')==profile['record_id'] and r.get('half')==0]
                expected = profile['expected_slot_sha256']
                hash_key = 'slot_sha256'
            core.require(len(candidates)==1 and candidates[0][hash_key]==expected, 'seed field mismatch')
            targets.append(dict(id=candidates[0]['id'], source_sha256=candidates[0]['source_sha256'],
                                target=entry['target'], status='trial-draft'))
    for plan in locale.get('name_slot_overlays', []):
        resource = index['SHIP/'+plan['resource']]
        core.require(resource['sha256']==plan['expected_sha256'], 'seed name resource mismatch')
        for entry in plan['targets']:
            rows = [r for r in resource['entries'] if r.get('slot')==entry['slot']]
            core.require(len(rows)==1, 'seed name ambiguous')
            targets.append(dict(id=rows[0]['id'], source_sha256=rows[0]['source_sha256'],
                                target=entry['target'], status='trial-draft'))
    core.require(len({r['id'] for r in targets})==len(targets), 'duplicate seed target')
    return targets


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', required=True, type=Path)
    p.add_argument('--profile',type=Path,default=ROOT/'profiles/scka-20043.json')
    p.add_argument('--seed',type=Path,default=ROOT/'locales/zh-CN/opening-trial-02.json')
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    profile=json.loads(args.profile.read_text('utf8'))
    core.require(profile['region']=='kr', 'unsupported source region')
    before=core.file_digest(args.iso)
    core.require(before==profile['expected_iso_sha256'], 'unknown ISO version/hash')
    out=core.output_directory(args.out)
    core.require(not any(out.iterdir()), 'output must be empty; catalog overwrite rejected')
    blobs=core.iso_files(args.iso,['SHIP.AFS','FILE.AFS'])
    # AFS reader is reused; only two transient archives, no ISO duplication.
    archives={}
    for name, blob in blobs.items():
        path=out/name; path.write_bytes(blob)
        entries=core.archive_entries(path)[1]
        core.require(len({key for key,_ in entries})==len(entries),'duplicate archive resource name')
        archives[name]=dict(entries)
    ship=archives['SHIP.AFS']
    resources=[extract_resource(name,blob) for name,blob in sorted(ship.items())
               if Path(name).suffix.lower() in SUPPORTED_EXTS]
    bundle=decompress_chunked(archives['FILE.AFS']['celfid.lix'])
    core.require(core.digest(bundle)==profile['expected_bundle_sha256'], 'bundle identity mismatch')
    cached=scan_candidates(bundle, 'FILE/celfid.lix')
    mirrors=[]
    for resource in resources:
        raw=ship[resource['resource'].split('/',1)[1]]
        if len(raw)<20:
            continue
        locations=[];start=0
        while True:
            pos=bundle.find(raw,start)
            if pos<0:break
            locations.append(pos);start=pos+1
        if locations:
            mirrors.append(dict(resource=resource['resource'],sha256=resource['sha256'],
                                decompressed_offsets=locations,
                                interpretation='exact resource mirror; linked-group semantics unverified'))
    summaries={}
    for ext in sorted(SUPPORTED_EXTS):
        rs=[r for r in resources if Path(r['resource']).suffix.lower()==ext]
        rows=[e for r in rs for e in r['entries']]
        summaries[ext]=dict(files=len(rs), fields=len(rows), nonempty=sum(e['source_bytes']>0 for e in rows),
            decoded=sum(e['decode']=='strict' for e in rows), decode_failed=sum(e['decode']=='failed' for e in rows),
            quarantined_controls=sum(e.get('controls')=='quarantined' for e in rows),
            backend_eligible=sum(e.get('backend_eligible',False) for e in rows),
            additional_candidates=sum(len(r.get('candidates',[])) for r in rs))
    draft=json.loads(args.seed.read_text('utf8'))
    targets=seed_targets(resources,draft)
    seeded={row['id']: row for row in targets}
    template=[]
    for resource in resources:
        for row in resource['entries']:
            if row['decode']=='strict' and row['source_bytes']:
                template.append(seeded.get(row['id'],dict(id=row['id'],
                    source_sha256=row['source_sha256'],target='',status='untranslated',
                    review_required=not row.get('backend_eligible',False))))
    catalog=dict(schema=1,source_locale='ko-KR',encoding='cp949-strict',iso_sha256=before,
                 resources=resources,celfid_candidates=cached,celfid_resource_mirrors=mirrors)
    manifest=dict(schema=1,iso_sha256=before,archives={n:core.digest(b) for n,b in blobs.items()},
        extensions=summaries,source_fields=sum(s['fields'] for s in summaries.values()),
        seeded_targets=len(targets),celfid_candidates=len(cached),
        target_template_entries=len(template),celfid_mirrored_resources=len(mirrors),
        ship_extension_inventory=dict(sorted(Counter(Path(n).suffix.lower() or '<none>' for n in ship).items())),
        complete_game_text=False,
        unresolved=['heuristic region identifiers','KR slot trailer fields','FPB decode/partition exceptions',
                    'UE2 textures and unparsed package text','ELF hard-coded text','SFD subtitle corpus',
                    'celfid structural/linked-group semantics','USA/JP reference ISO unavailable'])
    (out/'source-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n','utf8')
    (out/'target-seed.json').write_text(json.dumps(dict(schema=1,locale=draft['locale'],entries=targets),ensure_ascii=False,indent=2)+'\n','utf8')
    (out/'target-template.json').write_text(json.dumps(dict(schema=1,locale=draft['locale'],entries=template),ensure_ascii=False,indent=2)+'\n','utf8')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
    core.require(core.file_digest(args.iso)==before, 'original ISO changed')
    print(f"CATALOG PASS resources={len(resources)} fields={manifest['source_fields']} seeded_targets={len(targets)} complete_game_text=false")


if __name__=='__main__': main()
