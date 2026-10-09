"""Read-only CHA/MDG record geometry audit, with legacy source-view reconciliation."""
from __future__ import annotations
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from extract_strings import field
from audit_decode_quarantine import checked_span


def records(blob,ext):
    core.require(ext in ('.cha','.mdg'),'unsupported record extension')
    core.require(len(blob)>=8,'record header truncated')
    count,kind=struct.unpack_from('<II',blob)
    stride,wanted=(299,11) if ext=='.cha' else (526,5)
    core.require(kind==wanted and len(blob)==8+count*stride,'record geometry mismatch')
    result=[]
    for index in range(count):
        start=8+index*stride
        text_offsets=[4] if ext=='.cha' else [8,271]
        metadata_offsets=[0]+list(range(259,299,4)) if ext=='.cha' else [0,4,263,267]
        text_fields=[]
        for n,relative in enumerate(text_offsets):
            raw_slot=blob[start+relative:start+relative+255];nul=raw_slot.find(b'\0')
            core.require(nul>=0 and not any(raw_slot[nul:]),'text field dirty padding or missing terminator')
            text_fields.append(dict(field_index=n,offset=start+relative,slot_bytes=255,slot_sha256=core.digest(raw_slot),raw=raw_slot[:nul]))
        result.append(dict(index=index,offset=start,size=stride,sha256=core.digest(blob[start:start+stride]),
            metadata=[dict(offset=start+relative,record_relative=relative,value=struct.unpack_from('<I',blob,start+relative)[0],semantic='unverified-u32') for relative in metadata_offsets],text_fields=text_fields))
    return result


def classify_candidate(row,parsed):
    start=row['offset'];end=start+row['source_bytes']
    for record in parsed:
        for f in record['text_fields']:
            if f['offset']<=start<=end<=f['offset']+len(f['raw']):return dict(classification='covered-text',record_index=record['index'],field_index=f['field_index'])
        for m in record['metadata']:
            if m['offset']<=start<end<=m['offset']+4:return dict(classification='inside-u32-metadata',record_index=record['index'],metadata_offset=m['offset'],metadata_value=m['value'],semantic='unverified')
    return dict(classification='unresolved',semantic='unverified')


def audit(corpus_path,ship,out):
    before=core.file_digest(corpus_path);expected=json.loads((ROOT/'docs/EXTRACTION_COVERAGE.json').read_text('utf8'))['verified_archive_hashes']['SHIP.AFS']
    core.require(core.file_digest(ship)==expected,'SHIP identity mismatch')
    corpus=json.loads(corpus_path.read_text('utf8'));archive=Afs.open(ship);names=filename_toc(archive)
    inventory=[];aliases=[];candidates=[];new_fields=[]
    with ship.open('rb') as stream:
        for resource in corpus['resources']:
            name=resource['resource'].split('/',1)[1];ext=Path(name).suffix
            if ext not in ('.cha','.mdg'):continue
            blob=archive.read_entry(names.index(name),stream)
            core.require(len(blob)==resource['size'] and core.digest(blob)==resource['sha256'],'resource identity mismatch')
            parsed=records(blob,ext);fresh={}
            for record in parsed:
                body=[]
                for f in record['text_fields']:
                    row=field(resource['resource']+f"/record-index/{record['index']}/field/{f['field_index']}",f['raw'],f['offset'],
                        resource=resource['resource'],resource_sha256=resource['sha256'],record_index=record['index'],field_index=f['field_index'],
                        slot_bytes=255,slot_sha256=f['slot_sha256'],editable=False,reinsertion_approved=False,semantic='name-or-description-runtime-unverified')
                    fresh[(row['offset'],row['source_bytes'],row['source_sha256'])]=row;new_fields.append(row);body.append(row['id'])
                inventory.append(dict(resource=resource['resource'],record_index=record['index'],offset=record['offset'],size=record['size'],sha256=record['sha256'],metadata=record['metadata'],fields=body))
            for old in resource['entries']:
                checked_span(blob,old);key=(old['offset'],old['source_bytes'],old['source_sha256'])
                core.require(key in fresh,'legacy source field differs from record geometry')
                aliases.append(dict(old_id=old['id'],new_id=fresh[key]['id'],source_sha256=old['source_sha256']))
            core.require(len(resource['entries'])==len(fresh),'record field coverage mismatch')
            for row in resource.get('candidates',[]):
                checked_span(blob,row)
                result=classify_candidate(row,parsed)
                candidates.append(dict(id=row['id'],offset=row['offset'],source_bytes=row['source_bytes'],source_sha256=row['source_sha256'],**result,editable=False))
    summary=dict(schema=1,source_corpus_sha256=before,ship_sha256=expected,resources=len(set(r['resource'] for r in inventory)),
        records=len(inventory),text_fields=len(new_fields),legacy_fields_exactly_reconciled=len(aliases),
        decode_failures=sum(r['decode']!='strict' for r in new_fields),candidates=len(candidates),
        metadata_candidates=sum(r['classification']=='inside-u32-metadata' for r in candidates),
        unresolved_candidates=sum(r['classification']=='unresolved' for r in candidates),new_text_fields=0,
        complete_game_text=False,source_modified=False,metadata_semantics_complete=False)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('records.json',inventory),('text-fields.json',new_fields),('aliases.json',aliases),('candidate-contexts.json',candidates),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
    core.require(core.file_digest(ship)==expected and core.file_digest(corpus_path)==before,'input changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['corpus','ship','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.ship,a.out),sort_keys=True))
