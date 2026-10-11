"""Append non-ASCII translation glyphs without changing established inventory order."""
from pathlib import Path
import argparse
import hashlib
import json


def require(condition,message):
    if not condition: raise ValueError(message)


def collect(base,batches):
    chars=base['characters']
    require(isinstance(chars,list) and chars and all(isinstance(c,str) and len(c)==1 and ord(c)>=128 for c in chars), 'invalid base characters')
    require(len(chars)==len(set(chars)), 'duplicate base characters')
    result=list(chars);seen=set(chars);ids=set();fields=0
    for batch in batches:
        require(batch.get('locale')==base['locale'], 'inventory locale mismatch')
        require(isinstance(batch.get('entries'),list), 'missing translation entries')
        for row in batch['entries']:
            require(isinstance(row.get('id'),str) and row['id'] not in ids,'duplicate or invalid translation identity')
            ids.add(row['id']);fields+=1
            require(isinstance(row.get('target'),str) and bool(row['target']), 'empty or invalid target')
            for c in row['target']:
                require(not 0xd800<=ord(c)<=0xdfff, 'surrogate character')
                if ord(c)>=128 and c not in seen:result.append(c);seen.add(c)
    return dict(base,characters=result),dict(fields=fields,previous=len(chars),added=len(result)-len(chars),total=len(result),reinsertion_authorized=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();paths=[args.base]+args.batch
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result,report=collect(json.loads(args.base.read_text('utf8')),[json.loads(p.read_text('utf8')) for p in args.batch])
    report['input_sha256']=hashes
    # Everything is checked before publishing; never mutate an input in place.
    require(args.out.resolve() not in {p.resolve() for p in paths},'inventory output overlaps input')
    require(args.report.resolve() not in {p.resolve() for p in paths}|{args.out.resolve()},'report output overlaps input or inventory')
    for path,data in [(args.out,result),(args.report,report)]:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    print('FONT_INVENTORY_PASS '+json.dumps({k:v for k,v in report.items() if k!='input_sha256'},sort_keys=True))


if __name__=='__main__':main()
