"""Read-only font metric consumer and bounded serialization call audit."""
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
from research_inventory import font_data, package_tables
from research_native import ElfImage, ELF_SHA256, trace_call
from research_glyph_lookup import ReadOnlyMips

METRIC_VA, METRIC_SIZE = 0x2727C4, 24
FRAGMENTS = {
    'metric': (METRIC_VA, METRIC_SIZE, 'e533b6ce738e1c72655700bbe54148a810075dafdbca10ae17e032ddc4c1089d'),
    'mode_branch': (0x272730, 12, '8b3f06673b6d36fd19f206d3037b3040dfe348c02f20371b06da5cfa5cbc1190'),
    'serializer': (0x20F148, 352, 'e374819856b35e10e62d654943b3dc6b249cb4959780ac8e3c3b988e39fa07ed'),
}


def metric_prefix(code: bytes, metrics: bytes, glyph: int, auxiliary: int) -> dict:
    """Execute five scalar operations, excluding the intermediate stack store.

    Object pointers are synthetic. Memory has exactly the supplied metric bytes;
    The stack store at +12 is excluded; its source is loaded before overwrite.
    No padding, wraparound repair, clamp or replacement glyph is introduced.
    """
    core.require(len(code) == METRIC_SIZE and metrics and 0 <= glyph <= 0xffffffff,
                 'invalid metric model input')
    core.require(0 <= auxiliary <= 0xffffffff, 'invalid auxiliary field')
    obj = bytearray(0x6c)
    struct.pack_into('<I', obj, 0x54, auxiliary)
    struct.pack_into('<I', obj, 0x68, 0x10001000)
    model = ReadOnlyMips(code, METRIC_VA, [(0x10000000, bytes(obj)), (0x10001000, metrics)])
    core.require(struct.unpack_from('<I', code, 12)[0] == (43 << 26 | 29 << 21 | 3 << 16 | 0xe0),
                 'unexpected excluded stack store')
    regs = [0] * 32
    regs[20], regs[2] = 0x10000000, glyph
    for pc in (METRIC_VA, METRIC_VA + 4, METRIC_VA + 8, METRIC_VA + 16, METRIC_VA + 20):
        word = model.fetch(pc)
        core.require(model.transfer(word, pc, regs) is None, 'transfer in metric prefix')
        model.effect(word, regs)
    return dict(metric=regs[3], index=regs[5], steps=5)


def branch_target(word: int, pc: int) -> int:
    core.require(word >> 26 in (4, 5) and pc % 4 == 0, 'invalid scalar branch')
    immediate = word & 65535
    if immediate >= 32768: immediate -= 65536
    return (pc + 4 + immediate * 4) & 0xffffffff


def audit(blob: bytes) -> tuple[ElfImage, dict, bytes]:
    core.require(core.digest(blob) == ELF_SHA256, 'ELF fingerprint mismatch')
    image = ElfImage(blob); fragments = {}
    for name, (address, size, expected) in FRAGMENTS.items():
        offset = image.to_offset(address)
        code = blob[offset:offset + size]
        core.require(core.digest(code) == expected, 'fragment fingerprint mismatch: ' + name)
        fragments[name] = dict(va=address, size=size, sha256=expected)
    code = blob[image.to_offset(METRIC_VA):image.to_offset(METRIC_VA) + METRIC_SIZE]
    calls = [trace_call(image, va) for va in
             (0x20f158, 0x20f18c, 0x20f1a4, 0x20f1bc, 0x20f1d4,
              0x20f1e0, 0x20f244, 0x20f250, 0x20f25c, 0x20f268)]
    return image, dict(fragments=fragments, serialization_call_candidates=calls,
                       mode_branch=dict(flag_field='0x4C', branch_va=0x272734,
                           nonzero_target=branch_target(struct.unpack_from('<I', blob, image.to_offset(0x272734))[0], 0x272734),
                           zero_fallthrough=0x27273C, delay_va=0x272738,
                           metric_pointer_field='0x68', index_mask=65535,
                           intermediate_stack_store_excluded=True),
                       evidence='bounded static calls and offline synthetic-object metric loads; runtime object identity and execution unverified'), code


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--out', type=Path, default=ROOT / 'work/font-metrics')
    args = p.parse_args()
    game = json.loads((ROOT / 'profiles/scka-20043.json').read_text('utf8'))
    before = core.file_digest(args.iso)
    core.require(before == game['expected_iso_sha256'], 'unknown ISO version/hash')
    data = core.iso_files(args.iso, [game['boot'], 'FILE.AFS'])
    _, report, code = audit(data[game['boot']])
    out = core.output_directory(args.out)
    afs = out / 'FILE.AFS'; afs.write_bytes(data['FILE.AFS'])
    engine = dict(core.archive_entries(afs)[1])['MrtsEngine.u']
    core.require(core.digest(engine) == game['expected_engine_sha256'], 'engine fingerprint mismatch')
    fonts = {}
    for export in package_tables(engine)['exports']:
        if export['class'] != 'Font' or export['name'] not in game['fonts']: continue
        serial = engine[export['offset']:export['offset'] + export['size']]
        core.require(core.digest(serial) == game['fonts'][export['name']], 'font fingerprint mismatch')
        info = font_data(serial)
        metrics = serial[info['metrics_start']:info['metrics_start'] + info['metrics_bytes']]
        for glyph, expected in enumerate(metrics):
            result = metric_prefix(code, metrics, glyph, 0)
            core.require(result['metric'] == expected and result['index'] == glyph, 'metric model mismatch')
        try: metric_prefix(code, metrics, len(metrics), 0)
        except ValueError as exc:
            core.require(str(exc) == 'unmapped model memory', 'unexpected overflow failure')
        else: raise ValueError('out-of-range model read unexpectedly succeeded')
        fonts[export['name']] = dict(sha256=core.digest(serial), cases=len(metrics),
            histogram=dict(sorted(Counter(metrics).items())), minimum=min(metrics), maximum=max(metrics),
            out_of_range='unmapped model memory', height=info['height'])
    core.require(set(fonts) == set(game['fonts']), 'expected font exports missing')
    core.require(core.file_digest(args.iso) == before, 'original ISO hash changed')
    report.update(schema=1, iso_sha256=before, elf_sha256=ELF_SHA256, fonts=fonts)
    (out / 'font-metrics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'FONT METRIC MODEL PASS fonts={len(fonts)} cases_per_font=2667 overflow_rejected=true')


if __name__ == '__main__': main()

