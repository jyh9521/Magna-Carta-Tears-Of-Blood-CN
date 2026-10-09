"""Link script reference literals to exact bytes in ordinary package exports.

Byte containment and a preceding value are not bytecode decoding or reachability.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from extract_script_buffers import FILE_HASH


def search_literal(blob,exports,content,encoding):
    raw=content.encode(encoding,errors='strict')
    if not raw:return []
    terminator=b'\0\0' if encoding=='utf-16-le' else b'\0'
    needle=raw+terminator;hits=[]
    for export in exports:
        if export['class']=='TextBuffer':continue
        start=export['offset'];end=start+export['size']
        core.require(0<=start<=end<=len(blob),'export bounds')
        pos=start
        while True:
            pos=blob.find(needle,pos,end)
            if pos<0:break
            hits.append(dict(export_index=export['index'],export_name=export['name'],
                export_class=export['class'],owner_index=export['outer'],offset=pos,
                bytes=len(needle),preceding_byte=blob[pos-1] if pos>start else None,
                matched_sha256=core.digest(needle),instruction_boundary_verified=False,
                execution_verified=False,editable=False))
            pos+=1
    return hits


def audit(path,source_dir,out):
    core.require(core.file_digest(path)==FILE_HASH,'FILE identity mismatch')
    sources=json.loads((source_dir/'sources.json').read_text('utf8'))
    quotes=json.loads((source_dir/'literals.json').read_text('utf8'))
    by_id={r['id']:r for r in sources};core.require(len(by_id)==len(sources),'duplicate sources')
    archive=Afs.open(path);names=filename_toc(archive);result=[];counts=Counter()
    by_package={}
    for quote in quotes:
        core.require(quote['source_id'] in by_id,'missing script source')
        source=by_id[quote['source_id']]
        by_package.setdefault(source['package'],[]).append((source,quote))
    with path.open('rb') as stream:
        for name,items in by_package.items():
            blob=archive.read_entry(names.index(name),stream);tables=package_tables(blob)
            core.require(all(core.digest(blob)==s['package_sha256'] for s,q in items),'script package mismatch')
            for source,quote in items:
                text=quote['raw_literal']
                core.require(text.startswith('"') and text.endswith('"'),'literal delimiters')
                if '\\' in text:
                    counts['escaped_reference_not_interpreted']+=1;continue
                variants=[('canonical-cp949',text[1:-1],'cp949'),('canonical-utf16le',text[1:-1],'utf-16-le')]
                if 'alternative_reading' in quote:
                    variants.append(('packed-cp949-reading',quote['alternative_reading'][1:-1],'cp949'))
                for mechanism,content,encoding in variants:
                    try:hits=search_literal(blob,tables['exports'],content,encoding)
                    except UnicodeError:counts['variant_encoding_failures']+=1;continue
                    for hit in hits:
                        owner=hit['owner_index'];hit['owner_name']=tables['exports'][owner-1]['name'] if 0<owner<=len(tables['exports']) else None
                    if hits:
                        result.append(dict(source_id=source['id'],literal_id=quote['id'],
                            source_owner=source['owner_name'],mechanism=mechanism,
                            content=content,encoding=encoding,hits=hits))
                        counts[mechanism]+=1
    core.require(core.file_digest(path)==FILE_HASH,'FILE changed')
    summary=dict(source_sha256=FILE_HASH,literal_candidates=len(quotes),linked_variants=len(result),
        hit_occurrences=sum(len(r['hits']) for r in result),counts=dict(counts),
        complete_game_text=False,bytecode_decoder_complete=False,execution_verified=False)
    out=core.output_directory(out)
    for name,value in [('links.json',result),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--sources',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.sources,a.out),sort_keys=True))
if __name__=='__main__':main()
