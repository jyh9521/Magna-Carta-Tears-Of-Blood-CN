"""Verify sampled movie evidence and export upstream timed reference cues.

Sample review never proves exhaustive visual or spoken text coverage.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core


def frame_command(executable, destination, interval=8, width=384):
    core.require(isinstance(interval, int) and 1 <= interval <= 60, 'invalid sample interval')
    core.require(isinstance(width, int) and 64 <= width <= 1920, 'invalid sample width')
    return [str(executable), '-v', 'error', '-i', 'pipe:0', '-an', '-vf',
            f'fps=1/{interval},scale={width}:-1,tile=6x6', '-fps_mode',
            'passthrough', str(destination / 'sheet-%02d.png')]


def timestamp(text):
    match = re.fullmatch(r'(\d+):([0-5]\d):([0-5]\d)\.(\d{2})', text)
    core.require(match is not None, 'invalid ASS timestamp')
    h, m, s, c = map(int, match.groups())
    return ((h * 60 + m) * 60 + s) * 100 + c


def reference_cues(path, region):
    data = path.read_bytes()
    lines = data.decode('utf-8-sig').splitlines()
    result = []
    for line_number, line in enumerate(lines, 1):
        if not line.startswith('Dialogue:'): continue
        fields = line.split(':', 1)[1].strip().split(',', 9)
        core.require(len(fields) == 10, 'malformed ASS dialogue')
        start, end = timestamp(fields[1]), timestamp(fields[2])
        core.require(end > start, 'nonpositive ASS duration')
        result.append(dict(id=f'ASS/{region}/{path.stem}/line/{line_number}',
                           region=region, movie=path.stem, line=line_number,
                           start_centiseconds=start, end_centiseconds=end,
                           style=fields[3], text=fields[9], source_sha256=core.digest(data),
                           source_role='upstream-timed-reference',
                           original_verbatim_verified=False, editable=False))
    return result


def validate_evidence(index, observations, sources):
    movies = {Path(r['path'].split(';')[0]).stem: r for r in sources if r['path'].endswith('.SFD;1')}
    core.require(len(index) == len({r['movie'] for r in index}), 'duplicate movie index')
    core.require(set(movies) == {r['movie'] for r in index}, 'movie inventory mismatch')
    core.require(len(observations) == len({r['movie'] for r in observations}), 'duplicate movie review')
    core.require(set(movies) == {r['movie'] for r in observations}, 'review inventory mismatch')
    by_movie = {r['movie']: r for r in observations}
    for item in index:
        source = movies[item['movie']]
        core.require(item['exit'] == 0 and item['fed_bytes'] == source['size'], 'incomplete movie decode')
        core.require(item['source_sha256'] == source['sha256'], 'movie source mismatch')
        review = by_movie[item['movie']]
        core.require(review['source_sha256'] == source['sha256'], 'review source mismatch')
        core.require(review['images'] == item['images'] and review['sample_seconds'] == item['sample_seconds'], 'review sheet mismatch')
        core.require(review['exhaustive'] is False and review['review'] == 'sampled-visual-review', 'unsupported exhaustive claim')
        core.require(type(review['text_observed']) is bool and bool(review['observation']), 'missing visual observation')
        core.require(bool(item['images']), 'missing sheet')
        for picture in item['images']:
            path = Path(picture['path']).resolve()
            core.require(any(path.is_relative_to(ROOT / d) for d in ('work', 'build')), 'sheet outside ignored output')
            core.require(path.stat().st_size == picture['size'] and core.file_digest(path) == picture['sha256'], 'sheet identity mismatch')
            from PIL import Image
            with Image.open(path) as image:
                core.require(image.format == 'PNG', 'invalid sheet image')
                image.verify()
    return dict(movies=len(index), sheets=sum(len(r['images']) for r in index),
                sampled_text_observed=sum(r['text_observed'] for r in observations),
                exhaustive_visual_coverage=False, exhaustive_spoken_coverage=False,
                complete_game_text=False)


def audit(index_path, observations_path, sources_path, subs, out):
    index = json.loads(index_path.read_text('utf8'))
    observations = json.loads(observations_path.read_text('utf8'))
    sources = json.loads(sources_path.read_text('utf8'))
    summary = validate_evidence(index, observations, sources)
    cues = []
    ass_files = []
    for region in ('korean', 'japanese'):
        for path in sorted((subs / region).glob('*.ass')):
            rows = reference_cues(path, region)
            cues.extend(rows)
            ass_files.append(dict(region=region, movie=path.stem, sha256=core.file_digest(path), cues=len(rows)))
    core.require(bool(ass_files), 'no upstream timed references')
    summary.update(reference_files=len(ass_files), reference_cues=len(cues),
                   reference_counts={r: sum(f['cues'] for f in ass_files if f['region'] == r) for r in ('korean','japanese')})
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('summary.json', summary), ('reference-cues.json', cues),
                        ('reference-files.json', ass_files), ('visual-observations.json', observations)]:
        target = out / name
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        core.require(json.loads(target.read_text('utf8')) == value, 'reopen mismatch')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('index', 'observations', 'sources', 'subs', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.index, a.observations, a.sources, a.subs, a.out), sort_keys=True))
