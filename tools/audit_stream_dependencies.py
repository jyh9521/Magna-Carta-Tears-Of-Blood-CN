"""Bounded cross-package dependency source oracle after the Core root tree.

Script repetitions and native mip-order projections are diagnostic matches,
not independent stream parsing or runtime equivalence. Unknown spans stop.
"""
from __future__ import annotations
from pathlib import Path
import argparse, sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
import font_poc as core
from audit_container_payloads import unpack_chunks, probe_all_packages
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import ordinary_exports, Reader, property_block
from audit_compiled_scripts import body, compiled_script
from audit_class_defaults import class_body
from audit_stream_script_correspondence import align_prefix
from audit_stream_field_prefix import compare_piece
from audit_stream_class_headers import occurrences, check_tables, full_imports
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH

def resolve_reference(packs, pkg, index):
    if not index:
        return None
    core.require(pkg in packs, 'missing source package')
    _, tables, exports = packs[pkg]
    if index > 0:
        core.require(index <= len(exports), 'export reference out of bounds')
        return (pkg, index)
    imports = tables['imports']
    parts = []
    visited = set()
    outer = index
    while outer < 0:
        core.require(outer not in visited and -outer <= len(imports), 'import cycle or bounds')
        visited.add(outer)
        entry = imports[-outer - 1]
        parts.append(entry['name'])
        outer = entry['outer']
    core.require(outer == 0 and len(parts) >= 2, 'invalid import scope')
    target = parts[-1] + '.u'
    core.require(target in packs, 'missing imported package')
    matches = []
    target_exports = packs[target][2]
    for entry in target_exports:
        path = [entry['name']]
        outer = entry['outer']
        visited = set()
        while outer > 0:
            core.require(outer not in visited and outer <= len(target_exports), 'export outer cycle or bounds')
            visited.add(outer)
            parent = target_exports[outer - 1]
            path.append(parent['name'])
            outer = parent['outer']
        if outer == 0 and path == parts[:-1]:
            matches.append(entry['index'])
    core.require(len(matches) == 1, 'import identity ambiguous or absent')
    return (target, matches[0])

def equivalent_native_span(candidates):
    """Return common exact bytes without selecting an ambiguous object identity."""
    if not candidates:
        return None
    values = {raw for _, raw in candidates}
    if len(values) != 1:
        return None
    raw = next(iter(values))
    core.require(len(raw) >= 16, 'native span too short')
    identities = [key for key, _ in candidates]
    core.require(len(set(identities)) == len(identities), 'duplicate candidate identity')
    return identities, raw


def audit(archive, out, equivalent_native=False):
    core.require(core.file_digest(archive) == FILE_HASH, 'FILE identity mismatch')
    a = Afs.open(archive)
    names = filename_toc(a)
    packs = {}
    with archive.open('rb') as f:
        b, _ = unpack_chunks(a.read_entry(names.index('celfid.lix'), f))
        core.require(core.digest(b) == BUNDLE_HASH, 'bundle identity mismatch')
        for ix, name in enumerate(names):
            raw = a.read_entry(ix, f)
            if raw.startswith(bytes.fromhex('c1832a9e')):
                tables = package_tables(raw)
                packs[name] = (raw, tables, ordinary_exports(raw, tables))
    for st in probe_all_packages(b):
        name = Path(st['wrapper_path']).name
        if name in packs:
            original, ts, ex = packs[name]
            check_tables(dict(ts, exports=ex, imports=full_imports(original, ts)), st)
    from audit_stream_field_prefix import probe
    ct = next((t for t in probe_all_packages(b) if t['wrapper_path'].endswith('/Core.u')))
    cp = probe(b, packs['Core.u'][0], ct, extended=True)
    core.require(cp['root_complete'] and cp['question'] is None, 'initial Core oracle incomplete')
    seen = {('Core.u', i) for i in cp['completed_piece_sets']}
    followed = set(seen)
    anchors = {}
    for pkg, (original, ts, ex) in packs.items():
        for e in ex:
            if e['class_index'] != 0:
                continue
            raw = original[e['offset']:e['offset'] + e['size']]
            parsed = class_body(raw, ts, e, compiled_script)
            for offset in occurrences(b, raw[:parsed['header']['script_start']]):
                core.require(offset not in anchors, 'ambiguous Class header identity')
                anchors[offset] = (pkg, e['index'])
    pos = cp['stop_offset']
    initial_pos = pos
    chunks = []
    edges = []
    completed = []
    question = None

    def resolve(pkg, index):
        return resolve_reference(packs, pkg, index)

    def piece(raw, key, part):
        nonlocal pos
        check = compare_piece(b, pos, raw)
        core.require(check['matched'], str((key, part, check)))
        if raw:
            chunks.append(dict(package=key[0], export=key[1], part=part, **check))
        pos += len(raw)

    def obj(key, follow=True, depth=0):
        nonlocal pos
        if not key:
            return
        core.require(depth < 512, str(('depth', key)))
        pkg, index = key
        original, ts, ex = packs[pkg]
        e = ex[index - 1]
        raw = original[e['offset']:e['offset'] + e['size']]
        if key in seen:
            if follow and key not in followed:
                followed.add(key)
                r = Reader(raw, 0 if e['class_index'] == 0 else property_block(raw, ts['names'])['end'])
                r.index()
                nxt = r.index()
                if nxt:
                    obj(resolve(pkg, nxt), True, depth)
            return
        seen.add(key)
        if e['super_index']:
            parent = resolve(pkg, e['super_index'])
            edges.append((key, parent, 'super'))
            obj(parent, False, depth + 1)
        if e['class_index'] == 0:
            p = class_body(raw, ts, e, compiled_script)
            script = p['script']
            split = script['end'] if script else p['header']['script_start']
            nxt = p['header']['next_reference']
            child = p['header']['children_reference']
        elif e['class'] in ['Function', 'NativeFunction', 'State', 'Struct']:
            p = body(raw, ts, e)
            script = p['script']
            split = script['end']
            nxt = p['header']['next_reference']
            child = p['header']['children_reference']
        else:
            p = property_block(raw, ts['names'])
            r = Reader(raw, p['end'])
            r.index()
            nxt = r.index()
            split = len(raw)
            child = 0
            script = None
        if script:
            fit = align_prefix(b, pos, raw, script)
            if fit['matched'] and (not fit['unique_end']):
                nextbytes = raw[split:]
                if child and resolve(pkg, child) not in seen:
                    nk = resolve(pkg, child)
                    nb, nt, ne = packs[nk[0]]
                    nexp = ne[nk[1] - 1]
                    nr = nb[nexp['offset']:nexp['offset'] + nexp['size']]
                    if nexp['class'] in ['Function', 'NativeFunction', 'State', 'Struct']:
                        np = body(nr, nt, nexp)
                        nextbytes = nr[:np['script']['start']]
                    else:
                        nextbytes = nr
                good = [end for end in fit['ends'] if nextbytes and b[end['offset']:end['offset'] + len(nextbytes)] == nextbytes]
                if len(good) == 1:
                    fit['ends'] = good
                    fit['unique_end'] = True
                    fit['next_prefix_disambiguated'] = True
            core.require(fit['matched'] and fit['unique_end'], str((key, e['name'], fit)))
            end = fit['ends'][0]
            chunks.append(dict(package=pkg, export=index, part='bounded-prefix', start=pos, next_prefix_disambiguated=fit.get('next_prefix_disambiguated', False), **end))
            pos = end['offset']
        else:
            piece(raw[:split], key, 'prefix')
        if child:
            obj(resolve(pkg, child), True, depth + 1)
        piece(raw[split:], key, 'tail')
        completed.append(key)
        if e['class'] in ('StructProperty', 'ArrayProperty'):
            r = Reader(raw, property_block(raw, ts['names'])['end'])
            r.index()
            r.index()
            r.integer('I')
            flags = r.integer('I')
            r.index()
            r.take(2) if flags & 32 else None
            target = r.index()
            core.require(r.pos == len(raw) or e['class'] == 'ClassProperty', str(('target trailing', key, e['class'], r.pos, len(raw))))
            if target:
                obj(resolve(pkg, target), False, depth + 1)
        if follow:
            followed.add(key)
            if nxt:
                obj(resolve(pkg, nxt), True, depth)
    instances = []
    from audit_texture_mips import mips
    for pkg, (original, ts, ex) in packs.items():
        for e in ex:
            if (equivalent_native and e['class'] == 'Texture') or (e['class_index'] > 0 and ex[e['class_index'] - 1]['name'] == 'Texture'):
                instances.append((pkg, e['index']))
    roots = []
    embedded = []
    stream_tables = {t['package_offset'] - 264: t for t in probe_all_packages(b)}
    try:
        while True:
            if pos in anchors:
                key = anchors[pos]
                roots.append((pos, key))
                obj(key)
                continue
            if pos in stream_tables:
                t = stream_tables[pos]
                embedded.append(dict(kind='stream-package-tables', start=pos, end=t['table_end'], path=t['wrapper_path'], evidence='ordinary-table-identity' if Path(t['wrapper_path']).name in packs else 'parsed-table-only'))
                pos = t['table_end']
                continue
            import struct
            n = b[pos:pos + 256].split(b'\x00', 1)[0]
            if n.endswith(b'.ini') and n.decode('ascii') in names:
                with archive.open('rb') as f:
                    ini = a.read_entry(names.index(n.decode('ascii')), f)
                reserved, size = struct.unpack_from('<II', b, pos + 256)
                core.require(reserved == 0 and size == len(ini) and (b[pos + 264:pos + 264 + size] == ini), str(('embedded ini mismatch', pos)))
                embedded.append(dict(kind='source-identical-ini', name=n.decode('ascii'), start=pos, end=pos + 264 + size, bytes=size, sha256=core.digest(ini)))
                pos += 264 + size
                continue
            texture_candidates = []
            for key in instances:
                original, ts, ex = packs[key[0]]
                e = ex[key[1] - 1]
                raw = original[e['offset']:e['offset'] + e['size']]
                if b[pos:pos + 20] != raw[:20]:
                    continue
                props = property_block(raw, ts['names'], e['flags'])
                ms = mips(raw, props['end'], e['offset'])
                r = Reader(raw, props['end'])
                r.index()
                projected = raw[:r.pos]
                for m in ms:
                    source_start = r.pos
                    lazy = r.take(4)
                    r.index()
                    pixel_start = r.pos
                    r.take(m['size'])
                    dimensions = r.take(10)
                    projected += lazy + dimensions + raw[source_start + 4:pixel_start] + m['raw'] if m['width'] <= 8 and m['height'] <= 8 else raw[source_start:r.pos]
                if b[pos:pos + len(projected)] == projected:
                    texture_candidates.append((key, projected, raw, ms))
            if len(texture_candidates) == 1:
                key, projected, raw, ms = texture_candidates[0]
                embedded.append(dict(kind='texture-mip-order-projection', object=key, start=pos, end=pos + len(projected), mips=len(ms), source_sha256=core.digest(raw), stream_sha256=core.digest(projected)))
                pos += len(projected)
                seen.add(key)
                continue
            native_candidates = []
            for pkg, (original, ts, ex) in packs.items():
                for e in ex:
                    if e['class_index'] == 0 or e['class'] in ['Function', 'NativeFunction', 'State', 'Struct'] or e['size'] < 16:
                        continue
                    raw = original[e['offset']:e['offset'] + e['size']]
                    if b[pos:pos + len(raw)] == raw:
                        native_candidates.append(((pkg, e['index']), raw))
            span = equivalent_native_span(native_candidates) if equivalent_native else (equivalent_native_span(native_candidates) if len(native_candidates) == 1 else None)
            if span:
                identities, raw = span
                embedded.append(dict(kind='source-identical-native-object', object_candidates=identities, identity_unique=len(identities) == 1, start=pos, end=pos + len(raw), bytes=len(raw), sha256=core.digest(raw)))
                pos += len(raw)
                if len(identities) == 1:
                    seen.add(identities[0])
                continue
            break
    except (AssertionError, ValueError, KeyError) as error:
        question = str(error)
    result = dict(start=initial_pos, end=pos, bytes=pos - initial_pos, roots=roots, embedded=embedded, completed=completed, chunks=chunks, edges=edges, question=question, seen=len(seen))
    core.require(core.file_digest(archive) == FILE_HASH, 'FILE changed')
    summary = dict(schema=2, equivalent_native_enabled=equivalent_native, native_ambiguous_spans=sum(not x.get('identity_unique', True) for x in embedded), parsed_table_only_spans=sum(x.get('evidence')=='parsed-table-only' for x in embedded), source_sha256=FILE_HASH, bundle_sha256=BUNDLE_HASH, start=result['start'], stop_offset=result['end'], continuous_diagnostic_bytes=result['bytes'], root_requests=len(roots), completed_piece_sets=len(completed), piece_observations=len(chunks), embedded_spans=embedded, first_mismatch=question, stop_reason='source-oracle-mismatch' if question else 'next-span-unresolved', full_stream_mapping_verified=False, complete_game_text=False, source_modified=False, translation_gate='coverage-audit-pending')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('dependency-map.json', result), ('summary.json', summary)]:
        value = json.loads(json.dumps(value))
        p = out / name
        p.write_text(json.dumps(value, indent=2) + '\n', 'utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'JSON reopen')
    return summary
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--equivalent-native', action='store_true', help='Retain all exact-byte equivalent native identities; include imported Texture candidates')
    args = p.parse_args()
    print(json.dumps(audit(args.archive, args.out, args.equivalent_native), sort_keys=True))
