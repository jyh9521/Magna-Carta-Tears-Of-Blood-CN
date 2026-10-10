"""Full-frame movie OCR candidates, bound to original decoded frame hashes.

No OCR-negative result proves absence of text. No inferred text is importable.
Only byte-identical consecutive frames reuse an OCR result; no fps sampling,
scene threshold or subtitle-only crop excludes frames from the pass.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import font_poc as core
from audit_movie_decode import ISO_HASH


class MovieDecodeFailure(ValueError):
    pass


def decoder_outcome(exit_code, errors, frames, expected):
    """Recognize only an exact rawvideo muxer DTS diagnostic, never decoder errors.

    Callers must separately verify source identity and every native frame hash.
    The diagnostic remains recorded; no timestamp is rewritten.
    """
    lines = errors.splitlines()
    matches = [re.fullmatch(
        r'\[rawvideo @ [0-9a-fA-F]+\] Application provided invalid, non monotonically '
        r'increasing dts to muxer in stream 0: (-?\d+) >= (-?\d+)', line) for line in lines]
    known = bool(lines) and all(m and int(m[1]) >= int(m[2]) for m in matches)
    complete = exit_code == 0 and frames == expected and expected > 0 and (not errors or known)
    return dict(complete=complete, rawvideo_dts_diagnostic=known,
                diagnostic_retained=bool(errors), timestamps_rewritten=False)


def frame_reference(path):
    tb = None
    dimensions = None
    rows = []
    previous = None
    for line in path.read_text('ascii').splitlines():
        if line.startswith('#tb 0: '):
            tb = Fraction(line.split(': ', 1)[1])
        if line.startswith('#dimensions 0: '):
            m = re.fullmatch(r'#dimensions 0: (\d+)x(\d+)', line)
            core.require(m is not None, 'frame dimension header')
            dimensions = tuple(map(int, m.groups()))
        if not line or line.startswith('#'):
            continue
        parts = [x.strip() for x in line.split(',')]
        core.require(len(parts) == 6 and parts[0] == '0', 'frame reference shape')
        dts, pts, duration, size = map(int, parts[1:5])
        core.require(duration > 0 and size > 0 and re.fullmatch('[0-9a-f]{64}', parts[5]), 'frame reference values')
        core.require(previous is None or pts >= previous, 'nonmonotonic frame reference')
        previous = pts
        rows.append(dict(index=len(rows), dts=dts, pts=pts, duration=duration, size=size, sha256=parts[5]))
    core.require(tb is not None and tb > 0 and dimensions and rows, 'incomplete frame reference')
    w, h = dimensions
    core.require(w > 0 and h > 0 and w % 2 == h % 2 == 0, 'YUV420 dimensions')
    core.require(all(r['size'] == w * h * 3 // 2 for r in rows), 'unsupported native pixel format')
    return tb, dimensions, rows


def read_frame(stream, size):
    core.require(size > 0, 'frame size')
    raw = bytearray()
    while len(raw) < size:
        block = stream.read(size - len(raw))
        if not block:
            return bytes(raw)
        raw.extend(block)
    return bytes(raw)


def validate_ocr(texts, scores, boxes, width, height):
    texts, scores, boxes = list(texts or []), list(scores or []), list(boxes or [])
    core.require(len(texts) == len(scores) == len(boxes), 'OCR result lengths')
    rows = []
    for text, score, box in zip(texts, scores, boxes):
        core.require(isinstance(text, str) and math.isfinite(float(score)) and 0 <= float(score) <= 1, 'OCR text/score')
        core.require(len(box) == 4 and all(len(p) == 2 for p in box), 'OCR quadrilateral')
        core.require(all(math.isfinite(float(x)) and math.isfinite(float(y)) and
                         -1 <= x <= width + 1 and -1 <= y <= height + 1 for x, y in box), 'OCR box bounds')
        rows.append(dict(text=text, confidence=float(score), box=box,
                         original_verbatim_verified=False, editable=False))
    return rows


def consecutive_cues(rows, tb):
    """Exact candidate text runs only; never fuzzy-merge different source strings."""
    cues = []
    active = None
    for row in rows:
        texts = tuple(x['text'] for x in row['ocr'])
        end = row['pts'] + row['duration']
        if active and texts == tuple(active['texts']) and row['pts'] == active['end_pts']:
            active['end_pts'] = end
            active['last_frame'] = row['index']
            active['end_seconds'] = float(end * tb)
        else:
            active = None
            if texts:
                active = dict(first_frame=row['index'], last_frame=row['index'], start_pts=row['pts'], end_pts=end,
                              start_seconds=float(row['pts'] * tb), end_seconds=float(end * tb), texts=list(texts),
                              evidence_image=row.get('evidence_image'), original_verbatim_verified=False,
                              temporal_boundary_reviewed=False, editable=False)
                cues.append(active)
    return cues


class Backend:
    def __init__(self, language, provider, rec_version='PP-OCRv5'):
        from rapidocr import RapidOCR, OCRVersion, LangRec, ModelType
        self.language = language
        self.engine = RapidOCR(params={
            'Det.ocr_version': OCRVersion.PPOCRV4, 'Det.model_type': ModelType.MOBILE,
            'Rec.ocr_version': OCRVersion(rec_version), 'Rec.lang_type': LangRec(language),
            'Rec.model_type': ModelType.MOBILE, 'Global.text_score': 0.0,
            'Global.log_level': 'critical', 'EngineConfig.onnxruntime.intra_op_num_threads': 2,
            'EngineConfig.onnxruntime.inter_op_num_threads': 1,
            'EngineConfig.onnxruntime.use_dml': provider == 'directml'})
        sessions = [self.engine.text_det.session.session, self.engine.text_cls.session.session,
                    self.engine.text_rec.session.session]
        if provider == 'directml':
            core.require(all(s.get_providers()[0] == 'DmlExecutionProvider' for s in sessions), 'DirectML provider not active')
        self.metadata = dict(language=language, recognition_version=rec_version, rapidocr=importlib.metadata.version('rapidocr'),
                             onnxruntime=__import__('onnxruntime').__version__, models=[])
        for role, session in zip(('det', 'cls', 'rec'), sessions):
            path = Path(session._model_path)
            self.metadata['models'].append(dict(role=role, name=path.name, sha256=core.file_digest(path),
                                               providers=session.get_providers()))

    def __call__(self, image):
        result = self.engine(image)
        boxes = [] if result.boxes is None else result.boxes.tolist()
        return validate_ocr(result.txts, result.scores, boxes, image.shape[1], image.shape[0])


def decode_movie(stream, source, reference, executable, backend, out):
    import cv2
    import numpy as np
    tb, (w,h), expected = frame_reference(reference)
    core.require(core.file_digest(reference) == source['framehash_sha256'] and len(expected) == source['frames'], 'decoded reference identity')
    out.mkdir()
    command = [str(executable), '-v', 'error', '-nostdin', '-i', 'pipe:0', '-map', '0:v:0', '-an',
               '-fps_mode', 'passthrough', '-pix_fmt', 'yuv420p', '-f', 'rawvideo', 'pipe:1']
    feed = dict(bytes=0, digest=hashlib.sha256(), errors=[])
    rows = []
    text_frames = 0
    calls = 0
    reused = 0
    evidence = {}
    previous = None
    previous_ocr = None
    with (out/'decoder.stderr.txt').open('wb') as stderr, (out/'frames.jsonl').open('w', encoding='utf8') as records:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        def feeder():
            broken = False
            try:
                while feed['bytes'] < source['fed_bytes']:
                    block = stream.read(min(1024*1024, source['fed_bytes']-feed['bytes']))
                    core.require(bool(block), 'truncated ISO movie stream')
                    feed['bytes'] += len(block)
                    feed['digest'].update(block)
                    if not broken:
                        try: process.stdin.write(block)
                        except (BrokenPipeError, OSError): broken = True
                try: process.stdin.close()
                except (BrokenPipeError, OSError): pass
            except BaseException as error:
                feed['errors'].append(repr(error))
                process.kill()
        worker = threading.Thread(target=feeder, daemon=True)
        worker.start()
        try:
            for exp in expected:
                raw = read_frame(process.stdout, exp['size'])
                if len(raw) != exp['size']:
                    break
                digest = core.digest(raw)
                core.require(digest == exp['sha256'], 'native decoded frame hash mismatch')
                image = None
                if digest == previous:
                    ocr = previous_ocr
                    reused += 1
                else:
                    image = cv2.cvtColor(np.frombuffer(raw,dtype=np.uint8).reshape(h*3//2,w), cv2.COLOR_YUV2BGR_I420)
                    ocr = backend(image)
                    calls += 1
                item = dict(exp, ocr=ocr, ocr_reused_from_previous=digest == previous,
                            absence_of_text_verified=False, frame_identity_verified=True)
                if ocr:
                    text_frames += 1
                    key = core.digest(json.dumps([x['text'] for x in ocr], ensure_ascii=False).encode('utf8'))
                    if key not in evidence:
                        if image is None:
                            image = cv2.cvtColor(np.frombuffer(raw,dtype=np.uint8).reshape(h*3//2,w),cv2.COLOR_YUV2BGR_I420)
                        name = f"frame-{exp['index']:06d}.png"
                        encoded = cv2.imencode('.png', image)[1].tobytes()
                        (out/name).write_bytes(encoded)
                        evidence[key] = dict(path=name, sha256=core.digest(encoded), frame=exp['index'])
                    item['evidence_image'] = evidence[key]['path']
                rows.append(item)
                records.write(json.dumps(item,ensure_ascii=False)+'\n')
                previous, previous_ocr = digest, ocr
                if len(rows) % 100 == 0:
                    records.flush()
                    (out/'progress.json').write_text(json.dumps(dict(pid=os.getpid(),decoder_pid=process.pid,
                        frames=len(rows),expected=len(expected),ocr_calls=calls,text_frames=text_frames,status='running'))+'\n','utf8')
                    print(out.name, len(rows), '/', len(expected), flush=True)
            extra = process.stdout.read(1)
            core.require(not extra, 'unexpected extra decoded frame')
            worker.join(timeout=300)
            core.require(not worker.is_alive(), 'movie feeder did not terminate')
            exit_code = process.wait(timeout=300)
        except BaseException:
            process.kill(); process.wait(); worker.join(timeout=10)
            raise
        finally:
            process.stdout.close()
    core.require(not feed['errors'] and feed['bytes'] == source['fed_bytes'] and
                 feed['digest'].hexdigest() == source['source_sha256'], 'ISO movie source identity mismatch')
    errors = (out/'decoder.stderr.txt').read_text('utf8',errors='replace')
    outcome = decoder_outcome(exit_code, errors, len(rows), len(expected))
    if not outcome['complete']:
        (out/'decode-failure.json').write_text(json.dumps(dict(exit=exit_code,stderr=errors,
            frames=len(rows),expected=len(expected),source_sha256=feed['digest'].hexdigest()))+'\n','utf8')
        raise MovieDecodeFailure('decoder exit/log/frame-count failure; original evidence retained')
    cues = consecutive_cues(rows,tb)
    summary = dict(path=source['path'],source_sha256=source['source_sha256'],frames=len(rows),
                   native_frame_hash_matches=len(rows),ocr_calls=calls,identical_frame_reuse=reused,
                   frames_with_ocr_candidates=text_frames,distinct_candidate_images=len(evidence),
                   exact_text_runs=len(cues),timebase=str(tb),width=w,height=h,command=command,exit=exit_code,
                   decoder_outcome=outcome, decoder_stderr_sha256=core.file_digest(out/'decoder.stderr.txt'),
                   frame_sampling=False,full_frame_input=True,exhaustive_visual_transcription=False,
                   original_verbatim_verified=False,complete_game_text=False)
    for name,value in [('cues.json',cues),('evidence.json',list(evidence.values())),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'movie JSON reopen')
    reopened=[json.loads(line) for line in (out/'frames.jsonl').read_text('utf8').splitlines()]
    core.require(reopened==rows,'frame records reopen')
    for item in evidence.values():core.require(core.file_digest(out/item['path'])==item['sha256'],'frame evidence hash')
    (out/'progress.json').write_text(json.dumps(dict(status='complete',frames=len(rows)))+'\n','utf8')
    return summary


def audit(iso, decoded, executable, language, overrides, provider, selections, out):
    import pycdlib
    core.require(core.file_digest(iso)==ISO_HASH,'unsupported ISO identity')
    original_index=core.file_digest(decoded/'movies.json')
    sources=json.loads((decoded/'movies.json').read_text('utf8'))
    core.require(len(sources)==46 and len({s['path'] for s in sources})==46,'full movie inventory')
    stems={Path(s['path'].split(';')[0]).stem for s in sources}
    core.require(set(selections)<=stems and set(overrides)<=stems,'unknown movie selection/override')
    selected=[s for s in sources if not selections or Path(s['path'].split(';')[0]).stem in selections]
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    engines={};rows=[];failures=[]
    cd=pycdlib.PyCdlib();cd.open(str(iso))
    try:
        for source in selected:
            stem=Path(source['path'].split(';')[0]).stem
            lang=overrides.get(stem,language)
            if lang not in engines:engines[lang]=Backend(lang,provider)
            (out/'models.json').write_text(json.dumps({k:e.metadata for k,e in engines.items()},indent=2)+'\n','utf8')
            try:
                with cd.open_file_from_iso(iso_path=source['path']) as stream:
                    result=decode_movie(stream,source,decoded/(stem+'.framehash'),executable,engines[lang],out/stem)
                rows.append(dict(result,language=lang));print('COMPLETE',stem,result['frames'],flush=True)
            except MovieDecodeFailure as error:
                failures.append(dict(movie=stem,reason=str(error),status='deferred-decode-failure'))
                print('DEFERRED_DECODE_FAILURE',stem,flush=True)
            (out/'movies.json').write_text(json.dumps(rows,indent=2)+'\n','utf8')
            (out/'failures.json').write_text(json.dumps(failures,indent=2)+'\n','utf8')
    finally:cd.close()
    core.require(core.file_digest(iso)==ISO_HASH and core.file_digest(decoded/'movies.json')==original_index,'source changed')
    summary=dict(schema=1,source_iso_sha256=ISO_HASH,movies_requested=len(selected),movies_complete=len(rows),
                 deferred_decode_failures=len(failures),frames=sum(r['frames'] for r in rows),
                 native_frame_hash_matches=sum(r['native_frame_hash_matches'] for r in rows),
                 ocr_calls=sum(r['ocr_calls'] for r in rows),identical_frame_reuse=sum(r['identical_frame_reuse'] for r in rows),
                 frame_sampling=False,full_frame_input=True,exhaustive_visual_transcription=False,
                 original_verbatim_verified=False,complete_game_text=False,coverage_review_complete=False,
                 source_modified=False,translation_gate='coverage-audit-pending')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n','utf8')
    for name in ('summary.json','models.json','movies.json','failures.json'):json.loads((out/name).read_text('utf8'))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('iso','decoded','executable','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',required=True)
    p.add_argument('--language-override',action='append',default=[],metavar='MOVIE=LANGUAGE')
    p.add_argument('--provider',choices=('cpu','directml'),default='cpu')
    p.add_argument('--movie',action='append',default=[])
    a=p.parse_args();overrides={}
    for pair in a.language_override:
        parts=pair.split('=');core.require(len(parts)==2 and all(parts),'language override syntax')
        core.require(parts[0] not in overrides,'duplicate language override');overrides[parts[0]]=parts[1]
    print(json.dumps(audit(a.iso,a.decoded,a.executable,a.language,overrides,a.provider,a.movie,a.out),sort_keys=True))
