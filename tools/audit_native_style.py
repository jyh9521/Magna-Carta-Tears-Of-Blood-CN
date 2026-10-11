"""Bind version-locked style resource names to native records and UI consumers."""
from pathlib import Path
import argparse,struct,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from audit_text_slicing import scalar
import font_poc as core
ANCHORS={0x30d610:0x0320f809,0x30d614:0x24060043,0x30d618:0x0c069530,0x30d624:0x8e220058,0x310870:0x26040058,0x30d354:0x3c05004b,0x30d35c:0x24a57ab0,0x30d3dc:0x26050040,0x30d40c:0x8e020040,0x30d42c:0x0320f809,0x30d430:0x0220282d,0x30d444:0x0320f809,0x30d448:0x24060064,0x30d44c:0x0c069530,0x30d450:0x27a40060,0x30d480:0x26240004,0x30d49c:0x8e240004,0x30d4a0:0x0c045b1c,0x310ae0:0x8e850044,0x310aec:0x8e820040,0x310af0:0x00061880,0x310af4:0x00662021,0x310af8:0x00041880,0x310afc:0x00831821,0x310b00:0x00031880,0x310b04:0x00439021,0x310b08:0x8e420000,0x310b0c:0x1453003a,0x310b20:0x0c06cd10,0x310b24:0x26450004,0x310be8:0x0c06cd10,0x310bd8:0x26450058,0x3107c8:0x0c0c426c,0x3107dc:0x26040004,0x3107e0:0x0c06cd10,0x3107e4:0x27a50044,0x1a54c0:0x03e00008,0x1a54c4:0x0080102d}

def check_name_equality(source_names,target_names):
 """Compare complete byte-label equivalence classes, not Unicode casefold.

 Inputs must be the original and actual mapped NUL-free labels. The caller
 remains responsible for source fingerprints and both caption producers.
 """
 require(len(source_names)==len(target_names) and bool(source_names),'name table lengths mismatch or empty')
 require(all(isinstance(x,bytes) and b'\0' not in x for x in [*source_names,*target_names]),'name equality requires NUL-free byte labels')
 pairs=0
 for i,a in enumerate(source_names):
  for j in range(i+1,len(source_names)):
   require((a.lower()==source_names[j].lower())==(target_names[i].lower()==target_names[j].lower()),'name equality partition changed at '+str(i)+','+str(j))
   pairs+=1
 return dict(names=len(source_names),pairs=pairs,byte_case_equality_partition_preserved=True,runtime_verified=False)
def validate_anchors(image):
 for va,w in ANCHORS.items():require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0]==w,'native style anchor mismatch '+hex(va))

def record_address(image,index):
 require(0<=index<10000,'bounded record index required');memory={0x8040+i:b for i,b in enumerate(struct.pack('<I',0x9000))};result=scalar(image,0x310aec,0x310b08,{20:0x8000,6:index},memory);require(result['registers'][18]==0x9000+100*index,'native style stride mismatch');return result['registers'][18]

def expression_evidence(objects):
 rows=[]
 for obj in objects:
  ts=obj['tokens']
  for i,t in enumerate(ts[:-1]):
   if t.get('field')!='Name' or ts[i+1].get('field')!='StyleData' or ts[i+1]['depth']!=t['depth']+1:continue
   roots=[z for z in ts[:i+1] if z['depth']==0 and z['offset']<=t['offset']];require(roots,'source expression root missing');root=roots[-1];k=ts.index(root);end=k+1
   while end<len(ts) and ts[end]['depth']>root['depth']:end+=1
   tree=ts[k:end];symbols={s for z in tree for s in z.get('symbols',[])};fields={z.get('field') for z in tree};kind='string-comparison' if symbols&{'ComplementEqual_StrStr','EqualEqual_StrStr','NotEqual_StrStr'} else 'caption-assignment' if 'Caption' in fields and root['opcode']==15 else 'list-display' if 'AddList' in symbols else 'composition' if 'Concat_StrStr' in symbols else 'other'
   rows.append(dict(object_id=obj['id'],function=obj['function'],serial_sha256=obj['serial_sha256'],member_token_offset=t['offset'],kind=kind,tokens=tree))
 return rows

def caption_flow(objects):
 by={x['id']:x for x in objects};add=by.get('FILE/MrtsGame.u/export/12251');style=by.get('FILE/MrtsGame.u/export/11161');compare=by.get('FILE/MrtsGame.u/export/11048');require(add and style and compare,'style caption chain objects missing')
 ts={x['offset']:x for x in add['tokens']};require(ts[45]['opcode']==15 and ts[53].get('field')=='Caption' and ts[56].get('field')=='a_Name','caption producer assignment changed');require(ts[73]['opcode']==15 and ts[81].get('field')=='ID' and ts[84].get('field')=='a_ID','numeric list identity assignment changed')
 st={x['offset']:x for x in style['tokens']};require(st[85].get('symbols')==['AddList'] and st[88].get('field')=='Name' and st[91].get('field')=='StyleData','style list display input changed')
 ct={x['offset']:x for x in compare['tokens']};require(ct[224].get('symbols')==['ComplementEqual_StrStr'] and ct[225].get('field')=='Name' and ct[228].get('field')=='StyleData' and ct[234].get('field')=='SelectedItem' and ct[239].get('field')=='Caption','caption comparison changed')
 desc=by.get('FILE/MrtsGame.u/export/12135');require(desc,'description consumer missing');dt={x['offset']:x for x in desc['tokens']};require(dt[214]['opcode']==15 and dt[222].get('field')=='HelpText' and dt[225].get('field')=='Description' and dt[228].get('field')=='StyleData','description help assignment changed')
 return dict(description_help_consumer=desc,caption_producer=add,style_display_input=style,caption_comparison=compare,caption_parameter='a_Name',numeric_identity_parameter='a_ID',source_expression_chain_verified=True,runtime_verified=False)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('elf','ship','consumers','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();raw=a.elf.read_bytes();require(core.digest(raw)==ELF_SHA256,'original ELF mismatch');image=ElfImage(raw);validate_anchors(image);binding=bind_inline(image,'intUMrtsDataManagerexecGetStyleData');require(binding['callback']=='0x310760','style callback mismatch');require(image.blob[image.to_offset(0x4b7ab0):].split(b'\0',1)[0]==b'..\\Sgi\\00000468.sgi','style loader path mismatch')
 require(core.file_digest(a.ship)=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','original SHIP mismatch');data=dict(core.archive_entries(a.ship)[1])['00000468.sgi'];count,kind=struct.unpack_from('<II',data);require(kind==22 and len(data)==8+count*251,'style source record geometry mismatch');records=[]
 for i in range(count):
  at=8+251*i;slot=data[at+4:at+104];require(b'\0' in slot,'style name terminator missing');text=slot.split(b'\0',1)[0];records.append(dict(physical_index=i,key=struct.unpack_from('<I',data,at)[0],name_offset=at+4,name_sha256=core.digest(text),source_bytes=len(text),description_offset=at+184,description_sha256=core.digest(data[at+184:at+251].split(b'\0',1)[0])))
 for i in range(count):record_address(image,i)
 source=json.loads(a.consumers.read_text('utf8'));flow=caption_flow(source['selected_objects']);rows=expression_evidence(source['selected_objects']);counts={k:sum(x['kind']==k for x in rows) for k in ('string-comparison','caption-assignment','list-display','composition','other')};require(counts['caption-assignment'] and counts['list-display'] and counts['string-comparison'],'required source roles missing')
 report=dict(elf_sha256=ELF_SHA256,ship_sha256=core.file_digest(a.ship),sgi_sha256=core.digest(data),consumers_sha256=core.file_digest(a.consumers),native_binding=binding,loader='0x30d350',path='0x4b7ab0',array_offset=64,count_offset=68,native_stride=100,native_key_offset=0,native_name_offset=4,native_description_offset=88,serialized_stride=251,serialized_name_offset=4,serialized_name_capacity=100,serialized_description_offset=184,serialized_description_capacity=67,scalar_stride_cases=count,anchors={hex(k):hex(v) for k,v in ANCHORS.items()},records=records,expressions=rows,role_counts=counts,display_proven_statically=True,caption_comparison_producer_closed=True,caption_flow=flow,translation_write_policy_evaluated=False,runtime_verified=False)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('NATIVE_STYLE_CONSUMER_PASS records='+str(count)+' stride_cases='+str(count)+' roles='+json.dumps(counts,sort_keys=True)+' caption_producer_closed=true translation_policy_evaluated=false runtime_verified=false')
if __name__=='__main__':main()
