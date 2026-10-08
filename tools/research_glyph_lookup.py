"""Version-locked offline glyph lookup execution; not a PS2 runtime emulator."""
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
from research_native import ElfImage, ELF_SHA256

ENTRY, SIZE = 0x20EE80, 212
CODE_SHA256 = 'e8131662342bdf12c1bd0688559d97efb68caff7e06356d3108f616511036c22'
RETURN = 0x7FFFFFFC


def signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


class ReadOnlyMips:
    """Strict low32 subset; bounded immutable memory and classic delay slots."""
    def __init__(self, code: bytes, entry: int, blocks: list[tuple[int, bytes]]):
        core.require(entry % 4 == 0 and code and len(code) % 4 == 0, 'unaligned/empty code')
        self.code, self.entry = bytes(code), entry
        self.blocks = [(entry, bytes(code))] + [(a, bytes(b)) for a, b in blocks]
        ordered = sorted(self.blocks)
        for i, (address, blob) in enumerate(ordered):
            core.require(0 <= address and address + len(blob) <= 0x100000000, 'memory bounds')
            core.require(i == 0 or ordered[i - 1][0] + len(ordered[i - 1][1]) <= address, 'overlapping memory')

    def read(self, address: int, width: int, *, signed_load: bool = False) -> int:
        core.require(width in (1, 2, 4) and address % width == 0, 'unaligned/unsupported load')
        found = [b[address - a:address - a + width] for a, b in self.blocks if a <= address and address + width <= a + len(b)]
        core.require(len(found) == 1, 'unmapped model memory')
        return int.from_bytes(found[0], 'little', signed=signed_load) & 0xffffffff

    def fetch(self, pc: int) -> int:
        core.require(pc % 4 == 0 and self.entry <= pc <= self.entry + len(self.code) - 4, 'PC outside bounded code')
        return struct.unpack_from('<I', self.code, pc - self.entry)[0]

    @staticmethod
    def transfer(w: int, pc: int, r: list[int]) -> int | None:
        op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
        low = w & 65535; imm = low if low < 32768 else low - 65536
        if op in (4, 5):
            taken = r[rs] == r[rt] if op == 4 else r[rs] != r[rt]
            return (pc + 4 + imm * 4) & 0xffffffff if taken else pc + 8
        if op == 0 and w & 63 == 8:
            core.require(w & 0x1fffff == 8, 'noncanonical JR')
            return r[rs]
        return None

    def effect(self, w: int, r: list[int]) -> None:
        op, rs, rt, rd, shift, fn = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63
        low = w & 65535; imm = low if low < 32768 else low - 65536
        dest = rt
        if op == 9: result = r[rs] + imm
        elif op == 12: result = r[rs] & low
        elif op == 15:
            core.require(rs == 0, 'noncanonical LUI'); result = low << 16
        elif op in (32, 35, 36, 37):
            width = {32: 1, 35: 4, 36: 1, 37: 2}[op]
            result = self.read((r[rs] + imm) & 0xffffffff, width, signed_load=op == 32)
        elif op == 0 and fn in (0, 0x21, 0x23, 0x25, 0x2a):
            dest = rd
            core.require(rs == 0 if fn == 0 else shift == 0, 'noncanonical scalar operation')
            if fn == 0: result = r[rt] << shift
            elif fn == 0x21: result = r[rs] + r[rt]
            elif fn == 0x23: result = r[rs] - r[rt]
            elif fn == 0x25: result = r[rs] | r[rt]
            else: result = int(signed(r[rs]) < signed(r[rt]))
        else:
            raise ValueError(f'unsupported model instruction {w:08x}')
        if dest: r[dest] = result & 0xffffffff
        r[0] = 0

    def run(self, registers: dict[int, int], max_steps: int = 1024) -> dict:
        core.require(max_steps > 0 and all(0 <= k < 32 for k in registers), 'invalid execution bounds/registers')
        r = [0] * 32
        for k, v in registers.items():
            if k: r[k] = v & 0xffffffff
        r[31] = RETURN
        pc, steps = self.entry, 0
        while pc != RETURN:
            core.require(steps < max_steps, 'model step budget exhausted')
            word = self.fetch(pc); steps += 1
            target = self.transfer(word, pc, r)
            if target is None:
                self.effect(word, r); pc += 4
            else:
                core.require(steps < max_steps, 'model delay slot exceeds budget')
                delay = self.fetch(pc + 4); steps += 1
                core.require(self.transfer(delay, pc + 4, r) is None, 'control transfer in model delay slot')
                self.effect(delay, r); pc = target
        return dict(return_u32=r[2], steps=steps)


def lookup(code: bytes, ranges: list[int], bases: list[int], encoded: bytes, *, enabled: int = 1) -> dict:
    core.require(1 <= len(encoded) <= 2 and len(ranges) == len(bases) >= 2, 'invalid lookup fixture')
    core.require(all(0 <= x <= 65535 for x in ranges + bases), 'invalid uint16 table')
    obj = bytearray(0x88)
    struct.pack_into('<I', obj, 0x4c, enabled)
    struct.pack_into('<I', obj, 0x74, 0x10002000)
    struct.pack_into('<II', obj, 0x80, 0x10003000, len(ranges))
    model = ReadOnlyMips(code, ENTRY, [(0x10000000, bytes(obj)), (0x10001000, encoded),
                          (0x10002000, struct.pack(f'<{len(ranges)}H', *ranges)),
                          (0x10003000, struct.pack(f'<{len(bases)}H', *bases))])
    return model.run({4: 0x10000000, 5: 0x10001000})


def audit_font(code: bytes, info: dict, mapping: list[dict]) -> dict:
    ranges, bases = info['ranges'], info['bases']
    core.require(ranges == sorted(set(ranges)) and bases == sorted(bases), 'unexpected font table order')
    maximum, members = 0, 0
    for i in range(len(ranges) - 1):
        for value in range(ranges[i], ranges[i] + bases[i + 1] - bases[i]):
            result = lookup(code, ranges, bases, value.to_bytes(2, 'big'))
            core.require(result['return_u32'] == bases[i] + value - ranges[i], 'model/range member mismatch')
            maximum = max(maximum, result['steps']); members += 1
    for value in range(128):
        core.require(lookup(code, ranges, bases, bytes([value]))['return_u32'] == value, 'ASCII model mismatch')
    fallbacks = sorted({0x8000, ranges[0] - 1, ranges[-1], 0xffff} |
                       {ranges[i] + bases[i + 1] - bases[i] for i in range(len(ranges) - 1)})
    for value in fallbacks:
        core.require(lookup(code, ranges, bases, value.to_bytes(2, 'big'))['return_u32'] == 63, 'gap/fallback model mismatch')
    for item in mapping:
        core.require(lookup(code, ranges, bases, bytes.fromhex(item['bytes']))['return_u32'] == item['glyph'], 'locale map/model mismatch')
    # Isolated metadata-only experiment; no actual glyphs/metrics are allocated.
    core.require(ranges[-1] < 0xD0A1 and bases[-1] == info['glyphs'] and bases[-1] + 94 <= 65535,
                 'unsupported synthetic extension fixture')
    extended_ranges, extended_bases = ranges + [0xD0A1, 0xD0FF], bases + [bases[-1], bases[-1] + 94]
    for i in range(94):
        core.require(lookup(code, extended_ranges, extended_bases, (0xD0A1 + i).to_bytes(2, 'big'))['return_u32'] == info['glyphs'] + i,
                     'synthetic table extension mismatch')
    disabled = lookup(code, ranges, bases, b'\xb0', enabled=0)['return_u32']
    core.require(disabled == 0xffffffb0, 'disabled-mode signed-byte mismatch')
    return dict(range_members=members, ascii_cases=128, fallback_cases=len(fallbacks), locale_cases=len(mapping),
                max_member_steps=maximum, fallback_glyph=63,
                disabled_high_byte_return_u32=disabled,
                synthetic_extension=dict(cases=94, code_start='D0A1', code_end='D0FE', glyph_start=info['glyphs'],
                                         glyph_end=info['glyphs'] + 93, table_count=len(extended_ranges), actual_font_extended=False),
                object_fields=dict(multibyte_flag='0x4C', range_pointer='0x74', base_pointer='0x80', range_count='0x84'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--locale', type=Path, default=ROOT / 'locales/zh-CN/poc-map.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'work/glyph-lookup')
    args = parser.parse_args()
    game = json.loads((ROOT / 'profiles/scka-20043.json').read_text('utf8'))
    before = core.file_digest(args.iso)
    core.require(before == game['expected_iso_sha256'], 'unknown ISO version/hash')
    data = core.iso_files(args.iso, [game['boot'], 'FILE.AFS'])
    core.require(core.digest(data[game['boot']]) == ELF_SHA256, 'ELF fingerprint mismatch')
    image = ElfImage(data[game['boot']]); offset = image.to_offset(ENTRY)
    code = image.blob[offset:offset + SIZE]
    core.require(core.digest(code) == CODE_SHA256, 'lookup fragment fingerprint mismatch')
    out = core.output_directory(args.out)
    afs = out / 'FILE.AFS'; afs.write_bytes(data['FILE.AFS'])
    engine = dict(core.archive_entries(afs)[1])['MrtsEngine.u']
    core.require(core.digest(engine) == game['expected_engine_sha256'], 'engine fingerprint mismatch')
    mapping = json.loads(args.locale.read_text('utf8'))['entries']
    fonts = {}
    for export in package_tables(engine)['exports']:
        if export['class'] != 'Font' or export['name'] not in game['fonts']: continue
        serial = engine[export['offset']:export['offset'] + export['size']]
        core.require(core.digest(serial) == game['fonts'][export['name']], 'font fingerprint mismatch')
        fonts[export['name']] = dict(sha256=core.digest(serial), **audit_font(code, font_data(serial), mapping))
    core.require(set(fonts) == set(game['fonts']), 'expected font exports missing')
    core.require(core.file_digest(args.iso) == before, 'original ISO hash changed')
    report = dict(schema=1, iso_sha256=before, elf_sha256=ELF_SHA256, fragment_va=ENTRY, fragment_size=SIZE,
                  fragment_sha256=CODE_SHA256, locale_sha256=core.file_digest(args.locale), fonts=fonts,
                  evidence='offline bounded instruction execution with synthetic object pointers and original font tables; not PCSX2/runtime or width/wrap proof')
    (out / 'glyph-lookup.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f"GLYPH LOOKUP MODEL PASS fonts={len(fonts)} members_per_font={next(iter(fonts.values()))['range_members']} ascii_per_font=128 locale_cases_per_font={len(mapping)}")


if __name__ == '__main__': main()
