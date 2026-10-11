"""Validate explicit test-build translation/retention decisions for all literals.

Retention is a project scope decision, not proof that support values can never
be displayed. Original semantic classifications and runtime flags stay intact.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from font_poc import require,file_digest

def validate(source,batch,profile):
    require(profile['schema']==1 and profile['runtime_visibility_verified'] is False,'invalid compiled scope/runtime claim')
    originals={q['id']:q for q in source};translated={q['id']:q for q in batch['entries']};rows={q['id']:q for q in profile['decisions']}
    require(len(originals)==len(source) and len(translated)==len(batch['entries']) and len(rows)==len(profile['decisions']),'duplicate compiled scope identity')
    require(set(rows)==set(originals),'compiled source scope has missing/extra decisions')
    for ident,row in rows.items():
        q=originals[ident];require(row['source_sha256']==q['sha256'] and row['source_classification']==q['semantic_classification'],'compiled scope source identity mismatch')
        require(bool(row['reason']) and row['runtime_visibility_verified'] is False,'compiled scope reason/runtime mismatch')
        if ident in translated:require(row['decision']=='translate' and translated[ident]['source_sha256']==q['sha256'] and translated[ident]['status']=='reviewed','compiled translation scope mismatch')
        else:require(row['decision']=='retain-original' and bool(row['retention_kind']),'compiled retention scope mismatch')
    return dict(source_fields=len(rows),translated_fields=len(translated),retained_fields=len(rows)-len(translated),decisions_complete=True,full_game_visibility_proven=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('classifications','batch','profile','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(file_digest(a.classifications)==profile['classifications_sha256'],'compiled source classification fingerprint mismatch');result=validate(json.loads(a.classifications.read_text('utf8')),json.loads(a.batch.read_text('utf8')),profile);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n','utf8');print('COMPILED_SCOPE_DECISIONS_PASS source='+str(result['source_fields'])+' translated='+str(result['translated_fields'])+' retained='+str(result['retained_fields'])+' visibility_proven=false')
if __name__=='__main__':main()
