"""Read ordinary package P8 texture mips; export ignored visual audit images.

Only the observed palette-linked, one-byte-per-pixel layout is accepted.
Streamed packages, compressed texture formats and runtime use remain separate.
"""
from __future__ import annotations
import argparse,json,struct,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from PIL import Image,ImageDraw
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import Reader,ordinary_exports,property_block
from extract_script_buffers import FILE_HASH


def palette(serial,start):
    r=Reader(serial,start);count=r.index()
    core.require(count==256,'unsupported palette count')
    raw=r.take(count*4)
    core.require(r.pos==len(serial),'palette trailing bytes')
    return raw


def mips(serial,start,absolute_offset):
    r=Reader(serial,start);count=r.index()
    core.require(1<=count<=16,'unsupported mip count')
    rows=[]
    for i in range(count):
        lazy=r.integer('I');size=r.index()
        core.require(size>0,'empty/negative mip')
        offset=r.pos;raw=r.take(size)
        core.require(lazy==absolute_offset+r.pos,'lazy mip end mismatch')
        width=r.integer('I');height=r.integer('I');ub=r.integer('B');vb=r.integer('B')
        core.require(ub<=12 and vb<=12 and width==1<<ub and height==1<<vb,'mip dimensions mismatch')
        core.require(size==width*height,'unsupported non-P8 mip size')
        if rows:core.require(width==max(1,rows[-1]['width']//2) and height==max(1,rows[-1]['height']//2),'mip progression mismatch')
        rows.append(dict(index=i,offset=offset,size=size,sha256=core.digest(raw),
                         width=width,height=height,u_bits=ub,v_bits=vb,lazy_end=lazy,raw=raw))
    core.require(r.pos==len(serial),'texture trailing bytes')
    return rows


def property_value(serial,props,name,kind):
    rows=[p for p in props if p['name']==name and p['array_index']==0]
    core.require(len(rows)==1 and rows[0]['type']==kind,'required texture property mismatch: '+name)
    p=rows[0];return serial[p['value_offset']:p['value_offset']+p['value_bytes']]


def image_view(raw,width,height,colors):
    core.require(len(raw)==width*height and len(colors)==1024,'image view geometry')
    # Preserve every palette byte in the audit; BGRA display is an interpretation.
    im=Image.frombytes('P',(width,height),raw)
    im.putpalette(bytes(c for i in range(256) for c in (colors[i*4+2],colors[i*4+1],colors[i*4])))
    return im.convert('RGB')


def audit(path,out):
    core.require(core.file_digest(path)==FILE_HASH,'FILE identity mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output directory not empty')
    a=Afs.open(path);names=filename_toc(a);rows=[];palette_rows=[];counts=Counter();views=[]
    with path.open('rb') as stream:
        for ix,name in enumerate(names):
            blob=a.read_entry(ix,stream)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            t=package_tables(blob);exports=ordinary_exports(blob,t);by_index={e['index']:e for e in exports}
            colors={}
            for e in exports:
                if e['class']!='Palette':continue
                serial=blob[e['offset']:e['offset']+e['size']];body=property_block(serial,t['names'],e['flags'])
                raw=palette(serial,body['end']);colors[e['index']]=raw
                palette_rows.append(dict(id=f'FILE/{name}/export/{e["index"]}',serial_sha256=core.digest(serial),
                    colors_sha256=core.digest(raw),colors_bytes=len(raw),colors_count=256))
            for e in exports:
                if e['class']!='Texture':continue
                serial=blob[e['offset']:e['offset']+e['size']];body=property_block(serial,t['names'],e['flags']);props=body['properties']
                ref=Reader(property_value(serial,props,'Palette',5));pal=ref.index()
                core.require(ref.pos==len(ref.data) and pal in colors,'palette reference mismatch')
                parsed=mips(serial,body['end'],e['offset']);first=parsed[0]
                for prop,wanted in [('USize',first['width']),('VSize',first['height'])]:
                    core.require(struct.unpack('<I',property_value(serial,props,prop,2))[0]==wanted,'base texture dimensions disagreement')
                for prop,wanted in [('UBits',first['u_bits']),('VBits',first['v_bits'])]:
                    core.require(property_value(serial,props,prop,1)==bytes([wanted]),'base texture bits disagreement')
                filename=f'{Path(name).stem}-{e["index"]:05d}.png'
                im=image_view(first['raw'],first['width'],first['height'],colors[pal]);im.save(out/filename)
                with Image.open(out/filename) as reopened:core.require(reopened.size==im.size,'PNG reopen geometry')
                views.append((f'{name} / {e["index"]} / {e["name"]}',im))
                rows.append(dict(id=f'FILE/{name}/export/{e["index"]}',name=e['name'],outer=e['outer'],
                    outer_name=by_index[e['outer']]['name'] if e['outer'] in by_index else None,
                    package_sha256=core.digest(blob),serial_sha256=core.digest(serial),property_end=body['end'],
                    palette_export=pal,palette_sha256=core.digest(colors[pal]),
                    mips=[{k:v for k,v in m.items() if k!='raw'} for m in parsed],
                    image=filename,image_sha256=core.file_digest(out/filename),
                    channel_view='BGRA interpreted as RGB; alpha omitted for inspection',
                    editable=False,runtime_visibility_verified=False))
                counts[name]+=1
    sheets=[]
    for start in range(0,len(views),8):
        sheet=Image.new('RGB',(1080,600),(45,45,45));draw=ImageDraw.Draw(sheet)
        for j,(label,im) in enumerate(views[start:start+8]):
            x=j%4*270;y=j//4*300;draw.text((x+4,y+4),label,fill='white')
            view=im.copy();view.thumbnail((256,256));sheet.paste(view,(x+4,y+28))
        filename=f'sheet-{start//8+1:02d}.png';sheet.save(out/filename)
        sheets.append(dict(image=filename,sha256=core.file_digest(out/filename),first=start,count=min(8,len(views)-start)))
    core.require(core.file_digest(path)==FILE_HASH,'FILE changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,textures=len(rows),palettes=len(palette_rows),
        mip_levels=sum(len(x['mips']) for x in rows),packages=dict(counts),contact_sheets=len(sheets),
        all_native_tails_closed=True,visual_review_complete=False,streamed_textures_audited=False,
        complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    for name,value in [('textures.json',rows),('palettes.json',palette_rows),('sheets.json',sheets),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
if __name__=='__main__':main()
