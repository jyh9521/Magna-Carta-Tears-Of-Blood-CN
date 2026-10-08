"""Version-locked FontObj bitmap conversion projection; no runtime cache emulator."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core
from research_inventory import font_data, package_tables
from research_native import ElfImage, ELF_SHA256, trace_call
from research_glyph_lookup import ReadOnlyMips

ENTRY, SIZE = 0x333D64, 112
HASH = '1a7478c87683d03570c1a5f55842b97dc45f0d9ab2e076a665fb01c391b92f14'
FRAGMENTS = {
    'source_address': (0x333C30, 64, '7e71289240cdf118a534cbe02265aa04e34113c80a23349ed0203cc7ba999231'),
    'page_candidate': (0x333A20, 352, '3e20c552d22748f9901b0febefed15503151add0b935912d83dd9901b7960bc9'),
    'conversion': (ENTRY, SIZE, HASH),
}


def project_pixel(code: bytes, source: int, shift: int) -> int:
    """Execute five original scalar operations, not the loop, stores or EE MULT."""
    core.require(len(code) == SIZE and 0 <= source <= 255 and shift in (0, 2, 4, 6), 'invalid pixel projection')
    model = ReadOnlyMips(code, ENTRY, [])
    r = [0] * 32; r[5], r[6] = source, shift
    for offset in (0x10, 0x18, 0x20, 0x28, 0x2c):
        word = model.fetch(ENTRY + offset)
        core.require(model.transfer(word, ENTRY + offset, r) is None, 'transfer in pixel projection')
        model.effect(word, r)
    return r[14]


def convert_bitmap(bitmap: bytes, glyphs: int, height: int, width: int, stride: int, table: list[list[int]]) -> bytes:
    core.require(glyphs > 0 and height > 0 and 0 < width <= stride * 4, 'invalid bitmap geometry')
    core.require(len(bitmap) == glyphs * height * stride, 'bitmap length mismatch')
    core.require(len(table) == 256 and all(len(row) == 4 and all(0 <= p <= 255 for p in row) for row in table), 'invalid pixel table')
    return bytes(table[bitmap[row * stride + x // 4]][x % 4]
                 for row in range(glyphs * height) for x in range(width))


def audit(blob: bytes) -> tuple[dict, bytes]:
    core.require(core.digest(blob) == ELF_SHA256, 'ELF fingerprint mismatch')
    image = ElfImage(blob); fragments = {}
    for name, (va, size, expected) in FRAGMENTS.items():
        offset = image.to_offset(va); fragment = blob[offset:offset + size]
        core.require(core.digest(fragment) == expected, 'fragment fingerprint mismatch')
        fragments[name] = dict(va=va, size=size, sha256=expected)
    offset = image.to_offset(ENTRY)
    calls = [trace_call(image, va) for va in (0x333A4C, 0x333AB4, 0x333AFC, 0x333BEC, 0x272D00)]
    return dict(fragments=fragments, call_candidates=calls,
        candidate_source_fields=dict(font_pointer='object+0x28', bitmap='font+0x60', height_candidate='font+0x54', stride='font+0x5C', format_selector='font+0x94'),
        page_candidates=dict(comparison_limit=65, comparison_sites=[0x333A74, 0x333A8C],
            array_pointer='object+0x38', array_count='object+0x3C', array_capacity='object+0x40',
            glyph_index_mask=65535, full_cache_limit_verified=False),
        evidence='static candidate dataflow and five-instruction scalar projection; runtime field identity, format branch and cache execution unverified'), blob[offset:offset + SIZE]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--out', type=Path, default=ROOT / 'work/font-bitmap')
    args = p.parse_args()
    game = json.loads((ROOT / 'profiles/scka-20043.json').read_text('utf8'))
    before = core.file_digest(args.iso)
    core.require(before == game['expected_iso_sha256'], 'unknown ISO version/hash')
    data = core.iso_files(args.iso, [game['boot'], 'FILE.AFS'])
    report, code = audit(data[game['boot']])
    table = [[project_pixel(code, value, shift) for shift in (0, 2, 4, 6)] for value in range(256)]
    core.require(all(table[v][s // 2] == ((v >> s) & 3) * 60 for v in range(256) for s in (0, 2, 4, 6)), 'scalar projection mismatch')
    out = core.output_directory(args.out)
    afs = out / 'FILE.AFS'; afs.write_bytes(data['FILE.AFS'])
    engine = dict(core.archive_entries(afs)[1])['MrtsEngine.u']
    core.require(core.digest(engine) == game['expected_engine_sha256'], 'engine fingerprint mismatch')
    fonts = {}
    for export in package_tables(engine)['exports']:
        if export['class'] != 'Font' or export['name'] not in game['fonts']: continue
        serial = engine[export['offset']:export['offset'] + export['size']]
        core.require(core.digest(serial) == game['fonts'][export['name']], 'font fingerprint mismatch')
        info = font_data(serial); start = info['bitmap_start']
        bitmap = serial[start:start + info['bitmap_bytes']]
        projected = convert_bitmap(bitmap, info['glyphs'], info['height'], info['width'], info['row_stride'], table)
        reference = bytes(((bitmap[row * info['row_stride'] + x // 4] >> (2 * (x % 4))) & 3) * 60
            for row in range(info['glyphs'] * info['height']) for x in range(info['width']))
        core.require(projected == reference, 'original bitmap/reference mismatch')
        fonts[export['name']] = dict(sha256=core.digest(serial), glyphs=info['glyphs'], height=info['height'],
            width=info['width'], stride=info['row_stride'], source_bitmap_bytes=len(bitmap),
            projected_pixels=len(projected), projected_sha256=core.digest(projected),
            values=sorted(set(projected)), actual_cache_generated=False, format_branch_executed=False)
    core.require(set(fonts) == set(game['fonts']), 'expected font exports missing')
    core.require(core.file_digest(args.iso) == before, 'original ISO hash changed')
    report.update(schema=1, iso_sha256=before, elf_sha256=ELF_SHA256, scalar_cases=1024, fonts=fonts)
    (out / 'font-bitmap.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'FONT BITMAP PROJECTION PASS fonts={len(fonts)} scalar_cases=1024 runtime_cache_generated=false')


if __name__ == '__main__': main()
