"""Bind native PMF registration through a bounded R5900 stack-spill copy.

Only the observed low-word pointer/SQ/LQ/LWC1/SWC1 initializer grammar is
supported. Calls, branches and unknown instructions fail before a binding is
returned. This is static dataflow, not initializer or callback execution.
"""
from pathlib import Path
import argparse, hashlib, json, struct, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from research_native import ElfImage, ELF_SHA256
from audit_native_method_registration import require

def trace(image,start,end,destinations):
    require(type(start) is int and type(end) is int and start%4==end%4==0
        and 0<end-start<=65536 and bool(destinations),'invalid bounded initializer range')
    registers={0:0,29:0x10000000};fp={};memory={};stores={};instructions=[]
    def read(address):
        if address in memory:return memory[address]
        at=image.to_offset(address)
        require(at+4<=len(image.blob),'initializer source word bounds')
        return struct.unpack_from('<I',image.blob,at)[0],address
    for va in range(start,end,4):
        at=image.to_offset(va);word=struct.unpack_from('<I',image.blob,at)[0]
        instructions.append(dict(va=hex(va),word=hex(word)))
        op=word>>26;rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31
        low=word&65535;low=low-65536 if low&32768 else low
        base=registers.get(rs);address=(base+low)&0xffffffff if base is not None else None
        if word==0:pass
        elif op==15 and rs==0:registers[rt]=(word&65535)<<16
        elif op==9:registers[rt]=address
        elif op==0 and word&63 in (0x21,0x2d) and (word>>6)&31==0:
            a,b=registers.get(rs),registers.get(rt)
            registers[rd]=(a+b)&0xffffffff if a is not None and b is not None else None
        elif op in (0x1f,0x3f):
            require(rs==29 and address is not None,'only stack SQ/SD supported')
            memory[address]=(registers.get(rt),None)
        elif op in (0x1e,0x37):
            require(rs==29 and address in memory,'unknown/nonstack LQ/LD source')
            registers[rt]=memory[address][0]
        elif op==0x31:
            require(address is not None,'unknown LWC1 source pointer');fp[rt]=read(address)
        elif op==0x39:
            require(address is not None and rt in fp,'unknown SWC1 copy')
            value,source=fp[rt];memory[address]=(value,source)
            if address in destinations:
                require(address not in stores and source is not None and value is not None,'ambiguous/unbound descriptor word copy')
                stores[address]=dict(store_va=hex(va),destination=hex(address),source_word_va=hex(source),value=hex(value))
        else:raise ValueError('unsupported initializer instruction '+hex(va)+' '+hex(word))
        registers[0]=0
    require(set(stores)==set(destinations),'initializer range does not bind all descriptor words')
    return stores,instructions

def bind(image,identifiers,start,end):
    require(identifiers and len(set(identifiers))==len(identifiers),'duplicate/empty identifiers')
    tables={};blob=image.blob
    for name in identifiers:
        require(name.startswith('intU') and 'exec' in name,'qualified native identifier required')
        needle=name.encode('ascii')+b'\0';strings=[];at=0
        while (at:=blob.find(needle,at))>=0:
            if at==0 or blob[at-1]==0:strings.append(at)
            at+=1
        require(len(strings)==1,'missing/ambiguous native identifier')
        string_va=image.to_va(strings[0]);pointer=struct.pack('<I',string_va)
        hits=[at for at in range(0,len(blob)-15,4) if blob[at:at+4]==pointer and blob[at+4:at+16]==bytes(12)]
        require(len(hits)==1,'uninitialized native name table missing/ambiguous')
        tables[name]=image.to_va(hits[0])
    stores,instructions=trace(image,start,end,{va+i for va in tables.values() for i in (4,8,12)})
    rows=[]
    for name,va in tables.items():
        copied=[stores[va+i] for i in (4,8,12)];values=[int(q['value'],16) for q in copied]
        source=[int(q['source_word_va'],16) for q in copied]
        require(values[:2]==[0,0xffffffff] and values[2] and source==[source[0]+i for i in (0,4,8)],'unsupported/noncontiguous PMF descriptor')
        image.to_offset(values[2]);rows.append(dict(identifier=name,name_table=hex(va),source_descriptor=hex(source[0]),callback=hex(values[2]),descriptor_words=[hex(v) for v in values],word_copies=copied,static_copy_verified=True,initializer_execution_verified=False,callback_execution_verified=False))
    return dict(initializer_start=hex(start),initializer_end=hex(end),instructions=instructions,methods=rows,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--identifier',action='append',required=True);p.add_argument('--start',type=lambda s:int(s,0),required=True);p.add_argument('--end',type=lambda s:int(s,0),required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.elf.read_bytes();require(hashlib.sha256(raw).hexdigest()==ELF_SHA256,'original ELF mismatch')
    result=bind(ElfImage(raw),a.identifier,a.start,a.end);result['elf_sha256']=ELF_SHA256;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n','utf8');require(json.loads(a.out.read_text('utf8'))==result,'native stack output reopen mismatch');print('NATIVE_STACK_REGISTRATION_PASS methods='+str(len(result['methods']))+' exact_stack_copy=true unknown_ops=false runtime_verified=false')
if __name__=='__main__':main()
