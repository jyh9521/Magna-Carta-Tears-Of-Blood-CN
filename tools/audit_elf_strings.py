"""Read-only ELF string candidates; decoding and address hits are not text proof."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core
from research_native import ElfImage, ELF_SHA256, pair_candidates


def spans(blob, unit=1, alignment=0):
    core.require(unit in (1, 2) and 0 <= alignment < unit, 'invalid scan alignment')
    start = alignment
    for pos in range(alignment, len(blob) - unit + 1, unit):
        if blob[pos:pos + unit] == b'\0' * unit:
            yield start, blob[start:pos]
            start = pos + unit
    # Unterminated suffix is explicitly not a NUL-terminated candidate.


def candidates(blob):
    rows = []
    for encoding, unit in (('cp949', 1), ('utf-16-le', 2), ('utf-16-be', 2)):
        for alignment in range(unit):
            for offset, raw in spans(blob, unit, alignment):
                if len(raw) < 2 * unit: continue
                try: text = raw.decode(encoding, errors='strict')
                except UnicodeError: continue
                if not all(c.isprintable() or c in '\r\n\t' for c in text): continue
                rows.append(dict(id=f'ELF/candidate/{encoding}/{offset}/{len(raw)}',
                                 offset=offset, bytes=len(raw), encoding=encoding,
                                 alignment=alignment, text=text, sha256=core.digest(raw),
                                 hangul=any('\uac00' <= c <= '\ud7a3' for c in text),
                                 editable=False, semantic='unverified'))
    return rows


def audit(blob, expected_sha256=ELF_SHA256):
    core.require(core.digest(blob) == expected_sha256, 'ELF identity mismatch')
    image = ElfImage(blob)
    rows = candidates(blob)
    by_va = {}
    for row in rows:
        try: va = image.to_va(row['offset'])
        except ValueError: va = None
        row.update(va=va, address_hits=[])
        if va is not None: by_va.setdefault(va, []).append(row)
    for segment in image.segments:
        if segment['type'] != 1 or not segment['filesz']: continue
        start = segment['offset']; size = segment['filesz']
        words = list(struct.unpack_from('<' + str(size // 4) + 'I', blob, start))
        for j, word in enumerate(words):
            for row in by_va.get(word, []):
                row['address_hits'].append(dict(kind='aligned-u32', offset=start + j * 4))
        for hit in pair_candidates(words, set(by_va)):
            for row in by_va[hit['address']]:
                row['address_hits'].append(dict(kind='bounded-MIPS-pair',
                    upper_offset=start + hit['upper_word'] * 4,
                    lower_offset=start + hit['lower_word'] * 4,
                    operation=hit['operation'], delay_slot=hit['delay_slot']))
    summary = dict(source_sha256=core.digest(blob), source_bytes=len(blob),
                   scan_scope='whole file; maximal NUL spans; UTF16 both byte alignments',
                   candidates=len(rows), counts=dict(Counter(r['encoding'] for r in rows)),
                   referenced_candidates=sum(bool(r['address_hits']) for r in rows),
                   referenced_hangul_candidates=sum(r['hangul'] and bool(r['address_hits']) for r in rows),
                   complete_game_text=False, exhaustive_elf_text=False,
                   reachability_verified=False, original_modified=False)
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    before = core.file_digest(args.elf)
    rows, summary = audit(args.elf.read_bytes())
    out = core.output_directory(args.out)
    with (out / 'candidates.jsonl').open('w', encoding='utf8') as stream:
        for row in rows: stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    core.require(core.file_digest(args.elf) == before, 'original ELF changed')
    print(json.dumps(summary, sort_keys=True))

if __name__ == '__main__': main()
