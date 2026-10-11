"""Version-locked native text-list key lookup characterization."""
from pathlib import Path
import struct,json,argparse,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from audit_text_slicing import scalar
LOOKUP_WORDS=[0x8c870000,0x1000000d,0x0000402d,0x8c820000,0x000818c0,0x00681823,0x00031880,0x00431021,0x8c420000,0x14a20004,0,0xacc80000,0x10000005,0x24020001,0x25080001,0x0107102a,0x1440fff2,0x0000102d,0x03e00008,0]
PROFILES=[('GetStoreTextDataIndex',0x312e80,0x312f60,0x148),('GetDivinationTextDataIndex',0x3130e0,0x3131c0,0x160),('GetGymTextDataIndex',0x313210,0x3132f0,0x16c),('GetRoadSignTextDataIndex',0x3135a0,0x313680,0x190),('GetPilotTextDataIndex',0x3136d0,0x3137b0,0x19c)]
def expected_words(array_offset):
 require(0<=array_offset<=0x7ffb,'array offset out of bounded range');words=list(LOOKUP_WORDS);words[0]|=array_offset+4;words[3]|=array_offset;return words

def validate_lookup(image,va,array_offset):
 words=expected_words(array_offset);actual=[struct.unpack_from('<I',image.blob,image.to_offset(va+i*4))[0] for i in range(20)];require(actual==words,'native key lookup instruction mismatch');return words

def run_lookup(image,va,array_offset,keys,key):
 validate_lookup(image,va,array_offset);memory={}
 def put(at,data):memory.update({at+i:b for i,b in enumerate(data)})
 put(0x8000+array_offset,struct.pack('<II',0x9000,len(keys)));put(0xa000,struct.pack('<I',0xffffffff))
 for i,k in enumerate(keys):put(0x9000+i*28,struct.pack('<I',k)+bytes(24))
 result=scalar(image,va,va+72,{4:0x8000,5:key,6:0xa000},memory)
 return dict(found=bool(result['registers'][2]),index=struct.unpack('<I',bytes(memory[0xa000+i] for i in range(4)))[0],steps=result['steps'])

def characterize(image,va,array_offset):
 count=0
 for keys in ([],[0],[2,1,8],[238,300,301,303],[9,9,1],list(range(0,128,3))):
  for key in [-1,0,1,2,8,9,128,238,300,301,303,*keys]:
   actual=run_lookup(image,va,array_offset,keys,key);expected=next((i for i,k in enumerate(keys) if k==key),None);require(actual['found']==(expected is not None) and actual['index']==(expected if expected is not None else 0xffffffff),'native key lookup fixture mismatch');count+=1
 return count

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raw=a.elf.read_bytes();require(hashlib.sha256(raw).hexdigest()==ELF_SHA256,'original ELF mismatch');image=ElfImage(raw);rows=[]
 for name,callback,lookup,array_offset in PROFILES:
  b=bind_inline(image,'intUMrtsDataManagerexec'+name);require(int(b['callback'],16)==callback,'native index callback mismatch');require(any(int(x['target'],16)==lookup for x in b['bounded_callback_jals']),'native index helper call missing');words=validate_lookup(image,lookup,array_offset);cases=characterize(image,lookup,array_offset);rows.append(dict(method=name,binding=b,lookup=hex(lookup),array_offset=hex(array_offset),count_offset=hex(array_offset+4),stride=28,key_offset=0,main_offset=4,help_offset=16,words=[hex(w) for w in words],scalar_cases=cases,key_not_ordinal=True))
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(dict(elf_sha256=ELF_SHA256,methods=rows,runtime_verified=False),indent=2)+'\n','utf8');print('NATIVE_TEXT_INDEX_PASS methods='+str(len(rows))+' scalar_cases='+str(sum(x['scalar_cases'] for x in rows))+' key_not_ordinal=true runtime_verified=false')
if __name__=='__main__':main()
