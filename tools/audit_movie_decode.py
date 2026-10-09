"""Hash every decoded video frame without extracting proprietary movie copies.

Full decoding is timeline evidence, not exhaustive visual transcription.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
ISO_HASH='6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45'


def frame_summary(path):
    tb=None;frames=0;previous=None;first=None;last=None;sizes=set()
    with path.open('r',encoding='ascii') as f:
        for line in f:
            line=line.strip()
            if not line:continue
            if line.startswith('#tb 0: '):tb=Fraction(line.split(': ',1)[1])
            if line.startswith('#'):continue
            parts=[p.strip() for p in line.split(',')]
            core.require(len(parts)==6 and parts[0]=='0','framehash row shape')
            dts,pts,duration,size=map(int,parts[1:5]);digest=parts[5]
            core.require(duration>0 and size>0 and re.fullmatch('[0-9a-f]{64}',digest) is not None,'invalid framehash data')
            core.require(previous is None or pts>=previous,'nonmonotonic video PTS')
            if first is None:first=pts
            previous=pts;last=pts+duration;frames+=1;sizes.add(size)
    core.require(tb is not None and tb>0 and frames>0,'missing video frames/timebase')
    return dict(frames=frames,timebase=str(tb),first_pts=first,last_end_pts=last,timeline_seconds=float((last-first)*tb),frame_sizes=sorted(sizes),framehash_sha256=core.file_digest(path))


def decode(stream,size,expected,executable,out):
    hashes=out.with_suffix('.framehash');errors=out.with_suffix('.stderr.txt')
    command=[str(executable),'-v','error','-nostdin','-i','pipe:0','-map','0:v:0','-an','-fps_mode','passthrough','-f','framehash','-hash','sha256','pipe:1']
    fed=0;digest=hashlib.sha256()
    with hashes.open('wb') as stdout,errors.open('wb') as stderr:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
        try:
            while fed<size:
                block=stream.read(min(1024*1024,size-fed));core.require(bool(block),'truncated SFD')
                process.stdin.write(block);fed+=len(block);digest.update(block)
            process.stdin.close();exit_code=process.wait(timeout=300)
        except BaseException:
            process.kill();process.wait();raise
    core.require(exit_code==0 and fed==size and digest.hexdigest()==expected,'movie decode or source identity mismatch')
    # Do not silently accept decoder error logs even when the process exits zero.
    core.require(errors.stat().st_size==0,'decoder reported video errors')
    return dict(command=command,exit=exit_code,fed_bytes=fed,source_sha256=digest.hexdigest(),stderr='',**frame_summary(hashes))


def audit(iso,inventory,executable,out):
    import pycdlib
    core.require(core.file_digest(iso)==ISO_HASH,'ISO identity mismatch')
    files=json.loads(inventory.read_text('utf8'))
    movies=[x for x in files if x['path'].endswith('.SFD;1')]
    core.require(len(movies)==46 and len({x['path'] for x in movies})==46,'movie inventory mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    cd=pycdlib.PyCdlib();cd.open(str(iso));rows=[]
    try:
        for source in movies:
            stem=Path(source['path'].split(';')[0]).stem
            with cd.open_file_from_iso(iso_path=source['path']) as stream:
                result=decode(stream,source['size'],source['sha256'],executable,out/stem)
            rows.append(dict(path=source['path'],**result));print(stem,result['frames'],flush=True)
            (out/'movies.json').write_text(json.dumps(rows,indent=2)+'\n','utf8')
    finally:cd.close()
    core.require(core.file_digest(iso)==ISO_HASH,'ISO changed')
    summary=dict(schema=1,source_iso_sha256=ISO_HASH,movies=len(rows),decoded_frames=sum(x['frames'] for x in rows),video_timeline_seconds=sum(x['timeline_seconds'] for x in rows),full_source_hash_matches=len(rows),decode_exit_zero=len(rows),decoder_errors=0,frame_sampling=False,exhaustive_visual_transcription=False,exhaustive_spoken_transcription=False,complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    for name,value in [('movies.json',rows),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['iso','inventory','executable','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.iso,a.inventory,a.executable,a.out),sort_keys=True))
