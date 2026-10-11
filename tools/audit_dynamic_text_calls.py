"""Reparse original compiled objects and expose bounded getter call trees."""
from pathlib import Path
import argparse,json,sys,collections
r=Path(__file__).resolve().parents[1];sys.path[:0]=[str(r/'tools'),str(r/'lib')]
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import Reader
from audit_literal_contexts import symbolic,ancestry
from audit_compiled_scripts import body
import font_poc as core
from compiled_text_consumers import matching_fields
def annotate(tokens,serial,tables,natives,obj):
 tree=[]
 for z in tokens:
  d=dict(z);d.update(symbolic(z,serial,tables,natives));rd=Reader(serial,z['offset']+1)
  if z['opcode'] in (0,1,2,0x36,0x47,0x48):
   v=rd.index();core.require(-len(tables['imports'])<=v<=len(tables['exports']),'field reference bounds');d['field']=tables['exports'][v-1]['name'] if v>0 else tables['imports'][-v-1]['name'] if v<0 else None
  if z['opcode']==0x1d:d['int']=rd.integer('i')
  if z['opcode']==0x2c:d['int']=rd.integer('B')
  if z['opcode']==0x25:d['int']=0
  if z['opcode']==0x26:d['int']=1
  if z['opcode']==0x1f:d['literal']=next((s['text'] for s in obj['script']['strings'] if s['token_offset']==z['offset']),None)
  tree.append(d)
 return tree

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--objects',type=Path,required=True);p.add_argument('--objects-sha256',required=True);p.add_argument('--package',action='append',required=True);p.add_argument('--getter',action='append',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--function',action='append',default=[],help='Also emit every token of named functions, including later consumer statements');p.add_argument('--field',action='append',default=[],help='Emit whole objects referencing selected source property names');args=p.parse_args();archive=args.archive;core.require(core.file_digest(archive)==args.archive_sha256,'original archive fingerprint mismatch');core.require(core.file_digest(args.objects)==args.objects_sha256,'original inventory fingerprint mismatch')
xs=json.loads(args.objects.read_text('utf8'));natives=collections.defaultdict(set)
for x in xs:
 if 'native_index' in x['tail']:natives[x['tail']['native_index']].add(x['export']['name'])
wanted=set(args.getter);found_fields=set()
a=Afs.open(archive);names=filename_toc(a);packages={};out=[];selected_objects=[];found_functions=set()
with archive.open('rb') as stream:
 for x in xs:
  if x['package'] not in args.package:continue
  if x['package'] not in packages:
   b=a.read_entry(names.index(x['package']),stream);packages[x['package']]=(b,package_tables(b));core.require(core.digest(b)==x['package_sha256'],'original package fingerprint mismatch')
  b,tables=packages[x['package']];e=x['export'];serial=b[e['offset']:e['offset']+e['size']];core.require(core.digest(serial)==x['serial_sha256'],'original object fingerprint mismatch');parsed=body(serial,tables,e);core.require(all(parsed[k]==x[k] for k in parsed),'compiled object reparse mismatch');tokens=parsed['script']['tokens'];parents=ancestry(tokens)
  annotated=annotate(tokens,serial,tables,natives,x) if args.field or e['name'] in args.function else None
  selected_fields=matching_fields(annotated,args.field) if annotated is not None else []
  if e['name'] in args.function or selected_fields:
   found_functions.add(e['name']);found_fields.update(selected_fields);row=dict(id=x['id'],function=e['name'],serial_sha256=x['serial_sha256'],tokens=annotated,execution_verified=False)
   if selected_fields:row['selected_fields']=selected_fields
   selected_objects.append(row)
  for j,t in enumerate(tokens):
   if t['opcode'] not in (0x1b,0x1c,0x38):continue
   call=symbolic(t,serial,tables,natives)
   if not set(call.get('symbols',[]))&wanted:continue
   chain=parents[t['offset']];root=next((z for z in reversed(chain) if z['opcode'] in (0x0f,0x04) or z['opcode']>=0x70),t);k=next(i for i,z in enumerate(tokens) if z['offset']==root['offset']);end=k+1
   while end<len(tokens) and tokens[end]['depth']>root['depth']:end+=1
   tree=annotate(tokens[k:end],serial,tables,natives,x)
   item=dict(id=x['id'],function=e['name'],serial_sha256=x['serial_sha256'],call=call,tree=tree,parent_symbols=[symbolic(z,serial,tables,natives) for z in chain],execution_verified=False);out.append(item)
core.require(set(args.function)<=found_functions,'requested function not found in selected packages');core.require(set(args.field)<=found_fields,'requested property field not found in selected packages');args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(dict(file_sha256=args.archive_sha256,objects_sha256=args.objects_sha256,calls=out,selected_objects=selected_objects,execution_verified=False),ensure_ascii=False,indent=2),'utf8');print('DYNAMIC_TEXT_CALL_REPARSE_PASS calls='+str(len(out))+' execution_verified=false')
