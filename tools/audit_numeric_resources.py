"""Audit complete fixed-word resources with script and native load references."""
from pathlib import Path
import argparse,json,re,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_decode_quarantine import checked_span
from audit_config_semantics import script_sources,CORPUS_HASH
from extract_script_buffers import FILE_HASH
from audit_stream_resource_chain import SHIP_HASH
from research_native import ElfImage,ELF_SHA256,pair_candidates,trace_call
PROFILES={'.cls':dict(kind=24,words=25,struct='MrtsClassData',path='..\\ClassData\\00000343.cls'),
          '.att':dict(kind=5,words=6,struct='MrtsTargetData',path='..\\ATT\\00000465.att'),
          '.val':dict(kind=1,words=2,struct='MrtsValueData',path='..\\ValueData\\00000469.val')}


def parse_words(raw,ext):
    core.require(ext in PROFILES and len(raw)>=8,'numeric resource header')
    p=PROFILES[ext];count,kind=struct.unpack_from('<II',raw)
    core.require(kind==p['kind'] and len(raw)==8+count*p['words']*4,'numeric resource geometry mismatch')
    rows=[]
    for i in range(count):
        start=8+i*p['words']*4;part=raw[start:start+p['words']*4]
        rows.append(dict(index=i,start=start,end=start+len(part),sha256=core.digest(part),
            u32=list(struct.unpack('<'+'I'*p['words'],part)),s32=list(struct.unpack('<'+'i'*p['words'],part))))
    return rows


def word_context(row,records):
    start,size=row['offset'],row['source_bytes'];end=start+size
    core.require(size>0,'empty numeric candidate')
    matches=[r for r in records if r['start']<=start and end<=r['end']]
    core.require(len(matches)==1,'numeric candidate outside records');r=matches[0]
    first=(start-r['start'])//4;last=(end-1-r['start'])//4
    return dict(record=r['index'],record_sha256=r['sha256'],first_word=first,last_word=last,
        u32=r['u32'][first:last+1],category='fixed-word-payload-not-translatable',semantic_confidence='high-confidence-deduction')


def native_paths(elf,paths):
    image=ElfImage(elf);seg=image.segments[0]
    words=list(struct.unpack('<'+'I'*(seg['filesz']//4),elf[seg['offset']:seg['offset']+seg['filesz']]))
    targets={};result=[]
    for path in paths:
        needle=path.encode('ascii')+b'\0';positions=[];pos=0
        while True:
            pos=elf.find(needle,pos)
            if pos<0:break
            positions.append(pos);pos+=1
        core.require(len(positions)==1,'numeric load path identity')
        targets[image.to_va(positions[0])]=(path,positions[0])
    for hit in pair_candidates(words,set(targets)):
        path,offset=targets[hit['address']];upper=seg['va']+hit['upper_word']*4;lower=seg['va']+hit['lower_word']*4
        # Evidence retains bounded call arguments only; no inferred vtable implementation.
        calls=[]
        for i in range(hit['upper_word'],min(len(words)-1,hit['upper_word']+160)):
            w=words[i]
            if w>>26==3 or (w>>26==0 and w&63==9):calls.append(trace_call(image,seg['va']+i*4,24))
            if i>hit['lower_word'] and w==0x03e00008:break
        result.append(dict(path=path,string_offset=offset,string_va=hit['address'],upper_va=upper,lower_va=lower,
            upper_word=words[hit['upper_word']],lower_word=words[hit['lower_word']],calls=calls,
            evidence='bounded-native-address-construction-not-runtime-load-trace'))
    core.require(set(r['path'] for r in result)==set(paths),'numeric paths without native references')
    return result


def audit(corpus_path,ship,file,elf_path,out):
    for p,h in [(corpus_path,CORPUS_HASH),(ship,SHIP_HASH),(file,FILE_HASH),(elf_path,ELF_SHA256)]:core.require(core.file_digest(p)==h,'input identity mismatch')
    c=json.loads(corpus_path.read_text('utf8'));selected=[r for r in c['resources'] if Path(r['resource']).suffix in PROFILES]
    a=Afs.open(ship);names=filename_toc(a);fa=Afs.open(file);fn=filename_toc(fa)
    with file.open('rb') as f:sources=script_sources(fa,fn,f)
    structs=[]
    for source in sources:
        for ext,p in PROFILES.items():
            m=re.search(r'\bstruct\s+'+p['struct']+r'\s*\{([^}]+)\}',source['text'])
            if m:
                structs.append(dict(extension=ext,struct=p['struct'],source_id=source['id'],serial_sha256=source['serial_sha256'],
                    line=source['text'].count('\n',0,m.start())+1,declarations=m[1],evidence='script-struct-reference-not-native-disk-schema'))
    core.require(len(structs)==3,'script struct reference count')
    records=[];candidates=[]
    with ship.open('rb') as f:
        for resource in selected:
            raw=a.read_entry(names.index(resource['resource'].split('/')[1]),f)
            core.require(core.digest(raw)==resource['sha256'] and len(raw)==resource['size'],'resource identity mismatch')
            rs=parse_words(raw,Path(resource['resource']).suffix)
            records.append(dict(resource=resource['resource'],sha256=resource['sha256'],bytes=len(raw),
                geometry_verified=True,field_semantics_verified=False,records=rs))
            for e in resource['entries']:
                checked_span(raw,e);candidates.append(dict(id=e['id'],source_sha256=e['source_sha256'],offset=e['offset'],source_bytes=e['source_bytes'],
                    **word_context(e,rs),editable=False,backend_eligible=False))
    paths=native_paths(elf_path.read_bytes(),[p['path'] for p in PROFILES.values()])
    summary=dict(schema=1,resources=len(records),records=sum(len(r['records']) for r in records),words=sum(len(x['u32']) for r in records for x in r['records']),
        candidate_fields=len(candidates),candidate_fields_in_words=len(candidates),geometry_verified=True,
        resource_counts={r['resource']:len(r['records']) for r in records},native_path_references=len(paths),script_struct_references=len(structs),
        field_semantics_verified=False,native_reader_complete=False,complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('records.json',records),('candidate-contexts.json',candidates),('native-paths.json',paths),('struct-references.json',structs),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    for p,h in [(corpus_path,CORPUS_HASH),(ship,SHIP_HASH),(file,FILE_HASH),(elf_path,ELF_SHA256)]:core.require(core.file_digest(p)==h,'input changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['corpus','ship','file','elf','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.ship,a.file,a.elf,a.out),sort_keys=True))
