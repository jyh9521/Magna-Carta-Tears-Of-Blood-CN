"""Validate source-bound visible configuration translations without changing assets."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from config_translation import validate_value,group_labels
from audit_native_method_registration import require

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,required=True);p.add_argument('--batch',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.corpus.read_text('utf8'));b=json.loads(a.batch.read_text('utf8'))
    index={e['id']:(r,e) for r in c['resources'] for e in r['entries']};seen=set();labels=0
    groups=group_labels(index,b['entries'])
    for target in b['entries']:
        require(target['id'] not in seen,'duplicate configuration target');seen.add(target['id']);resource,entry=index[target['id']]
        require(resource['resource'].startswith('FILE/') and resource['resource'].lower().endswith(('.int','.ini')),'not a configuration value')
        require(entry['semantic']=='visible-text-candidate' and entry['source_encoding']=='ascii','configuration role/encoding mismatch')
        require(entry['source_sha256']==target['source_sha256'] and target['status']=='reviewed','source mismatch/unreviewed configuration target')
        validate_value(entry['references']['und'],target['target'],target['value_kind'],parent_labels=groups);labels+=target['value_kind']=='preference-descriptor'
    print(f'CONFIG_TRANSLATION_VALIDATION_PASS fields={len(seen)} descriptors={labels} machine_fields_preserved=true template_tokens_preserved=true runtime_verified=false')

if __name__=='__main__':main()
