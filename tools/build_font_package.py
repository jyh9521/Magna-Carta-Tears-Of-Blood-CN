"""Integrate fingerprinted expanded Fonts into a separate MrtsEngine package.

Use after build_font_expansion.py. No celfid/AFS/ISO output is generated.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'src')]
import font_poc as core
from research_inventory import package_tables
from font_resource import verify_append
from package_resource import replace_exports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--expansion-dir', type=Path, required=True)
    parser.add_argument('--profile', type=Path, default=ROOT / 'profiles/scka-20043.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'work/font-package')
    args = parser.parse_args()
    game = json.loads(args.profile.read_text('utf8'))
    expansion = json.loads((args.expansion_dir / 'font-expansion.json').read_text('utf8'))
    core.require(core.file_digest(args.iso) == game['expected_iso_sha256'] == expansion['iso_sha256'], 'ISO fingerprint mismatch')
    out = core.output_directory(args.out)
    archive = out / 'original-FILE.AFS'; archive.write_bytes(core.iso_files(args.iso, ['FILE.AFS'])['FILE.AFS'])
    engine = dict(core.archive_entries(archive)[1])['MrtsEngine.u']
    core.require(core.digest(engine) == game['expected_engine_sha256'], 'engine fingerprint mismatch')
    replacements = {}
    for entry in package_tables(engine)['exports']:
        if entry['class'] != 'Font' or entry['name'] not in game['fonts']: continue
        name = entry['name']; old = engine[entry['offset']:entry['offset'] + entry['size']]
        new = (args.expansion_dir / (name + '.modified.bin')).read_bytes()
        item = expansion['fonts'][name]
        core.require(core.digest(old) == game['fonts'][name] == item['original_sha256'], 'original Font mismatch')
        core.require(core.digest(new) == item['modified_sha256'], 'expanded Font mismatch')
        verify_append(old, new, item['new_mapping_cases'], int(expansion['code_start'], 16))
        replacements[entry['index']] = new
    core.require(len(replacements) == len(game['fonts']) == 2, 'expected two expanded Fonts')
    modified, report = replace_exports(engine, replacements, expected_sha256=game['expected_engine_sha256'], expected_version=(118, 15))
    report.update(original_sha256=core.digest(engine), modified_sha256=core.digest(modified),
                  iso_sha256=game['expected_iso_sha256'], celfid_rebuilt=False, iso_generated=False)
    (out / 'MrtsEngine.original.u').write_bytes(engine)
    (out / 'MrtsEngine.modified.u').write_bytes(modified)
    (out / 'font-package.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    core.require(core.file_digest(args.iso) == game['expected_iso_sha256'], 'original ISO changed')
    print(f"FONT PACKAGE STATIC PASS exports={report['exports']} replaced={len(replacements)} bytes={len(engine)}->{len(modified)} untargeted_exports_preserved=true celfid_rebuilt=false iso_generated=false")


if __name__ == '__main__': main()
