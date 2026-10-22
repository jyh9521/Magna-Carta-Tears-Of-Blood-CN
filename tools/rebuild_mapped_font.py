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
    placement=settings.get('placement','legacy-clamped')
    require(placement in ('legacy-clamped','shared-origin-guarded'),'unknown glyph placement')
    prepared={}
    horizontal_guard=settings.get('horizontal_guard',0)
    require(type(horizontal_guard) is int and horizontal_guard>=0,'invalid horizontal guard')
    require(not horizontal_guard or placement=='shared-origin-guarded','horizontal guard requires shared origin')
    if placement=='shared-origin-guarded':
        # Quantize before measuring; weak Lanczos lobes are not visible ink.
        # One translation for the complete repertoire preserves the font baseline.
        guard=settings.get('edge_guard',1)
        require(type(guard) is int and guard>=1,'positive edge guard required')
        for q in mapping['entries']:
            im,box=ink(q['character'])
            levels=im.point(lut if options is not None else [(v*3+127)//255 for v in range(256)])
            prepared[q['character']]=(levels,levels.getbbox(),im.info.get('bold_guard'),im)
        boxes=[b for _,b,_,_ in prepared.values() if b]
        require(bool(boxes),'empty glyph repertoire')
        top=min(b[1] for b in boxes);bottom=max(b[3] for b in boxes)
        require(bottom-top<=info['height']-2*guard,'shared baseline exceeds guarded cell')
        origin_y=guard-top
    result=bytearray(serial);allowed=set();proof=[]
    for q in mapping['entries']:
        g=q['glyph'];require(g>=settings['original_glyphs'] and g<info['glyphs'],'mapped glyph outside appended slots')
        code=int(q['bytes'],16);i=max(i for i,v in enumerate(info['ranges']) if v<=code)
        require(info['bases'][i]+code-info['ranges'][i]==g,'map/table mismatch')
        ch=q['character']
        if placement=='shared-origin-guarded':
            im,box,reason,coverage=prepared[ch];im.info['bold_guard']=reason
        else:im,box=ink(ch)
        tile=im.crop(box) if box else Image.new('L',(1,1));advance=settings['advance_overrides'].get(ch,settings['advance'])
        require(0<advance<=info['width'],'invalid advance')
        fitted=False
        if horizontal_guard:
            limit=min(advance,info['width'])-2*horizontal_guard
            require(limit>0,'advance has no guarded ink area')
            if tile.width>limit:
                # Fit coverage horizontally before quantization; do not cut strokes.
                tile=coverage.crop(box).resize((limit,tile.height),Image.Resampling.LANCZOS)
                tile=tile.point(lut if options is not None else [(v*3+127)//255 for v in range(256)])
                fitted=True
        # Very wide serif swashes are fitted, never clipped.
        if placement=='shared-origin-guarded':require(tile.width<=info['width'],'glyph exceeds horizontal slot')
        elif tile.width>info['width']:tile=tile.resize((info['width'],tile.height),Image.Resampling.LANCZOS)
        require(tile.height<=info['height'],'glyph exceeds vertical slot')
        x=max(0,(advance-tile.width)//2);x=min(x,info['width']-tile.width)
        if horizontal_guard:require(horizontal_guard<=x and x+tile.width<=advance-horizontal_guard,'glyph leaves horizontal guard')
        if placement=='shared-origin-guarded':
            y=box[1]+origin_y if box else guard
            require(guard<=y and y+tile.height<=info['height']-guard,'glyph leaves guarded baseline')
        else:y=max(0,min((box[1] if box else ref[1])+origin_y,info['height']-tile.height))
        image=Image.new('L',(info['width'],info['height']));image.paste(tile,(x,y));packed=bytearray(info['height']*info['row_stride'])
        for yy in range(info['height']):
            for xx in range(info['width']):
                v=image.getpixel((xx,yy));level=v if placement=='shared-origin-guarded' else lut[v] if options is not None else (v*3+127)//255
                packed[yy*info['row_stride']+xx//4]|=level<<(2*(xx%4))
        require(any(packed) or ch.isspace(),'glyph vanished after quantization')
        at=info['bitmap_start']+g*len(packed);result[at:at+len(packed)]=packed;ma=info['metrics_start']+g;result[ma]=advance
        allowed.update(range(at,at+len(packed)));allowed.add(ma);proof.append(dict(character=ch,glyph=g,ink_box=[x,y,x+tile.width,y+tile.height],advance=advance))
        if options is not None:proof[-1]['bold_guard']=im.info.get('bold_guard')
        if placement=='shared-origin-guarded':proof[-1].update(origin_y=origin_y,source_ink_box=box,edge_guard=guard,placement=placement,horizontal_guard=horizontal_guard,horizontally_fitted=fitted)
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
        original=(a.base/(name+'.modified.bin')).read_bytes();require(digest(original)==s['base_sha256'],'font baseline mismatch');new,proof=rebuild(original,mapping,a.font,s)
        padding=profile.get('bitmap_padding','preserve');require(padding in ('preserve','zero-outside-metric'),'unknown bitmap padding policy')
        padding_receipt=None
        if padding=='zero-outside-metric':
            from sanitize_font_padding import sanitize
            new,padding_receipt=sanitize(new)
        path=a.out/(name+'.modified.bin');path.write_bytes(new);require(path.read_bytes()==new,'font reopen failed');report[name]=dict(original_sha256=digest(original),modified_sha256=digest(new),glyphs=font_data(new)['glyphs'],mapped=len(proof),proof=proof,padding=padding_receipt)
    (a.out/'font-rebuild.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('MAPPED_FONT_REBUILD_PASS fonts=2 mapped='+str(len(mapping['entries']))+' bitmap_padding='+profile.get('bitmap_padding','preserve')+' original_effective_ink_tables_preserved=true clipping=0')
if __name__=='__main__':main()
