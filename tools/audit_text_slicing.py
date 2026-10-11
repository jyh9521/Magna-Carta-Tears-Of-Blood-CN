"""Execute version-locked scalar slicing fragments on synthetic mapped byte strings.

This is bounded instruction evidence, not a game execution or allocation model.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from research_native import ElfImage,ELF_SHA256
MASK64=(1<<64)-1

def require(condition,message):
 if not condition:raise ValueError(message)

def signed(value,bits=32):
 value&=(1<<bits)-1;return value-(1<<bits) if value>>(bits-1) else value

def scalar(image,start,stop,registers,memory,limit=10000):
 regs=[0]*32
 for k,v in registers.items():regs[k]=v&MASK64
 pc=start;pending=None;steps=0
 def read(addr,size):
  if any(addr+i not in memory for i in range(size)):raise ValueError('scalar memory access outside supplied fixture')
  return int.from_bytes(bytes(memory[addr+i] for i in range(size)),'little')
 while pc!=stop:
  if steps>=limit:raise ValueError('scalar instruction bound exceeded')
  steps+=1;word=struct.unpack_from('<I',image.blob,image.to_offset(pc))[0];op=word>>26;rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31;shift=(word>>6)&31;fn=word&63;imm=word&65535;old_pending=pending;pending=None;branch=None
  if word==0:pass
  elif op==9:regs[rt]=(regs[rs]+signed(imm,16))&0xffffffff
  elif op==12:regs[rt]=regs[rs]&imm
  elif op==15:regs[rt]=imm<<16
  elif op==32:regs[rt]=signed(read((regs[rs]+signed(imm,16))&0xffffffff,1),8)&MASK64
  elif op==35:regs[rt]=read((regs[rs]+signed(imm,16))&0xffffffff,4)
  elif op==43:
   addr=(regs[rs]+signed(imm,16))&0xffffffff
   if any(addr+i not in memory for i in range(4)):raise ValueError('scalar memory write outside supplied fixture')
   for i,b in enumerate((regs[rt]&0xffffffff).to_bytes(4,'little')):memory[addr+i]=b
  elif op==0 and fn==0:regs[rd]=(regs[rt]<<shift)&0xffffffff
  elif op==0 and fn==0x21:regs[rd]=(regs[rs]+regs[rt])&0xffffffff
  elif op==0 and fn==0x2d:regs[rd]=(regs[rs]+regs[rt])&MASK64
  elif op==0 and fn==0x23:regs[rd]=(regs[rs]-regs[rt])&0xffffffff
  elif op==0 and fn==0x24:regs[rd]=regs[rs]&regs[rt]
  elif op==0 and fn==0x2a:regs[rd]=int(signed(regs[rs])<signed(regs[rt]))
  elif op==0 and fn==0x3c:regs[rd]=(regs[rt]<<(shift+32))&MASK64
  elif op==0 and fn==0x3f:regs[rd]=(signed(regs[rt],64)>>(shift+32))&MASK64
  elif op==0 and fn==0x0a:
   if regs[rt]==0:regs[rd]=regs[rs]
  elif op in (4,5):
   condition=(regs[rs]==regs[rt]) if op==4 else (regs[rs]!=regs[rt]);branch=pc+4+4*signed(imm,16) if condition else pc+8
  elif op==1 and rt==1:branch=pc+4+4*signed(imm,16) if signed(regs[rs])>=0 else pc+8
  else:raise ValueError('unsupported scalar instruction at '+hex(pc)+' word='+hex(word))
  regs[0]=0
  if old_pending is not None:
   if branch is not None:raise ValueError('transfer in scalar delay slot')
   pc=old_pending
  else:
   pc+=4
   if branch is not None:pending=branch
 return dict(registers=regs,steps=steps)

def fixture_memory(data):
 memory={0x9000+i:b for i,b in enumerate(data+b'\0')}
 for i,b in enumerate(struct.pack('<II',0x9000,len(data)+1)):memory[0x8000+i]=b
 return memory

def left_character_boundary(image,data,count):
 x=scalar(image,0x187ee8,0x187f40,{7:0x9000,5:0x8000,3:len(data)+1,6:count},fixture_memory(data));return x['registers'][6]

def mid_character_span(image,data,start,count=65535):
 x=scalar(image,0x188138,0x1881d4,{9:0x9000,5:0x8000,4:len(data)+1,6:start,7:count},fixture_memory(data));return x['registers'][6],x['registers'][7]

def left_byte_boundary(image,data,count):
 x=scalar(image,0x188034,0x188064,{5:0x8000,6:count},fixture_memory(data));return x['registers'][6]

def characterize(image):
 rows=[]
 for length in range(0,33):
  data=b''.join((b'A' if i%3==0 else bytes([0xb0+i%16,0xa1+i%32])) for i in range(length))
  ends=[0];i=0
  while i<len(data):i+=2 if data[i]&128 else 1;ends.append(i)
  for n in range(-2,length+3):
   expected=ends[min(max(n,0),length)];actual=left_character_boundary(image,data,n);require(actual==expected,'original character boundary mismatch');require(left_byte_boundary(image,data,n)==min(max(n,0),len(data)),'original byte clamp mismatch');start,span=mid_character_span(image,data,n);require(start==expected and span==len(data)-expected,'original MidA span mismatch')
   for count in (0,1,3,65535):
    a,b=mid_character_span(image,data,n,count);require(a==expected and b==ends[min(max(n,0)+count,length)]-expected,'original MidA count mismatch')
   rows.append(dict(characters=length,request=n,byte_boundary=actual))
 return dict(cases=len(rows),source_instruction_execution=True,allocation_and_game_execution_verified=False)

def registration_evidence(image):
 def word(va):return struct.unpack_from('<I',image.blob,image.to_offset(va))[0]
 def pointer_slot(address):
  hits=[]
  for va in range(0x4d2000,0x4d4000,4):
   a,b,c=word(va),word(va+4),word(va+8)
   if a>>26!=15 or (a>>16)&31!=3 or b>>26!=9 or (b>>21)&31!=3 or (b>>16)&31!=3 or c>>26!=31 or (c>>21)&31!=29 or (c>>16)&31!=3:continue
   value=((a&65535)<<16)+signed(b&65535,16)
   if value==address:hits.append((va,c&65535))
  if len(hits)!=1:raise ValueError('ambiguous initializer pointer slot')
  return hits[0]
 rows=[]
 for name,source,table,callback,callee in [('LeftA',0x47b6c0,0x47c910,0x197190,0x187ea0),('MidA',0x47b6b0,0x47c900,0x196fa0,0x1880f0),('Left',0x47b640,0x47c890,0x196560,0x188020),('Mid',0x47b630,0x47c880,0x1963d0,0x1823b0)]:
  expected=('intUObjectexec'+name).encode('ascii')+b'\0';off=image.to_offset(word(table));require(image.blob[off:off+len(expected)]==expected,'method identifier mismatch')
  require([word(source+i) for i in (0,4,8)]==[0,0xffffffff,callback],'method source descriptor mismatch')
  src_va,src_slot=pointer_slot(source);dst_va,dst_slot=pointer_slot(table+4)
  sequence=[0x7bb90000|src_slot,0xc7220000,0xc7210004,0xc7200008,0x7bb90000|dst_slot,0xe7220000,0x7bb90000|dst_slot,0xe7210004,0x7bb90000|dst_slot,0xe7200008]
  matches=[va for va in range(0x4d5000,0x4d6500,4) if [word(va+i*4) for i in range(len(sequence))]==sequence];require(len(matches)==1,'method descriptor copy not exact')
  callsites=[va for va in range(callback,callback+0x300,4) if word(va)>>26==3 and ((word(va)&0x3ffffff)<<2)==callee];require(bool(callsites),'callback does not call scalar helper')
  rows.append(dict(name=name,source_descriptor=hex(source),name_table=hex(table),callback=hex(callback),callee=hex(callee),initializer_source=hex(src_va),initializer_destination=hex(dst_va),exact_copy_window=hex(matches[0]),callee_calls=[hex(v) for v in callsites],static_descriptor_copy_verified=True,initializer_execution_verified=False))
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();blob=a.elf.read_bytes();require(hashlib.sha256(blob).hexdigest()==ELF_SHA256,'original ELF fingerprint mismatch');image=ElfImage(blob);summary=characterize(image)
 windows=[(0x187ee8,0x187f44),(0x188034,0x188068),(0x188138,0x1881d8),(0x4d39b8,0x4d39d0),(0x4d5df0,0x4d5e18)]
 report=dict(elf_sha256=ELF_SHA256,summary=summary,registrations=registration_evidence(image),windows=[dict(start=hex(s),end=hex(e),sha256=hashlib.sha256(blob[image.to_offset(s):image.to_offset(e)]).hexdigest()) for s,e in windows]);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n','utf8');print('TEXT_SLICING_SCALAR_PASS '+json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
