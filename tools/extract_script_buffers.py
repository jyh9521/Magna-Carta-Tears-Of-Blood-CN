"""Extract complete TextBuffer serial bodies from ordinary FILE UE2 packages.

Exported script source and literals are references, not confirmed visible text.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import compact, package_tables
FILE_HASH='a9f7e2b34bfb5475bab2793821520295d120e2a122ccd363812f2d03c025072b'


def text_buffer(serial):
    core.require(len(serial)>=10 and serial[:9]==bytes(9), 'unsupported TextBuffer prefix')
    count,pos=compact(serial,9)
    core.require(count!=0, 'empty count requires separate layout review')
    unit=2 if count<0 else 1
    core.require(pos+abs(count)*unit==len(serial), 'TextBuffer size mismatch')
    raw=serial[pos:]
    core.require(raw.endswith(bytes(unit)), 'TextBuffer terminator missing')
    codec='utf-16-le' if unit==2 else 'cp949'
    return dict(text=raw[:-unit].decode(codec,errors='strict'), encoding=codec,
                data_offset=pos, count=count, data_sha256=core.digest(raw))


def literals(text):
    """Preserve double-quoted lexical candidates; exclude comments and name literals.

    Escapes are retained, not interpreted. Semantic visibility is unverified.
    """
    result=[];pos=0
    while pos<len(text):
        if text.startswith('//',pos):
            end=text.find('\n',pos+2);pos=len(text) if end<0 else end+1;continue
        if text.startswith('/*',pos):
            end=text.find('*/',pos+2)
            core.require(end>=0,'unterminated script comment');pos=end+2;continue
        if text[pos] in ('"', "'"):
            quote=text[pos];start=pos;pos+=1
            while pos<len(text) and text[pos]!=quote:
                if text[pos]=='\\':pos+=1
                pos+=1
            core.require(pos<len(text),'unterminated script literal')
            pos+=1
            if quote=='"':result.append(dict(character_offset=start,
                line=text.count('\n',0,start)+1, raw_literal=text[start:pos],
                semantic='unverified',editable=False))
            continue
        pos+=1
    return result



def packed_cp949_view(text):
    """Alternative reading of wide code units; never replace canonical source.

    ASCII stays ASCII. Non-ASCII units are interpreted as a CP949 byte pair
    in high-byte/low-byte order. Runtime use and provenance remain unverified.
    """
    parts=[]
    for char in text:
        value=ord(char)
        if value<128: parts.append(char)
        else:
            core.require(256<=value<=65535,'unsupported packed unit')
            parts.append(bytes((value>>8,value&255)).decode('cp949',errors='strict'))
    return ''.join(parts)


def audit(path,out):
    core.require(core.file_digest(path)==FILE_HASH, 'FILE archive identity mismatch')
    archive=Afs.open(path);names=filename_toc(archive);out=core.output_directory(out)
    counts=Counter();questions=[];sources=[];quotes=[]
    with path.open('rb') as stream:
        for index,name in enumerate(names):
            blob=archive.read_entry(index,stream)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);counts['ordinary_packages']+=1
            for export in tables['exports']:
                if export['class']!='TextBuffer':continue
                ident=f'FILE/{name}/export/{export["index"]}/TextBuffer'
                serial=blob[export['offset']:export['offset']+export['size']]
                try:body=text_buffer(serial)
                except (ValueError,IndexError,UnicodeError) as error:
                    questions.append(dict(id=ident,stage='body',error=str(error)));continue
                owner=export['outer'];owner_name=tables['exports'][owner-1]['name'] if 0<owner<=len(tables['exports']) else None
                row=dict(id=ident,package=name,package_sha256=core.digest(blob),
                    serial_offset=export['offset'],serial_size=len(serial),serial_sha256=core.digest(serial),
                    owner_index=owner,owner_name=owner_name,source_role='script-reference',
                    semantic='unverified',editable=False,**body)
                sources.append(row);counts['text_buffers']+=1;counts[body['encoding']]+=1
                try:
                    for number,quote in enumerate(literals(body['text'])):
                        item=dict(id=ident+f'/literal/{number}',source_id=ident,**quote)
                        if body['encoding']=='utf-16-le' and any(ord(c)>127 for c in quote['raw_literal']):
                            try:
                                item['alternative_reading']=packed_cp949_view(quote['raw_literal'])
                                item['alternative_mechanism']='high-low CP949 pair per non-ASCII code unit'
                                item['alternative_runtime_verified']=False
                            except (UnicodeError,ValueError): pass
                        quotes.append(item)
                except ValueError as error:questions.append(dict(id=ident,stage='lexical',error=str(error)))
    core.require(core.file_digest(path)==FILE_HASH,'original FILE changed')
    summary=dict(source_sha256=FILE_HASH,counts=dict(counts),literal_candidates=len(quotes),
                 parse_questions=len(questions),complete_game_text=False,
                 exhaustive_script_semantics=False,streamed_serial_mapping='unresolved')
    for name,value in [('sources.json',sources),('literals.json',quotes),('questions.json',questions),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
if __name__=='__main__':main()
