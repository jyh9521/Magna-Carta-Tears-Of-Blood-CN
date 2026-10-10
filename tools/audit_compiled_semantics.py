"""Classify every compiled string using reparsed ancestor call context."""
from pathlib import Path
from collections import Counter
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from audit_literal_contexts import audit as context_audit
DISPLAY={'SetCaption','SetText','SetHelpText','AddButton','AddPage','AddList','SetMessage','SetBoxName','AddMessage','Message','ClientMessage','DrawText','DrawTextClipped','MrtsDrawTextLine','AddText','SetSentinel','TextSize'}
DIAGNOSTIC={'Log','Warn','Error','LogEventString','LogWorldEventString','BadParameters','EndLogging'}
INTERNAL={'LoadObjectB','LoadObjectNB','AddNBObject','DynamicLoadObject','FindObject','ConsoleCommand','ClientTravel','GiveWeapon','ParseOption','GetDefaultURL','UpdateURL','GetIntOption','GetPropertyText','SetPropertyText','AddFile','Localize'}
COMPARISONS={'NotEqual_StrStr','EqualEqual_StrStr','ComplementEqual_StrStr'}


def classify(row):
    text=row['text'];calls=row['call_context'];symbols=[s for c in calls for s in c['symbols']]
    binding=None
    for call in reversed(calls):
        recognized=set(call['symbols'])&(DISPLAY|DIAGNOSTIC|INTERNAL)
        if recognized:
            core.require(len(recognized)==1,'ambiguous semantic call symbols');binding=next(iter(recognized));break
    if not text:category,reason='internal-empty-value','empty-string-still-preserved'
    elif binding in INTERNAL:category,reason='internal-lookup-or-command-candidate','nearest-recognized-lookup-or-command'
    elif binding in DIAGNOSTIC:category,reason='diagnostic-text-candidate','nearest-recognized-diagnostic-call'
    elif binding in DISPLAY:
        if row['owner']=='DisplayDebug':category,reason='diagnostic-text-candidate','displaydebug-owner-with-display-call'
        else:category,reason='visible-text-candidate','nearest-recognized-display-call'
    elif set(symbols)&COMPARISONS:category,reason='unresolved','comparison-does-not-prove-nonvisible'
    elif row['assignment_context']:category,reason='unresolved','assignment-consumer-not-established'
    else:category,reason='unresolved','no-reviewed-consumer-symbol'
    return dict(row,semantic_classification=category,semantic_reason=reason,nearest_reviewed_symbol=binding,
        semantic_review='context-classified-not-runtime-proof',editable=False,backend_eligible=False,runtime_visibility_verified=False)


def audit(archive,objects,strings,out):
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    context_summary=context_audit(archive,objects,strings,out/'reparsed-contexts')
    rows=json.loads((out/'reparsed-contexts/contexts.json').read_text('utf8'));result=[classify(r) for r in rows]
    core.require(len(result)==1207 and len({r['id'] for r in result})==1207,'compiled string count')
    summary=dict(schema=1,string_constants=len(result),counts=dict(sorted(Counter(r['semantic_classification'] for r in result).items())),
        reasons=dict(sorted(Counter(r['semantic_reason'] for r in result).items())),objects_reparsed=context_summary['objects_reparsed'],
        all_contexts_reparsed=True,context_role_review_complete=True,runtime_visibility_verified=False,backend_eligible_values=0,
        complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    for name,value in [('classifications.json',result),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['archive','objects','strings','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.objects,a.strings,a.out),sort_keys=True))
