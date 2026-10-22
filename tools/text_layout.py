"""Metric-based layout planning; source text and non-newline controls stay intact."""
import re
CLOSING='，。！？；：、）】》”’·…,.!?;:%'
NUMERIC=re.compile(r'\d+(?:\.\d+)?(?:%|倍|级|个|次|秒|分钟|小时)?|[A-Za-z]+(?:[-_][A-Za-z]+)*|\$D\d{2}')

def atoms(text,terms):
 out=[];at=0;terms=sorted({t for t in terms if len(t)>1},key=lambda t:-len(t))
 while at<len(text):
  match=NUMERIC.match(text,at);word=match.group() if match else next((t for t in terms if text.startswith(t,at)),text[at]);at+=len(word)
  if word in CLOSING and out:out[-1]+=word
  else:out.append(word)
 return out

def wrap(text,measure,width,terms):
 if width<=0:raise ValueError('positive line width required')
 # Preserve explicit paragraph breaks and non-newline command spelling/order.
 parts=text.split('$n$n');out=[]
 for j in range(1,len(parts)):
  prefix=re.match(r'['+re.escape(CLOSING)+r']+',parts[j])
  if prefix:
   parts[j-1]+=prefix.group();parts[j]=parts[j][len(prefix.group()):]
 for part in parts:
  part=part.replace('$n','');sentences=re.findall(r'.*?[。！？]|.+$',part);tokens=[]
  for sentence in sentences:
   if measure(sentence)<=width:tokens.append(sentence);continue
   for clause in re.findall(r'.*?[，；：]|.+$',sentence):
    if measure(clause)<=width:tokens.append(clause)
    else:tokens+=atoms(clause,terms)
  normalized=[]
  for token in tokens:
   if normalized and token and token[0] in CLOSING:
    prefix=re.match(r'['+re.escape(CLOSING)+r']+',token).group()
    normalized[-1]+=prefix;token=token[len(prefix):]
   if token:normalized.append(token)
  tokens=normalized
  lines=[];line=''
  for token in tokens:
   if measure(token)>width:raise ValueError('protected phrase exceeds line width: '+token)
   if line and measure(line+token)>width:lines.append(line);line=token
   else:line+=token
  if line:lines.append(line)
  out.append('$n'.join(lines))
 result='$n$n'.join(out)
 if result.replace('$n','')!=text.replace('$n',''):raise ValueError('layout changed visible content')
 return result
