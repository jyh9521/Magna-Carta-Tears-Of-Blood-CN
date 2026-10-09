"""Read-only coverage audit; a matching catalog is not proof of all game text.

Original references/candidates are written only to ignored work/build output.
Reuse upstream AFS readers and the existing exporter, never rebuild archives.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
import font_poc as core
from afs import filename_toc
from cri_afs import Afs
from extract_strings import extract_resource
from translate.catalog import SUPPORTED_EXTS
from translate.fpb import parse_fpb_raw


def compare_inventory(names: list[str], resources: list[dict]) -> dict:
    core.require(len(names) == len(set(names)), 'duplicate archive resource name')
    catalog_names = [r['resource'].split('/', 1)[1] for r in resources]
    core.require(len(catalog_names) == len(set(catalog_names)), 'duplicate catalog resource')
    expected = {name for name in names if Path(name).suffix.lower() in SUPPORTED_EXTS}
    actual = set(catalog_names)
    return dict(missing_supported=sorted(expected-actual),
                unexpected_catalog=sorted(actual-expected),
                supported_resources=len(expected),
                outside_supported_formats=dict(sorted(Counter(
                    Path(n).suffix.lower() or '<none>' for n in names if n not in expected).items())))


def alternate_candidate(row: dict, raw: bytes) -> dict | None:
    core.require(len(raw) == row['source_bytes'] and core.digest(raw) == row['source_sha256'],
                 'source field byte identity mismatch')
    try:
        text = raw.decode('cp932', errors='strict')
        if text.encode('cp932') != raw:
            return None
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None
    # This detects a candidate interpretation, NOT an encoding decision.
    if not re.search('[\u3040-\u30ff]', text):
        return None
    return dict(id=row['id'], source_sha256=row['source_sha256'],
                source_decode=row['decode'], interpretation='candidate-cp932',
                references={'ja-JP': text}, semantic='unverified', editable=False)


class HashSink:
    """Hash ISO extraction without storing another archive on disk or in RAM."""
    def __init__(self):
        self.hash = hashlib.sha256()
        self.bytes = 0

    def write(self, data: bytes) -> int:
        self.hash.update(data)
        self.bytes += len(data)
        return len(data)


def iso_inventory(iso: Path, archive_dir: Path, expected: str) -> dict:
    import pycdlib
    before = core.file_digest(iso)
    core.require(before == expected, 'unsupported ISO identity')
    cd = pycdlib.PyCdlib()
    cd.open(str(iso))
    rows, hashes = [], {}
    try:
        for parent, directories, files in cd.walk(iso_path='/'):
            for name in files:
                path = parent.rstrip('/')+'/'+name
                record = cd.get_record(iso_path=path)
                rows.append(dict(path=path, size=record.data_length))
        for name in ['SHIP.AFS', 'FILE.AFS', 'LINEAR.AFS']:
            sink = HashSink()
            cd.get_file_from_iso_fp(sink, iso_path='/'+name+';1')
            local = archive_dir/name
            core.require(sink.bytes == local.stat().st_size and sink.hash.hexdigest() == core.file_digest(local),
                         'local archive differs from ISO: '+name)
            hashes[name] = sink.hash.hexdigest()
    finally:
        cd.close()
    core.require(core.file_digest(iso) == before, 'original ISO changed')
    return dict(files=sorted(rows, key=lambda r:r['path']), verified_archive_hashes=hashes)


def subtitle_inventory(disc: dict, subs: Path) -> tuple[dict, list[dict]]:
    movies = {Path(r['path'].split(';')[0]).stem for r in disc['files']
              if r['path'].upper().endswith('.SFD;1')}
    result, cues = {}, []
    for locale in ['korean', 'japanese']:
        files = sorted((subs/locale).rglob('*.ass'))
        names = {p.stem for p in files}
        core.require(len(names) == len(files), 'duplicate subtitle movie identity')
        count = 0
        for file in files:
            source_hash = core.file_digest(file)
            for index, line in enumerate(file.read_text('utf-8-sig').splitlines()):
                if line.startswith('Dialogue:'):
                    cells = line.split(':', 1)[1].split(',', 9)
                    core.require(len(cells) == 10, 'malformed ASS dialogue')
                    cues.append(dict(locale=locale, movie=file.stem, line=index+1,
                                     source_sha256=source_hash, fields=cells,
                                     visible_text_review='unverified'))
                    count += 1
        result[locale] = dict(ass_files=len(files), dialogue_cues=count,
                             matched_movies=len(names & movies),
                             movies_without_ass=sorted(movies-names),
                             ass_without_movie=sorted(names-movies))
    return result, cues


def audit(catalog_dir: Path, archive_dir: Path, out: Path, iso: Path) -> dict:
    catalog = json.loads((catalog_dir/'source-catalog.json').read_text('utf8'))
    manifest = json.loads((catalog_dir/'manifest.json').read_text('utf8'))
    core.require(catalog['iso_sha256'] == manifest['iso_sha256'], 'catalog input identity mismatch')
    core.require(manifest.get('complete_game_text') is False, 'unexpected complete-game assertion')
    disc = iso_inventory(iso, archive_dir, manifest['iso_sha256'])
    subtitles, cues = subtitle_inventory(disc, ROOT/'subs')
    ship_path = archive_dir/'SHIP.AFS'
    core.require(core.file_digest(ship_path) == manifest['archives']['SHIP.AFS'], 'SHIP archive identity mismatch')
    core.require(core.file_digest(archive_dir/'FILE.AFS') == manifest['archives']['FILE.AFS'], 'FILE archive identity mismatch')
    source_before = core.file_digest(catalog_dir/'source-catalog.json')
    archive = Afs.open(ship_path)
    names = filename_toc(archive)
    inventory = compare_inventory(names, catalog['resources'])
    core.require(not inventory['missing_supported'] and not inventory['unexpected_catalog'],
                 'supported resource inventory mismatch')
    index = {name: i for i, name in enumerate(names)}
    inventory_rows = []
    for label in ['SHIP.AFS', 'FILE.AFS', 'LINEAR.AFS']:
        path = archive_dir/label
        afs = Afs.open(path)
        for i, name in enumerate(filename_toc(afs)):
            inventory_rows.append(dict(archive=label, index=i, name=name,
                coverage='catalog-structural-or-candidate' if label=='SHIP.AFS' and name in index
                    and Path(name).suffix.lower() in SUPPORTED_EXTS else 'not-in-main-text-catalog'))
    alternatives, extra, problems = [], [], []
    with ship_path.open('rb') as stream:
        for resource in catalog['resources']:
            name = resource['resource'].split('/', 1)[1]
            blob = archive.read_entry(index[name], stream)
            fresh = extract_resource(name, blob)
            core.require(fresh == resource, 're-extraction differs: '+name)
            # Pool offsets are relative to the FPB pool, not to the resource.
            data = parse_fpb_raw(blob)[2] if name.endswith('.fpb') and resource.get('audit', {}).get('status')=='parsed' else blob
            for row in resource['entries']:
                raw = data[row['offset']:row['offset']+row['source_bytes']]
                candidate = alternate_candidate(row, raw)
                if candidate:
                    alternatives.append(candidate)
            extra.extend(resource.get('candidates', []))
            detail = resource.get('audit', {})
            if (resource.get('error') or detail.get('status') not in (None, 'parsed')
                    or detail.get('view_gaps') or detail.get('partition_reasons')):
                problems.append(dict(resource=resource['resource'], error=resource.get('error'), audit=detail))
    fields = [e for r in catalog['resources'] for e in r['entries']]
    primary_spans = {(r['resource'], e['offset'], e['source_bytes'])
                     for r in catalog['resources'] for e in r['entries']}
    extra_not_same_span = [e for r in catalog['resources'] for e in r.get('candidates', [])
                          if (r['resource'], e['offset'], e['source_bytes']) not in primary_spans]
    summary = dict(schema=1, source_iso_sha256=catalog['iso_sha256'],
        source_catalog_sha256=source_before, archive_inventory=inventory,
        resources_reextracted=len(catalog['resources']), source_records=len(fields),
        decode_failed=sum(e['decode']=='failed' for e in fields),
        quarantined_controls=sum(e.get('controls')=='quarantined' for e in fields),
        additional_slot_candidates=len(extra), additional_candidates_not_same_span=len(extra_not_same_span),
        cp932_candidate_interpretations=len(alternatives),
        resources_with_parse_or_partition_questions=len(problems),
        archive_entries_indexed=dict(Counter(e['archive'] for e in inventory_rows)),
        verified_archive_hashes=disc['verified_archive_hashes'],
        iso_files=len(disc['files']),
        iso_sfd_files=sum(r['path'].upper().endswith('.SFD;1') for r in disc['files']),
        upstream_subtitles=subtitles,
        complete_game_text=False, translation_gate='coverage-audit-not-complete',
        unresolved=manifest['unresolved'],
        result='known-supported-catalog-reextraction-matches; not whole-game coverage')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'audit output must be empty')
    products = {'summary.json': summary, 'archive-inventory.json': inventory_rows,
                'encoding-candidates.json': alternatives, 'slot-extra-candidates.json': extra,
                'parse-partition-questions.json': problems, 'iso-inventory.json': disc,
                'subtitle-cues.json': cues}
    for name, value in products.items():
        p = out/name
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'output reopen mismatch')
    core.require(core.file_digest(catalog_dir/'source-catalog.json') == source_before, 'source catalog changed')
    core.require(core.file_digest(ship_path) == manifest['archives']['SHIP.AFS'], 'SHIP input changed')
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog-dir', type=Path, required=True)
    p.add_argument('--archive-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--iso', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.catalog_dir, a.archive_dir, a.out, a.iso), sort_keys=True))


if __name__ == '__main__':
    main()
