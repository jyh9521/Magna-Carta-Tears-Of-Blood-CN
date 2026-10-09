"""Bounded structural reader for the 13 observed class replication scripts.

This is not a general Function decoder, execution proof or bytecode writer.
Numeric token layouts are retained; unidentified semantics are not invented.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from audit_class_defaults import audit


def replication_script(reader,virtual_size,tables):
    start=reader.pos;virtual=0;tokens=[];references=[]
    def ref():
        nonlocal virtual
        at=reader.pos;n=reader.index()
        core.require(-len(tables['imports'])<=n<=len(tables['exports']),'script reference bounds')
        references.append(dict(offset=at,value=n));virtual+=4
    def fixed(n):
        nonlocal virtual
        reader.take(n);virtual+=n
    def token(depth=0):
        nonlocal virtual
        core.require(depth<64,'script recursion limit')
        at=reader.pos;vo=virtual;x=reader.integer('B');virtual+=1
        tokens.append(dict(offset=at,virtual_offset=vo,opcode=x))
        if x>=0x70:
            while token(depth+1)!=0x16:pass
        elif x==0x48:ref()
        elif x in (0x2d,0x39,0x3a):token(depth+1)
        elif x==0x18:fixed(2);token(depth+1)
        elif x==0x24:fixed(1)
        elif x in (0x16,0x26,0x27,0x28,0x2a):pass
        elif x==0x19:token(depth+1);fixed(3);token(depth+1)
        elif x==0x2e:ref();token(depth+1)
        else:raise ValueError(f'unsupported replication opcode 0x{x:02x}')
        core.require(virtual<=virtual_size,'script virtual size overflow')
        return x
    while virtual<virtual_size:token()
    core.require(virtual==virtual_size,'script virtual size mismatch')
    return dict(start=start,end=reader.pos,disk_bytes=reader.pos-start,virtual_bytes=virtual,
        sha256=core.digest(reader.data[start:reader.pos]),tokens=tokens,references=references,
        opcode_semantics_complete=False,execution_verified=False,editable=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out,replication_script),sort_keys=True))
if __name__=='__main__':main()
