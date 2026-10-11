"""Guarded, same-size P8 pixel overlays in observed streamed texture copies.

The profile binds each payload to its full source hash, exact export identity,
pixel hash and palette hash. This does not infer a general streamed serializer.
Palette, texture properties, lazy pointers and package tables are unchanged.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from font_poc import require,digest,file_digest
from audit_container_payloads import probe_all_packages
from audit_object_properties import property_block
from audit_stream_texture import stream_mips


def patch_pixels(payload, profile, replacements):
    require(digest(payload)==profile['payload_sha256'],'texture stream source mismatch')
    tables=probe_all_packages(payload)
    modified=bytearray(payload);ranges=[];proofs=[]
    for row in profile['textures']:
        ts=[t for t in tables if t['wrapper_path']==row['package']]
        require(len(ts)==1,'texture package identity ambiguous')
        t=ts[0];es=[e for e in t['exports'] if e['name']==row['name'] and e['class']=='Texture']
        require(len(es)==1,'texture export identity ambiguous');e=es[0]
        start=row['serial_offset'];raw=payload[start:start+e['declared_size']]
        p=property_block(raw,t['names'],e['flags']);mips=stream_mips(raw,p['end'],e['declared_offset'])
        require(len(mips)==1 and mips[0]['width']==mips[0]['height']==256,'unsupported texture geometry/mips')
        m=mips[0];at=start+m['pixel_offset'];end=at+m['bytes']
        require(at==row['pixel_offset'] and m['sha256']==row['pixel_sha256'],'texture pixel identity mismatch')
        pa=row['palette_offset'];pal=payload[pa:pa+1024]
        require(len(pal)==1024 and digest(pal)==row['palette_sha256'],'palette source mismatch')
        new=replacements[row['asset_key']];require(len(new)==m['bytes'],'texture overlay size changed')
        require(not any(at<b and a<end for a,b in ranges),'overlapping texture overlays')
        modified[at:end]=new;ranges.append((at,end));proofs.append(dict(name=row['name'],pixel_offset=at,bytes=len(new),original_sha256=m['sha256'],modified_sha256=digest(new)))
    before=0
    for a,b in sorted(ranges):
        require(payload[before:a]==modified[before:a],'unselected texture bytes changed');before=b
    require(payload[before:]==modified[before:],'texture tail changed')
    return bytes(modified),proofs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('payload','profile','pixels','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'))
    replacements={k:(a.pixels/v).read_bytes() for k,v in profile['pixel_files'].items()}
    data,report=patch_pixels(a.payload.read_bytes(),profile,replacements)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(data)
    require(a.out.read_bytes()==data,'texture output reopen mismatch')
    print('INDEXED_TEXTURE_PIXEL_PASS textures='+str(len(report))+' unchanged_tables_palette_properties=true')

if __name__=='__main__':main()
