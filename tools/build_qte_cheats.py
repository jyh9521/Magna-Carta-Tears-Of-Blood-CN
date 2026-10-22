"""Generate the Korean native GetGreat auto-QTE candidate on separate copies."""
import argparse
import json
from pathlib import Path
from build_gameplay_cheats import validate, transform, sha


def render(p):
    r=p['codes'][0]
    return (f"gametitle=Magna Carta NTSC-K QTE candidate ({p['serial']} / {p['crc']})\n"
            '// Original native debug path; no global controller injection.\n'
            '// First input starts an attack rhythm; subsequent timeout beats auto-complete.\n'
            f"[{r['label']}]\ndescription={r['description']}\n"
            f"// {r['binding']}; {r['expected']} -> {r['replacement']}; runtime pending.\n"
            f"patch=1,EE,{r['va']},word,{r['replacement']}\n")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['baseline','apply','modified','rollback','pnach'])
    ap.add_argument('--profile',type=Path,required=True);ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args();p=json.loads(a.profile.read_text('utf8'));r=p['codes'][0];blob=a.input.read_bytes()
    if a.mode=='baseline':
        validate(blob,p);print('BASELINE PASS GetGreat_original_bit1=true sha256='+sha(blob));return
    if a.mode=='modified':
        validate(blob,p,r,modified=True);print('MODIFIED PASS GetGreat_return1=true sha256='+sha(blob));return
    if not a.output or a.output.resolve()==a.input.resolve():raise ValueError('separate output required')
    if a.mode=='pnach':validate(blob,p);result=render(p).encode('utf8')
    else:result=transform(blob,p,r,rollback=a.mode=='rollback')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    if a.output.read_bytes()!=result:raise ValueError('output readback mismatch')
    print(a.mode.upper()+' PASS sha256='+sha(result))


if __name__=='__main__':main()
