"""Validate reviewed compiled literals against reparsed original package bytes.

This front-end does not authorize or write bytecode/package/cache changes.
"""
from pathlib import Path
import argparse, json, re, sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from font_poc import require,digest,archive_entries
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from audit_compiled_scripts import body
from audit_literal_contexts import ancestry,symbolic
from localization.text import protected_tokens

def validate_language(batch,profile):
    require(batch.get('schema')==profile.get('schema')==1 and bool(batch.get('locale')),'compiled translation schema/locale mismatch')
    index={q['id']:q for q in profile['bindings']};require(len(index)==len(profile['bindings']),'duplicate compiled source binding')
    seen=set();rows=[]
    require(profile.get('runtime_visibility_verified') is False and profile.get('import_approved') is False,'compiled front-end cannot claim runtime/import')
    for e in batch['entries']:
        require(e['id'] in index and e['id'] not in seen,'unknown/duplicate compiled translation');seen.add(e['id']);q=index[e['id']]
        require(e['source_sha256']==q['source_sha256'] and e['source']==q['source'],'compiled language source mismatch')
        require(e['status']=='reviewed' and e['reinsertion_policy'] in ('pending-compiled-backend','translate-compiled-function'),'compiled language status/import mismatch')
        require(isinstance(e['target'],str) and bool(e['target']) and not any(ord(c)<32 for c in e['target']) and '—' not in e['target'],'invalid compiled target')
        require(protected_tokens(e['source'])==protected_tokens(e['target']),'compiled protected token mismatch')
        require(re.findall(r'\d+',e['source'])==re.findall(r'\d+',e['target']),'compiled numeric label changed')
        require(not re.search(r'[가-힣ぁ-ヿ]',e['target']),'compiled untranslated target script')
        rows.append(e)
    require(bool(rows),'empty compiled translation batch')
    retained=profile['retained'];require(len({x['id'] for x in retained})==len(retained),'duplicate compiled retention')
    for x in retained:
        require(x['id'] in index and x['id'] not in seen and x['decision']=='retain-original'
            and x['source_sha256']==index[x['id']]['source_sha256'] and x['source']==index[x['id']]['source']
            and x['runtime_visibility_verified'] is False and bool(x['reason']),'invalid compiled retention binding')
    require(seen|{x['id'] for x in retained}==set(index),'compiled frontier decision gap')
    return rows

def reparse(profile,objects,members):
    index={q['id']:q for q in objects};require(len(index)==len(objects),'duplicate compiled object')
    natives=defaultdict(set)
    for q in objects:
        if 'native_index' in q['tail']:natives[q['tail']['native_index']].add(q['export']['name'])
    packages={};parsed={};proofs=[]
    for q in profile['bindings']:
        oid,n=q['id'].rsplit('/string/',1);obj=index[oid];name=obj['package']
        if name not in packages:
            blob=members[name];require(digest(blob)==obj['package_sha256'],'compiled package mismatch');t=package_tables(blob);packages[name]=(blob,t,ordinary_exports(blob,t))
        blob,t,exports=packages[name];exp=exports[obj['export']['index']-1];require(exp==obj['export'],'compiled export metadata mismatch')
        raw=blob[exp['offset']:exp['offset']+exp['size']];require(digest(raw)==obj['serial_sha256']==q['serial_sha256'],'compiled serial mismatch')
        if oid not in parsed:
            b=body(raw,t,exp);require(b['script']==obj['script'] and b['header']==obj['header'] and b['tail']==obj['tail'],'compiled body reparse mismatch');parsed[oid]=(b,ancestry(b['script']['tokens']))
        b,parents=parsed[oid];s=b['script']['strings'][int(n)];at=s['offset'];span=raw[at:at+s['source_bytes']]
        require(s['text']==q['source'] and s['sha256']==q['source_sha256']==digest(span)
            and s['source_bytes']==q['source_bytes'] and exp['offset']+at==q['absolute_offset']
            and s['opcode']==0x1f and raw[at+s['source_bytes']]==0,'compiled literal framing mismatch')
        calls=[symbolic(p,raw,t,natives) for p in parents[s['token_offset']] if p['opcode']>=0x60 or p['opcode'] in (0x1b,0x38,0x1c)]
        require(calls==q['call_context'],'compiled call ancestry mismatch')
        proofs.append(dict(id=q['id'],source_sha256=digest(span),serial_sha256=digest(raw),absolute_offset=exp['offset']+at,source_bytes=s['source_bytes'],call_context=calls,source_bytes_reparsed=True,runtime_visibility_verified=False,import_approved=False))
    return proofs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','objects','classifications','batch','profile','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));batch=json.loads(a.batch.read_text('utf8'));rows=validate_language(batch,profile)
    require(digest(a.archive.read_bytes())==profile['file_sha256'] and digest(a.objects.read_bytes())==profile['objects_sha256'] and digest(a.classifications.read_bytes())==profile['classifications_sha256'],'compiled input fingerprint mismatch')
    proofs=reparse(profile,json.loads(a.objects.read_text('utf8')),dict(archive_entries(a.archive)[1]))
    result=dict(schema=1,translated_fields=len(rows),retained_fields=len(profile['retained']),reparsed_fields=len(proofs),proofs=proofs,source_modified=False,bytecode_reinsertion_complete=False,runtime_visibility_verified=False,import_approved=False)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(a.out.read_text('utf8'))==result,'compiled validation output reopen mismatch');print('COMPILED_TRANSLATION_FRONTEND_PASS fields='+str(len(rows))+' retained='+str(len(profile['retained']))+' original_bytes_contexts_reparsed='+str(len(proofs))+' backend_pending=true runtime_verified=false')
if __name__=='__main__':main()
