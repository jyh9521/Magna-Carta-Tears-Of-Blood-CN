"""Read bounded P8 stream mips with explicitly checked field-order variants."""
import argparse
import json
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from audit_object_properties import Reader,property_block
from audit_texture_mips import palette,image_view,property_value
from audit_container_payloads import unpack_chunks,probe_all_packages
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
from cri_afs import Afs
from afs import filename_toc


def stream_mips(serial,start,original_offset):
    r=Reader(serial,start)
    count=r.index();core.require(1<=count<=16,'mip count')
    rows=[]
    for i in range(count):
        lazy=r.integer('I');record_start=r.pos;variants=[]
        for order in ['pixels-before-dimensions','dimensions-before-pixels']:
            q=Reader(serial,record_start)
            try:
                if order=='dimensions-before-pixels':w,h,ub,vb=struct.unpack('<IIBB',q.take(10))
                size=q.index();core.require(size>0,'pixel count');offset=q.pos;pixels=q.take(size)
                logical_end=q.pos-(10 if order=='dimensions-before-pixels' else 0)
                if order=='pixels-before-dimensions':w,h,ub,vb=struct.unpack('<IIBB',q.take(10))
                core.require(ub<=12 and vb<=12 and w==1<<ub and h==1<<vb and size==w*h,'P8 geometry')
                core.require(lazy==original_offset+logical_end,'original lazy end')
                if rows:core.require(w==max(1,rows[-1]['width']//2) and h==max(1,rows[-1]['height']//2),'mip progression')
                variants.append(dict(index=i,width=w,height=h,bytes=size,pixel_offset=offset,end=q.pos,order=order,lazy_end=lazy,sha256=core.digest(pixels),raw=pixels))
            except (ValueError,struct.error):pass
        core.require(len(variants)==1,'mip order missing or ambiguous')
        row=variants[0];rows.append(row);r.pos=row['end']
    core.require(r.pos==len(serial),'texture trailing bytes')
    return rows


def audit(file,out):
    core.require(core.file_digest(file)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(file);names=filename_toc(a)
    with file.open('rb') as f:b,_=unpack_chunks(a.read_entry(names.index('celfid.lix'),f))
    core.require(core.digest(b)==BUNDLE_HASH,'bundle identity mismatch')
    tables=[t for t in probe_all_packages(b) if t['wrapper_path']=='../Textures/00014366.utx']
    core.require(len(tables)==1,'texture table identity');t=tables[0]
    e=t['exports'][0];core.require((e['name'],e['declared_offset'],e['declared_size'])==('range_256',403,2845),'export metadata mismatch')
    raw=b[3214774:3217619];props=property_block(raw,t['names'],e['flags'])
    core.require(props['end']==61,'property boundary mismatch')
    core.require(property_value(raw,props['properties'],'Palette',5)==b'\x02','palette reference mismatch')
    ms=stream_mips(raw,props['end'],e['declared_offset'])
    pal=b[3217619:3218646];pp=property_block(pal,t['names'],t['exports'][1]['flags'])
    colors=palette(pal,pp['end']);core.require(pp['end']==1,'palette property boundary')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for m in ms:
        image_view(m['raw'],m['width'],m['height'],colors).save(out/('mip-'+str(m['index'])+'.png'))
    summary=dict(schema=1,texture_start=3214774,texture_end=3217619,texture_bytes=len(raw),texture_sha256=core.digest(raw),palette_start=3217619,palette_end=3218646,palette_sha256=core.digest(pal),mips=[{k:v for k,v in m.items() if k!='raw'} for m in ms],geometry_verified=True,table_identity_unique=True,serial_identity_runtime_verified=False,full_native_tail_verified=False,complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    p=out/'summary.json';p.write_text(json.dumps(summary,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==summary,'summary reopen')
    core.require(core.file_digest(file)==FILE_HASH,'FILE changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.file,a.out),sort_keys=True))
