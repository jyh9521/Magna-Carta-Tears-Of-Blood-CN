"""Audit the actual FPB header record and native loader/getter binding.

Legacy catalog sequence aliases are not rewritten by this read-only audit.
"""
from pathlib import Path
import argparse, hashlib, json, struct, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from cri_afs import Afs
from afs import filename_toc
from translate.fpb import parse_fpb_raw


def native_records(blob):
    header,windows,pool=parse_fpb_raw(blob)
    records=[struct.unpack_from('<III',header,4),*windows]
    require(len(records)==struct.unpack_from('<I',header)[0],'native record count mismatch')
    require(all(o+n<=len(pool) for _,o,n in records),'native record pool bounds')
    return records,pool


def lookup(records,key):
    return next((i for i,row in enumerate(records) if row[0]==key),None)


def native_evidence(image):
    binding=bind_inline(image,'intUMrtsFieldDataexecGetPlayBookDataText')
    require(binding['callback']=='0x3424d0','unexpected PlayBook callback')
    require({'va':'0x342538','target':'0x342560'} in binding['bounded_callback_jals'],'getter call missing')
    # Exact source words, including virtual-read sizes and branch delay slots.
    anchors={0x3007fc:0x3c05004b,0x300804:0x24a577a0,
        0x300840:0x8e120340,0x300868:0x0320f809,0x30086c:0x24060004,
        0x3008d8:0x2644019c,0x3008e0:0x24050010,
        0x30094c:0x264401a8,0x300954:0x24050010,
        0x3009a0:0x2645019c,0x3009cc:0x264501a8,
        0x3009bc:0x00101900,0x3009fc:0x0320f809,0x300a00:0x24060004,
        0x300a60:0x0320f809,0x300a64:0x00512821,
        0x300a80:0x0320f809,0x300a84:0x24450004,
        0x300a8c:0x8fc205ec,0x300a94:0x1440ffbe,
        0x300aac:0x0320f809,0x300ab0:0x24060004,
        0x300afc:0x8e42019c,0x300b0c:0x8e4201a8,
        0x300b28:0x8c430000,0x300b2c:0x8c460004,
        0x300b34:0x0c045b1c,0x300b38:0x00432821,
        0x342564:0x28a12710,0x34257c:0x8c8701a0,
        0x342588:0x8c83019c,0x34258c:0x00083100,
        0x342594:0x8e030000,0x342598:0x14650018,
        0x3425a0:0x26030004,0x342604:0x1460ffe0,
        0x342614:0x8c8701ac,0x342618:0x24a5d8f0,
        0x342624:0x8c8301a8,0x342634:0x14650018}
    for va,word in anchors.items():
        require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0]==word,f'native anchor mismatch {va:#x}')
    off=image.to_offset(0x4b77a0)
    require(image.blob[off:].split(b'\0',1)[0]==b'..\\FPB\\%08d.fpb','FPB path mismatch')
    return dict(binding=binding,loader_va='0x3007c0',getter_va='0x342560',
        exact_words={hex(k):hex(v) for k,v in anchors.items()},
        format='u32 count, count triples (key,offset,length), u32 pool_size, pool',
        header_record_offset=4,array_offsets=['0x19c','0x1a8'],record_stride=16,
        key_threshold=10000,second_array_key_subtraction=10000,
        first_match=True,static_binding_verified=True,runtime_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True);p.add_argument('--ship',type=Path,required=True)
    p.add_argument('--corpus',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();raw=a.elf.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==ELF_SHA256,'original ELF fingerprint mismatch')
    corpus=json.loads(a.corpus.read_text('utf8'));resources={r['resource']:r for r in corpus['resources']}
    archive=Afs.open(a.ship);names=filename_toc(archive);rows=[];failed=[]
    with a.ship.open('rb') as f:
        for i,name in enumerate(names):
            if not name.endswith('.fpb'):continue
            blob=archive.read_entry(i,f)
            try:records,pool=native_records(blob)
            except ValueError as e:failed.append(dict(resource=name,error=str(e)));continue
            resource=resources.get('SHIP/'+name)
            if resource:require(hashlib.sha256(blob).hexdigest()==resource['sha256'],'FPB source fingerprint mismatch')
            key,offset,length=records[0]
            links=[e['id'] for e in (resource or {}).get('entries',[]) if e.get('offset')==offset and e.get('source_bytes')==length]
            rows.append(dict(resource='SHIP/'+name,source_sha256=hashlib.sha256(blob).hexdigest(),
                header_key=key,header_offset=offset,header_length=length,records=len(records),
                header_source_sha256=hashlib.sha256(pool[offset:offset+length]).hexdigest(),
                existing_geometry_links=links,
                duplicate_keys=sorted({k for k,_,_ in records if sum(r[0]==k for r in records)>1})))
    report=dict(native_evidence=native_evidence(ElfImage(raw)),parsed=len(rows),failed=failed,
        nonzero_header_keys=sum(r['header_key']!=0 for r in rows),resources=rows,
        source_modified=False,legacy_catalog_ids_changed=False,runtime_verified=False)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n','utf8')
    require(json.loads(a.out.read_text('utf8'))==report,'audit output readback mismatch')
    print(f"NATIVE_PLAYBOOK_PASS parsed={len(rows)} failed={len(failed)} nonzero_header_keys={report['nonzero_header_keys']} static_binding=true runtime_verified=false")


if __name__=='__main__':main()
