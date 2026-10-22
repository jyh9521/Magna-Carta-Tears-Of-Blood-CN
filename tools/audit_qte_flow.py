"""Read-only original native binding and source/compiled QTE-call audit.

Tracks a narrow GetGreat dependency, not full Unreal VM execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from research_native import ElfImage, ELF_SHA256
from audit_native_method_registration import bind_inline
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from audit_compiled_scripts import body
from extract_script_buffers import FILE_HASH,text_buffer


def audit(elf,archive):
    eb=elf.read_bytes();assert hashlib.sha256(eb).hexdigest()==ELF_SHA256
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==FILE_HASH
    binding=bind_inline(ElfImage(eb),'intUMrtsDataManagerexecGetGreat')
    assert binding['callback']=='0x2f8b40'
    assert {'va':'0x2f8b58','target':'0x2f8b80'} in binding['bounded_callback_jals']
    a=Afs.open(archive)
    with archive.open('rb') as f:blob=a.read_entry(filename_toc(a).index('MrtsGame.u'),f)
    t=package_tables(blob);exports=ordinary_exports(blob,t);by={r['index']:r for r in exports}
    source_export=by[12857]
    source=text_buffer(blob[source_export['offset']:source_export['offset']+source_export['size']])['text']
    source=source.replace('\r\r\n','\n').replace('\r\n','\n')
    assert source.count('Magi.DataManager.GetGreat()')==2
    targets={-(i+1) for i,v in enumerate(t['imports']) if v['name']=='GetGreat'}
    assert len(targets)==1
    uses=[]
    for r in exports:
        if r['class'] not in ('Function','NativeFunction','State'):continue
        raw=blob[r['offset']:r['offset']+r['size']]
        z=body(raw,t,r)
        refs=[v for v in z['script']['references'] if v['kind']=='object' and v['value'] in targets]
        if refs:uses.append(dict(index=r['index'],name=r['name'],outer=r['outer'],getgreat_refs=len(refs),serial_sha256=hashlib.sha256(raw).hexdigest()))
    assert [(r['index'],r['name'],r['getgreat_refs']) for r in uses]==[(8221,'TimeOver',1),(8311,'TestBit',1)]
    # Source assertions support the intended path; compiled refs alone do not prove semantics.
    assertions=['RecordBit( 0, 0 );','Bits[ CurBit ].Result = RR_Great;','if( IsInState( \'RMIdle\' ) == true )','DesireBit = CurBit;','GotoState( \'RMFinish\' );','if( bNowPlaying == true )','PlayRhythm();']
    assert all(s in source for s in assertions)
    return dict(elf_sha256=ELF_SHA256,file_afs_sha256=FILE_HASH,native_binding=binding,
                source_export=12857,source_serial_sha256=hashlib.sha256(blob[source_export['offset']:source_export['offset']+source_export['size']]).hexdigest(),
                compiled_getgreat_users=uses,source_assertions=assertions,
                first_input_required=True,full_vm_execution_verified=False,runtime_verified=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--elf',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();r=audit(a.elf,a.archive);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');assert json.loads(a.out.read_text('utf8'))==r
    print('QTE_FLOW PASS native_binding=true compiled_GetGreat_users=TimeOver,TestBit first_input_required=true runtime_verified=false')
