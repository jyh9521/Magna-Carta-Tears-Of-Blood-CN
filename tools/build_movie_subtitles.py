"""Render source-bound translated ASS, then rebuild only explicitly selected SFDs.

Translation review does not assert full film transcription or playback acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
import font_poc as core


def centiseconds(value):
    match = re.fullmatch(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', value)
    core.require(match is not None, 'invalid ASS timestamp')
    h,m,s,c = map(int, match.groups())
    core.require(m < 60 and s < 60, 'invalid ASS time component')
    return ((h*60+m)*60+s)*100+c


def stamp(value):
    core.require(type(value) is int and value >= 0, 'invalid centiseconds')
    h,rem = divmod(value,360000); m,rem=divmod(rem,6000);s,c=divmod(rem,100)
    return f'{h}:{m:02}:{s:02}.{c:02}'


def reference_events(text):
    result=[]
    for line in text.splitlines():
        if not line.startswith('Dialogue:'): continue
        cells=line.split(',',9)
        core.require(len(cells)==10, 'invalid ASS event')
        start,end=centiseconds(cells[1]),centiseconds(cells[2])
        core.require(start<end, 'nonpositive ASS event')
        result.append(dict(start=start,end=end,original=cells[9],drawing=bool(re.search(r'\\p[1-9]',cells[9]))))
    return result


def translated_events(reference, targets):
    core.require(len(reference)==len(targets), 'translation/reference event count mismatch')
    groups=[]
    for index,(row,target) in enumerate(zip(reference,targets)):
        core.require(target is None or isinstance(target,str), 'invalid movie target')
        if target is None:
            core.require(row['drawing'], 'null target for non-drawing event')
            continue
        core.require(not any(ch in target for ch in '{}\\\n\r\x00'), 'ASS control injection in translation')
        if not target.strip(): continue
        # Multi-line reference events differ by one centisecond in a few files.
        same=next((g for g in groups if abs(g['start']-row['start'])<=2 and abs(g['end']-row['end'])<=2),None)
        if same is None:
            groups.append(dict(start=row['start'],end=row['end'],parts=[target],source_indices=[index]))
        else:
            same['start']=min(same['start'],row['start']);same['end']=max(same['end'],row['end'])
            same['parts'].append(target);same['source_indices'].append(index)
    groups.sort(key=lambda g:(g['start'],g['end']))
    merged=[]
    for group in groups:
        group['target']=''.join(group.pop('parts'))
        if merged and group['target']==merged[-1]['target'] and 0<=group['start']-merged[-1]['end']<=2:
            merged[-1]['end']=group['end'];merged[-1]['source_indices']+=group['source_indices']
        else: merged.append(group)
    return merged


def wrap_pixels(text, font, width, max_lines=3, protected=()):
    core.require(text and width>0, 'empty text or invalid width')
    atoms=sorted(set(t for t in protected if t),key=lambda t:(-len(t),t))
    pattern='|'.join(re.escape(t) for t in atoms)
    tokens=re.findall('(?:'+pattern+')|.' if atoms else '.',text)
    # Bind punctuation to the preceding lexical atom before measuring. This
    # handles runs of punctuation, not just a single overflowing mark.
    grouped=[]
    for token in tokens:
        if unicodedata.category(token[0]).startswith('P') or token.isspace():
            core.require(bool(grouped),'subtitle starts with punctuation')
            grouped[-1]+=token
        else:grouped.append(token)
    tokens=grouped
    lines=[[]]
    for char in tokens:
        core.require(font.getlength(char)<=width,'glyph exceeds line width')
        if font.getlength(''.join(lines[-1])+char)>width and lines[-1]:
            lines.append([char])
        else:lines[-1].append(char)
    lines=[''.join(line) for line in lines]
    core.require(len(lines)<=max_lines, 'movie subtitle line count overflow')
    core.require(all(font.getlength(line)<=width for line in lines),'movie subtitle pixel overflow')
    core.require(all(not unicodedata.category(line[0]).startswith('P') for line in lines),'punctuation at subtitle line start')
    return lines


def wrap_units(units, font, width):
    """Wrap reviewed lexical/phrase atoms, never subdividing an atom."""
    core.require(isinstance(units,list) and bool(units),'empty reviewed phrase units')
    lines=[];line=''
    for unit in units:
        core.require(isinstance(unit,str) and bool(unit.strip()),'empty reviewed phrase')
        core.require(not any(c in unit for c in '{}\\\n\r\x00'),'ASS control in reviewed phrase')
        core.require(not unicodedata.category(unit[0]).startswith('P'),'reviewed phrase starts with punctuation')
        core.require(font.getlength(unit)<=width,'reviewed phrase exceeds line width')
        if line and font.getlength(line+unit)>width:
            lines.append(line);line=''
        line+=unit
    if line:lines.append(line)
    return lines


def render_ass(events, font_path, width, height, *, mask=False, story_panel=False, bottom_ratio=0.70, safe_region=None, font_size=None, pixel_font_size=False, semantic_pages=None):
    from PIL import ImageFont
    core.require(width>=320 and height>=240,'unsupported video geometry')
    core.require(not mask, 'opaque subtitle masks are not supported')
    size=font_size or (20 if width>=600 else 18)
    core.require(type(size) is int and 12<=size<=36,'unsupported subtitle font size')
    font=ImageFont.truetype(str(font_path),size)
    family=font.getname()[0]
    # ASS normalizes size to ascent + descent, unlike Pillow's EM pixels.
    # Calibrate the style to the same pixel measure used by wrapping; position
    # rows separately so the font's unusually tall metrics do not waste space.
    core.require(type(pixel_font_size) is bool,'invalid pixel font size mode')
    ass_size=sum(font.getmetrics()) if pixel_font_size else size
    core.require(isinstance(bottom_ratio,(int,float)) and 0.60<=bottom_ratio<=0.92,'unsupported subtitle position')
    region=safe_region or [24,round(height*(bottom_ratio-0.34)),width-24,round(height*bottom_ratio)]
    core.require(len(region)==4 and all(isinstance(x,(int,float)) for x in region),'invalid subtitle rectangle')
    x1,y1,x2,y2=region
    core.require(0<=x1<x2<=width and 0<=y1<y2<=height,'subtitle rectangle out of bounds')
    usable=x2-x1-8;bottom=round(y2-4);center=round((x1+x2)/2)
    capacity=int((y2-y1-8)//(size+4))
    core.require(capacity>=1,'subtitle rectangle has no line capacity')
    if semantic_pages is not None:
        core.require(len(semantic_pages)==len(events),'semantic review/event count mismatch')
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Text,{family},{ass_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&HFF000000,0,0,0,0,100,100,0,0,1,1.5,0,2,24,24,12,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    output=[header]; report=[]
    for row_index,row in enumerate(events):
        core.require(not any(unicodedata.category(c)=='Pd' for c in row['target']),'dash in subtitle target')
        from validate_translation_batch import glossary_terms
        protected=[target for _,target in glossary_terms(ROOT/'GLOSSARY.md')]
        if semantic_pages is None:
            lines=wrap_pixels(row['target'],font,usable,max_lines=100,protected=protected)
            pages=[lines[i:i+capacity] for i in range(0,len(lines),capacity)]
        else:
            reviewed=semantic_pages[row_index]
            core.require(reviewed['target']==row['target'],'semantic review target mismatch')
            units=reviewed['page_units']
            core.require(isinstance(units,list) and bool(units),'empty semantic pages')
            core.require(''.join(u for page in units for u in page)==row['target'],'semantic pages alter target')
            pages=[wrap_units(page,font,usable) for page in units]
            core.require(all(len(page)<=capacity for page in pages),'reviewed semantic page exceeds safe height')
            lines=[line for page in pages for line in page]
            # A reviewed boundary must not split a canonical name/term.
            boundaries=[];offset=0
            for page in pages:
                for line in page:
                    offset+=len(line);boundaries.append(offset)
            for term in protected:
                for match in re.finditer(re.escape(term),row['target']):
                    core.require(not any(match.start()<p<match.end() for p in boundaries),'semantic break splits glossary term')
        total=sum(len(line) for line in lines); consumed=0
        duration=row['end']-row['start']; previous=row['start']
        for index,page in enumerate(pages):
            consumed+=sum(len(line) for line in page)
            end=row['end'] if index==len(pages)-1 else row['start']+round(duration*consumed/total)
            core.require(previous<end,'subtitle pagination interval too short')
            position=f'{{\\an2\\pos({center},{bottom})}}'
            if pixel_font_size:
                for line_index,line in enumerate(page):
                    line_bottom=bottom-(len(page)-1-line_index)*(size+4)
                    line_pos=f'{{\\an2\\pos({center},{line_bottom})}}'
                    output.append(f'Dialogue: 1,{stamp(previous)},{stamp(end)},Text,,0,0,0,,'+line_pos+line+'\n')
            else:
                output.append(f'Dialogue: 1,{stamp(previous)},{stamp(end)},Text,,0,0,0,,'+position+r'\N'.join(page)+'\n')
            part=dict(row,start=previous,end=end,target=''.join(page))
            report.append(dict(**part,source_target=row['target'],page_index=index,page_count=len(pages),lines=page,
                               pixel_widths=[round(font.getlength(x),3) for x in page],opaque_background=False,
                               position=[center,bottom],font_size=size,ass_font_size=ass_size,pixel_font_size=pixel_font_size,safe_region=region,
                               geometry_line_capacity=capacity,fixed_line_limit=None,semantic_reviewed=semantic_pages is not None,
                               phrase_units=semantic_pages[row_index]['page_units'][index] if semantic_pages is not None else None))
            previous=end
    return ''.join(output),report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--locale',type=Path,required=True);p.add_argument('--font',type=Path,required=True)
    p.add_argument('--probes',type=Path,required=True);p.add_argument('--decoded',type=Path,required=True)
    p.add_argument('--iso',type=Path);p.add_argument('--executable',type=Path);p.add_argument('--build',action='store_true')
    p.add_argument('--only',action='append');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--story',action='store_true',help='Read explicitly paginated native-picture translations instead of reference ASS')
    a=p.parse_args();out=core.output_directory(a.out)
    locale=json.loads(a.locale.read_text('utf8')); profile=json.loads((ROOT/'profiles/scka-20043.json').read_text('utf8'))
    review=json.loads((a.locale.parent/locale['layout_review']).read_text('utf8')) if locale.get('layout_review') else None
    expected=locale['font_sha256']
    core.require(core.file_digest(a.font)==expected,'subtitle font fingerprint mismatch')
    probes={Path(x['path'].split(';')[0]).stem:x for x in json.loads(a.probes.read_text('utf8'))}
    decoded={Path(x['path'].split(';')[0]).stem:x for x in json.loads(a.decoded.read_text('utf8'))}
    names=a.only or list(locale['movies']);core.require(set(names)<=set(locale['movies']),'unknown selected movie')
    scope=json.loads((a.locale.parent/locale['review_scope']).read_text('utf8'))
    core.require(not set(scope['subtitle_required']) & set(scope['no_subtitles']),'conflicting movie decisions')
    core.require(set(names)<=set(scope['subtitle_required']),'movie excluded by reviewed scope')
    receipts=[]
    for name in names:
        if a.story:
            core.require(probes[name]['source_sha256']==locale['source_sha256'][name],'story source fingerprint mismatch')
            events=[dict(start=round(r['start']*100),end=round(r['end']*100),target=r['target'],source_indices=[i])
                    for i,r in enumerate(locale['movies'][name])]
            core.require(all(e['start']>=0 and e['end']>e['start'] for e in events),'invalid story interval')
            core.require(all(events[i]['end']<=events[i+1]['start'] for i in range(len(events)-1)),'story intervals overlap')
            core.require(all(not any(c in e['target'] for c in '{}\\\n\r\x00') for e in events),'story ASS control injection')
            reference_hash=core.file_digest(a.locale)
        else:
            ref=ROOT/locale['reference']/(name+'.ass')
            core.require(core.file_digest(ref)==locale['reference_sha256'][name], 'subtitle reference fingerprint mismatch')
            events=translated_events(reference_events(ref.read_text('utf-8-sig')),locale['movies'][name])
            reference_hash=locale['reference_sha256'][name]
        video=next(s for s in probes[name]['metadata']['streams'] if s['codec_type']=='video')
        core.require(all(e['end']/100<=decoded[name]['timeline_seconds']+.1 for e in events),'cue outside original video')
        layout=locale.get('movie_layout',{}).get(name,{})
        ratio=layout.get('position_ratio',locale.get('subtitle_position_ratio',0.70))
        region=layout.get('safe_region')
        ass,report=render_ass(events,a.font,video['width'],video['height'],story_panel=a.story,bottom_ratio=ratio,
                              safe_region=region,font_size=layout.get('font_size'),pixel_font_size=layout.get('pixel_font_size',False),
                              semantic_pages=review['movies'][name] if review is not None and region is not None else None)
        (out/(name+'.ass')).write_text(ass,'utf8',newline='\n')
        receipts.append(dict(movie=name,reference_sha256=reference_hash,ass_sha256=core.file_digest(out/(name+'.ass')),story_panel=a.story,
                             original_sfd_sha256=probes[name]['source_sha256'],events=report,layout_static_pass=True,
                             original_subtitle_band_masked=False,opaque_background=False,runtime_verified=False))
    (out/'subtitles.json').write_text(json.dumps(dict(schema=1,locale=locale['locale'],font_sha256=expected,movies=receipts,
                            full_movie_coverage=False,timing_verified=False),ensure_ascii=False,indent=2)+'\n','utf8')
    print(f'SUBTITLE RENDER PASS movies={len(receipts)} cues={sum(len(x["events"]) for x in receipts)} font_verified=true pixel_overflow=0',flush=True)
    if a.build:
        core.require(a.iso is not None and a.executable is not None,'build requires ISO and FFmpeg')
        core.require(core.file_digest(a.iso)==profile['expected_iso_sha256'],'original ISO fingerprint mismatch')
        import pycdlib
        from sfd_muxer import SFD, SofdecMuxer
        import shutil
        cd=pycdlib.PyCdlib();cd.open(str(a.iso.resolve()))
        try:
            for receipt in receipts:
                name=receipt['movie'];wd=out/name;wd.mkdir();src=wd/'original.SFD'
                cd.get_file_from_iso(local_path=str(src),iso_path=probes[name]['path'])
                core.require(core.file_digest(src)==receipt['original_sfd_sha256'],'original SFD fingerprint mismatch')
                original=SFD.from_file(src);m1v=wd/'original.m1v';sfa=wd/'original.adx'
                m1v.write_bytes(original.extract_video());audio=original.extract_audio();sfa.write_bytes(audio)
                (wd/'fonts').mkdir();shutil.copyfile(a.font,wd/'fonts/font.otf');shutil.copyfile(out/(name+'.ass'),wd/'subtitle.ass')
                output=wd/'subbed.m1v'
                cmd=[str(a.executable.resolve()),'-nostdin','-y','-hide_banner','-loglevel','warning','-i','original.m1v',
                     '-vf','ass=subtitle.ass:fontsdir=fonts','-c:v','mpeg1video','-bf','0','-b:v','5500k','-minrate','5500k','-maxrate','5500k',
                     '-bufsize','1800k','-r','30000/1001',str(output.name)]
                result=subprocess.run(cmd,cwd=wd,capture_output=True)
                (wd/'encode.log').write_bytes(result.stderr);core.require(result.returncode==0,'subtitle encode failed')
                candidate=wd/(name+'.SFD');SofdecMuxer(output,sfa).write(candidate)
                from movie_playback import repair_sfd
                playback_bytes,playback_proof=repair_sfd(candidate.read_bytes())
                candidate.write_bytes(playback_bytes)
                core.require(SFD.from_file(candidate).extract_audio()==audio,'original ADX changed')
                # Framehash output avoids the null muxer's timestamp rescaling.
                # Still retain the log and require a full, exact frame count.
                check=[str(a.executable.resolve()),'-v','error','-nostdin','-i',str(candidate.resolve()),'-map','0:v:0','-an',
                       '-fps_mode','passthrough','-f','framehash','-hash','sha256','-']
                verified=subprocess.run(check,capture_output=True)
                (wd/'decode-framehash.txt').write_bytes(verified.stdout);(wd/'decode.log').write_bytes(verified.stderr)
                frames=sum(bool(line) and not line.startswith(b'#') for line in verified.stdout.splitlines())
                from audit_movie_ocr import decoder_outcome
                outcome=decoder_outcome(verified.returncode,verified.stderr.decode('utf8'),frames,decoded[name]['frames'])
                core.require(outcome['complete'],'rebuilt SFD full decode failed or frame count changed')
                receipt.update(candidate=str(candidate.resolve()),candidate_sha256=core.file_digest(candidate),adx_sha256=core.digest(audio),
                               adx_byte_identical=True,full_decode_exit=verified.returncode,encode_command=cmd,decoded_frames=frames,
                               decoder_outcome=outcome,playback_repair=playback_proof,container_timing_verified=False)
                (out/'build-progress.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n','utf8')
                print(f'SUBTITLE SFD PASS movie={name} adx_identical=true full_decode_exit=0',flush=True)
        finally:cd.close()
        core.require(core.file_digest(a.iso)==profile['expected_iso_sha256'],'original ISO changed')


if __name__=='__main__':main()
