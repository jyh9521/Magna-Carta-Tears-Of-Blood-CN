"""Merge fingerprinted native-header overlays into a complete resource-copy set."""
from pathlib import Path
import argparse,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from audit_native_method_registration import require
from audit_native_playbook import native_records

def sha(data):return hashlib.sha256(data).hexdigest()

def merge_receipts(imports,headers):
    result=copy.deepcopy(imports);by={r['resource']:r for r in result['resources']}
    require(len(by)==len(result['resources']),'duplicate base resource identity')
    require(imports['map_sha256']==headers['map_sha256'] and imports['font_sha256']==headers['font_sha256'],'header/base mapping or font mismatch')
    seen=set()
    for overlay in headers['resources']:
        name=overlay['resource'];require(name in by and name not in seen,'missing or duplicate header overlay');seen.add(name)
        base=by[name]
        require('header_fields' not in base,'header overlay already applied')
        require(overlay['base_sha256']==base['modified_sha256'] and overlay['original_sha256']==base['original_sha256'],'header overlay base fingerprint mismatch')
        delta=overlay['offset_delta'];require(type(delta) is int,'invalid header offset delta')
        require(overlay['new_length']-overlay['old_length']==delta,'inconsistent header offset delta')
        for field in base['fields']:
            require(field['new_offset']>=overlay['old_length'],'body field overlaps header')
            field['new_offset']+=delta
        base.update(modified_sha256=overlay['modified_sha256'],modified_bytes=base['modified_bytes']+delta,
                    selected_fields=base['selected_fields']+1,header_fields=[copy.deepcopy(overlay)])
    require(len(seen)==headers['imported_header_fields'],'header count mismatch')
    result.update(native_header_fields=len(seen),total_selected_fields=sum(r['selected_fields'] for r in result['resources']),
                  full_game_scope_complete=False,iso_generated=False)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('imports','headers','batch','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();imports=json.loads(a.imports.read_text('utf8'));headers=json.loads(a.headers.read_text('utf8'))
    require(sha(a.batch.read_bytes())==headers['batch_sha256'],'header translation batch fingerprint mismatch')
    merged=merge_receipts(imports,headers);overlays={r['resource']:r for r in headers['resources']}
    require(not a.out.exists(),'output already exists');a.out.mkdir(parents=True)
    for row,old in zip(merged['resources'],imports['resources']):
        name=Path(row['resource']).name;require(name==row['resource'].split('/',1)[1],'unsafe resource name')
        source=a.imports.parent/name;base=source.read_bytes();require(sha(base)==old['modified_sha256'],'base copy fingerprint mismatch')
        if row['resource'] in overlays:
            overlay=overlays[row['resource']];data=Path(overlay['path']).read_bytes()
            require(sha(data)==overlay['modified_sha256'],'header copy fingerprint mismatch')
            before,bp=native_records(base);after,np=native_records(data)
            require(before[0]==(overlay['native_key'],0,overlay['old_length']) and after[0]==(overlay['native_key'],0,overlay['new_length']),'header geometry mismatch')
            require([r[0] for r in before]==[r[0] for r in after],'native keys/order changed')
            require(bp[before[0][2]:]==np[after[0][2]:],'header overlay changed body/gap/tail')
            require(np[:after[0][2]].hex()==overlay['encoded_hex'],'header bytes mismatch')
            require(all(new==(k,o+overlay['offset_delta'],n) for (k,o,n),new in zip(before[1:],after[1:])),'native window relocation mismatch')
        else:data=base
        require(sha(data)==row['modified_sha256'] and len(data)==row['modified_bytes'],'merged copy fingerprint/size mismatch')
        dest=a.out/name;dest.write_bytes(data);require(dest.read_bytes()==data,'merged copy readback mismatch')
    merged.update(parent_import_sha256=sha(a.imports.read_bytes()),header_import_sha256=sha(a.headers.read_bytes()))
    output=a.out/'reinsertion.json';output.write_text(json.dumps(merged,indent=2)+'\n','utf8')
    require(json.loads(output.read_text('utf8'))==merged,'merged receipt readback mismatch')
    print(f"RESOURCE_IMPORT_MERGE_PASS resources={len(merged['resources'])} fields={merged['total_selected_fields']} header_fields={merged['native_header_fields']} all_copies_reopened=true iso_generated=false")

if __name__=='__main__':main()
