"""Version-locked named resource storage andnumeric lookup evidence.

Static loader/lookup/compiled producer checks are separate from event reachability.
"""
from pathlib import Path
import json,struct,argparse,sys
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','lib')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from audit_text_slicing import scalar
from font_poc import archive_entries,digest
SPECS={
 '00000460.cha':dict(sha256='bf86e54bcbb7c0fa9698a63be5ee41a7e6d05b43c9ecb23793441ccbfc079ef1',count=301,kind=11,stride=299,fields=[(4,255,44)],array=40,native_stride=56,loader=0x30afe0,path=0x4b79b0,path_text=b'..\\CharData\\00000460.cha',callback=0x310070,identifier='intUMrtsDataManagerexecGetCharData',stride_start=0x310190,stride_stop=0x3101a4,index_reg=7,this_reg=17,result_reg=16),
 '00000466.abi':dict(sha256='47ac38102c32aa596e6f501585f5bd36eef82eeb6d7fc9f140aec5f6680baf57',count=358,kind=7,stride=192,fields=[(4,40,4),(64,128,36)],array=76,native_stride=48,loader=0x30cec0,path=0x4b7a70,path_text=b'..\\ABI\\00000466.abi',callback=0x310300,identifier='intUMrtsDataManagerexecGetSkillData',stride_start=0x31049c,stride_stop=0x3104b0,index_reg=5,this_reg=17,result_reg=21),
 '00000953.itm':dict(sha256='33b630a4ff776d97f137913ce379a5d36dfbe365f6ef282f126b75d0230ab617',count=479,kind=25,stride=594,fields=[(4,255,12),(331,255,80)],array=148,native_stride=100,loader=0x2fdb00,path=0x4b76a0,path_text=b'..\\Item\\00000953.itm',callback=0x30fdd0,identifier='intUMrtsDataManagerexecGetItemData',stride_start=0x2fe578,stride_stop=0x2fe59c,index_reg=5,this_reg=4,result_reg=2)}
ANCHORS={
 0x30b0f0:0x0320f809,0x30b0f4:0x0200282d,0x30b108:0x0320f809,0x30b10c:0x240600ff,0x30b130:0x0c069530,0x30b134:0x27a40060,0x30b164:0x2604002c,
 0x310184:0x8ca5002c,0x3101a4:0x8e020000,0x3101a8:0x14c20027,0x3100d8:0x0c0c405c,0x3100f0:0x2604002c,0x310140:0x0c0c3e48,
 0x30cf94:0x0320f809,0x30cf98:0x0220282d,0x30cfac:0x0320f809,0x30cfb0:0x24060028,0x30cfe8:0x26240004,0x30d098:0x0320f809,0x30d09c:0x24060080,0x30d0d4:0x26240024,
 0x310490:0x8e240050,0x3104b0:0x8ea20000,0x3104b4:0x16020018,0x3104d0:0x26a50004,0x3104dc:0x26a50024,0x310368:0x0c0c40fc,
 0x2fdc4c:0x0320f809,0x2fdc50:0x0240282d,0x2fdcf4:0x0320f809,0x2fdcf8:0x240600ff,0x2fdd30:0x2644000c,0x2fdf78:0x0320f809,0x2fdf7c:0x240600ff,0x2fdfb4:0x26440050,
 0x2fdc90:0x1682000b,0x2fdca8:0xac540008,
 0x2fe54c:0x14a30003,0x2fe578:0x8c820094,0x2fe5a0:0,0x30fe5c:0x0c0bf944,0x30fe7c:0x2665000c,0x30fe98:0x26650050}

def validate_anchors(image):
 for va,w in ANCHORS.items():require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0]==w,'named resource anchor mismatch '+hex(va))

def stride_address(image,name,index):
 s=SPECS[name];require(type(index) is int and 0<=index<s['count'],'bounded physical index required');mem={0x8000+s['array']+i:b for i,b in enumerate(struct.pack('<I',0x9000))};result=scalar(image,s['stride_start'],s['stride_stop'],{s['this_reg']:0x8000,s['index_reg']:index},mem);address=result['registers'][s['result_reg']];require(address==0x9000+s['native_stride']*index,'named native stride mismatch');return address

def item_hash_fixture(keys):
 # Exact numeric hash-node geometry; missing keys return original fallback data.
 require(all(type(k) is int and 0<=k<2**32 for k in keys),'u32keys required');mem={};nodes=[];by={};buckets=[0xffffffff]*8
 for physical,key in enumerate(keys):
  if key in by:nodes[by[key]][2]=physical
  else:
   node=len(nodes);bucket=key&7;nodes.append([buckets[bucket],key,physical]);by[key]=node;buckets[bucket]=node
 def put(at,values):
  for i,b in enumerate(struct.pack('<'+'I'*len(values),*values)):mem[at+i]=b
 put(0x8808,[0xa000]);put(0x8814,[0x9000,8]);put(0x8094,[0xc000]);put(0x9000,buckets)
 for i,node in enumerate(nodes):put(0xa000+12*i,node)
 return mem

def item_lookup(image,keys,key):
 result=scalar(image,0x2fe510,0x2fe59c,{4:0x8000,5:key},item_hash_fixture(keys));return result['registers'][2]

def compiled_roles(objects):
 by={o['id']:o for o in objects};required={'FILE/MrtsGame.u/export/10975':{113:'ShowChatMessageBox',121:'Name',124:'CharData',161:'Name',164:'ItemData'},'FILE/MrtsGame.u/export/11048':{306:'GetSkillData',313:'Skill',316:'StyleData',324:'Name',327:'SkillData',343:'AddList',346:'Name',349:'SkillData',352:'Comment',355:'SkillData'},'FILE/MrtsGame.u/export/12107':{214:'GetSkillData',221:'Skill',224:'StyleData',260:'AddList',263:'Name',266:'SkillData',269:'Comment',272:'SkillData'}};out=[]
 for identity,checks in required.items():
  require(identity in by,'named consumer object missing');obj=by[identity];ts={t['offset']:t for t in obj['tokens']}
  for at,label in checks.items():require(ts[at].get('field')==label or ts[at].get('symbols')==[label],'named consumer token mismatch')
  out.append(obj)
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('elf','ship','consumers','profile','out'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'original ELF mismatch');image=ElfImage(raw);validate_anchors(image);require(digest(a.ship.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','original SHIP mismatch');ship=dict(archive_entries(a.ship)[1]);profiles=json.loads(a.profile.read_text('utf8'));records={};methods=[];cases=0
 for name,s in SPECS.items():
  data=ship[name];require(digest(data)==s['sha256'] and len(data)==8+s['count']*s['stride'] and struct.unpack_from('<II',data)==(s['count'],s['kind']),'named source geometry/hash mismatch');require(image.blob[image.to_offset(s['path']):].split(b'\0',1)[0]==s['path_text'],'named loader path mismatch');require(struct.unpack_from('<I',raw,image.to_offset(s['loader']+4))[0]==0x3c05004b and struct.unpack_from('<I',raw,image.to_offset(s['loader']+12))[0]==0x24a50000|(s['path']&65535),'named loader path instructions mismatch');b=bind_inline(image,s['identifier'],callback_limit=1024);require(int(b['callback'],16)==s['callback'],'named callback mismatch');methods.append(b);rows=[]
  for i in range(s['count']):
   stride_address(image,name,i);cases+=1;at=8+i*s['stride'];key=struct.unpack_from('<I',data,at)[0];rows.append(dict(physical_index=i,key=key,fields=[dict(offset=at+off,capacity=cap,native_string_offset=native,source_sha256=digest(data[at+off:at+off+cap].split(b'\0',1)[0])) for off,cap,native in s['fields']]))
  records[name]=rows
 source_bindings=[]
 for b in profiles['bindings']:
  name=Path(b['source_resource']).name;s=SPECS[name];row=records[name][b['physical_index']];field=row['fields'][b['field']];require(b['source_record_key']==row['key'],'named source key mismatch');require(b['source_offset']==field['offset'] and b['source_sha256']==field['source_sha256'] and b['native_string_offset']==field['native_string_offset'],'named field binding mismatch');source_bindings.append(b['id'])
 keys=[q['key'] for q in records['00000953.itm']]
 for key in keys:require(item_lookup(image,keys,key)==0xc000+100*max(i for i,k in enumerate(keys) if k==key),'native item key lookup mismatch')
 require(item_lookup(image,keys,0xffffffff)==0x8564,'native missing item fallback mismatch');require(item_lookup(image,[9,17,9],9)==0xc000+200,'native duplicate item fixture mismatch')
 consumers=json.loads(a.consumers.read_text('utf8'));roles=compiled_roles(consumers['selected_objects']);report=dict(schema=1,elf_sha256=ELF_SHA256,ship_sha256=digest(a.ship.read_bytes()),profile_sha256=digest(a.profile.read_bytes()),consumers_sha256=digest(a.consumers.read_bytes()),methods=methods,records=records,scalar_stride_cases=cases,item_hash_cases=len(keys)+2,compiled_producer_objects=roles,source_bound_fields=source_bindings,static_storage_and_numeric_lookup_verified=True,runtime_verified=False,all_other_consumers_proven_absent=False);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('NATIVE_NAMED_RESOURCE_PASS source_fields='+str(len(source_bindings))+' stride_cases='+str(cases)+' item_hash_cases='+str(len(keys)+2)+' numeric_keys_and_string_storage_verified=true runtime_verified=false')
if __name__=='__main__':main()
