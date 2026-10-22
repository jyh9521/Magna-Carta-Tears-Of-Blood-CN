"""Build a separate, version-bound ISO with lossless repairs of audited movies."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from audit_movie_playback import file_hash, digest, structure
from movie_playback import repair_sfd
from iso import _portable_metadata, patch_iso, SECTOR
from udf_overlay import plan_udf_overlay, apply_udf_overlay
from iso_validation import verify_iso_overlay


def build(args):
    if file_hash(args.iso)!=args.expected_sha256:raise ValueError('input ISO hash mismatch')
    if args.output.exists() or args.iso.resolve()==args.output.resolve():raise ValueError('output exists/aliases input')
    args.out.mkdir(parents=True,exist_ok=True)
    if any(args.out.iterdir()):raise ValueError('working output must be empty')
    audit=json.loads(args.audit.read_text('utf8'))
    files,_=_portable_metadata(args.iso)
    names={name for name in files if name.endswith('.SFD')}
    if len(audit)!=46 or {r['path'] for r in audit}!=names:raise ValueError('audited movie inventory mismatch')
    replacements={};receipts=[]
    with args.iso.open('rb') as f:
        for row in audit:
            name=row['path'];lba,size=files[name];f.seek(lba*SECTOR);data=f.read(size)
            if digest(data)!=row['candidate']['sha256']:raise ValueError('audited input movie mismatch '+name)
            if row['original']['sha256']==row['candidate']['sha256']:continue
            fixed,proof=repair_sfd(data);target=args.out/(Path(name).stem+'.SFD')
            target.write_bytes(fixed)
            if target.read_bytes()!=fixed:raise ValueError('output reopen mismatch')
            proof.update(path=name,sfd_path=str(target.resolve()),lba=lba)
            receipts.append(proof);replacements[name]=target
            print(f'MOVIE_REPAIR {Path(name).stem} frames={proof["frames"]} B7=true DTS_backwards=0 video_lossless=true ADX_identical=true',flush=True)
    if len(replacements)!=25:raise ValueError('repair set must match all 25 audited changed movies')
    udf=plan_udf_overlay(args.iso,replacements)
    if udf['extra_sectors'] or any(p['original']!=p['modified'] for p in udf['patches']):
        raise ValueError('same-size repair unexpectedly alters UDF metadata')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    counts=patch_iso(args.iso,args.output,replacements,verbose=False)
    apply_udf_overlay(args.output,udf)
    verification=verify_iso_overlay(args.iso,args.output,replacements,udf_plan=udf)
    if counts!=(25,0):raise ValueError('unexpected movie relocation')
    if file_hash(args.iso)!=args.expected_sha256:raise ValueError('input ISO changed')
    proof=dict(schema=1,baseline_iso=str(args.iso.resolve()),baseline_sha256=args.expected_sha256,
               modified_iso=str(args.output.resolve()),modified_sha256=file_hash(args.output),
               audit_sha256=file_hash(args.audit),changed_movies=25,retained_original_movies=21,
               changed_fields=['video PES PTS/DTS','MPEG sequence_end_code B7','last video PES length/padding'],
               iso_bytes=args.output.stat().st_size,verification=verification,movies=receipts,
               subtitles_preserved=True,gameplay_resources_unchanged=True,iso_udf_metadata_unchanged=True,
               runtime_verified=False)
    p=args.out/'DIFF_FILE.json';p.write_text(json.dumps(proof,indent=2),encoding='utf8')
    if json.loads(p.read_text('utf8'))!=proof:raise ValueError('proof reopen mismatch')
    print('ALL_MOVIES_REPAIRED movies=25 originals_retained=21 nonmovie_bytes_preserved=true sha256='+proof['modified_sha256'],flush=True)


def rollback(args):
    proof=json.loads(args.proof.read_text('utf8'));source=Path(proof['baseline_iso']);modified=Path(proof['modified_iso'])
    if file_hash(source)!=proof['baseline_sha256'] or file_hash(modified)!=proof['modified_sha256']:
        raise ValueError('rollback input version mismatch')
    if args.output.exists() or args.output.resolve() in (source.resolve(),modified.resolve()):
        raise ValueError('rollback must target a new independent copy')
    args.output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(modified,args.output)
    files,_=_portable_metadata(source)
    with source.open('rb') as old,args.output.open('r+b') as new:
        for row in proof['movies']:
            lba,size=files[row['path']]
            if (lba,size)!=(row['lba'],row['bytes']):raise ValueError('rollback geometry mismatch')
            old.seek(lba*SECTOR);data=old.read(size)
            if digest(data)!=row['input_sha256']:raise ValueError('rollback movie fingerprint mismatch')
            new.seek(lba*SECTOR);new.write(data)
    if file_hash(args.output)!=proof['baseline_sha256']:raise ValueError('rollback ISO hash not restored')
    if file_hash(modified)!=proof['modified_sha256']:raise ValueError('modified ISO changed during rollback')
    print('ROLLBACK_PASS baseline_iso_hash_restored=true movies_restored=25 modified_iso_kept=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build')
    for name in ('iso','audit','out','output'):b.add_argument('--'+name,type=Path,required=True)
    b.add_argument('--expected-sha256',required=True)
    r=sub.add_parser('rollback');r.add_argument('--proof',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    args=p.parse_args();build(args) if args.mode=='build' else rollback(args)
