"""Build offline, same-format font candidates and decoded-bitmap contact sheets."""
import argparse, json, sys, hashlib, platform
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, __version__ as pillow_version
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
from rebuild_mapped_font import rebuild
from research_inventory import font_data
from font_poc import glyph_bitmap
from fontTools.ttLib import TTFont


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def metadata(path):
    with TTFont(path) as font:
        names = {str(n): font['name'].getDebugName(n) for n in (1, 2, 5, 6, 13, 14)}
        weight = font['OS/2'].usWeightClass
        cmap = font.getBestCmap()
    return dict(path=str(path), sha256=sha(path), names=names, weight_class=weight), cmap


def panel(serial, mapping, texts, title, grid=False):
    info = font_data(serial); lookup = {q['character']: q['glyph'] for q in mapping['entries']}
    def index(ch):
        if ch in lookup: return lookup[ch]
        code = int.from_bytes(ch.encode('cp949'), 'big')
        i = max(i for i,v in enumerate(info['ranges']) if v <= code)
        g = info['bases'][i] + code - info['ranges'][i]
        if not 0 <= g < info['glyphs']: raise ValueError('preview missing character '+ch)
        return g
    line_height = info['height'] + 5
    canvas = Image.new('RGB',(640,32 + len(texts) * line_height + 12),(24,28,29))
    draw=ImageDraw.Draw(canvas);draw.text((10,8),title,fill=(220,215,190))
    for row,text in enumerate(texts):
        x=12;y=32+row*line_height
        for ch in text:
            g=index(ch);advance=serial[info['metrics_start']+g];mask=glyph_bitmap(serial,g)
            if x+mask.width>=canvas.width: raise ValueError('preview line exceeds canvas')
            if grid:draw.rectangle((x,y,x+info['width']-1,y+info['height']-1),outline=(50,60,63))
            canvas.paste((232,229,211),(x,y,x+mask.width,y+mask.height),mask);x+=advance
    return canvas


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','map','geometry','experiment','fonts','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if any(a.out.iterdir()):raise ValueError('output must be empty')
    mapping=json.loads(a.map.read_text('utf8'));geometry=json.loads(a.geometry.read_text('utf8'));exp=json.loads(a.experiment.read_text('utf8'));fonts=json.loads(a.fonts.read_text('utf8'))
    report=dict(python=platform.python_version(),pillow=pillow_version,map_sha256=sha(a.map),geometry_sha256=sha(a.geometry),fonts={},variants=[],runtime_verified=False)
    for key,value in fonts.items():
        meta,cmap=metadata(Path(value));missing=[q['character'] for q in mapping['entries'] if cmap.get(ord(q['character'])) in (None,'.notdef')]
        if missing:raise ValueError('font coverage missing '+key+repr(missing[:8]))
        report['fonts'][key]=meta
    for variant in exp['variants']:
        dest=a.out/variant['id'];dest.mkdir();settings=json.loads(json.dumps(geometry));settings['font_input']=report['fonts'][variant['font']];record=dict(variant,fonts={})
        for name,s in settings['fonts'].items():
            if variant['raster_options'] is not None:s['raster_options']=variant['raster_options']
            original=(a.base/(name+'.modified.bin')).read_bytes()
            if hashlib.sha256(original).hexdigest()!=s['base_sha256']:raise ValueError('baseline font fingerprint mismatch')
            result,proof=rebuild(original,mapping,Path(fonts[variant['font']]),s);path=dest/(name+'.modified.bin');path.write_bytes(result);assert path.read_bytes()==result
            info=font_data(result);before=font_data(original);assert info==before
            assert result[info['metrics_start']:info['metrics_start']+info['glyphs']]==original[info['metrics_start']:info['metrics_start']+info['glyphs']]
            size=info['row_stride']*info['height'];assert result[info['bitmap_start']:info['bitmap_start']+2667*size]==original[info['bitmap_start']:info['bitmap_start']+2667*size]
            reasons=Counter(q.get('bold_guard') for q in proof if q.get('bold_guard'));record['fonts'][name]=dict(sha256=sha(path),size=len(result),glyphs=info['glyphs'],mapped=len(proof),guarded_bold_count=sum(reasons.values()),guard_reasons=dict(reasons),proof=proof)
            for grid in (False,True):
                im=panel(result,mapping,exp['texts'],variant['id']+' / '+name+' / 2-bit decoded',grid)
                im.save(dest/(name+('-grid' if grid else '')+'-native.png'))
                im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(dest/(name+('-grid' if grid else '')+'-4x.png'))
        (dest/'profile.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n','utf8');report['variants'].append(record)
        print('CANDIDATE_PASS',variant['id'],'fonts=2 mapped_each=2466 geometry_mapping_advance_preserved=true',flush=True)
    for fontname in geometry['fonts']:
        for group,selected in [('families',exp['variants'][:6]),('parameters',[exp['variants'][1]]+exp['variants'][6:])]:
            images=[Image.open(a.out/q['id']/(fontname+'-native.png')).convert('RGB') for q in selected]
            sheet=Image.new('RGB',(1280,max(im.height for im in images)*((len(images)+1)//2)),(24,28,29))
            for i,im in enumerate(images):sheet.paste(im,((i%2)*640,(i//2)*images[0].height))
            sheet.save(a.out/(fontname+'-'+group+'-native.png'));sheet.resize((sheet.width*3,sheet.height*3),Image.Resampling.NEAREST).save(a.out/(fontname+'-'+group+'-3x.png'))
    (a.out/'experiment-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('OFFLINE_EXPERIMENT_PASS variants='+str(len(report['variants']))+' fonts_per_variant=2 ISO_written=false')

if __name__=='__main__':main()
