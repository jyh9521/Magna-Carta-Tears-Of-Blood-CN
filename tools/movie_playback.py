"""Lossless playback repair for generated, sectorized MPEG-1 I/P + ADX SFD.

No re-encoding, no source-region/language assumptions, no dependency monkey
patching. Unsupported B/D pictures, header layouts, rates or occupied padding
are rejected rather than silently producing a different stream.
"""
from bisect import bisect_left
from fractions import Fraction
import struct

from audit_movie_playback import (PREFIX, RATES, SECTOR, digest, picture_header,
                                  pes_header, structure, video_info)


def timestamp_bytes(ticks, mark):
    if not isinstance(ticks,int) or not 0 <= ticks < (1 << 33) or mark not in (1,2,3):
        raise ValueError('invalid MPEG timestamp')
    return bytes([(mark << 4) | ((ticks >> 29) & 14) | 1,
                  (ticks >> 22) & 255, ((ticks >> 14) & 254) | 1,
                  (ticks >> 7) & 255, ((ticks << 1) & 254) | 1])


def picture_timeline(video):
    info=video_info(video)
    rates={r['frame_rate_code'] for r in info['sequences']}
    if len(rates)!=1 or next(iter(rates)) not in RATES:
        raise ValueError('changing/unsupported frame rate')
    period=Fraction(90000)/Fraction(RATES[next(iter(rates))])
    positions=[];pos=0;previous=None
    while (pos:=video.find(PREFIX+b'\x00',pos))>=0:
        kind,tr=picture_header(video,pos)
        if kind not in (1,2):
            raise ValueError('B/D pictures require a reordering-aware backend')
        if previous is None:
            if kind!=1 or tr!=0:raise ValueError('timeline must begin with I picture zero')
        elif not ((kind==1 and tr==0) or tr==previous+1):
            raise ValueError('nonsequential I/P temporal reference')
        previous=tr;positions.append(pos);pos+=4
    if not positions:raise ValueError('missing pictures')
    return positions,period


def repair_sfd(data):
    before,video,audio=structure(data)
    if before['issues'] or before['unknown_sectors'] or before['scr_backwards']:
        raise ValueError('unsupported/corrupt input container')
    if set(before['stream_ids'])-{'bb','bf','be','c0','e0'}:
        raise ValueError('unsupported stream inventory')
    if before['video']['sequence_end_offsets']:
        raise ValueError('video already contains sequence end; reject double repair')
    positions,period=picture_timeline(video)
    result=bytearray(data);packets=[];es_offset=0;changed_timestamps=0
    for sector in range(0,len(data),SECTOR):
        if data[sector:sector+4]==PREFIX+b'\xb9':break
        if data[sector:sector+4]!=PREFIX+b'\xba':raise ValueError('non-pack sector')
        pos=sector+12;limit=sector+SECTOR
        while pos+6<=limit and data[pos:pos+3]==PREFIX:
            sid=data[pos+3];n=struct.unpack_from('>H',data,pos+4)[0];end=pos+6+n
            if end>limit:raise ValueError('PES exceeds sector')
            if sid==0xe0:
                payload,_,_=pes_header(data,pos+6,end)
                if payload-(pos+6)!=12:raise ValueError('unsupported video PES header length')
                cursor=pos+6
                while data[cursor]==255:cursor+=1
                std=data[cursor:cursor+2]
                if std[0]&0xc0!=0x40:raise ValueError('missing video STD buffer')
                first=bisect_left(positions,es_offset)
                has_picture=first<len(positions) and positions[first]<es_offset+end-payload
                if has_picture:
                    # I/P stream has identical decode/presentation order. Count
                    # full-ES access units, not sector-local picture fragments.
                    ticks=int(first*period)
                    header=std+timestamp_bytes(ticks,3)+timestamp_bytes(ticks,1)
                else:
                    header=b'\xff'*9+std+b'\x0f'
                if result[pos+6:payload]!=header:changed_timestamps+=1
                result[pos+6:payload]=header
                packets.append(dict(pes=pos,payload=payload,end=end,sector=sector,
                                    es_offset=es_offset,bytes=end-payload,has_picture=has_picture))
                es_offset+=end-payload
            pos=end
    if es_offset!=len(video) or not packets:raise ValueError('video packet inventory mismatch')
    last=packets[-1];end=last['end'];limit=last['sector']+SECTOR
    tail=data[end:limit]
    if len(tail)<10 or tail[:4]!=PREFIX+b'\xbe' or struct.unpack_from('>H',tail,4)[0]!=len(tail)-6:
        raise ValueError('insufficient/unsupported trailing padding for video end')
    n=struct.unpack_from('>H',result,last['pes']+4)[0]
    struct.pack_into('>H',result,last['pes']+4,n+4)
    remaining=len(tail)-4
    result[end:limit]=PREFIX+b'\xb7'+PREFIX+b'\xbe'+struct.pack('>H',remaining-6)+tail[6:6+remaining-6]
    after,new_video,new_audio=structure(bytes(result))
    if after['issues'] or len(result)!=len(data) or new_video!=video+PREFIX+b'\xb7' or new_audio!=audio:
        raise ValueError('lossless payload/structure validation failed')
    if after['video']['pictures']!=len(positions) or after['video']['sequence_end_offsets']!=[len(video)]:
        raise ValueError('picture/end inventory mismatch')
    if after['timing']['e0']['explicit_dts_backwards']:
        raise ValueError('explicit DTS still backwards')
    return bytes(result),dict(schema=1,input_sha256=digest(data),output_sha256=digest(bytes(result)),
                              bytes=len(data),video_before_sha256=digest(video),
                              video_after_sha256=digest(new_video),audio_sha256=digest(audio),
                              video_preserved_except_appended_b7=True,audio_byte_identical=True,
                              frames=len(positions),frame_period_ticks=str(period),
                              timestamp_packets_changed=changed_timestamps,
                              video_sequence_end_added=True,explicit_dts_backwards=0,
                              runtime_verified=False)
