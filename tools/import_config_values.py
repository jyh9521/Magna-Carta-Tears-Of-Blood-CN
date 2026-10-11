"""Rebuild separate configuration file copies from reviewed, source-bound values."""
from pathlib import Path
import argparse,hashlib,json,sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from config_translation import rewrite_values,group_labels
from localization.text import MappedEncoder
from research_inventory import font_data
from extract_script_buffers import FILE_HASH
from cri_afs import Afs
from afs import filename_toc
from audit_native_method_registration import require

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','corpus','batch','map','font-resource','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();require(sha(a.archive.read_bytes())==FILE_HASH,'original FILE fingerprint mismatch')
    corpus=json.loads(a.corpus.read_text('utf8'));batch=json.loads(a.batch.read_text('utf8'))
    index={e['id']:(r,e) for r in corpus['resources'] for e in r['entries']};groups=defaultdict(list);seen=set()
    for t in batch['entries']:
        require(t['id'] not in seen,'duplicate configuration target');seen.add(t['id']);r,e=index[t['id']]
        require(r['resource'].startswith('FILE/') and r['resource'].lower().endswith(('.int','.ini')),'unsupported configuration source')
        require(e['semantic']=='visible-text-candidate' and e['source_encoding']=='ascii' and t['status']=='reviewed','configuration role/encoding/review gate mismatch')
        require(t.get('reinsertion_policy','translate')=='translate','configuration policy does not authorize writing')
        groups[r['resource']].append((r,e,t))
    mapping=json.loads(a.map.read_text('utf8'));require(mapping['locale']==batch['locale'],'configuration font locale mismatch')
    encoder=MappedEncoder(mapping['entries'],font_tables=font_data(a.font_resource.read_bytes()))
    parents=group_labels(index,batch['entries'])
    archive=Afs.open(a.archive);names=filename_toc(archive);require(not a.out.exists(),'output already exists');a.out.mkdir(parents=True);rows=[]
    with a.archive.open('rb') as f:
        for resource,items in sorted(groups.items()):
            name=resource.split('/',1)[1];require(Path(name).name==name,'invalid configuration member name')
            original=archive.read_entry(names.index(name),f);require(sha(original)==items[0][0]['sha256'],'configuration resource fingerprint mismatch')
            modified,fields=rewrite_values(original,[e for _,e,_ in items],[t for _,_,t in items],encoder,parent_labels=parents)
            out=a.out/name;out.write_bytes(modified);require(out.read_bytes()==modified,'configuration copy readback mismatch')
            rows.append(dict(resource=resource,original_sha256=sha(original),modified_sha256=sha(modified),original_bytes=len(original),modified_bytes=len(modified),selected_fields=len(fields),fields=fields))
    report=dict(schema=1,locale=batch['locale'],archive_sha256=FILE_HASH,corpus_sha256=sha(a.corpus.read_bytes()),batch_sha256=sha(a.batch.read_bytes()),map_sha256=sha(a.map.read_bytes()),font_sha256=sha(a.font_resource.read_bytes()),resources=rows,imported_fields=len(seen),runtime_verified=False,iso_generated=False)
    out=a.out/'config-imports.json';out.write_text(json.dumps(report,indent=2)+'\n','utf8');require(json.loads(out.read_text())==report,'configuration receipt readback mismatch')
    require(sha(a.archive.read_bytes())==FILE_HASH,'original FILE changed')
    print(f'CONFIG_IMPORT_PASS resources={len(rows)} fields={len(seen)} structure_templates_untargeted_preserved=true original_unchanged=true iso_generated=false')

if __name__=='__main__':main()
