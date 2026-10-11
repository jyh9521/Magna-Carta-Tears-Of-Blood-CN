"""Version-locked FPB numeric lookup to queued chat text protocol audit.

Specific event reachability and visual rendering are separate from this static route.
"""
from pathlib import Path
import argparse,json,struct,sys
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','lib')]
from research_native import ElfImage,ELF_SHA256
from audit_native_method_registration import bind_inline,require
from audit_native_playbook import native_records,lookup
from font_poc import archive_entries,digest
ANCHORS={3656480: 2390884472, 3656484: 2391081112, 3656488: 2353136160, 3656492: 2353267520, 3656496: 202180952, 3656500: 665190544, 3656556: 2409758868, 3656572: 2410676368, 3656596: 33562669, 3656652: 201612060, 3656656: 33564717, 3656688: 2391867540, 3656744: 272629768, 3656768: 4202541, 3656772: 202241324, 3656776: 665190528, 3656804: 4204589, 3656808: 2410021024, 3656816: 2402877464, 3656820: 52492297, 3658952: 12621869, 3658976: 646971396, 3658992: 2361524228, 3659008: 2894200840, 3659012: 2894200844, 3659024: 2382757892, 3659036: 2382626816, 3659040: 201612060, 3659044: 2388983808}

def validate_anchors(image):
 for va,word in ANCHORS.items():require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0]==word,'chat protocol anchor mismatch '+hex(va))

def source_match(raw,binding):
 require(digest(raw)==binding['source_resource_sha256'],'FPB resource fingerprint mismatch');records,pool=native_records(raw)
 matches=[(i,k) for i,(k,offset,length) in enumerate(records) if offset==binding['source_offset'] and length==binding['source_bytes'] and digest(pool[offset:offset+length])==binding['source_sha256']]
 require(len(matches)==1,'source FPB span match missing or ambiguous');physical,key=matches[0];require(physical==binding['physical_index'] and key==binding['native_record_key'],'source FPB key/index mismatch');require(lookup(records,key)==physical,'source FPB first-key lookup selects another record');return dict(id=binding['id'],native_record_key=key,physical_index=physical,source_sha256=binding['source_sha256'],source_span_unique=True,numeric_key_first_match=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--ship',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'original ELF fingerprint mismatch');require(digest(a.ship.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','original SHIP fingerprint mismatch');image=ElfImage(raw);validate_anchors(image);binding=bind_inline(image,'intUMrtsGameEventexecThen_2DObjectControl_Chat',callback_limit=2048);require(binding['callback']=='0x37cad0' and binding['callback_end']=='0x37d1bc','chat callback range mismatch');require({'va':'0x37cb30','target':'0x342560'} in binding['bounded_callback_jals'],'FPB text getter call missing');profile=json.loads(a.profile.read_text('utf8'));ship=dict(archive_entries(a.ship)[1]);rows=[]
 for b in profile['bindings']:
  require(b['source_resource'].startswith('SHIP/') and Path(b['source_resource']).name in ship,'source FPB resource missing');rows.append(source_match(ship[Path(b['source_resource']).name],b))
 result=dict(elf_sha256=ELF_SHA256,profile_sha256=digest(a.profile.read_bytes()),binding=binding,anchors={hex(va):hex(w) for va,w in ANCHORS.items()},source_records=rows,protocol=dict(field_data_pointer_chain=[0x78,0x220,0x340],numeric_text_key_field=0x98,independent_numeric_talker_field=0x94,getter_output_fstring_stack=0x90,temporary_fstring_stack=0x80,chat_payload_string_offset=4,payload_constructor='0x37d4b0',queue_vtable_slot=0x18,text_uses_string_copy_not_identifier_lookup=True),static_protocol_verified=True,specific_event_execution_verified=False,runtime_verified=False);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n','utf8');print('NATIVE_FPB_CHAT_PROTOCOL_PASS fields='+str(len(rows))+' unique_source_spans=true numeric_keys_first_match=true text_payload_copy=true specific_events_verified=false runtime_verified=false')
if __name__=='__main__':main()
