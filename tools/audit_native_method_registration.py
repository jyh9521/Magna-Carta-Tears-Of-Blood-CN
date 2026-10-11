"""Bind qualified method identifiers through exact inline 12-byte PMF copies.

This version-locked static audit supports the observed a0/v1 inline initializer
template, not every compiler's registration scheme or actual initialization.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from research_native import ElfImage,ELF_SHA256


def require(condition,message):
    if not condition:raise ValueError(message)


def pointer(upper,lower,register):
    require(upper>>26==15 and (upper>>21)&31==0 and (upper>>16)&31==register,'pointer LUI mismatch')
    require(lower>>26==9 and (lower>>21)&31==register and (lower>>16)&31==register,'pointer ADDIU mismatch')
    low=lower&65535
    return (((upper&65535)<<16)+(low-65536 if low&32768 else low))&0xffffffff


def bind_inline(image,identifier,*,callback_limit=512):
    require(isinstance(callback_limit,int) and not isinstance(callback_limit,bool) and 8<=callback_limit<=65536 and callback_limit%4==0,
            "callback window must be an aligned integer from8 to65536bytes")
    raw=identifier.encode('ascii')+b'\0';blob=image.blob
    require(identifier.startswith('intU') and 'exec' in identifier,'qualified native identifier required')
    strings=[];start=0
    while (off:=blob.find(raw,start))>=0:
        start=off+1
        if off==0 or blob[off-1]==0:strings.append(off)
    require(len(strings)==1,'qualified method identifier missing or ambiguous')
    string_va=image.to_va(strings[0]);tables=[];start=0
    while (off:=blob.find(struct.pack('<I',string_va),start))>=0:
        start=off+1
        if off%4==0 and blob[off+4:off+16]==bytes(12):tables.append(image.to_va(off))
    require(len(tables)==1,'uninitialized method name table missing or ambiguous')
    table=tables[0];copies=[]
    tail=(0xc4820000,0xc4810004,0xc4800008,0xe4620000,0xe4610004,0xe4600008)
    for off in range(0,len(blob)-39,4):
        words=struct.unpack_from('<10I',blob,off)
        if words[4:]!=tail:continue
        try:source=pointer(words[0],words[1],4);destination=pointer(words[2],words[3],3)
        except ValueError:continue
        if destination!=table+4:continue
        descriptor=struct.unpack_from('<3I',blob,image.to_offset(source))
        require(descriptor[:2]==(0,0xffffffff) and descriptor[2]!=0,'unsupported method source descriptor')
        image.to_offset(descriptor[2])
        copies.append(dict(copy_va=hex(image.to_va(off)),source_descriptor=hex(source),
                           descriptor_words=[hex(w) for w in descriptor],callback=hex(descriptor[2]),
                           exact_instruction_words=[hex(w) for w in words]))
    require(len(copies)==1,'exact inline method descriptor copy missing or ambiguous')
    result=dict(identifier=identifier,string_va=hex(string_va),name_table=hex(table),**copies[0],
                static_copy_verified=True,initializer_execution_verified=False)
    callback=int(result['callback'],16);calls=[];end=None
    for at in range(callback,callback+callback_limit-4,4):
        word=struct.unpack_from('<I',blob,image.to_offset(at))[0]
        if word>>26==3:calls.append(dict(va=hex(at),target=hex(((at+4)&0xf0000000)|((word&0x3ffffff)<<2))))
        if word==0x03e00008:
            image.to_offset(at+7)
            end=at+8;break
    require(end is not None,'callback return not found within bounded window')
    result.update(callback_scan_limit=callback_limit,callback_end=hex(end),callback_sha256=hashlib.sha256(blob[image.to_offset(callback):image.to_offset(end-1)+1]).hexdigest(),
                  bounded_callback_jals=calls,callback_execution_verified=False)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--identifier',action='append',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--callback-limit',type=int,default=512,help='Explicit aligned static return-scan bound; never expanded automatically')
    a=p.parse_args();raw=a.elf.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==ELF_SHA256,'original ELF fingerprint mismatch')
    image=ElfImage(raw);rows=[bind_inline(image,name,callback_limit=a.callback_limit) for name in a.identifier]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(dict(elf_sha256=ELF_SHA256,methods=rows,runtime_verified=False),indent=2)+'\n','utf8')
    print('NATIVE_METHOD_REGISTRATION_PASS methods='+str(len(rows))+' exact_inline_copy=true runtime_verified=false')


if __name__=='__main__':main()
