"""Build isolated expanded Font resources; no package, ISO or engine patch."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'src')]
import font_poc as core
from build_locale import patch_font, preview_fonts
from font_resource import append_font, verify_append, parts
from localization.text import MappedEncoder
from research_inventory import package_tables, font_data
from research_glyph_lookup import lookup, ENTRY, SIZE, CODE_SHA256
from research_native import ElfImage, ELF_SHA256


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--font', type=Path, required=True)
    p.add_argument('--locale', type=Path, default=ROOT / 'locales/zh-CN/poc-text.json')
    p.add_argument('--range-start', type=lambda v: int(v, 0), default=0xD0A1)
    p.add_argument('--out', type=Path, default=ROOT / 'work/font-expansion')
    args = p.parse_args()
    locale = json.loads(args.locale.read_text('utf8'))
    game = json.loads((ROOT / locale['game_profile']).read_text('utf8'))
    old_map = json.loads((ROOT / locale['glyph_map']).read_text('utf8'))
    core.require(core.file_digest(args.font) == locale['font_input']['sha256'], 'font input mismatch')
    from fontTools.ttLib import TTFont
    with TTFont(args.font) as face:
        cmap = face.getBestCmap()
        core.require(all(cmap.get(ord(item['character'])) not in (None, '.notdef') for item in old_map['entries']), 'missing font glyph')
    before = core.file_digest(args.iso)
    core.require(before == game['expected_iso_sha256'], 'unknown ISO version/hash')
    data = core.iso_files(args.iso, [game['boot'], 'FILE.AFS'])
    core.require(core.digest(data[game['boot']]) == ELF_SHA256, 'ELF fingerprint mismatch')
    image = ElfImage(data[game['boot']]); offset = image.to_offset(ENTRY)
    code = image.blob[offset:offset + SIZE]
    core.require(core.digest(code) == CODE_SHA256, 'lookup fingerprint mismatch')
    out = core.output_directory(args.out)
    afs = out / 'FILE.AFS'; afs.write_bytes(data['FILE.AFS'])
    engine = dict(core.archive_entries(afs)[1])['MrtsEngine.u']
    core.require(core.digest(engine) == game['expected_engine_sha256'], 'engine fingerprint mismatch')
    originals = {}
    for export in package_tables(engine)['exports']:
        if export['class'] == 'Font' and export['name'] in game['fonts']:
            serial = engine[export['offset']:export['offset'] + export['size']]
            core.require(core.digest(serial) == game['fonts'][export['name']], 'Font fingerprint mismatch')
            originals[export['name']] = serial
    core.require(set(originals) == set(game['fonts']), 'expected fonts missing')
    counts = {font_data(serial)['glyphs'] for serial in originals.values()}
    core.require(len(counts) == 1, 'original Font glyph counts differ')
    first = counts.pop(); count = len(old_map['entries'])
    entries = [dict(character=item['character'], bytes=f'{args.range_start + row:04X}', glyph=first + row)
               for row, item in enumerate(old_map['entries'])]
    modified_fonts = {}; results = {}
    for name, serial in originals.items():
        info = font_data(serial)
        expanded = append_font(serial, bytes(count * info['height'] * info['row_stride']), bytes(count), args.range_start,
                               expected_sha256=game['fonts'][name])
        encoder = MappedEncoder(entries, font_tables=font_data(expanded))
        modified = patch_font(expanded, encoder, args.font, locale['alignment_reference'], locale['advance'])
        result = verify_append(serial, modified, count, args.range_start)
        new_info, _, metrics, _ = parts(modified)
        for item in entries:
            core.require(lookup(code, new_info['ranges'], new_info['bases'], bytes.fromhex(item['bytes']))['return_u32'] == item['glyph'], 'new glyph lookup mismatch')
            core.require(metrics[item['glyph']] == locale['advance'], 'new metric mismatch')
        # Preserve lookup for every original code-range member, not merely the PoC.
        preserved = 0
        for row in range(len(info['ranges']) - 1):
            for value in range(info['ranges'][row], info['ranges'][row] + info['bases'][row + 1] - info['bases'][row]):
                expected = info['bases'][row] + value - info['ranges'][row]
                core.require(lookup(code, new_info['ranges'], new_info['bases'], value.to_bytes(2, 'big'))['return_u32'] == expected, 'original code mapping changed')
                preserved += 1
        for value in range(128):
            core.require(lookup(code, new_info['ranges'], new_info['bases'], bytes([value]))['return_u32'] == value, 'ASCII mapping changed')
        result.update(original_ascii_cases=128, original_sha256=core.digest(serial), modified_sha256=core.digest(modified),
            original_bytes=len(serial), modified_bytes=len(modified), original_mapping_cases=preserved,
            new_mapping_cases=count, runtime='unverified; standalone Font resource only')
        (out / (name + '.original.bin')).write_bytes(serial)
        (out / (name + '.modified.bin')).write_bytes(modified)
        modified_fonts[name] = modified; results[name] = result
    preview_fonts(modified_fonts, encoder, out)
    (out / 'experimental-map.json').write_text(json.dumps(dict(locale=locale['locale'], encoding='mapped-double-byte', entries=entries), ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    core.require(core.file_digest(args.iso) == before, 'original ISO changed')
    report = dict(schema=1, iso_sha256=before, elf_sha256=ELF_SHA256, font_input_sha256=core.file_digest(args.font), fonts=results,
                  code_start=f'{args.range_start:04X}', code_end=f'{args.range_start + count - 1:04X}',
                  packages_rebuilt=False, iso_generated=False, runtime='unverified')
    (out / 'font-expansion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(f'FONT EXPANSION STATIC PASS fonts={len(results)} glyphs={first}->{first + count} added={count} original_glyphs_preserved=true iso_generated=false')


if __name__ == '__main__': main()
