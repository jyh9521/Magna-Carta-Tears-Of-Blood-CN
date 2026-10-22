"""Clear packed padding beyond each metric; preserve every effective ink pixel."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from research_inventory import font_data
from font_poc import require,digest

def sanitize(raw):
    info=font_data(raw);out=bytearray(raw);changed=0;pixels=0
    for g in range(info['glyphs']):
        advance=raw[info['metrics_start']+g]
        require(0<=advance<=info['width'],'metric outside cell')
        at=info['bitmap_start']+g*info['height']*info['row_stride'];before=pixels
        for y in range(info['height']):
            for x in range(advance,info['row_stride']*4):
                i=at+y*info['row_stride']+x//4;mask=3<<(2*(x%4))
                if out[i]&mask:pixels+=1;out[i]&=255^mask
        changed+=pixels>before
    require(font_data(bytes(out))==info,'layout changed')
    end=info['bitmap_start']+info['bitmap_bytes']
    require(raw[:info['bitmap_start']]==out[:info['bitmap_start']] and raw[end:]==out[end:],'metadata changed')
    return bytes(out),dict(glyphs=info['glyphs'],changed_glyphs=changed,cleared_padding_pixels=pixels,effective_ink_preserved=True,source_sha256=digest(raw),modified_sha256=digest(bytes(out)))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--font-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);require(not any(a.out.iterdir()),'output not empty');proof={}
    for n in ('NormalFont','KatakanaFont'):
        raw=(a.font_dir/(n+'.modified.bin')).read_bytes();new,proof[n]=sanitize(raw);(a.out/(n+'.modified.bin')).write_bytes(new)
    (a.out/'padding-verification.json').write_text(json.dumps(proof,indent=2)+'\n','utf8');print('FONT_PADDING_PASS '+json.dumps(proof))
if __name__=='__main__':main()
