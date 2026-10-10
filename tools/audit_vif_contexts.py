"""Read-only, fail-closed DMA_RET/VIF byte geometry for a verified stream region.

This is not a VIF executor or a complete StaticMesh serializer. Packet layout
references and its narrower proof boundary are documented in docs/STREAM_VIF_REVIEW.md.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
from audit_stream_candidate_contexts import SpanIndex
from audit_stream_tail_contexts import segment_candidate

CONTEXT_HASH = 'e6fe9490ee825564820016e3cd388ebacc37cf606c3a63e79315458a0b3cccc1'
VECTOR_BYTES = (4, 2, 1, 0, 8, 4, 2, 0, 12, 6, 3, 0, 16, 8, 4, 2)
COMMAND_NAMES = {0: 'NOP', 1: 'STCYCL', 0x17: 'MSCNT'}


def unpack_size(word, cl, wl):
    """Return consumed input bytes, including word padding, not output geometry."""
    cmd = (word >> 24) & 0x7f
    core.require(0x60 <= cmd <= 0x7f, 'not UNPACK')
    size = VECTOR_BYTES[cmd & 15]
    core.require(size > 0, 'reserved UNPACK format')
    core.require(0 <= cl <= 255 and 0 <= wl <= 255, 'cycle byte bounds')
    # CL zero stays zero. Only WL and NUM zero encode 256.
    count = ((word >> 16) & 255) or 256
    write = wl or 256
    inputs = count if write <= cl else cl * (count // write) + min(count % write, cl)
    raw = inputs * size
    return dict(vector_bytes=size, num=count, input_vectors=inputs,
                raw_bytes=raw, padded_bytes=(raw + 3) // 4 * 4,
                unsigned=bool(word & 0x4000), masked=bool(cmd & 0x10))


def packet(data, start, limit):
    core.require(0 <= start <= limit <= len(data) and start + 16 <= limit, 'DMA tag bounds')
    word, addr = struct.unpack_from('<II', data, start)
    qwc = word & 0xffff
    core.require(qwc > 0 and word == 0x60000000 | qwc and addr == 0,
                 'unreviewed DMA tag: expected plain RET with zero address')
    end = start + 16 + qwc * 16
    core.require(end <= limit, 'DMA packet overrun')
    pos = start + 8  # Two VIF words embedded in the tag precede its payload.
    cl = wl = None
    commands = []
    spans = [dict(start=start, end=start + 8, kind='verified-dma-ret-header')]
    while pos < end:
        core.require(pos + 4 <= end, 'VIF command bounds')
        at = pos
        value = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        cmd = (value >> 24) & 127
        core.require(value >> 31 == 0, 'unreviewed VIF interrupt')
        row = dict(start=at, command_word=value, opcode=cmd, data_start=pos, data_bytes=0)
        if cmd == 1:
            core.require(value & 0x00ff0000 == 0, 'STCYCL reserved NUM')
            cl, wl = value & 255, (value >> 8) & 255
            row.update(name='STCYCL', cl=cl, wl=wl)
        elif 0x60 <= cmd <= 0x7f:
            core.require(cl is not None, 'UNPACK before explicit STCYCL')
            geometry = unpack_size(value, cl, wl)
            row.update(name='UNPACK', cl=cl, wl=wl, geometry=geometry,
                       data_bytes=geometry['padded_bytes'])
        elif cmd in (0, 0x17):
            core.require(value == cmd << 24, 'unreviewed NOP/MSCNT bits')
            row['name'] = COMMAND_NAMES[cmd]
        else:
            raise ValueError('unreviewed VIF opcode: ' + hex(cmd))
        core.require(pos + row['data_bytes'] <= end, 'UNPACK packet overrun')
        spans.append(dict(start=at, end=pos, kind='verified-vif-command', opcode=cmd))
        if row['data_bytes']:
            raw_end = pos + row['geometry']['raw_bytes']
            if raw_end > pos:
                spans.append(dict(start=pos, end=raw_end, kind='verified-vif-unpack-input',
                                  command_start=at, format=cmd & 15))
            if raw_end < pos + row['data_bytes']:
                spans.append(dict(start=raw_end, end=pos + row['data_bytes'], kind='verified-vif-word-padding'))
        pos += row['data_bytes']
        row['end'] = pos
        commands.append(row)
    core.require(pos == end, 'VIF packet end mismatch')
    core.require(commands[0]['opcode'] == 1 and commands[1]['opcode'] == 0x6c,
                 'reviewed packet prefix mismatch')
    core.require(commands[-2]['opcode'] == 0x17 and commands[-1]['opcode'] == 0,
                 'reviewed packet suffix mismatch')
    return dict(start=start, end=end, qwc=qwc, dma_id=6, commands=commands, spans=spans)


def packet_block(data, size_offset, end):
    core.require(0 <= size_offset and size_offset + 20 <= end <= len(data), 'block bounds')
    size, count, a, b, c = struct.unpack_from('<5I', data, size_offset)
    core.require(size == end - size_offset - 4, 'block byte count mismatch')
    core.require(0 < count <= (size - 16) // 16, 'packet count bounds')
    pos = size_offset + 20
    packets = []
    spans = []
    for _ in range(count):
        item = packet(data, pos, end)
        packets.append(item)
        spans.extend(item['spans'])
        pos = item['end']
    core.require(pos == end, 'packet count/end mismatch')
    core.require(size == 16 + sum(16 + p['qwc'] * 16 for p in packets), 'independent QWC size mismatch')
    for span in spans:
        span['sha256'] = core.digest(data[span['start']:span['end']])
    SpanIndex(spans)
    return dict(start=size_offset, end=end, byte_count=size, packet_count=count,
                opaque_header_words=[a, b, c], packets=packets, spans=spans)


def annotate(data, rows, spans):
    spans = SpanIndex(spans).rows
    updated = []
    for row in rows:
        core.require(0 <= row['offset'] and row['bytes'] > 0 and
                     row['offset'] + row['bytes'] <= len(data), 'candidate bounds')
        start = row['offset']
        core.require(core.digest(data[start:start + row['bytes']]) == row['source_sha256'], 'candidate hash mismatch')
        item = dict(row)
        if row['category'] == 'unresolved-byte-context':
            parts = segment_candidate(row, spans)
            if parts:
                for part in parts:
                    part['sha256'] = core.digest(data[part['start']:part['end']])
                item.update(category=parts[0]['context']['kind'] if len(parts) == 1 else
                            'verified-vif-composite-boundary-context', context_parts=parts,
                            runtime_execution_verified=False, editable=False)
        updated.append(item)
    return updated


def audit(file, contexts, out):
    core.require(core.file_digest(file) == FILE_HASH, 'unsupported FILE archive')
    core.require(core.file_digest(contexts) == CONTEXT_HASH, 'unsupported context snapshot')
    afs = Afs.open(file)
    with file.open('rb') as stream:
        data, _ = unpack_chunks(afs.read_entry(filename_toc(afs).index('celfid.lix'), stream))
    core.require(core.digest(data) == BUNDLE_HASH, 'unsupported stream payload')
    block = packet_block(data, 3201559, 3214763)
    rows = json.loads(contexts.read_text('utf8'))
    updated = annotate(data, rows, block['spans'])
    summary = dict(schema=1, candidates=len(rows), packets=block['packet_count'],
                   packet_block_bytes=block['byte_count'], dma_qwc=sum(p['qwc'] for p in block['packets']),
                   vif_commands=sum(len(p['commands']) for p in block['packets']),
                   unpack_commands=sum(c['name'] == 'UNPACK' for p in block['packets'] for c in p['commands']),
                   unpack_input_padded_bytes=sum(c['data_bytes'] for p in block['packets'] for c in p['commands']),
                   recontextualized=sum(a != b for a, b in zip(rows, updated)),
                   counts=dict(sorted(Counter(r['category'] for r in updated).items())),
                   unresolved_byte_contexts=sum(r['category'] == 'unresolved-byte-context' for r in updated),
                   source_modified=False, full_native_mesh_verified=False, full_map_native_verified=False,
                   runtime_execution_verified=False, complete_game_text=False, coverage_review_complete=False,
                   translation_gate='coverage-audit-pending')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('contexts.json', updated), ('packets.json', block), ('summary.json', summary)]:
        path = out / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')
        core.require(json.loads(path.read_text('utf8')) == value, 'JSON reopen mismatch')
    core.require(core.file_digest(file) == FILE_HASH and core.file_digest(contexts) == CONTEXT_HASH,
                 'input changed')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('file', 'contexts', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.file, args.contexts, args.out), sort_keys=True))
