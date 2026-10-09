"""Review quarantined lexical structures without relaxing the import validator."""
from __future__ import annotations
import argparse,json,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
import font_poc as core
from localization.text import TOKEN,protected_tokens


def observations(text,names):
 result=[];pos=0
 while pos<len(text):
  ch=text[pos]
  if ord(ch)<32:
   result.append(dict(offset=pos,end=pos+1,lexeme=ch,classification='control-character',codepoint=ord(ch)));pos+=1;continue
  if ch not in '$%<>{}':pos+=1;continue
  match=TOKEN.match(text,pos)
  if match:pos=match.end();continue
  end=pos+1;classification='unknown-special';links=[]
  if ch=='%' and re.search(r'\d+(?:\.\d+)?$',text[:pos]):classification='numeric-percent-candidate'
  elif ch=='<' and '>' in text[pos+1:]:
   candidate_end=text.index('>',pos+1)+1;inside=text[pos+1:candidate_end-1]
   if '<' not in inside:
    end=candidate_end;classification='closed-nonascii-angle-candidate';links=names.get(inside,[])
  elif ch=='>' and pos>0 and text[pos-1]=='-':classification='arrow-candidate'
  result.append(dict(offset=pos,end=end,lexeme=text[pos:end],classification=classification,name_source_links=links,runtime_semantics_verified=False))
  pos=end
 return result


def audit(corpus_path,out):
 before=core.file_digest(corpus_path);c=json.loads(corpus_path.read_text('utf8'));names={}
 for resource in c['resources']:
  if not resource['resource'].endswith('.itm'):continue
  for row in resource['entries']:
   if row.get('field_index')==0 and row['decode']=='strict':
    text=row['references']['ko-KR'];names.setdefault(text,[]).append(dict(id=row['id'],source_sha256=row['source_sha256'],record_key=row['record_key']))
 result=[]
 for resource in c['resources']:
  for row in resource['entries']:
   if row.get('controls')!='quarantined':continue
   core.require(row['decode']=='strict','quarantined source not decoded');text=row['references']['ko-KR'];findings=observations(text,names)
   core.require(bool(findings),'quarantine without lexical finding')
   try:protected_tokens(text);validator_accepts=True
   except ValueError:validator_accepts=False
   result.append(dict(id=row['id'],resource=resource['resource'],source_sha256=row['source_sha256'],source_text=text,observations=findings,
    current_protected_token_validator_accepts=validator_accepts,editable=False,reinsertion_approved=False,semantic_review='pending'))
 counts=Counter(f['classification'] for r in result for f in r['observations'])
 summary=dict(schema=1,source_corpus_sha256=before,quarantined_fields=len(result),observations=sum(counts.values()),classifications=dict(sorted(counts.items())),
  angle_observations_with_exact_item_name=sum(bool(f.get('name_source_links')) for r in result for f in r['observations']),
  fields_with_control_characters=sum(any(f['classification']=='control-character' for f in r['observations']) for r in result),
  validator_modified=False,source_modified=False,complete_game_text=False,translation_gate='coverage-audit-pending')
 out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
 for name,value in [('control-observations.json',result),('summary.json',summary)]:
  p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
 core.require(core.file_digest(corpus_path)==before,'input changed');return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.corpus,a.out),sort_keys=True))
