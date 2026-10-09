"""Inventory every FILE .ini/.int entry without inferring runtime visibility."""
from pathlib import Path
import argparse,json,sys,re
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks
from extract_script_buffers import FILE_HASH
from audit_bundle_contexts import BUNDLE_HASH

def parse_lines(raw):
    core.require(b'\0' not in raw,'NUL in config')
    try:raw.decode('ascii','strict')
    except UnicodeError as error:raise ValueError('unsupported config encoding') from error
    rows=[];section=None;offset=0;entries=[];section_occurrences=Counter()
    for number,line in enumerate(raw.splitlines(keepends=True),1):
        content=line.rstrip(b'\r\n');text=content.decode('ascii');stripped=text.strip()
        row=dict(line=number,offset=offset,bytes=len(line),sha256=core.digest(line))
        if not stripped:row['kind']='blank'
        elif stripped.startswith((';','#')):row['kind']='comment'
        elif stripped.startswith('[') and stripped.endswith(']'):
            section=stripped[1:-1];core.require(bool(section),'empty section')
            section_occurrences[section]+=1;row.update(kind='section',section=section,section_occurrence=section_occurrences[section])
        elif '=' in text:
            core.require(section is not None,'entry outside section')
            key,value=text.split('=',1);core.require(bool(key.strip()),'empty config key')
            value_offset=offset+len(key.encode('ascii'))+1
            row.update(kind='entry',section=section,section_occurrence=section_occurrences[section],key=key,value=value,value_offset=value_offset,value_bytes=len(value),value_sha256=core.digest(value.encode('ascii')),placeholder_candidates=re.findall(r'%[A-Za-z]',value),semantic_review='pending',editable=False)
            entries.append(row)
        else:raise ValueError('unrecognized config line '+str(number))
        rows.append(row);offset+=len(line)
    core.require(offset==len(raw),'line coverage mismatch')
    return rows,entries

def exact_positions(blob,needle):
    core.require(bool(needle),'empty mirror needle')
    positions=[];start=0
    while True:
        offset=blob.find(needle,start)
        if offset<0:return positions
        positions.append(offset);start=offset+1

def audit(archive,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    afs=Afs.open(archive);names=filename_toc(afs);resources=[];entries=[]
    with archive.open('rb') as f:
        bundle,_=unpack_chunks(afs.read_entry(names.index('celfid.lix'),f));core.require(core.digest(bundle)==BUNDLE_HASH,'bundle mismatch')
        for index,name in enumerate(names):
            if not name.lower().endswith(('.ini','.int')):continue
            raw=afs.read_entry(index,f);lines,values=parse_lines(raw)
            resources.append(dict(resource='FILE/'+name,bytes=len(raw),sha256=core.digest(raw),encoding='ascii',line_count=len(lines),line_kinds=dict(Counter(x['kind'] for x in lines)),entry_count=len(values),exact_bundle_body_offsets=exact_positions(bundle,raw)))
            for row in values:entries.append(dict(id='FILE/'+name+'/line/'+str(row['line']),resource='FILE/'+name,**row))
    ids=[x['id'] for x in entries];core.require(len(ids)==len(set(ids)),'duplicate entry ID')
    summary=dict(schema=1,resources=len(resources),ini_resources=sum(x['resource'].endswith('.ini') for x in resources),int_resources=sum(x['resource'].endswith('.int') for x in resources),entries=len(entries),nonempty_values=sum(bool(x['value']) for x in entries),empty_values=sum(not x['value'] for x in entries),all_bytes_accounted_for=True,all_ascii=True,decode_failures=0,bundle_body_mirrors=sum(len(x['exact_bundle_body_offsets']) for x in resources),runtime_visibility_verified=False,semantic_review_complete=False,translation_backend=False,complete_game_text=False,source_modified=False,source_sha256=FILE_HASH)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('resources.json',resources),('entries.json',entries),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    core.require(core.file_digest(archive)==FILE_HASH,'FILE changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
