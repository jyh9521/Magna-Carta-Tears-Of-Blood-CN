"""Bounded compact-string records in a version-locked map native prefix.

Record framing is verified; FURL field roles remain high-confidence deductions.
No global native serializer order or runtime visibility is asserted.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks, probe_all_packages
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
from audit_config_semantics import script_sources
from audit_object_properties import Reader, string_value
from audit_vif_contexts import annotate

CONTEXT_HASH = '292279727338500d9717a3f6426b5f88ecfa01f2258fc5c7c17a418182e6478a'


def compact_strings(data, start, end, count):
    core.require(0 <= start <= end <= len(data) and 0 < count <= 32, 'string sequence bounds/count')
    r = Reader(data[:end], start)
    records = []
    for _ in range(count):
        at = r.pos
        length = r.index()
        core.require(-4096 <= length <= 4096, 'unreviewed string length')
        text_at = r.pos
        r.take(length if length >= 0 else -length * 2)
        value = string_value(data[at:r.pos])
        records.append(dict(start=at, text_start=text_at, end=r.pos, length=length,
                            sha256=core.digest(data[at:r.pos]), **value))
    core.require(r.pos == end, 'string sequence trailing bytes')
    return records


def audit(file, contexts, out):
    core.require(core.file_digest(file) == FILE_HASH and core.file_digest(contexts) == CONTEXT_HASH, 'input identity mismatch')
    a = Afs.open(file)
    names = filename_toc(a)
    with file.open('rb') as stream:
        data, _ = unpack_chunks(a.read_entry(names.index('celfid.lix'), stream))
        sources = script_sources(a, names, stream)
    core.require(core.digest(data) == BUNDLE_HASH, 'stream identity mismatch')
    tables = next(t for t in probe_all_packages(data) if t['package_offset'] == 4185632)
    core.require(tables['wrapper_path'] == '../Maps/00000118.unr' and tables['table_end'] == 4188034, 'map identity mismatch')
    source = next(s for s in sources if s['id'] == 'FILE/Engine.u/export/5485/TextBuffer')
    core.require('struct URL' in source['text'] and all(x in source['text'] for x in
                 ('Protocol', 'Host', 'Port', 'Map', 'Op', 'Portal', 'Valid')), 'URL declaration mismatch')
    records = compact_strings(data, 4188198, 4188219, 4)
    # Disk order is not claimed as a globally established UE serializer schema.
    for row, field in zip(records, ('Protocol', 'Host', 'Map', 'Portal')):
        row.update(inferred_field=field, field_confidence='high-confidence-deduction',
                   source_declaration=dict(id=source['id'], serial_sha256=source['serial_sha256']),
                   semantic='internal-routing-candidate', editable=False, runtime_visibility_verified=False)
    spans = [dict(start=r['start'], end=r['end'], kind='bounded-map-native-string-record',
                  sha256=r['sha256'], inferred_field=r['inferred_field'],
                  field_confidence=r['field_confidence']) for r in records]
    rows = json.loads(contexts.read_text('utf8'))
    updated = annotate(data, rows, spans)
    summary = dict(schema=1, candidates=len(rows), string_records=len(records), string_record_bytes=21,
                   nonempty_string_records=sum(bool(r['text']) for r in records),
                   script_sources_reparsed=len(sources),
                   recontextualized=sum(a != b for a,b in zip(rows,updated)),
                   counts=dict(sorted(Counter(r['category'] for r in updated).items())),
                   unresolved_byte_contexts=sum(r['category'] == 'unresolved-byte-context' for r in updated),
                   native_url_order_verified=False, full_map_native_verified=False, runtime_visibility_verified=False,
                   source_modified=False, complete_game_text=False, coverage_review_complete=False,
                   translation_gate='coverage-audit-pending')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('contexts.json', updated), ('records.json', records), ('summary.json', summary)]:
        p = out / name
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'JSON reopen mismatch')
    core.require(core.file_digest(file) == FILE_HASH and core.file_digest(contexts) == CONTEXT_HASH, 'input changed')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('file', 'contexts', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.file, a.contexts, a.out), sort_keys=True))
