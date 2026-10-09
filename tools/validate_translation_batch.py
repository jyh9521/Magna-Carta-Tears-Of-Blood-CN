"""Validate review batches against an extracted source catalog and one MD glossary.

Passing checks authorizes neither unknown-format reinsertion nor runtime QA.
"""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'lib'),str(ROOT/'tools')]
from localization.text import validate_target
import font_poc as core


def glossary_terms(path: Path) -> list[tuple[str,str]]:
    terms=[]
    for line in path.read_text('utf8').splitlines():
        if not line.startswith('|'):
            continue
        cells=[cell.strip() for cell in line.strip('|').split('|')]
        if len(cells)==5 and cells[3] in ('暂定统一','已统一'):
            terms.append((cells[0],cells[1]))
    core.require(bool(terms),'glossary terms missing')
    core.require(len({source for source,_ in terms})==len(terms),'duplicate glossary source')
    return terms


def validate(catalog: dict,batch: dict,terms: list[tuple[str,str]],font_cmap=None) -> dict:
    core.require(batch.get('schema')==1 and isinstance(batch.get('locale'),str), 'invalid batch schema')
    rows=[row for resource in catalog['resources'] for row in resource['entries']]
    core.require(len({row['id'] for row in rows})==len(rows),'ambiguous source id')
    index={row['id']:row for row in rows}
    seen=set();characters=set()
    for target in batch['entries']:
        identity=target['id']
        core.require(identity not in seen,'duplicate translation id');seen.add(identity)
        core.require(identity in index,'unknown translation id')
        source=index[identity]
        core.require(source['source_sha256']==target['source_sha256'],'source identity mismatch')
        core.require(source['decode']=='strict' and source.get('controls')=='recognized','quarantined source')
        core.require(target.get('status') in ('draft','trial-draft','reviewed'),'invalid translation status')
        text=source['references'][catalog['source_locale']]
        validate_target(text,target['target'])
        for original,canonical in terms:
            if original in text:
                core.require(canonical in target['target'],'glossary mismatch: '+original)
        chars={ch for ch in target['target'] if ord(ch)>127};characters.update(chars)
        if font_cmap is not None:
            core.require(all(font_cmap.get(ord(ch)) not in (None,'.notdef') for ch in chars),'missing font glyph')
    return dict(entries=len(seen),unique_non_ascii_characters=len(characters),
                glyph_capacity='not assessed', reinsertion='not performed', runtime='unverified')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,required=True);p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--glossary',type=Path,default=ROOT/'GLOSSARY.md');p.add_argument('--font',type=Path)
    args=p.parse_args();cmap=None
    if args.font:
        from fontTools.ttLib import TTFont
        with TTFont(args.font) as face:cmap=face.getBestCmap()
    result=validate(json.loads(args.catalog.read_text('utf8')),json.loads(args.batch.read_text('utf8')),
                    glossary_terms(args.glossary),cmap)
    print('TRANSLATION BATCH PASS '+json.dumps(result,sort_keys=True))


if __name__=='__main__': main()
