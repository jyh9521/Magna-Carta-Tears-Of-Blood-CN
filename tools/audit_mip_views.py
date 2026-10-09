"""Hash-bound visual inventory of all smaller ordinary-package P8 mip levels."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from PIL import Image,ImageDraw
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_texture_mips import palette,mips,image_view,property_value,native_class_name
from audit_object_properties import Reader,property_block,ordinary_exports
from research_inventory import package_tables
from extract_script_buffers import FILE_HASH


def sheets(views,out):
    result=[]
    for first in range(0,len(views),24):
        sheet=Image.new('RGB',(1080,680),(45,45,45));draw=ImageDraw.Draw(sheet)
        for index,(identity,im) in enumerate(views[first:first+24]):
            core.require(im.width<=128 and im.height<=128,'native sheet size limit')
            x=index%6*180;y=index//6*170
            draw.text((x+3,y+3),identity,fill='white');sheet.paste(im,(x+3,y+34))
        name=f'smaller-mips-{first//24+1:02d}.png';sheet.save(out/name)
        with Image.open(out/name) as check:core.require(check.size==sheet.size,'sheet reopen geometry')
        result.append(dict(image=name,sha256=core.file_digest(out/name),first=first,count=min(24,len(views)-first),resized=False))
    return result


def audit(archive,manifest,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    mh=core.file_digest(manifest);textures=json.loads(manifest.read_text('utf8'))
    core.require(isinstance(textures,list) and len({r['id'] for r in textures})==len(textures),'texture inventory duplicate')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    afs=Afs.open(archive);names=filename_toc(afs);rows=[];views=[]
    with archive.open('rb') as stream:
        for texture in textures:
            parts=texture['id'].split('/');core.require(len(parts)==4 and parts[0]=='FILE' and parts[2]=='export','texture identity')
            blob=afs.read_entry(names.index(parts[1]),stream)
            core.require(core.digest(blob)==texture['package_sha256'],'texture package hash')
            serial_start=texture['mips'][0]['lazy_end']-texture['mips'][0]['offset']-texture['mips'][0]['size']
            # lazy_end is the absolute end of pixels, not the complete mip record.
            tables=package_tables(blob);exports=ordinary_exports(blob,tables);export=exports[int(parts[3])-1]
            core.require(export['index']==int(parts[3]) and native_class_name(export,exports)=='Texture' and export['offset']==serial_start,'texture export coordinate')
            serial=blob[export['offset']:export['offset']+export['size']]
            core.require(core.digest(serial)==texture['serial_sha256'],'texture serial hash')
            body=property_block(serial,tables['names']);ref=Reader(property_value(serial,body['properties'],'Palette',5));pal=ref.index()
            core.require(ref.pos==len(ref.data) and pal==texture['palette_export'],'palette link')
            pe=exports[pal-1];core.require(native_class_name(pe,exports)=='Palette','palette class')
            ps=blob[pe['offset']:pe['offset']+pe['size']];pb=property_block(ps,tables['names']);colors=palette(ps,pb['end'])
            core.require(core.digest(colors)==texture['palette_sha256'],'palette hash')
            parsed=mips(serial,body['end'],export['offset'])
            core.require([{k:v for k,v in row.items() if k!='raw'} for row in parsed]==texture['mips'],'mip manifest mismatch')
            for row in parsed[1:]:
                identity=texture['id']+f"/mip/{row['index']}";filename=f"{Path(parts[1]).stem}-{parts[3]}-mip-{row['index']}.png"
                im=image_view(row['raw'],row['width'],row['height'],colors);im.save(out/filename)
                with Image.open(out/filename) as check:core.require(check.size==im.size,'image reopen geometry')
                rows.append(dict(id=identity,raw_sha256=row['sha256'],width=im.width,height=im.height,image=filename,image_sha256=core.file_digest(out/filename),editable=False,runtime_visibility_verified=False))
                views.append((f"{Path(parts[1]).stem}:{parts[3]} mip {row['index']}",im))
    contact=sheets(views,out)
    core.require(core.file_digest(archive)==FILE_HASH and core.file_digest(manifest)==mh,'input changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,manifest_sha256=mh,textures=len(textures),smaller_mips=len(rows),contact_sheets=len(contact),all_images_native_size=True,visual_review_complete=False,streamed_textures_audited=False,complete_game_text=False,source_modified=False)
    for name,value in [('images.json',rows),('sheets.json',contact),('summary.json',summary)]:
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(path.read_text('utf8'))==value,'JSON reopen')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['archive','manifest','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.manifest,a.out),sort_keys=True))
