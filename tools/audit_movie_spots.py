"""OCR only uncertainty-selected native frames; never a full visual census."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,threading
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from audit_movie_ocr import Backend,frame_reference,read_frame,decoder_outcome,MovieDecodeFailure,validate_ocr
from audit_movie_decode import ISO_HASH


def targets(segments,frames,tb):
    core.require(bool(frames) and tb>0,'missing frame timeline')
    result=[]
    for segment in segments:
        if not segment['targeted_ocr_requested']:continue
        core.require(0<=segment['start']<=segment['end'],'invalid ASR interval')
        midpoint=(Fraction(str(segment['start']))+Fraction(str(segment['end'])))/2
        selected=min(frames,key=lambda f:abs(Fraction(f['pts'])*tb-midpoint))
        result.append(dict(segment_id=segment['segment_id'],frame_index=selected['index'],
                           pts=selected['pts'],asr_midpoint_seconds=float(midpoint),
                           selected_frame_seconds=float(Fraction(selected['pts'])*tb),
                           selection='nearest-ASR-midpoint-not-subtitle-boundary-proof'))
    return result


def verify_saved_frames(saved,expected,folder,dimensions):
    core.require(len(saved)==len(expected),'resumed frame count')
    for row,frame in zip(saved,expected):
        core.require(all(row[k]==v for k,v in frame.items()),'resumed frame identity')
        name=row['image'];core.require(Path(name).name==name and name.endswith('.png'),'resumed image path escape')
        core.require(core.file_digest(folder/name)==row['image_sha256'],'resumed image identity')
        core.require(row['absence_of_text_verified'] is False and row['original_verbatim_verified'] is False,'resumed evidence flags')
        ocr=row['ocr']
        core.require(validate_ocr([x['text'] for x in ocr],[x['confidence'] for x in ocr],
                                  [x['box'] for x in ocr],*dimensions)==ocr,'resumed OCR evidence')


def extract(stream,source,executable,expected,dimensions,backend,out):
    import numpy as np,cv2
    out.mkdir(parents=True,exist_ok=False);w,h=dimensions
    expression='+'.join('eq(n\\,'+str(f['index'])+')' for f in expected)
    command=[str(executable),'-v','error','-nostdin','-i','pipe:0','-map','0:v:0','-an',
             '-vf','select='+expression,'-fps_mode','passthrough','-pix_fmt','yuv420p','-f','rawvideo','pipe:1']
    feed=dict(bytes=0,digest=hashlib.sha256(),errors=[])
    with (out/'decoder.stderr.txt').open('wb') as stderr:
        p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr)
        def pump():
            try:
                broken=False
                while feed['bytes']<source['fed_bytes']:
                    b=stream.read(min(1048576,source['fed_bytes']-feed['bytes']));core.require(bool(b),'truncated source')
                    feed['bytes']+=len(b);feed['digest'].update(b)
                    if not broken:
                        try:p.stdin.write(b)
                        except (BrokenPipeError,OSError):broken=True
                try:p.stdin.close()
                except (BrokenPipeError,OSError):pass
            except BaseException as error:feed['errors'].append(repr(error));p.kill()
        worker=threading.Thread(target=pump,daemon=True);worker.start();rows=[]
        try:
            for frame in expected:
                raw=read_frame(p.stdout,frame['size'])
                if len(raw)!=frame['size']:raise MovieDecodeFailure('truncated selected video frame')
                core.require(core.digest(raw)==frame['sha256'],'selected frame hash mismatch')
                image=cv2.cvtColor(np.frombuffer(raw,dtype=np.uint8).reshape(h*3//2,w),cv2.COLOR_YUV2BGR_I420)
                png=cv2.imencode('.png',image)[1].tobytes();name='frame-'+str(frame['index'])+'.png';(out/name).write_bytes(png)
                rows.append(dict(frame,image=name,image_sha256=core.digest(png),ocr=backend(image),
                                 absence_of_text_verified=False,original_verbatim_verified=False))
            core.require(not p.stdout.read(1),'unexpected selected frame')
            worker.join(timeout=300);core.require(not worker.is_alive(),'source feeder timeout');code=p.wait(timeout=300)
        except BaseException:p.kill();p.wait();worker.join(timeout=10);raise
        finally:p.stdout.close()
    core.require(not feed['errors'] and feed['bytes']==source['fed_bytes'] and
                 feed['digest'].hexdigest()==source['source_sha256'],'selected movie source mismatch')
    outcome=decoder_outcome(code,(out/'decoder.stderr.txt').read_text('utf8'),len(rows),len(expected))
    (out/'frames.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf8')
    if not outcome['complete']:raise MovieDecodeFailure('selected video decoder exit/log failure')
    core.require(json.loads((out/'frames.json').read_text('utf8'))==rows,'selected frame JSON reopen')
    for row in rows:core.require(core.file_digest(out/row['image'])==row['image_sha256'],'selected image changed')
    return rows,outcome


def audit(iso,decoded,probes,review,executable,out,resume=False,versions=None):
    import pycdlib
    core.require(core.file_digest(iso)==ISO_HASH,'unsupported ISO')
    before={str(p):core.file_digest(p) for p in (decoded/'movies.json',probes,review)}
    sources={Path(s['path'].split(';')[0]).stem:s for s in json.loads((decoded/'movies.json').read_text('utf8'))}
    probes_by_movie={Path(s['path'].split(';')[0]).stem:s for s in json.loads(probes.read_text('utf8'))}
    reviews=json.loads(review.read_text('utf8'));core.require(len(reviews)==len(sources)==46,'movie review inventory')
    out=core.output_directory(out)
    if resume:core.require((out/'movies.json').is_file(),'missing resumable movie inventory')
    else:core.require(not any(out.iterdir()),'output must be empty')
    previous=json.loads((out/'movies.json').read_text('utf8')) if resume else []
    completed={r['movie']:r for r in previous if 'status' not in r}
    core.require(len(completed)==len(previous),'deferred/duplicate movie requires separate output')
    versions=versions or {};engines={};results=[];cd=pycdlib.PyCdlib();cd.open(str(iso))
    try:
        for movie in reviews:
            stem=movie['movie'];segments=movie.get('segments',[])
            if not any(s['targeted_ocr_requested'] for s in segments):continue
            source=sources[stem];core.require(source['source_sha256']==movie['source_sha256'],'review source identity')
            audio=[s for s in probes_by_movie[stem]['metadata']['streams'] if s['codec_type']=='audio']
            core.require(len(audio)==1 and Fraction(audio[0].get('start_time','0'))==0,'audio/video origin requires explicit offset')
            tb,dimensions,frames=frame_reference(decoded/(stem+'.framehash'));selected=targets(segments,frames,tb)
            indexes={s['frame_index'] for s in selected};expected=[f for f in frames if f['index'] in indexes]
            language={'ko':'korean','ja':'japan'}[movie['language']]
            if language not in engines:
                engines[language]=Backend(language,'cpu',versions.get(language,'PP-OCRv5'))
                (out/'models.json').write_text(json.dumps({k:e.metadata for k,e in engines.items()},indent=2)+'\n','utf8')
            if stem in completed:
                prior=completed[stem];core.require(prior['targets']==selected,'resumed selection changed')
                saved=json.loads((out/stem/'frames.json').read_text('utf8'))
                core.require(len(saved)==prior['selected_frames'],'resumed summary count')
                verify_saved_frames(saved,expected,out/stem,dimensions)
                current_outcome=decoder_outcome(0,(out/stem/'decoder.stderr.txt').read_text('utf8'),len(saved),len(expected))
                core.require(current_outcome==prior['decoder_outcome'] and current_outcome['complete'],'resumed decoder evidence')
                results.append(prior);print('SPOT_OCR_REUSED',stem,len(saved),flush=True);continue
            try:
                with cd.open_file_from_iso(iso_path=source['path']) as stream:
                    rows,outcome=extract(stream,source,executable,expected,dimensions,engines[language],out/stem)
            except MovieDecodeFailure as error:
                failure=dict(movie=stem,status='temporarily-deferred-selected-video-decode',reason=str(error))
                (out/stem/'decode-failure.json').write_text(json.dumps(failure)+'\n','utf8')
                results.append(dict(failure,targets=selected,selected_frames=0));continue
            results.append(dict(movie=stem,targets=selected,selected_frames=len(rows),decoder_outcome=outcome,
                                full_visual_transcription=False,original_verbatim_verified=False))
            (out/'movies.json').write_text(json.dumps(results,indent=2)+'\n','utf8');print('SPOT_OCR_COMPLETE',stem,len(rows),flush=True)
    finally:cd.close()
    summary=dict(movies=len(results),selected_frames=sum(r['selected_frames'] for r in results),
                 uncertainty_segments=sum(len(r['targets']) for r in results),
                 deferred_decodes=sum('status' in r for r in results),
                 all_selected_frame_hashes_verified=all('status' not in r for r in results),full_frame_ocr=False,full_visual_transcription=False,
                 original_verbatim_verified=False,source_modified=False,coverage_review_complete=False)
    for name,value in [('movies.json',results),('summary.json',summary),('models.json',{k:e.metadata for k,e in engines.items()})]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n','utf8');json.loads((out/name).read_text('utf8'))
    core.require(core.file_digest(iso)==ISO_HASH and all(core.file_digest(Path(p))==h for p,h in before.items()),'source changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('iso','decoded','probes','review','executable','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--resume',action='store_true');p.add_argument('--rec-version-override',action='append',default=[])
    a=p.parse_args();versions={}
    for item in a.rec_version_override:
        parts=item.split('=');core.require(len(parts)==2 and all(parts) and parts[0] not in versions,'recognition version override')
        versions[parts[0]]=parts[1]
    print(json.dumps(audit(a.iso,a.decoded,a.probes,a.review,a.executable,a.out,a.resume,versions),sort_keys=True))
