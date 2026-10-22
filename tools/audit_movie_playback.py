"""Compare every original/localized SFD, without claiming game-player acceptance.

Reads version-bound ISO9660/UDF views and audits complete video/audio decoding,
elementary payloads, sector/PES boundaries, SCR/PTS/DTS and MPEG picture headers.
All proprietary intermediate files stay in the explicitly selected output tree.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'lib'), str(ROOT / 'tools')]
from iso import _portable_metadata

SECTOR = 2048
PREFIX = b'\x00\x00\x01'
RATES = {1: '24000/1001', 2: '24', 3: '25', 4: '30000/1001',
         5: '30', 6: '50', 7: '60000/1001', 8: '60'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while block := f.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def timestamp(data):
    if len(data) != 5 or not all(data[i] & 1 for i in (0, 2, 4)):
        raise ValueError('timestamp marker bits/length mismatch')
    return ((data[0] >> 1 & 7) << 30 | data[1] << 22 |
            (data[2] >> 1) << 15 | data[3] << 7 | data[4] >> 1)


def picture_header(data, offset=0):
    if data[offset:offset + 4] != PREFIX + b'\x00' or offset + 6 > len(data):
        raise ValueError('truncated/invalid picture header')
    return ((data[offset + 5] >> 3) & 7,
            (data[offset + 4] << 2) | (data[offset + 5] >> 6))


def video_info(data):
    sequence = []; pictures = []; gops = []; ends = []
    pos = 0
    while (pos := data.find(PREFIX, pos)) >= 0:
        if pos + 4 > len(data):
            break
        code = data[pos + 3]
        if code == 0xb3 and pos + 12 <= len(data):
            sequence.append(dict(offset=pos, width=(data[pos+4] << 4) | (data[pos+5] >> 4),
                                 height=((data[pos+5] & 15) << 8) | data[pos+6],
                                 frame_rate_code=data[pos+7] & 15,
                                 frame_rate=RATES.get(data[pos+7] & 15),
                                 bit_rate_value=(data[pos+8] << 10) | (data[pos+9] << 2) | (data[pos+10] >> 6)))
        elif code == 0x00:
            kind, tr = picture_header(data, pos)
            pictures.append(dict(offset=pos, kind=kind, temporal_reference=tr))
        elif code == 0xb8:
            gops.append(pos)
        elif code == 0xb7:
            ends.append(pos)
        pos += 4
    return dict(bytes=len(data), sha256=digest(data), pictures=len(pictures),
                picture_types={str(k): sum(p['kind'] == k for p in pictures) for k in (1, 2, 3, 4)},
                temporal_reference_max=max((p['temporal_reference'] for p in pictures), default=None),
                pictures_with_temporal_reference_above_3=sum(p['temporal_reference'] > 3 for p in pictures),
                sequences=sequence, gops=len(gops), sequence_end_offsets=ends)


def pes_header(data, start, end):
    cursor = start
    while cursor < end and data[cursor] == 0xff:
        cursor += 1
    if cursor < end and data[cursor] & 0xc0 == 0x40:
        cursor += 2
    pts = dts = None
    if cursor >= end:
        raise ValueError('missing PES header')
    marker = data[cursor] >> 4
    if marker == 2:
        pts = timestamp(data[cursor:cursor+5]); cursor += 5
    elif marker == 3:
        pts = timestamp(data[cursor:cursor+5]); dts = timestamp(data[cursor+5:cursor+10]); cursor += 10
    elif data[cursor] == 0x0f:
        cursor += 1
    else:
        raise ValueError('unsupported PES header')
    if cursor > end:
        raise ValueError('PES header beyond packet')
    return cursor, pts, dts


def structure(data):
    video = bytearray(); audio = bytearray(); packets = []; scrs = []; mux_rates = set()
    issues = []; unknown = []; end_offsets = []; stream_ids = {}; messages = []
    if len(data) % SECTOR:
        issues.append('unaligned_file_size')
    for sector in range(0, len(data), SECTOR):
        limit = min(sector + SECTOR, len(data))
        if data[sector:sector+4] == PREFIX + b'\xb9':
            end_offsets.append(sector)
            if any(b != 0xff for b in data[sector+4:]):
                issues.append('non_ff_bytes_after_program_end')
            break
        if data[sector:sector+4] != PREFIX + b'\xba':
            unknown.append(dict(offset=sector, head=data[sector:sector+16].hex()))
            continue
        try:
            scr = timestamp(data[sector+4:sector+9])
            scrs.append(dict(offset=sector, scr=scr))
            rate = (data[sector+9] & 127) << 15 | data[sector+10] << 7 | data[sector+11] >> 1
            mux_rates.add(rate)
        except ValueError as e:
            issues.append(f'{sector}:{e}'); continue
        pos = sector + 12
        while pos + 6 <= limit and data[pos:pos+3] == PREFIX:
            sid = data[pos+3]; length = struct.unpack_from('>H', data, pos+4)[0]
            end = pos + 6 + length
            stream_ids[f'{sid:02x}'] = stream_ids.get(f'{sid:02x}', 0) + 1
            if end > limit:
                issues.append(f'PES_exceeds_sector:{pos}:{length}'); break
            if 0xc0 <= sid <= 0xef:
                try:
                    payload, pts, dts = pes_header(data, pos+6, end)
                    row = dict(offset=pos, stream_id=sid, pts=pts, dts=dts, scr=scr,
                               elementary_offset=len(video) if sid >= 0xe0 else len(audio), bytes=end-payload)
                    packets.append(row)
                    if sid == 0xe0:
                        video.extend(data[payload:end])
                    elif sid == 0xc0:
                        audio.extend(data[payload:end])
                    else:
                        issues.append(f'unsupported_media_stream:{sid:02x}')
                except ValueError as e:
                    issues.append(f'{pos}:{e}')
            elif sid == 0xbf:
                messages.append(dict(offset=pos, bytes=length, head=data[pos+6:min(end,pos+150)].hex()))
            pos = end
    if len(end_offsets) != 1:
        issues.append('missing_program_end_sector')
    scr_back = [dict(previous=a, next=b) for a,b in zip(scrs,scrs[1:]) if b['scr'] < a['scr']]
    timing = {}
    for sid in (0xc0, 0xe0):
        seq = [p for p in packets if p['stream_id'] == sid]
        values = [p for p in seq if p['dts'] is not None]
        backward = [dict(previous=a,next=b) for a,b in zip(values,values[1:]) if b['dts'] < a['dts']]
        pts = [p['pts'] for p in seq if p['pts'] is not None]
        ahead = [(p['dts'] if p['dts'] is not None else p['pts'])-p['scr'] for p in seq
                 if p['dts'] is not None or p['pts'] is not None]
        timing[f'{sid:02x}'] = dict(packets=len(seq), pts_count=len(pts), explicit_dts_count=len(values),
                                   first_pts=pts[0] if pts else None,last_pts=pts[-1] if pts else None,
                                   max_pts=max(pts) if pts else None, explicit_dts_backwards=backward,
                                   max_timestamp_ahead_of_scr=max(ahead) if ahead else None,
                                   first=seq[0] if seq else None,last=seq[-1] if seq else None)
    adx = None
    if audio:
        if audio[:2] != b'\x80\x00' or len(audio) < 20:
            issues.append('invalid_ADX_header')
        else:
            rate,samples = struct.unpack_from('>II', audio, 8)
            adx = dict(channels=audio[7],sample_rate=rate,samples=samples,
                       duration=samples/rate if rate else None,block_bytes=audio[5])
    result = dict(bytes=len(data),sha256=digest(data),issues=issues,unknown_sectors=unknown,
                  program_end_offsets=end_offsets,stream_ids=stream_ids,sofdec_messages=messages,
                  scr_first=scrs[0] if scrs else None,scr_last=scrs[-1] if scrs else None,
                  scr_backwards=scr_back,mux_rates=sorted(mux_rates),timing=timing,
                  video=video_info(bytes(video)),audio=dict(bytes=len(audio),sha256=digest(bytes(audio)),adx=adx))
    return result, bytes(video), bytes(audio)


def framehash_summary(data):
    rows = {}; metadata = []
    for line in data.decode('utf8', 'replace').splitlines():
        if line.startswith('#'):
            metadata.append(line); continue
        if not line.strip():
            continue
        fields = [p.strip() for p in line.split(',')]
        if len(fields) != 6:
            raise ValueError('invalid framehash row')
        stream,dts,pts,duration,size = map(int, fields[:5])
        rows.setdefault(stream, []).append((dts,pts,duration,size,fields[5]))
    result = {}
    for sid, seq in rows.items():
        result[str(sid)] = dict(frames=len(seq),first=list(seq[0]),last=list(seq[-1]),
                               pts_backwards=sum(b[1]<a[1] for a,b in zip(seq,seq[1:])),
                               image_or_pcm_hash=digest('\n'.join(x[4] for x in seq).encode()))
    return dict(metadata=metadata,streams=result)


def examine(iso, extent, directory, decoder, probe):
    lba,size = extent
    with iso.open('rb') as f:
        f.seek(lba*SECTOR); data=f.read(size)
    if len(data) != size:
        raise ValueError('truncated ISO extent')
    result, video, audio = structure(data)
    # This is a diagnostic of the installed dependency, not the parsing oracle.
    from sfd_muxer.container import _parse_picture
    pos = 0; reader_errors = 0; actual_pictures = 0
    while (pos := video.find(PREFIX + b'\x00', pos)) >= 0:
        actual_pictures += 1
        reader_errors += _parse_picture(video, pos) != picture_header(video, pos)
        pos += 4
    result['muxer_temporal_reference_audit'] = dict(actual_pictures=actual_pictures,
                                                  installed_reader_incorrect=reader_errors)
    directory.mkdir(parents=True)
    path = directory/'input.SFD'; path.write_bytes(data)
    cmd = [str(probe),'-v','error','-select_streams','v:0','-show_streams','-show_packets',
           '-show_entries','packet=pts,dts,pts_time,dts_time,pos,size:stream','-of','json',str(path)]
    p = subprocess.run(cmd,capture_output=True,timeout=300)
    (directory/'probe.json').write_bytes(p.stdout); (directory/'probe.stderr.txt').write_bytes(p.stderr)
    probe_data=json.loads(p.stdout)
    seq=probe_data.get('packets',[])
    values=[x for x in seq if 'dts' in x]
    backwards=[dict(previous=a,next=b) for a,b in zip(values,values[1:]) if int(b['dts'])<int(a['dts'])]
    result['probe']=dict(command=cmd,exit=p.returncode,stderr=p.stderr.decode('utf8','replace'),
                         streams=probe_data.get('streams',[]),packets=len(seq),
                         dts_backwards=backwards,first=seq[0] if seq else None,last=seq[-1] if seq else None)
    cmd=[str(decoder),'-v','error','-nostdin','-threads','2','-i',str(path),
         '-map','0:v:0','-map','0:a?','-fps_mode','passthrough','-f','framehash','-hash','sha256','-']
    p=subprocess.run(cmd,capture_output=True,timeout=600)
    (directory/'decoded.framehash').write_bytes(p.stdout);(directory/'decode.stderr.txt').write_bytes(p.stderr)
    result['decode']=dict(command=cmd,exit=p.returncode,stderr=p.stderr.decode('utf8','replace'),
                          **framehash_summary(p.stdout))
    # Probe and decoder are independent checks of the sector parser's picture inventory.
    result['picture_count_agrees']=result['video']['pictures']==result['probe']['packets']==result['decode']['streams'].get('0',{}).get('frames')
    path.unlink()  # raw ISO payload is reproducible; retain evidence, not redundant movies
    return result


def compare(original, candidate):
    findings=[]
    if candidate['sha256']==original['sha256']:
        return ['original_bytes_retained']
    if candidate['audio']['sha256']!=original['audio']['sha256']:
        findings.append('audio_payload_changed')
    if not candidate['picture_count_agrees']:
        findings.append('picture_inventory_mismatch')
    if candidate['video']['pictures']!=original['video']['pictures']:
        findings.append('video_frame_count_changed')
    if candidate['decode']['exit']!=0:
        findings.append('full_decode_failed')
    if candidate['decode']['stderr']:
        findings.append('full_decode_stderr')
    if candidate['probe']['dts_backwards']:
        findings.append('demuxed_video_dts_backwards')
    if candidate['timing']['e0']['explicit_dts_backwards']:
        findings.append('explicit_video_dts_backwards')
    if candidate['issues']:
        findings.append('container_structure_issue')
    if candidate['mux_rates']!=original['mux_rates']:
        findings.append('mux_rate_changed')
    if candidate['video']['sequence_end_offsets'] != original['video']['sequence_end_offsets']:
        # Positions naturally change when re-encoding: report presence, not position, as a finding.
        if bool(candidate['video']['sequence_end_offsets']) != bool(original['video']['sequence_end_offsets']):
            findings.append('sequence_end_presence_changed')
    return findings


def audit(args):
    args.out.mkdir(parents=True,exist_ok=True)
    if any(args.out.iterdir()):
        raise ValueError('output directory must be empty')
    if file_hash(args.original)!=args.original_sha256 or file_hash(args.candidate)!=args.candidate_sha256:
        raise ValueError('ISO input hash mismatch')
    old,_=_portable_metadata(args.original);new,_=_portable_metadata(args.candidate)
    names=sorted(name for name in old if name.endswith('.SFD'))
    if len(names)!=args.expected_movies or set(names)!=set(name for name in new if name.endswith('.SFD')):
        raise ValueError('movie inventory mismatch')
    # Verify complete SFD contents agree in both filesystem views before playback checks.
    import pycdlib
    view_records=[]
    for label,iso,extents in [('original',args.original,old),('candidate',args.candidate,new)]:
        cd=pycdlib.PyCdlib();cd.open(str(iso))
        try:
            udf_paths={}
            if cd.has_udf():
                for parent,_,children in cd.walk(udf_path='/'):
                    for child in children:
                        path=parent.rstrip('/')+'/'+child
                        if path.upper() in udf_paths:raise ValueError('ambiguous UDF path')
                        udf_paths[path.upper()]=path
            for name in names:
                with iso.open('rb') as f:
                    lba,size=extents[name];f.seek(lba*SECTOR);h=digest(f.read(size))
                if cd.has_udf():
                    import io
                    b=io.BytesIO();cd.get_file_from_iso_fp(b,udf_path=udf_paths[name.upper()])
                    if digest(b.getvalue())!=h:
                        raise ValueError('ISO9660/UDF movie mismatch:'+name)
                view_records.append(dict(label=label,path=name,sha256=h,udf_verified=cd.has_udf()))
        finally:cd.close()
    (args.out/'filesystem-views.json').write_text(json.dumps(view_records,indent=2),encoding='utf8')
    def one(name):
        stem=Path(name).stem
        before=examine(args.original,old[name],args.out/stem/'original',args.decoder,args.probe)
        after=examine(args.candidate,new[name],args.out/stem/'candidate',args.decoder,args.probe)
        row=dict(path=name,original=before,candidate=after,findings=compare(before,after),runtime_verified=False)
        p=args.out/stem/'comparison.json';p.write_text(json.dumps(row,indent=2),encoding='utf8')
        if json.loads(p.read_text('utf8'))!=row:raise ValueError('comparison reopen mismatch')
        print(f'MOVIE_AUDIT {stem} changed={before["sha256"]!=after["sha256"]} findings={",".join(row["findings"])}',flush=True)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows=list(pool.map(one,names))
    counts={}
    for row in rows:
        for finding in row['findings']:counts[finding]=counts.get(finding,0)+1
    summary=dict(schema=1,original_iso=str(args.original.resolve()),candidate_iso=str(args.candidate.resolve()),
                 original_sha256=args.original_sha256,candidate_sha256=args.candidate_sha256,
                 movies=len(rows),changed=sum(r['original']['sha256']!=r['candidate']['sha256'] for r in rows),
                 original_frames=sum(r['original']['decode']['streams']['0']['frames'] for r in rows),
                 candidate_frames=sum(r['candidate']['decode']['streams']['0']['frames'] for r in rows),
                 full_decode_exit_zero=sum(r[k]['decode']['exit']==0 for r in rows for k in ('original','candidate')),
                 audio_payload_byte_identical=sum(r['original']['audio']['sha256']==r['candidate']['audio']['sha256'] for r in rows),
                 audio_pcm_decode_identical=sum(r['original']['decode']['streams'].get('1')==r['candidate']['decode']['streams'].get('1') for r in rows),
                 audio_pcm_content_hash_identical=sum(r['original']['decode']['streams'].get('1',{}).get('image_or_pcm_hash')==r['candidate']['decode']['streams'].get('1',{}).get('image_or_pcm_hash') for r in rows),
                 decoder_stderr_nonempty=sum(bool(r[k]['decode']['stderr']) for r in rows for k in ('original','candidate')),
                 container_issues=sum(bool(r[k]['issues']) for r in rows for k in ('original','candidate')),
                 unknown_sectors=sum(len(r[k]['unknown_sectors']) for r in rows for k in ('original','candidate')),
                 candidate_wrong_temporal_reference_readings=sum(r['candidate']['muxer_temporal_reference_audit']['installed_reader_incorrect'] for r in rows if r['original']['sha256']!=r['candidate']['sha256']),
                 findings=counts,runtime_verified=False,visual_subtitle_review=False,
                 decoder_version=subprocess.check_output([str(args.decoder),'-version']).decode('utf8','replace').splitlines()[0])
    import importlib.metadata
    import sfd_muxer.container
    summary['installed_muxer']=dict(version=importlib.metadata.version('sfd-muxer'),
                                    container_sha256=file_hash(sfd_muxer.container.__file__))
    if file_hash(args.original)!=args.original_sha256 or file_hash(args.candidate)!=args.candidate_sha256:
        raise ValueError('ISO changed during audit')
    for name,data in [('movies.json',rows),('summary.json',summary)]:
        p=args.out/name;p.write_text(json.dumps(data,indent=2),encoding='utf8')
        if json.loads(p.read_text('utf8'))!=data:raise ValueError('report reopen mismatch')
    print('ALL_MOVIES_AUDITED '+json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','candidate','decoder','probe','out'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('original-sha256','candidate-sha256'):p.add_argument('--'+name,required=True)
    p.add_argument('--expected-movies',type=int,default=46);p.add_argument('--jobs',type=int,choices=(1,2),default=2)
    audit(p.parse_args())
