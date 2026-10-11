"""Validate review batches against an extracted source catalog and one MD glossary.

Passing checks authorizes neither unknown-format reinsertion nor runtime QA.
"""
import argparse
import json
import re
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'lib'),str(ROOT/'tools')]
from localization.text import validate_target
import font_poc as core
from source_interpretation import source_text,control_policy


class GlossaryTerms(list):
    """List-compatible terms carrying explicit disambiguation from the MD table."""
    def __init__(self):
        super().__init__()
        self.exact_only=set()


def glossary_terms(path: Path) -> list[tuple[str,str]]:
    terms=GlossaryTerms()
    for line in path.read_text('utf8').splitlines():
        if not line.startswith('|'):
            continue
        cells=[cell.strip() for cell in line.strip('|').split('|')]
        if len(cells)==5 and cells[3] in ('暂定统一','已统一'):
            terms.append((cells[0],cells[1]))
            if '[match=exact-source]' in cells[4]:terms.exact_only.add(cells[0])
    core.require(bool(terms),'glossary terms missing')
    core.require(len({source for source,_ in terms})==len(terms),'duplicate glossary source')
    return terms


def validate(catalog: dict,batch: dict,terms: list[tuple[str,str]],font_cmap=None) -> dict:
    core.require(batch.get('schema')==1 and isinstance(batch.get('locale'),str), 'invalid batch schema')
    rows=[row for resource in catalog['resources'] for row in resource['entries']]
    core.require(len({row['id'] for row in rows})==len(rows),'ambiguous source id')
    index={row['id']:row for row in rows}
    aliases={}
    for row in rows:
        for alias in row.get('source_aliases',[]):
            aliases.setdefault(alias,set()).add(row['id'])
    seen=set();characters=set()
    for target in batch['entries']:
        identity=target['id']
        if identity not in index:
            candidates=aliases.get(identity,set())
            core.require(bool(candidates),'unknown translation id')
            core.require(len(candidates)==1,'ambiguous translation alias')
            identity=next(iter(candidates))
        core.require(identity not in seen,'duplicate translation id or resolved alias');seen.add(identity)
        source=index[identity]
        core.require(source['source_sha256']==target['source_sha256'],'source identity mismatch')
        core.require(source['decode']=='strict' and source.get('controls')=='recognized','quarantined source')
        core.require(target.get('status') in ('draft','trial-draft','reviewed'),'invalid translation status')
        core.require(target.get('reinsertion_policy','translate') in
                     ('translate','retain-original','pending-role-review'),
                     'invalid reinsertion policy')
        text=source_text(source,catalog['source_locale'])
        from ui_punctuation import validated_empty_suffix
        if target['target'] == '':
            validated_empty_suffix(source,target)
        else:
            validate_target(text,target['target'],control_policy=control_policy(source,target['target']))
        # Longest non-overlapping terms prevent a short name (e.g. 리스) from
        # matching inside a longer registered name (e.g. 크리스 아크웨이).
        canonical_by_source = dict(terms)
        if terms:
            pattern = '|'.join(re.escape(term) for term in
                               sorted(canonical_by_source, key=len, reverse=True))
            for match in re.finditer(pattern, text):
                original = match.group()
                # Apple/apology, jade/prison and grammatical particles can
                # share Korean spellings. These MD terms only bind complete
                # field values; this is not an exclusion of their name fields.
                if original in getattr(terms,'exact_only',set()) and text.strip()!=original:
                    continue
                core.require(canonical_by_source[original] in target['target'],
                             'glossary mismatch: '+original)
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
