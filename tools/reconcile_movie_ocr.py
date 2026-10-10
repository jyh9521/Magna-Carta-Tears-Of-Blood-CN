"""Recover complete hash-verified OCR records with a rawvideo DTS diagnostic.

Original run outputs, failure events and diagnostics remain unchanged. Only
finished per-movie failure records qualify; a live partial JSONL never qualifies.
"""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core
from audit_movie_ocr import frame_reference, consecutive_cues, validate_ocr, decoder_outcome


def verify_frames(rows, expected, dimensions):
    core.require(len(rows) == len(expected), 'incomplete OCR frame records')
    for row, exp in zip(rows, expected):
        core.require(all(row[k] == v for k, v in exp.items()), 'native frame identity mismatch')
        core.require(row['frame_identity_verified'] and row['absence_of_text_verified'] is False,
                     'frame evidence flags mismatch')
        ocr = row['ocr']
        checked = validate_ocr([x['text'] for x in ocr], [x['confidence'] for x in ocr],
                               [x['box'] for x in ocr], *dimensions)
        core.require(checked == ocr, 'OCR evidence mismatch')
        reused = row['ocr_reused_from_previous']
        if reused:
            core.require(row['index'] > 0 and rows[row['index'] - 1]['sha256'] == row['sha256']
                         and rows[row['index'] - 1]['ocr'] == ocr, 'invalid OCR reuse')
    return dict(frames=len(rows), native_frame_hash_matches=len(rows),
                ocr_calls=sum(not r['ocr_reused_from_previous'] for r in rows),
                identical_frame_reuse=sum(r['ocr_reused_from_previous'] for r in rows))


def reconcile(run, decoded, movie, out):
    core.require(movie.isdecimal(), 'movie identifier must be numeric')
    folder = run / movie
    failure = folder / 'decode-failure.json'
    core.require(failure.is_file(), 'no finished per-movie failure record')
    originals = {p.name: core.file_digest(p) for p in [failure, folder/'frames.jsonl', folder/'decoder.stderr.txt']}
    source = next(x for x in json.loads((decoded/'movies.json').read_text('utf8'))
                  if Path(x['path'].split(';')[0]).stem == movie)
    f = json.loads(failure.read_text('utf8')); errors = (folder/'decoder.stderr.txt').read_text('utf8')
    core.require(f['stderr'] == errors and f['source_sha256'] == source['source_sha256'], 'failure identity mismatch')
    tb, dimensions, expected = frame_reference(decoded/(movie+'.framehash'))
    outcome = decoder_outcome(f['exit'], errors, f['frames'], len(expected))
    core.require(outcome['complete'] and outcome['rawvideo_dts_diagnostic'], 'not a recoverable DTS diagnostic')
    rows = [json.loads(x) for x in (folder/'frames.jsonl').read_text('utf8').splitlines()]
    stats = verify_frames(rows, expected, dimensions)
    evidence = {}
    for row in rows:
        if not row['ocr']: continue
        name = row['evidence_image']
        core.require(Path(name).name == name and name.endswith('.png'), 'evidence path escape')
        core.require((folder/name).is_file(), 'missing native image')
        if name not in evidence: evidence[name] = dict(path=name, sha256=core.file_digest(folder/name))
    cues = consecutive_cues(rows, tb)
    summary = dict(movie=movie, source_sha256=source['source_sha256'], original_artifact_hashes=originals,
                   **stats, candidate_images=len(evidence), exact_text_runs=len(cues),
                   original_failure_retained=True, decoder_outcome=outcome,
                   decoder_exit=f['exit'], frame_sampling=False, timestamps_rewritten=False,
                   original_verbatim_verified=False, exhaustive_visual_transcription=False,
                   coverage_review_complete=False, source_modified=False)
    out = core.output_directory(out); core.require(not any(out.iterdir()), 'output must be empty')
    for name, value in [('summary.json',summary), ('cues.json',cues), ('evidence.json',list(evidence.values()))]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'reconciled JSON reopen')
    for name, digest in originals.items():core.require(core.file_digest(folder/name) == digest, 'run artifact changed')
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('run','decoded','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--movie',required=True)
    a=p.parse_args();print(json.dumps(reconcile(a.run,a.decoded,a.movie,a.out),sort_keys=True))
