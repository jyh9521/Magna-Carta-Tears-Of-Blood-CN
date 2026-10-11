"""Bind native FieldTextData keys to source TUI records, not physical ordinals."""
from pathlib import Path
import argparse,json,struct,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from audit_text_slicing import scalar
from extract_script_buffers import FILE_HASH
import font_poc as core

def exact(image,words):
 for va,word in words.items():require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0]==word,'native field anchor mismatch '+hex(va))
 return {hex(k):hex(v) for k,v in words.items()}

def native_binding(image):
 binding=bind_inline(image,'intUMrtsUIInfoexecGetFieldTextData');require(binding['callback']=='0x3f2c90','unexpected field callback')
 require({'va':'0x3f2dac','target':'0x3f2e00'} in binding['bounded_callback_jals'],'field callback helper mismatch')
 anchors={0x30ac44:0x3c05004b,0x30ac4c:0x24a57990,0x30aca0:0x0320f809,0x30aca4:0x24060004,
  0x30acb8:0x0320f809,0x30acbc:0x24060004,0x30acc0:0xae00013c,0x30acc8:0xae000140,
  0x30ad10:0x2604013c,0x30ad18:0x2405001c,0x30ad24:0x0c0c7520,0x30ad28:0x2605013c,
  0x30ad50:0x001318c0,0x30ad54:0x00731823,0x30ad58:0x8e02013c,0x30ad5c:0x00031880,
  0x30ad64:0x24060004,0x30ad6c:0x00438821,0x30ad70:0x0320f809,0x30ad74:0x0220282d,
  0x30ad88:0x0320f809,0x30ad8c:0x24060100,0x30ad94:0x26240004,0x30adb0:0x0c069530,
  0x30ae1c:0x0320f809,0x30ae20:0x24060100,0x30ae28:0x26240010,0x30ae44:0x0c069530,
  0x3f2e20:0x8c84002c,0x3f2e28:0x0c0c49e8,0x3f2e2c:0x27a6005c,0x3f2e44:0x2464013c,
  0x3f2e48:0x8c630140,0x3f2e5c:0x000520c0,0x3f2e60:0x00852023,0x3f2e64:0x00042080,
  0x3f2e6c:0x24730004,0x3f2ed8:0x24710010,0x1a54c0:0x03e00008,0x1a54c4:0x0080102d}
 # Verify the complete lookup helper, including its compare against the stored key.
 lookup_words=[0x8c870140,0x1000000d,0x0000402d,0x8c82013c,0x000818c0,0x00681823,
  0x00031880,0x00431021,0x8c420000,0x14a20004,0,0xacc80000,0x10000005,0x24020001,
  0x25080001,0x0107102a,0x1440fff2,0x0000102d,0x03e00008,0]
 anchors.update({0x3127a0+i*4:w for i,w in enumerate(lookup_words)})
 path=image.blob[image.to_offset(0x4b7990):].split(b'\0',1)[0];require(path==b'..\\UIText\\00001240.tui','field source path mismatch')
 return dict(binding=binding,loader='0x30ac40',lookup='0x3127a0',getter_helper='0x3f2e00',array_offset='0x13c',count_offset='0x140',record_stride=28,record_key_offset=0,main_offset=4,help_offset=16,exact_words=exact(image,anchors),key_not_ordinal=True,buffer_conversion='0x1a54c0 returns a0 unchanged in JR delay slot',runtime_verified=False)

def run_lookup(image,keys,key):
 memory={}
 def put(at,b):memory.update({at+i:c for i,c in enumerate(b)})
 put(0x8000+0x13c,struct.pack('<II',0x9000,len(keys)));put(0xa000,struct.pack('<I',0xffffffff))
 for i,k in enumerate(keys):put(0x9000+i*28,struct.pack('<I',k)+bytes(24))
 result=scalar(image,0x3127a0,0x3127e8,{4:0x8000,5:key,6:0xa000},memory)
 return dict(found=bool(result['registers'][2]),index=struct.unpack('<I',bytes(memory[0xa000+i] for i in range(4)))[0],steps=result['steps'])

def characterize(image):
 cases=0
 for keys in ([],[0],[2,1,8],[238,300,301,303],[9,9,1],list(range(0,128,3))):
  for key in [-1,0,1,2,8,9,128,238,300,301,303,*keys]:
   actual=run_lookup(image,keys,key);expected=next((i for i,k in enumerate(keys) if k==key),None)
   require(actual['found']==(expected is not None),'lookup found mismatch');require(actual['index']==(expected if expected is not None else 0xffffffff),'lookup ordinal mismatch');cases+=1
 return cases

def source_key_index(corpus):
 rows={}
 for r in corpus['resources']:
  if r['resource']!='SHIP/00001240.tui':continue
  for e in r['entries']:
   pair=(e['record_id'],e['half']);require(pair not in rows,'duplicate native field key/half');rows[pair]=e
 require(rows,'field source records missing');return rows

def bind_calls(calls,index):
 rows=[];dynamic=[]
 for q in calls:
  if q['call']['symbols']!=['GetFieldTextData']:continue
  tree=q['tree'];positions=[i for i,t in enumerate(tree) if t['offset']==q['call']['offset']];require(len(positions)==1,'field call token ambiguous');i=positions[0]
  require(i+1<len(tree),'field argument missing');arg=tree[i+1]
  require(arg['depth']==tree[i]['depth']+1,'field argument depth mismatch')
  if 'int' not in arg:dynamic.append(dict(id=q['id'],call_offset=q['call']['offset'],argument=arg));continue
  key=arg['int'];require((key,0) in index and (key,1) in index,'literal native field key missing')
  main,help=index[key,0],index[key,1]
  rows.append(dict(id=q['id'],function=q['function'],call_offset=q['call']['offset'],key=key,
   main_id=main['id'],help_id=help['id'],physical_index=main['record_index'],main_source_sha256=main['source_sha256'],help_source_sha256=help['source_sha256'],key_differs_from_ordinal=key!=main['record_index'],execution_verified=False))
 return rows,dynamic

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('elf','ship','corpus','calls','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();raw=a.elf.read_bytes();require(core.digest(raw)==ELF_SHA256,'original ELF mismatch');image=ElfImage(raw)
 calls=json.loads(a.calls.read_text('utf8'));corpus=json.loads(a.corpus.read_text('utf8'));index=source_key_index(corpus)
 require(calls['file_sha256']==FILE_HASH,'call source FILE mismatch')
 require(core.file_digest(a.ship)=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','original SHIP mismatch')
 data=dict(core.archive_entries(a.ship)[1])['00001240.tui']
 source=next(r for r in corpus['resources'] if r['resource']=='SHIP/00001240.tui')
 require(core.digest(data)==source['sha256'],'source field resource mismatch')
 for (key,half),e in index.items():
  require(struct.unpack_from('<I',data,8+516*e['record_index'])[0]==key,'source native key mismatch')
  require(e['offset']==12+516*e['record_index']+256*half,'source native field geometry mismatch')
  require(core.digest(data[e['offset']:e['offset']+e['source_bytes']])==e['source_sha256'],'source native field hash mismatch')
 evidence=native_binding(image);cases=characterize(image);bound,dynamic=bind_calls(calls['calls'],index)
 report=dict(elf_sha256=ELF_SHA256,corpus_sha256=core.file_digest(a.corpus),calls_sha256=core.file_digest(a.calls),native=evidence,scalar_cases=cases,literal_calls=bound,dynamic_calls=dynamic,source_modified=False,runtime_verified=False)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(f'NATIVE_FIELD_KEY_PASS literal_calls={len(bound)} dynamic_calls={len(dynamic)} key_not_ordinal={sum(x["key_differs_from_ordinal"] for x in bound)} scalar_cases={cases} buffer_conversion_identity=true runtime_verified=false')
if __name__=='__main__':main()
