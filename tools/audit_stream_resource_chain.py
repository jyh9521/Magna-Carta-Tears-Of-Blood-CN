"""Verify single-record wrappers and exact SHIP bodies in celfid's tail.

Byte correspondence does not establish text visibility or native serialization.
"""
import argparse
import json
import struct
import sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
SHIP_HASH = '09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a'
CONTEXT_HASH = '2854119fbeafeede363009ec7af8d8662ea549f13aec78eb8db80384e09414c4'
CHAIN_START = 3218646
CHAIN_END = 4185028


def parse_chain(bundle, start, end, sources):
    core.require(type(start) is int and type(end) is int and 0 <= start < end <= len(bundle), 'chain bounds')
    rows = []
    pos = start
    identities = set()
    while pos < end:
        core.require(pos + 132 <= end, 'truncated resource wrapper')
        record = bundle[pos:pos+132]
        path_raw, size = record[:128], struct.unpack_from('<I', record, 128)[0]
        nul = path_raw.find(b'\0')
        core.require(nul >= 0 and not any(path_raw[nul:]), 'wrapper padding')
        path = path_raw[:nul].decode('ascii', 'strict')
        core.require(path.startswith('..\\') and len(path.split('\\')) == 3, 'resource path shape')
        name = path.split('\\')[-1]
        core.require(name in sources and name not in identities, 'missing or repeated resource identity')
        source = sources[name]
        core.require(size == len(source) and size > 0 and pos + 132 + size <= end, 'resource body size')
        body = bundle[pos+132:pos+132+size]
        core.require(body == source, 'resource source bytes mismatch')
        rows.append(dict(path=path, resource='SHIP/'+name, start=pos, body_start=pos+132, end=pos+132+size, bytes=size, sha256=core.digest(body), wrapper_sha256=core.digest(record), editable=False, runtime_visibility_verified=False))
        identities.add(name)
        pos += 132 + size
    core.require(pos == end, 'chain end mismatch')
    return rows


def attach_contexts(contexts, bundle, chain):
    result = []
    for item in contexts:
        row = dict(item)
        start, end = row['offset'], row['offset']+row['bytes']
        core.require(0 <= start < end <= len(bundle) and core.digest(bundle[start:end]) == row['source_sha256'], 'candidate bytes mismatch')
        if row['category'] == 'unresolved-byte-context':
            for span in chain:
                if span['start'] <= start and end <= span['body_start']:
                    row.update(category='source-resource-wrapper', context=dict(start=span['start'], end=span['body_start'], kind='source-resource-wrapper', resource=span['resource']))
                    break
                if span['body_start'] <= start and end <= span['end']:
                    row.update(category='source-identical-resource-body', context=dict(start=span['body_start'], end=span['end'], kind='source-identical-resource-body', resource=span['resource']))
                    break
        result.append(row)
    return result


def audit(file, ship, contexts_path, out):
    core.require(core.file_digest(file) == FILE_HASH and core.file_digest(ship) == SHIP_HASH, 'archive identity mismatch')
    # Bind the earlier all-candidate snapshot rather than accepting arbitrary labels.
    expected = CONTEXT_HASH
    core.require(core.file_digest(contexts_path) == expected, 'context snapshot mismatch')
    afs = Afs.open(file)
    names = filename_toc(afs)
    with file.open('rb') as f: bundle, _ = unpack_chunks(afs.read_entry(names.index('celfid.lix'), f))
    core.require(core.digest(bundle) == BUNDLE_HASH, 'bundle identity mismatch')
    sa = Afs.open(ship)
    sn = filename_toc(sa)
    sources = {}
    # Read only names requested by bounded wrapper geometry; source matching follows.
    pos = CHAIN_START
    with ship.open('rb') as f:
        while pos < CHAIN_END:
            core.require(pos+132 <= CHAIN_END, 'wrapper bounds')
            name = bundle[pos:pos+128].split(b'\0', 1)[0].decode('ascii').split('\\')[-1]
            core.require(sn.count(name) == 1, 'SHIP identity missing or ambiguous')
            sources[name] = sa.read_entry(sn.index(name), f)
            size = struct.unpack_from('<I', bundle, pos+128)[0]
            core.require(size > 0 and pos+132+size <= CHAIN_END, 'wrapper advance bounds')
            pos += 132 + size
    chain = parse_chain(bundle, CHAIN_START, CHAIN_END, sources)
    old = json.loads(contexts_path.read_text('utf8'))
    rows = attach_contexts(old, bundle, chain)
    summary = dict(schema=1, previous_context_sha256=expected, chain_start=CHAIN_START, chain_end=CHAIN_END, chain_bytes=CHAIN_END-CHAIN_START, resources=len(chain), body_bytes=sum(x['bytes'] for x in chain), wrapper_bytes=132*len(chain), candidates=len(rows), counts=dict(sorted(Counter(x['category'] for x in rows).items())), recontextualized=sum(a!=b for a,b in zip(old,rows)), source_modified=False, semantic_review_complete=False, complete_game_text=False, translation_gate='coverage-audit-pending')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('chain.json', chain), ('contexts.json', rows), ('summary.json', summary)]:
        p=out/name; p.write_text(json.dumps(value, indent=2)+'\n', 'utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'JSON reopen')
    core.require(core.file_digest(file) == FILE_HASH and core.file_digest(ship) == SHIP_HASH, 'source modified')
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['file','ship','contexts','out']: p.add_argument('--'+n, type=Path, required=True)
    a=p.parse_args(); print(json.dumps(audit(a.file,a.ship,a.contexts,a.out), sort_keys=True))
