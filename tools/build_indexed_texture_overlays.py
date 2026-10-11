"""Reproduce profile-bound artwork packing and streamed P8 overlays from originals.

Artwork is stored as project-owned PNGs. Only indexed pixels in the explicit
rectangles are edited; original palette indices elsewhere remain exact.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from font_poc import require,digest,file_digest,archive_entries,output_directory,manifest_overlay
from audit_container_payloads import unpack_chunks
from translate.celfid import recompress_chunked,decompress_chunked
from build_locale import checked_archive
from patch_indexed_texture_pixels import patch_pixels
from PIL import Image
import numpy as np


def artwork(patch):
    path=Path(patch['image']);require(file_digest(path)==patch['image_sha256'],'artwork fingerprint mismatch')
    im=Image.open(path).convert('RGBA')
    if patch['crop']:im=im.crop(patch['crop'])
    box=im.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox();require(box is not None,'artwork is empty')
    a=im.crop(box).getchannel('A').resize(tuple(patch['resize']),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',a.size,tuple(patch['ink'])+(255,));result.putalpha(a);return result


def build(archive,profile,out):
    require(file_digest(archive)==profile['archive_sha256'],'texture archive version mismatch')
    out=output_directory(out);require(not any(out.iterdir()),'texture output not empty')
    _,entries=archive_entries(archive);members=dict(entries);payloads={};pixels={};proofs={};overrides={}
    for name,row in profile['streams'].items():
        require(digest(members[name])==row['source_compressed_sha256'],'compressed texture source mismatch')
        b,_=unpack_chunks(members[name]);require(digest(b)==row['payload_sha256'],'texture payload mismatch');payloads[name]=b
    for canvas in profile['canvases']:
        image=Image.new('RGBA',tuple(canvas['size']),'white');views={};mask=Image.new('L',image.size,0)
        from PIL import ImageDraw
        for ref in canvas['references']:
            b=payloads[ref['stream']];pal=b[ref['palette_offset']:ref['palette_offset']+1024];raw=b[ref['pixel_offset']:ref['pixel_offset']+65536]
            require(digest(pal)==ref['palette_sha256'] and digest(raw)==ref['pixel_sha256'],'reference image identity mismatch')
            im=Image.frombytes('P',(256,256),raw);im.putpalette(bytes(v for i in range(256) for v in pal[i*4:i*4+3]));image.paste(im.convert('RGBA'),tuple(ref['position']));views[ref['asset_key']]=(ref,pal,raw)
        for patch in canvas['patches']:
            image.paste((255,255,255,255),tuple(patch['clear_rect']));image.alpha_composite(artwork(patch),tuple(patch['position']));r=patch['rect'];ImageDraw.Draw(mask).rectangle((r[0],r[1],r[2]-1,r[3]-1),fill=255)
        preview=Image.new('RGB',image.size,'white')
        for key,(ref,pal,raw) in views.items():
            x,y=ref['position'];rgb=np.asarray(image.convert('RGB').crop((x,y,x+256,y+256)),dtype=np.int32);allowed=np.asarray(mask.crop((x,y,x+256,y+256)))>0
            colors=np.frombuffer(pal,dtype=np.uint8).reshape(256,4)[:,:3].astype(np.int32);arr=np.frombuffer(raw,dtype=np.uint8).reshape(256,256).copy()
            for yy,xx in np.argwhere(allowed):
                if not np.array_equal(colors[arr[yy,xx]],rgb[yy,xx]):arr[yy,xx]=np.argmin(np.sum((colors-rgb[yy,xx])**2,axis=1))
            pixels[key]=arr.tobytes();(out/(key+'.p8')).write_bytes(pixels[key]);im=Image.frombytes('P',(256,256),pixels[key]);im.putpalette(colors.astype(np.uint8).flatten().tolist());preview.paste(im.convert('RGB'),(x,y))
        preview.save(out/(canvas['name']+'-indexed-preview.png'))
    for name,row in profile['streams'].items():
        data,proof=patch_pixels(payloads[name],row,pixels);compressed=recompress_chunked(data);require(decompress_chunked(compressed)==data,'texture compression roundtrip mismatch');overrides[name.lower()]=compressed;proofs[name]=proof
        (out/(name+'.payload.bin')).write_bytes(data);(out/name).write_bytes(compressed)
    # LINEAR's native manifest uses extensionless resource IDs, not .lin names.
    overrides[entries[0][0].lower()]=manifest_overlay(entries[0][1],{Path(k).stem:len(v) for k,v in overrides.items()})
    changes=checked_archive(archive,out/'LINEAR.AFS',overrides)
    result=dict(schema=1,source_archive_sha256=profile['archive_sha256'],modified_archive_sha256=file_digest(out/'LINEAR.AFS'),texture_proofs=proofs,afs_changes=changes,runtime_verified=False)
    (out/'texture-integration.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
    print('INDEXED_TEXTURE_AFS_PASS streams='+str(len(proofs))+' textures='+str(sum(len(x) for x in proofs.values()))+' palettes_tables_untargeted_pixels_preserved=true')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','profile','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.archive,json.loads(a.profile.read_text('utf8')),a.out)

if __name__=='__main__':main()
