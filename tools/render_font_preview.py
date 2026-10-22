"""Render decoded 2-bit glyphs at metric width, not the entire storage cell."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from PIL import Image
from research_inventory import font_data

def compose(lines,glyphs,advances,height,width=440,line_pitch=28):
 if width<=0 or line_pitch<height:raise ValueError('invalid preview dimensions')
 canvas=Image.new('RGB',(width,12+line_pitch*len(lines)),(25,29,33))
 for row,line in enumerate(lines):
  x=8
  for ch in line:
   advance=advances[ch];glyph=glyphs[ch]
   if not 0<advance<=glyph.width:raise ValueError('invalid glyph advance')
   # Original narrow ASCII slots can contain data outside their metric extent.
   # Never paste these pixels over the next character in a logical-width preview.
   tile=glyph.crop((0,0,advance,height));canvas.paste((228,228,220),(x,6+row*line_pitch),tile);x+=advance
  if x>width-8:raise ValueError('preview text exceeds width')
 return canvas

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('font','map','text','out'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--width',type=int,default=440);p.add_argument('--scale',type=int,default=4);a=p.parse_args()
 if a.scale<1:raise ValueError('positive integer scale required')
 raw=a.font.read_bytes();info=font_data(raw);mapping={q['character']:q['glyph'] for q in json.loads(a.map.read_text('utf8'))['entries']};lines=a.text.read_text('utf8').splitlines();glyphs={};advances={}
 for ch in set(''.join(lines)):
  g=mapping.get(ch,ord(ch) if ord(ch)<256 else -1)
  if not 0<=g<info['glyphs']:raise ValueError('unmapped preview character '+ch)
  at=info['bitmap_start']+g*info['height']*info['row_stride'];b=raw[at:at+info['height']*info['row_stride']];im=Image.new('L',(info['width'],info['height']));im.putdata([((b[y*info['row_stride']+x//4]>>(2*(x%4)))&3)*85 for y in range(info['height']) for x in range(info['width'])]);glyphs[ch]=im;advances[ch]=raw[info['metrics_start']+g]
 canvas=compose(lines,glyphs,advances,info['height'],a.width,max(28,info['height']));a.out.mkdir(parents=True,exist_ok=True);canvas.save(a.out/'font-layout-native.png');canvas.resize((canvas.width*a.scale,canvas.height*a.scale),Image.Resampling.NEAREST).save(a.out/'font-layout-4x.png');print('FONT_PREVIEW_PASS metric_extent_clipped=true scale='+str(a.scale)+' font_bytes_unchanged=true')
if __name__=='__main__':main()
