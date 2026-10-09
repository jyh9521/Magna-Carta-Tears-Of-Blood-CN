"""Inspect every original SFD with installed ffprobe; stream ISO bytes, no copies."""
from __future__ import annotations
import argparse,json,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core

def probe(stream,size,executable):
    command=[str(executable),'-v','error','-count_packets','-show_streams','-show_format','-of','json','-i','pipe:0']
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    fed=0;h=hashlib.sha256();broken=False
    try:
        while fed<size:
            block=stream.read(min(1024*1024,size-fed));core.require(bool(block),'truncated SFD input')
            try:process.stdin.write(block)
            except BrokenPipeError:broken=True;break
            h.update(block);fed+=len(block)
        try:process.stdin.close()
        except BrokenPipeError:broken=True
        process.stdin=None
        stdout,stderr=process.communicate(timeout=120)
    except BaseException:
        process.kill();process.wait();raise
    return dict(command=command,exit=process.returncode,fed_bytes=fed,input_bytes=size,full_input=fed==size and not broken,
        fed_sha256=h.hexdigest(),stderr=stderr.decode('utf8','replace'),
        metadata=json.loads(stdout) if stdout.strip() else {},stdout_sha256=core.digest(stdout))

def audit(iso,inventory,out,ffprobe):
    import pycdlib
    expected=json.loads((inventory/'summary.json').read_text('utf8'))['source_iso_sha256']
    core.require(core.file_digest(iso)==expected,'ISO identity mismatch')
    files=json.loads((inventory/'iso-files.json').read_text('utf8'))
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    cd=pycdlib.PyCdlib();cd.open(str(iso));rows=[]
    try:
        for source in files:
            if not source['path'].endswith('.SFD;1'):continue
            with cd.open_file_from_iso(iso_path=source['path']) as stream:
                result=probe(stream,source['size'],ffprobe)
            if result['full_input']:core.require(result['fed_sha256']==source['sha256'],'SFD identity mismatch')
            row=dict(path=source['path'],source_sha256=source['sha256'],**result,
                     visual_text_review='pending',spoken_text_review='pending')
            rows.append(row);print(source['path'],result['exit'],result['fed_bytes'],flush=True)
            (out/'sfd-probes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    finally:cd.close()
    core.require(core.file_digest(iso)==expected,'ISO changed')
    summary=dict(schema=1,source_iso_sha256=expected,sfd_files=len(rows),probe_exit_zero=sum(r['exit']==0 for r in rows),
        full_input_hash_matches=sum(r['full_input'] for r in rows),
        video_streams=sum(s.get('codec_type')=='video' for r in rows for s in r['metadata'].get('streams',[])),
        audio_streams=sum(s.get('codec_type')=='audio' for r in rows for s in r['metadata'].get('streams',[])),
        complete_game_text=False,result='all SFD stream metadata inspected; visual and spoken text review pending')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    core.require(json.loads((out/'sfd-probes.json').read_text('utf8'))==rows,'SFD reopen mismatch')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--iso',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--ffprobe',type=Path,required=True);a=p.parse_args()
    print(json.dumps(audit(a.iso,a.inventory,a.out,a.ffprobe),sort_keys=True))
