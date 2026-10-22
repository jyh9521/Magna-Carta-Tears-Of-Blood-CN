"""Pack profile-bound UI labels from a fingerprinted font into existing P8 atlases."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from font_poc import require,file_digest,digest,archive_entries,manifest_overlay
from audit_container_payloads import unpack_chunks
from translate.celfid import recompress_chunked,decompress_chunked
from patch_indexed_texture_pixels import patch_pixels
from build_locale import checked_archive
from PIL import Image,ImageFont,ImageDraw,ImageFilter
import numpy as np

def clean_label(rect,patch,font,palette):
    """Mask-first P8 text: discard resampling lobes before adding a local outline."""
    w,h=rect;guard=patch.get('edge_guard',1);threshold=patch.get('coverage_threshold',48)
    require(type(guard) is int and guard>=1 and 0<threshold<255,'invalid label mask guard/threshold')
    require(w>2*guard+2 and h>2*guard+2,'label cell too small')
    face=ImageFont.truetype(str(font),patch['size']*4)
    mask=Image.new('L',(1024,512));ImageDraw.Draw(mask).text((8,8),patch['text'],font=face,fill=255)
    box=mask.getbbox();require(box is not None,'empty label');mask=mask.crop(box)
    scale=min((w-2*guard-2)/mask.width,(h-2*guard-2)/mask.height,0.25)
    size=(max(1,round(mask.width*scale)),max(1,round(mask.height*scale)))
    mask=mask.resize(size,Image.Resampling.LANCZOS)
    cell=Image.new('L',(w,h));cell.paste(mask,((w-size[0])//2,(h-size[1])//2))
    coverage=np.asarray(cell);support=Image.fromarray(np.where(coverage>=threshold,255,0).astype(np.uint8))
    expanded=np.asarray(support.filter(ImageFilter.MaxFilter(3)))>0
    active=coverage>=threshold;result=np.zeros((h,w),np.uint8)
    colors=np.frombuffer(palette,np.uint8).reshape(256,4)[:,:3].astype(np.int32)
    # Restrict to the neutral ramp, not unrelated coloured UI entries.
    palette_mode=patch.get('palette_mode','neutral')
    require(palette_mode in ('neutral','color'),'unknown label palette mode')
    allowed=np.flatnonzero(((colors.max(1)-colors.min(1)<=12) if palette_mode=='neutral' else np.ones(256,bool))&(colors.mean(1)>=30))
    require(len(allowed)>0 and tuple(colors[1])==(4,4,4),'neutral ramp/outline absent')
    result[expanded]=1
    for y,x in zip(*np.where(active)):
        rgb=np.array(patch['ink'])*coverage[y,x]/255
        result[y,x]=allowed[np.argmin(np.sum((colors[allowed]-rgb)**2,axis=1))]
    require(not np.any(result[:guard]) and not np.any(result[-guard:]) and not np.any(result[:,:guard]) and not np.any(result[:,-guard:]),'label leaves transparent guard')
    return result

def render_labels(original,palette,patches,font):
    colors=np.frombuffer(palette,dtype=np.uint8).reshape(256,4)[:,:3].astype(np.int32)
    arr=np.frombuffer(original,dtype=np.uint8).reshape(256,256).copy();allowed=np.zeros((256,256),bool)
    require(tuple(colors[0])==(0,0,0),'masked black index mismatch')
    for q in patches:
        x,y,x1,y1=q['rect'];require(0<=x<x1<=256 and 0<=y<y1<=256,'patch bounds')
        if 'clear_rect' in q:
            cx,cy,cx1,cy1=q['clear_rect']
            require(0<=cx<=x<x1<=cx1<=256 and 0<=cy<=y<y1<=cy1<=256,'clear rectangle must contain label and remain inside atlas')
            arr[cy:cy1,cx:cx1]=0;allowed[cy:cy1,cx:cx1]=True
        mode=q.get('raster_mode','legacy-rgb')
        require(mode in ('legacy-rgb','coverage-mask'),'unknown label raster mode')
        if mode=='coverage-mask':
            arr[y:y1,x:x1]=clean_label((x1-x,y1-y),q,font,palette);allowed[y:y1,x:x1]=True
            continue
        face=ImageFont.truetype(str(font),q['size']*4);im=Image.new('RGB',(256*4,128*4))
        ImageDraw.Draw(im).text((8,8),q['text'],font=face,fill=tuple(q['ink']),stroke_width=4,stroke_fill=tuple(q['stroke']))
        box=im.getbbox();require(box is not None,'empty label');im=im.crop(box)
        scale=min((x1-x)/im.width,(y1-y)/im.height,1/4);size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
        im=im.resize(size,Image.Resampling.LANCZOS);tile=Image.new('RGB',(x1-x,y1-y));tile.paste(im,((tile.width-im.width)//2,(tile.height-im.height)//2))
        rgb=np.asarray(tile,dtype=np.int32);region=arr[y:y1,x:x1]
        for yy in range(y1-y):
            for xx in range(x1-x):
                if not np.any(rgb[yy,xx]):region[yy,xx]=0
                else:region[yy,xx]=1+np.argmin(np.sum((colors[1:]-rgb[yy,xx])**2,axis=1))
        allowed[y:y1,x:x1]=True
    require(np.array_equal(arr[~allowed],np.frombuffer(original,dtype=np.uint8).reshape(256,256)[~allowed]),'outside rectangle pixels changed')
    return arr.tobytes()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','profile','font','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(file_digest(a.archive)==profile['base_archive_sha256'] and file_digest(a.font)==profile['font_sha256'],'input fingerprint mismatch');a.out.mkdir(parents=True,exist_ok=True);require(not any(a.out.iterdir()),'output not empty');_,entries=archive_entries(a.archive);members=dict(entries);overrides={};proofs={}
    for n,row in profile['streams'].items():
        require(digest(members[n])==row['source_compressed_sha256'],'stream hash mismatch');b,_=unpack_chunks(members[n]);t=row['textures'][0];at=t['pixel_offset'];pa=t['palette_offset'];pal=b[pa:pa+1024];new=render_labels(b[at:at+65536],pal,row['patches'],a.font);modified,proof=patch_pixels(b,row,{t['asset_key']:new});compressed=recompress_chunked(modified);require(decompress_chunked(compressed)==modified,'compression mismatch');overrides[n.lower()]=compressed;proofs[n]=proof
        (a.out/(n+'.payload')).write_bytes(modified);im=Image.frombytes('P',(256,256),new);im.putpalette([v for i in range(256) for v in pal[i*4:i*4+3]]);im.convert('RGB').resize((768,768)).save(a.out/(n+'-preview.png'))
    overrides[entries[0][0].lower()]=manifest_overlay(entries[0][1],{Path(n).stem:len(b) for n,b in overrides.items()});changes=checked_archive(a.archive,a.out/'LINEAR.AFS',overrides)
    (a.out/'ui-texture-build.json').write_text(json.dumps(dict(texture_proofs=proofs,changes=changes,archive_sha256=file_digest(a.out/'LINEAR.AFS'),runtime_verified=False),indent=2)+'\n','utf8');print('TEXT_TEXTURE_AFS_PASS streams='+str(len(profile['streams']))+' patches='+str(sum(len(row['patches']) for row in profile['streams'].values()))+' palettes_outside_pixels_preserved=true')
if __name__=='__main__':main()
