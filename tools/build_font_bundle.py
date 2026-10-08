"""Build an isolated expanded-font startup bundle candidate; no AFS/ISO output."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core
from bundle_resource import replace_cached_package
from translate.celfid import decompress_chunked, recompress_chunked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--package-dir', type=Path, required=True)
    parser.add_argument('--profile', type=Path, default=ROOT / 'profiles/scka-20043.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'work/font-bundle')
    args = parser.parse_args()
    game = json.loads(args.profile.read_text('utf8'))
    package_report = json.loads((args.package_dir / 'font-package.json').read_text('utf8'))
    core.require(core.file_digest(args.iso) == game['expected_iso_sha256'] == package_report['iso_sha256'], 'ISO fingerprint mismatch')
    out = core.output_directory(args.out)
    archive = out / 'original-FILE.AFS'; archive.write_bytes(core.iso_files(args.iso, ['FILE.AFS'])['FILE.AFS'])
    files = dict(core.archive_entries(archive)[1])
    original = files['MrtsEngine.u']; modified = (args.package_dir / 'MrtsEngine.modified.u').read_bytes()
    core.require(core.digest(modified) == package_report['modified_sha256'], 'modified package fingerprint mismatch')
    core.require(core.digest(original) == package_report['original_sha256'] == game['expected_engine_sha256'], 'original package mismatch')
    bundle = decompress_chunked(files['celfid.lix'])
    indices = {item['index'] for item in package_report['changed']}
    core.require(indices == {735, 736}, 'unexpected Font package targets')
    candidate, report = replace_cached_package(bundle, original, modified, indices,
        expected_bundle_sha256=game['expected_bundle_sha256'], expected_package_sha256=game['expected_engine_sha256'],
        cached_path='../System/UFile/MrtsEngine.u')
    compressed = recompress_chunked(candidate)
    core.require(decompress_chunked(compressed) == candidate, 'bundle compression round trip failed')
    for name, data in [('bundle.original.bin', bundle), ('bundle.modified.bin', candidate),
                       ('celfid.original.lix', files['celfid.lix']), ('celfid.modified.lix', compressed)]:
        (out / name).write_bytes(data)
    report.update(original_sha256=core.digest(bundle), modified_sha256=core.digest(candidate),
                  compressed_sha256=core.digest(compressed), compressed_sizes=[len(files['celfid.lix']), len(compressed)],
                  iso_sha256=game['expected_iso_sha256'], package_sha256=core.digest(modified), iso_generated=False)
    (out / 'font-bundle.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    core.require(core.file_digest(args.iso) == game['expected_iso_sha256'], 'original ISO changed')
    print(f"FONT BUNDLE STATIC PASS segments={len(report['segments'])} file_records={report['file_records']} bytes={len(bundle)}->{len(candidate)} compression_roundtrip=true iso_generated=false runtime=unverified")


if __name__ == '__main__': main()
