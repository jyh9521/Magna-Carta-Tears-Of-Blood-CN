"""Pack profile-bound UI labels from a fingerprinted font into existing P8 atlases."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from font_poc import require,file_digest,digest,archive_entries,manifest_overlay
from audit_container_payloads import unpack_chunks
from translate.celfid import recompress_chunked,decompress_chunked
from patch_indexed_texture_pixels import patch_pixels
from build_locale import checked_archive
from PIL import Image,ImageFont,ImageDraw
import numpy as np

def render_labels(original,palette,patches,font):
    colors=np.frombuffer(palette,dtype=np.uint8).reshape(256,4)[:,:3].astype(np.int32)
    arr=np.frombuffer(original,dtype=np.uint8).reshape(256,256).copy();allowed=np.zeros((256,256),bool)
    require(tuple(colors[0])==(0,0,0),'masked black index mismatch')
    for q in patches:
        x,y,x1,y1=q['rect'];require(0<=x<x1<=256 and 0<=y<y1<=256,'patch bounds')
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
    (a.out/'ui-texture-build.json').write_text(json.dumps(dict(texture_proofs=proofs,changes=changes,archive_sha256=file_digest(a.out/'LINEAR.AFS'),runtime_verified=False),indent=2)+'\n','utf8');print('TEXT_TEXTURE_AFS_PASS streams=3 patches=15 palettes_outside_pixels_preserved=true')
if __name__=='__main__':main()
