"""Bind reviewed UI target hashes to a derived catalog; source bytes stay frozen."""
from pathlib import Path
import argparse,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from import_audited_fields import binding_index,resolve_source
from ui_punctuation import omit_period,validated_empty_suffix
from font_poc import require


def prepare(corpus,changes):
    c=json.loads(json.dumps(corpus));index,aliases=binding_index(c);seen=set()
    for row in changes:
        if not row['id'].startswith('SHIP/'):continue
        r,e=resolve_source(index,aliases,row);canonical=e['canonical_id'];require(canonical not in seen,'duplicate UI review');seen.add(canonical)
        require(omit_period(row['previous_target'])==row['target'] and row['status']=='reviewed','invalid UI punctuation review')
        if row['target']=='':validated_empty_suffix(e,row)
        original=index[canonical][1]
        if 'source_control_interpretation' in original:
            original['source_control_interpretation']['target_sha256']=hashlib.sha256(row['target'].encode('utf8')).hexdigest()
    return c


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('corpus','review','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();c=prepare(json.loads(a.corpus.read_text('utf8')),json.loads(a.review.read_text('utf8')));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(a.out.read_text('utf8'))==c,'UI catalog reopen mismatch');print('UI_PUNCTUATION_CATALOG_PASS source_fields_preserved=true')

if __name__=='__main__':main()
