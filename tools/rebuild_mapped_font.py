"""Re-rasterize explicitly mapped glyphs without changing tables or original slots."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from font_poc import require,digest,file_digest
from research_inventory import font_data
from PIL import Image,ImageFont,ImageDraw

def rebuild(serial,mapping,font_path,settings):
    info=font_data(serial);size=settings['raster_size'];face=ImageFont.truetype(str(font_path),size)
    require(4<=size<=info['height'],'unsupported raster size')
    options=settings.get('raster_options')
    if options is not None:
        from font_rasterization import render_ink,quantization_lut
        lut=quantization_lut(options)
    # Use actual ink, not advance/bearing bbox, to place CJK body near the top.
    def ink(ch):
        if options is not None:
            guard_width=min(info['width'],settings['advance_overrides'].get(ch,settings['advance']))
            im,box,reason=render_ink(ch,font_path,size,options,guard_width,info['height'])
            require(box is not None or ch.isspace(),'empty glyph '+ch)
            im.info['bold_guard']=reason
            return im,box
        im=Image.new('L',(96,96));ImageDraw.Draw(im).text((32,24),ch,font=face,fill=255)
        box=im.getbbox();require(box is not None or ch.isspace(),'empty glyph '+ch);return im,box
    _,ref=ink(settings['reference']);origin_y=settings['body_top']-ref[1]
    result=bytearray(serial);allowed=set();proof=[]
    for q in mapping['entries']:
        g=q['glyph'];require(g>=settings['original_glyphs'] and g<info['glyphs'],'mapped glyph outside appended slots')
        code=int(q['bytes'],16);i=max(i for i,v in enumerate(info['ranges']) if v<=code)
        require(info['bases'][i]+code-info['ranges'][i]==g,'map/table mismatch')
        ch=q['character'];im,box=ink(ch);tile=im.crop(box) if box else Image.new('L',(1,1));advance=settings['advance_overrides'].get(ch,settings['advance'])
        require(0<advance<=info['width'],'invalid advance')
        # Very wide serif swashes are fitted, never clipped.
        if tile.width>info['width']:tile=tile.resize((info['width'],tile.height),Image.Resampling.LANCZOS)
        require(tile.height<=info['height'],'glyph exceeds vertical slot')
        x=max(0,(advance-tile.width)//2);x=min(x,info['width']-tile.width)
        y=max(0,min((box[1] if box else ref[1])+origin_y,info['height']-tile.height))
        image=Image.new('L',(info['width'],info['height']));image.paste(tile,(x,y));packed=bytearray(info['height']*info['row_stride'])
        for yy in range(info['height']):
            for xx in range(info['width']):
                v=image.getpixel((xx,yy));level=lut[v] if options is not None else (v*3+127)//255
                packed[yy*info['row_stride']+xx//4]|=level<<(2*(xx%4))
        require(any(packed) or ch.isspace(),'glyph vanished after quantization')
        at=info['bitmap_start']+g*len(packed);result[at:at+len(packed)]=packed;ma=info['metrics_start']+g;result[ma]=advance
        allowed.update(range(at,at+len(packed)));allowed.add(ma);proof.append(dict(character=ch,glyph=g,ink_box=[x,y,x+tile.width,y+tile.height],advance=advance))
        if options is not None:proof[-1]['bold_guard']=im.info.get('bold_guard')
    require(font_data(result)==info and len(result)==len(serial),'font tables/geometry changed')
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(serial,result))),'original font bytes changed')
    return bytes(result),proof

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','map','font','profile','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(file_digest(a.font)==profile['font_input']['sha256'],'font source hash mismatch');mapping=json.loads(a.map.read_text('utf8'))
    from fontTools.ttLib import TTFont
    with TTFont(a.font) as face:
        cmap=face.getBestCmap();require(all(cmap.get(ord(q['character'])) not in (None,'.notdef') for q in mapping['entries']),'missing source font glyph')
    a.out.mkdir(parents=True,exist_ok=True);require(not any(a.out.iterdir()),'output not empty');report={}
    for name,s in profile['fonts'].items():
        original=(a.base/(name+'.modified.bin')).read_bytes();require(digest(original)==s['base_sha256'],'font baseline mismatch');new,proof=rebuild(original,mapping,a.font,s);path=a.out/(name+'.modified.bin');path.write_bytes(new);require(path.read_bytes()==new,'font reopen failed');report[name]=dict(original_sha256=digest(original),modified_sha256=digest(new),glyphs=font_data(new)['glyphs'],mapped=len(proof),proof=proof)
    (a.out/'font-rebuild.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('MAPPED_FONT_REBUILD_PASS fonts=2 mapped='+str(len(mapping['entries']))+' original_slots_tables_preserved=true clipping=0')
if __name__=='__main__':main()
