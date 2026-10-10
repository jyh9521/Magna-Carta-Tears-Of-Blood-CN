"""Local original-language movie speech candidates with audio/source identity.

ASR is not verbatim proof and cannot inventory silent visual text. Full audio is
decoded; VAD is disabled, and model-skipped intervals remain reviewable in PCM.
"""
from pathlib import Path
from collections import Counter
import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import time
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from audit_movie_decode import ISO_HASH


def wave_identity(path):
    with wave.open(str(path),'rb') as w:
        core.require((w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype()) ==
                     (1,2,16000,'NONE'),'unsupported normalized audio')
        samples=w.getnframes();raw=w.readframes(samples)
        core.require(samples>0 and len(raw)==samples*2,'truncated/empty PCM')
    return dict(samples=samples,sample_rate=16000,channels=1,sample_width=2,
                duration_seconds=samples/16000,pcm_sha256=core.digest(raw),wav_sha256=core.file_digest(path))


def pcm_samples(path):
    """Pass verified 16 kHz mono PCM directly, avoiding a second decoder API."""
    import numpy as np
    wave_identity(path)
    with wave.open(str(path),'rb') as w:raw=w.readframes(w.getnframes())
    return np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0


def segment_record(segment,duration):
    row=dict(segment)
    for n in ('start','end','avg_logprob','no_speech_prob','compression_ratio'):
        core.require(isinstance(row[n],(int,float)) and math.isfinite(row[n]),'ASR nonfinite metric')
    core.require(0<=row['start']<=row['end']<=duration+0.1,'ASR segment time bounds')
    core.require(isinstance(row['text'],str) and 0<=row['no_speech_prob']<=1 and
                 row['compression_ratio']>=0,'ASR text/metric shape')
    for word in row.get('words') or []:
        core.require(isinstance(word['word'],str) and all(math.isfinite(word[n]) for n in ('start','end','probability')),
                     'ASR word shape')
        core.require(0<=word['start']<=word['end']<=duration+0.1 and 0<=word['probability']<=1,'ASR word bounds')
    flags=[]
    if row['avg_logprob'] < -0.6:flags.append('low-average-log-probability')
    if row['no_speech_prob'] > 0.6:flags.append('high-no-speech-probability')
    if row['compression_ratio'] > 2.4:flags.append('high-compression-ratio')
    if any(w['probability']<0.5 for w in row.get('words') or []):flags.append('low-word-probability')
    row.update(uncertainty_flags=flags,original_verbatim_verified=False,listen_reviewed=False,
               visual_confirmation=False,editable=False,backend_eligible=False)
    return row


def decode_audio(stream,source,executable,out):
    out.mkdir(parents=True,exist_ok=False)
    audio=out/'audio.wav';errors=out/'decoder.stderr.txt'
    command=[str(executable),'-v','error','-nostdin','-i','pipe:0','-map','0:a:0','-vn',
             '-ac','1','-ar','16000','-c:a','pcm_s16le','-f','wav',str(audio)]
    fed=0;digest=hashlib.sha256();broken=False
    with errors.open('wb') as stderr:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=stderr)
        try:
            while fed<source['fed_bytes']:
                block=stream.read(min(1024*1024,source['fed_bytes']-fed));core.require(bool(block),'truncated SFD stream')
                fed+=len(block);digest.update(block)
                if not broken:
                    try:process.stdin.write(block)
                    except (BrokenPipeError,OSError):broken=True
            try:process.stdin.close()
            except (BrokenPipeError,OSError):pass
            code=process.wait(timeout=300)
        except BaseException:
            process.kill();process.wait();raise
    core.require(fed==source['fed_bytes'] and digest.hexdigest()==source['source_sha256'],'movie source mismatch')
    result=dict(command=command,exit=code,source_sha256=digest.hexdigest(),fed_bytes=fed,
                stderr_sha256=core.file_digest(errors),decoder_log_empty=errors.stat().st_size==0)
    if code!=0 or errors.stat().st_size:
        result['status']='temporarily-deferred-audio-decode'
    else:
        result.update(status='audio-decode-complete',audio=wave_identity(audio))
    (out/'decode.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
    return result


def inventory(decoded,probes):
    sources=json.loads(decoded.read_text('utf8'));p=json.loads(probes.read_text('utf8'))
    core.require(len(sources)==len(p)==46,'movie inventory count')
    by_path={x['path']:x for x in p}
    core.require(len(by_path)==46 and {x['path'] for x in sources}==set(by_path),'movie inventory set')
    result=[]
    for source in sources:
        probe=by_path[source['path']]
        core.require(source['source_sha256']==probe['source_sha256'] and probe['exit']==0,'probe identity mismatch')
        audio=[s for s in probe['metadata']['streams'] if s['codec_type']=='audio']
        core.require(len(audio)<=1,'multiple audio tracks require explicit selection')
        result.append(dict(source,audio_streams=len(audio),audio_stream_metadata=audio))
    return result


def audit(iso,decoded,probes,executable,model,language,overrides,selections,out,device,compute):
    import pycdlib
    from faster_whisper import WhisperModel
    core.require(core.file_digest(iso)==ISO_HASH,'unsupported ISO')
    before={str(p):core.file_digest(p) for p in (decoded,probes)}
    sources=inventory(decoded,probes)
    stems={Path(x['path'].split(';')[0]).stem for x in sources}
    core.require(set(selections)<=stems and set(overrides)<=stems,'unknown movie selection/language override')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    weights={p.name:core.file_digest(p) for p in model.iterdir() if p.is_file()}
    core.require({'model.bin','config.json','tokenizer.json'}<=weights.keys(),'incomplete local model')
    engine=WhisperModel(str(model),device=device,compute_type=compute,cpu_threads=8)
    options=dict(task='transcribe',beam_size=5,temperature=0.0,condition_on_previous_text=False,
                 word_timestamps=True,vad_filter=False)
    metadata=dict(model_files=weights,provenance=json.loads((model/'provenance.json').read_text('utf8')),
                  faster_whisper=importlib.metadata.version('faster-whisper'),
                  ctranslate2=importlib.metadata.version('ctranslate2'),device=engine.model.device,
                  compute_type=engine.model.compute_type,options=options,language=language,overrides=overrides)
    (out/'model.json').write_text(json.dumps(metadata,indent=2)+'\n','utf8')
    cd=pycdlib.PyCdlib();cd.open(str(iso));results=[]
    try:
        for source in sources:
            movie=Path(source['path'].split(';')[0]).stem
            if selections and movie not in selections:continue
            lang=overrides.get(movie,language)
            if not source['audio_streams']:
                results.append(dict(movie=movie,path=source['path'],source_sha256=source['source_sha256'],
                                    status='no-audio-stream',visual_review='required',no_text_verified=False))
            else:
                folder=out/movie
                with cd.open_file_from_iso(iso_path=source['path']) as stream:
                    result=decode_audio(stream,source,executable,folder)
                result.update(movie=movie,language=lang)
                if result['status']=='audio-decode-complete':
                    started=time.monotonic();duration=result['audio']['duration_seconds'];rows=[]
                    segments,info=engine.transcribe(pcm_samples(folder/'audio.wav'),language=lang,**options)
                    for segment in segments:
                        rows.append(segment_record(dataclasses.asdict(segment),duration))
                        (folder/'segments.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf8')
                        print('ASR_SEGMENT',movie,len(rows),round(segment.end,2),flush=True)
                    result.update(status='asr-candidates-complete',segments=len(rows),
                                  uncertain_segments=sum(bool(x['uncertainty_flags']) for x in rows),
                                  asr_seconds=round(time.monotonic()-started,3),
                                  model_reported_language=info.language,language_selection='explicit',
                                  language_probability=info.language_probability,
                                  original_verbatim_verified=False,listen_reviewed=False,visual_confirmation=False)
                    if not rows:(folder/'segments.json').write_text('[]\n','utf8')
                    core.require(json.loads((folder/'segments.json').read_text('utf8'))==rows,'segment JSON reopen')
                (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
                results.append(result)
            (out/'movies.json').write_text(json.dumps(results,indent=2)+'\n','utf8')
            print('ASR_MOVIE_COMPLETE',movie,results[-1]['status'],flush=True)
    finally:cd.close()
    core.require(core.file_digest(iso)==ISO_HASH and all(core.file_digest(Path(p))==h for p,h in before.items()),'source changed')
    core.require(all(core.file_digest(model/n)==h for n,h in weights.items()),'model changed')
    summary=dict(movies_requested=len(results),statuses=dict(Counter(x['status'] for x in results)),
                 asr_segments=sum(x.get('segments',0) for x in results),source_modified=False,
                 original_verbatim_verified=False,exhaustive_spoken_transcription=False,
                 silent_visual_text_covered=False,coverage_review_complete=False,
                 translation_gate='coverage-audit-pending')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n','utf8')
    for n in ('movies.json','summary.json','model.json'):json.loads((out/n).read_text('utf8'))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('iso','decoded','probes','executable','model','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',required=True);p.add_argument('--language-override',action='append',default=[])
    p.add_argument('--movie',action='append',default=[]);p.add_argument('--device',choices=('cpu','cuda'),default='cpu')
    p.add_argument('--compute',default='int8');a=p.parse_args();overrides={}
    for item in a.language_override:
        parts=item.split('=');core.require(len(parts)==2 and all(parts) and parts[0] not in overrides,'language override syntax')
        overrides[parts[0]]=parts[1]
    print(json.dumps(audit(a.iso,a.decoded,a.probes,a.executable,a.model,a.language,overrides,a.movie,a.out,a.device,a.compute),sort_keys=True))
