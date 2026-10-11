"""Fingerprint-gated ordinary Function literal rewriting for version 118.

Coordinates are VM offsets (compact references occupy four VM bytes), not
package or streamed-cache offsets. Original branch targets and skip distances
are relocated, never normalized to an inferred expression end. Streamed cache
writing and runtime acceptance are deliberately outside this backend.
"""
from pathlib import Path
import argparse, json, struct, sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import require,digest,archive_entries,output_directory
from audit_compiled_scripts import body
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from package_resource import replace_exports
from validate_compiled_translations import validate_language,reparse


def shifted(position,edits):
    """Map an old coordinate; a target inside replaced text has no safe mapping."""
    require(type(position) is int and position>=0,'invalid relocation coordinate')
    delta=0
    for e in edits:
        start,end=e['start'],e['end']
        require(0<=start<=end,'invalid relocation interval')
        require(not start<position<end,'branch/skip target inside replaced literal')
        if position>=end:delta+=e['delta']
    return position+delta


def direct_children(tokens):
    result=defaultdict(list);stack=[]
    for i,t in enumerate(tokens):
        while stack and tokens[stack[-1]]['depth']>=t['depth']:stack.pop()
        require(t['depth']==len(stack),'token depth discontinuity')
        if stack:result[stack[-1]].append(i)
        stack.append(i)
    return result


def encode_target(text,mapping):
    entries=mapping['entries'];codes={q['character']:bytes.fromhex(q['bytes']) for q in entries}
    require(len(codes)==len(entries) and len(set(codes.values()))==len(entries),'duplicate character/code mapping')
    require(all(len(ch)==1 and ord(ch)>=128 and len(code)==2 and code[0]>=128 and 0 not in code for ch,code in codes.items()),'invalid mapped double-byte framing')
    result=bytearray()
    for ch in text:
        if ord(ch)<128:require(0<ord(ch)<128,'NUL in compiled target');result.append(ord(ch))
        else:require(ch in codes,'missing mapped glyph '+ch);result+=codes[ch]
    require(bool(result),'empty compiled target')
    return bytes(result)


def rewrite_function(raw,tables,export,replacements,*,expected_sha256):
    require(digest(raw)==expected_sha256,'compiled serial fingerprint mismatch')
    require(export['class']=='Function','only ordinary Function rewriting is supported')
    before=body(raw,tables,export,include_spans=True);s=before['script'];ts=s['tokens']
    require(not before['tail']['flags']&0x40,'replicated Function offsets require a separate backend')
    require(not any(t['opcode'] in (0x0c,0x2f) for t in ts),'label-table/Iterator rewriting requires a separate backend')
    require(replacements and all(type(i) is int and 0<=i<len(s['strings']) for i in replacements),'invalid literal index')
    by_offset={t['offset']:t for t in ts};disk=[];virtual=[];literal_receipts=[]
    for i,new in sorted(replacements.items()):
        q=s['strings'][i];t=by_offset[q['token_offset']];at=q['offset'];n=q['source_bytes']
        require(q['opcode']==0x1f and q['terminated'] and raw[at+n]==0,'unsupported literal framing')
        require(type(new) is bytes and new and b'\0' not in new,'invalid replacement literal bytes')
        require(n>0 and digest(raw[at:at+n])==q['sha256'],'literal source span mismatch')
        disk.append(dict(start=at,end=at+n,delta=len(new)-n,new=new,label='literal-'+str(i)))
        virtual.append(dict(start=t['virtual_offset']+1,end=t['virtual_offset']+1+n,delta=len(new)-n))
        literal_receipts.append(dict(index=i,old_offset=at,old_bytes=n,new_bytes=len(new),source_sha256=q['sha256'],target_sha256=digest(new)))
    disk.sort(key=lambda x:x['start']);virtual.sort(key=lambda x:x['start'])
    require(all(a['end']<=b['start'] for a,b in zip(disk,disk[1:])),'overlapping literal edits')
    size=s['virtual_bytes'];new_size=shifted(size,virtual)
    require(0<=new_size<=4*1024*1024,'modified VM size limit')
    children=direct_children(ts);branches=[];edits=list(disk)
    token_boundaries={t['virtual_offset'] for t in ts}|{size}
    for i,t in enumerate(ts):
        x=t['opcode'];at=t['offset'];vo=t['virtual_offset'];base=None
        if x in (0x06,0x07,0x0a):
            field=at+1;old=struct.unpack_from('<H',raw,field)[0]
            if x==0x0a and old==65535:continue
            require(old in token_boundaries,'absolute branch target is not a token boundary')
            target=old;new=shifted(target,virtual)
        elif x in (0x12,0x19):
            require(len(children[i])==2,'context direct-child framing mismatch')
            child=ts[children[i][1]];field=child['offset']-3;base=child['virtual_offset']
            require(field>=at+1 and field+3<=s['end'],'context skip field bounds')
            old=struct.unpack_from('<H',raw,field)[0];target=base+old
            require(target<=size,'context skip target outside VM script')
            new=shifted(target,virtual)-shifted(base,virtual)
        elif x==0x18:
            field=at+1;base=vo+3;old=struct.unpack_from('<H',raw,field)[0];target=base+old
            require(target<=size,'Skip target outside VM script')
            new=shifted(target,virtual)-shifted(base,virtual)
        else:continue # Assert's u16 is diagnostic data, not a branch.
        require(0<=new<65535,'relocated branch/skip exceeds supported u16 range')
        branches.append(dict(opcode=x,token_virtual=vo,field_offset=field,old_value=old,new_value=new,old_base=base,old_target=target,new_target=shifted(target,virtual)))
        edits.append(dict(start=field,end=field+2,delta=0,new=struct.pack('<H',new),label='operand-'+str(field)))
    require(struct.unpack_from('<I',raw,s['start']-4)[0]==size,'VM size header mismatch')
    edits.append(dict(start=s['start']-4,end=s['start'],delta=0,new=struct.pack('<I',new_size),label='virtual-size'))
    edits.sort(key=lambda x:x['start']);result=bytearray();end=0;receipt=[]
    for q in edits:
        require(end<=q['start']<q['end']<=len(raw),'overlapping/out-of-bounds compiled edits')
        result+=raw[end:q['start']];new_at=len(result);result+=q['new'];end=q['end']
        receipt.append(dict(label=q['label'],old_offset=q['start'],old_bytes=q['end']-q['start'],new_offset=new_at,new_bytes=len(q['new'])))
    result+=raw[end:];result=bytes(result);after=body(result,tables,export,include_spans=True);ns=after['script']
    property_identity=lambda p:{k:v for k,v in p.items() if k not in ('native_tail_bytes','native_tail_sha256')}
    require(property_identity(before['property_block'])==property_identity(after['property_block']) and before['tail']==after['tail'],'properties/Function tail changed')
    require({k:v for k,v in before['header'].items() if k!='virtual_script_bytes'}=={k:v for k,v in after['header'].items() if k!='virtual_script_bytes'},'unrelated Function header changed')
    require(len(ts)==len(ns['tokens']) and len(s['references'])==len(ns['references']) and len(s['strings'])==len(ns['strings']),'compiled topology changed')
    for old,new in zip(ts,ns['tokens'],strict=True):
        require(all(old[k]==new[k] for k in ('opcode','depth','parent_opcode')),'compiled token topology changed')
        require(new['offset']==shifted(old['offset'],disk) and new['end']==shifted(old['end'],disk)
            and new['virtual_offset']==shifted(old['virtual_offset'],virtual) and new['virtual_end']==shifted(old['virtual_end'],virtual),'compiled coordinate readback mismatch')
    for old,new in zip(s['references'],ns['references'],strict=True):
        require(old['value']==new['value'] and old['kind']==new['kind'] and new['offset']==shifted(old['offset'],disk),'protected reference changed')
    for i,(old,new) in enumerate(zip(s['strings'],ns['strings'],strict=True)):
        expected=replacements.get(i,raw[old['offset']:old['offset']+old['source_bytes']])
        require(result[new['offset']:new['offset']+new['source_bytes']]==expected,'literal bytes readback mismatch')
    for q in branches:
        require(struct.unpack_from('<H',result,shifted(q['field_offset'],disk))[0]==q['new_value'],'branch operand readback mismatch')
    # Exact unchanged intervals, independently of parser readback.
    old_pos=new_pos=0
    for q in receipt:
        n=q['old_offset']-old_pos;require(result[new_pos:new_pos+n]==raw[old_pos:old_pos+n],'untargeted Function bytes changed')
        old_pos=q['old_offset']+q['old_bytes'];new_pos=q['new_offset']+q['new_bytes']
    require(result[new_pos:]==raw[old_pos:],'untargeted Function tail bytes changed')
    return result,dict(source_sha256=digest(raw),modified_sha256=digest(result),old_size=len(raw),new_size=len(result),old_virtual_bytes=size,new_virtual_bytes=new_size,literals=literal_receipts,branches=branches,edits=receipt,untargeted_bytes_preserved=True,stream_cache_synchronized=False,runtime_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','objects','classifications','batch','profile','mapping','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));batch=json.loads(a.batch.read_text('utf8'))
    rows=validate_language(batch,profile)
    require(all(q['reinsertion_policy']=='translate-compiled-function' for q in rows),'compiled Function import is not approved')
    require(digest(a.archive.read_bytes())==profile['file_sha256'] and digest(a.objects.read_bytes())==profile['objects_sha256'] and digest(a.classifications.read_bytes())==profile['classifications_sha256'],'compiled input fingerprint mismatch')
    members=dict(archive_entries(a.archive)[1]);objects=json.loads(a.objects.read_text('utf8'));reparse(profile,objects,members)
    mapping=json.loads(a.mapping.read_text('utf8'))
    grouped=defaultdict(dict)
    for q in rows:
        oid,index=q['id'].rsplit('/string/',1);grouped[oid][int(index)]=encode_target(q['target'],mapping)
    out=output_directory(a.out);require(not any(out.iterdir()),'compiled output must be empty');byid={q['id']:q for q in objects};packages=defaultdict(dict);reports=[]
    for oid,replacements in sorted(grouped.items()):
        obj=byid[oid];blob=members[obj['package']];e=obj['export'];tables=package_tables(blob);raw=blob[e['offset']:e['offset']+e['size']]
        modified,report=rewrite_function(raw,tables,e,replacements,expected_sha256=obj['serial_sha256']);packages[obj['package']][e['index']]=modified;reports.append(dict(id=oid,**report))
    package_receipts=[]
    for name,replacements in sorted(packages.items()):
        source=members[name];modified,receipt=replace_exports(source,replacements,expected_sha256=digest(source),expected_version=(118,15));dest=out/name;dest.write_bytes(modified)
        require(dest.read_bytes()==modified,'compiled package reopen mismatch')
        tables=package_tables(modified);exports=ordinary_exports(modified,tables)
        for index,payload in replacements.items():
            e=exports[index-1];require(modified[e['offset']:e['offset']+e['size']]==payload,'appended Function readback mismatch');body(payload,tables,e,include_spans=True)
        package_receipts.append(dict(package=name,path=str(dest),source_sha256=digest(source),modified_sha256=digest(modified),**receipt))
    result=dict(schema=1,objects_sha256=digest(a.objects.read_bytes()),batch_sha256=digest(a.batch.read_bytes()),profile_sha256=digest(a.profile.read_bytes()),mapping_sha256=digest(a.mapping.read_bytes()),translated_fields=len(rows),functions=len(reports),packages=package_receipts,function_receipts=reports,ordinary_package_copies_verified=True,stream_cache_synchronized=False,font_coverage_verified=False,final_iso_complete=False,runtime_verified=False)
    dest=out/'compiled-imports.json';dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(dest.read_text('utf8'))==result,'compiled report reopen mismatch')
    print(f'ORDINARY_COMPILED_IMPORT_PASS fields={len(rows)} functions={len(reports)} packages={len(package_receipts)} branches={sum(len(q["branches"]) for q in reports)} stream_pending=true runtime_verified=false')
if __name__=='__main__':main()
