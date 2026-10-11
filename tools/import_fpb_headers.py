"""Import source-bound native FPB header records into selected resource copies."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from localization.text import MappedEncoder,rewrite_fpb_header
from research_inventory import font_data
from audit_native_playbook import native_records
from audit_native_method_registration import require
from cri_afs import Afs
from afs import filename_toc

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('archive','corpus','batch','native-audit','imports','map','font-resource','out'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();original=a.archive.read_bytes()
    imports=json.loads(a.imports.read_text('utf8'));corpus=json.loads(a.corpus.read_text('utf8'))
    batch=json.loads(a.batch.read_text('utf8'));audit=json.loads(a.native_audit.read_text('utf8'))
    require(sha(original)==imports['archive_sha256'],'original archive fingerprint mismatch')
    require(sha(a.corpus.read_bytes())==imports['corpus_sha256'],'source corpus fingerprint mismatch')
    require(audit['native_evidence']['static_binding_verified'] is True,'native loader/getter evidence missing')
    entries={e['id']:(r,e) for r in corpus['resources'] for e in r['entries']}
    bindings={r['resource']:r for r in audit['resources']};bases={r['resource']:r for r in imports['resources']}
    mapping=json.loads(a.map.read_text('utf8'))
    encoder=MappedEncoder(mapping['entries'],font_tables=font_data(a.font_resource.read_bytes()))
    archive=Afs.open(a.archive);names=filename_toc(archive);receipts=[];seen=set()
    require(not a.out.exists(),'output already exists');a.out.mkdir(parents=True)
    with a.archive.open('rb') as stream:
        for target in batch['entries']:
            identity=target['id'];require(identity not in seen,'duplicate header target');seen.add(identity)
            require(target['status']=='reviewed' and target['reinsertion_policy']=='translate-header-record','header policy not authorized')
            resource,entry=entries[identity];name=resource['resource'];binding=bindings[name]
            require(entry['source_sha256']==target['source_sha256']==binding['header_source_sha256'],'header source binding mismatch')
            require(binding['header_key']==target['native_key'] and entry['offset']==0 and entry['source_bytes']==binding['header_length'],'header identity mismatch')
            original_resource=archive.read_entry(names.index(name.split('/',1)[1]),stream)
            require(sha(original_resource)==resource['sha256']==binding['source_sha256'],'original resource fingerprint mismatch')
            base=a.imports.parent/name.split('/',1)[1];raw=base.read_bytes()
            require(sha(raw)==bases[name]['modified_sha256'],'selected copy fingerprint mismatch')
            rebuilt,receipt=rewrite_fpb_header(raw,target['native_key'],target['source_sha256'],target['target'],encoder)
            old_records,old_pool=native_records(raw);new_records,new_pool=native_records(rebuilt)
            require([s for s,_,_ in old_records]==[s for s,_,_ in new_records],'native record keys/order changed')
            require(new_pool[:new_records[0][2]]==encoder.encode(target['target']),'header encoded readback mismatch')
            dest=a.out/base.name;dest.write_bytes(rebuilt);require(dest.read_bytes()==rebuilt,'output readback mismatch')
            receipts.append(dict(resource=name,id=identity,original_sha256=sha(original_resource),base_sha256=sha(raw),
                modified_sha256=sha(rebuilt),path=str(dest.resolve()),**receipt))
    report=dict(batch_sha256=sha(a.batch.read_bytes()),native_audit_sha256=sha(a.native_audit.read_bytes()),
        map_sha256=sha(a.map.read_bytes()),font_sha256=sha(a.font_resource.read_bytes()),resources=receipts,
        imported_header_fields=len(receipts),legacy_ids_changed=False,original_archive_modified=False,runtime_verified=False)
    report_path=a.out/'headers.json';report_path.write_text(json.dumps(report,indent=2)+'\n','utf8')
    require(json.loads(report_path.read_text('utf8'))==report,'receipt readback mismatch')
    print(f'FPB_HEADER_IMPORT_PASS resources={len(receipts)} header_fields={len(receipts)} body_windows_preserved=true original_unchanged=true runtime_verified=false')

if __name__=='__main__':main()
