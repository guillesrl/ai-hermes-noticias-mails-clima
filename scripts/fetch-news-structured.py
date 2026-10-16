#!/usr/bin/env python3
"""Recopila noticias RSS con identificadores estables y metadatos estructurados."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, subprocess
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
 ('Ars Technica','https://feeds.arstechnica.com/arstechnica/technology-lab'),
 ('Ars Technica Security','https://arstechnica.com/security/feed/'),
 ('The Verge','https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'),
 ('TechCrunch','https://techcrunch.com/category/artificial-intelligence/feed/'),
 ('Infobae Tecnología','https://www.infobae.com/arc/outboundfeeds/rss/category/tecno/'),
 ('Xataka','https://feeds.weblogssl.com/xataka2'),
 ('Genbeta','https://feeds.weblogssl.com/genbeta'),
 ('MIT Technology Review','https://www.technologyreview.com/feed/'),
 ('NVIDIA Blog','https://blogs.nvidia.com/feed/'),
 ('IEEE Spectrum','https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss'),
 ('OpenAI News','https://openai.com/news/rss.xml'),
]

def clean(s):
 s=re.sub(r'<!\[CDATA\[|\]\]>','',s); s=re.sub(r'<[^>]+>',' ',s)
 s=re.sub(r'&#(\d+);',lambda m:chr(int(m.group(1))),s)
 for a,b in (('&amp;','&'),('&quot;','"'),('&#39;',"'"),('&lt;','<'),('&gt;','>')): s=s.replace(a,b)
 return re.sub(r'\s+',' ',s).strip()

def date_of(s):
 try: return parsedate_to_datetime(s.strip()).astimezone(dt.timezone.utc)
 except Exception:
  try: return dt.datetime.fromisoformat(s.strip().replace('Z','+00:00')).astimezone(dt.timezone.utc)
  except Exception: return None

def field(block,*names):
 for n in names:
  m=re.search(r'<%s[^>]*>(.*?)</%s>'%(n,n),block,re.I|re.S)
  if m:return m.group(1)
 return ''

def fetch(url):
 try:return subprocess.run(['curl','-sL','--max-time','15','-H','User-Agent: Mozilla/5.0',url],capture_output=True,text=True,timeout=20).stdout
 except Exception:return ''

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--hours',type=int,default=24); ap.add_argument('--json-out',required=True); ap.add_argument('--text-out',required=True); args=ap.parse_args()
 now=dt.datetime.now(dt.timezone.utc); rows=[]; seen=set()
 for source,url in FEEDS:
  xml=fetch(url)
  for block in re.findall(r'<item[ >].*?</item>|<entry[ >].*?</entry>',xml,re.I|re.S):
   d=date_of(clean(field(block,'pubDate','updated','published','dc:date')))
   if not d or (now-d).total_seconds()/3600>args.hours or (now-d).total_seconds()/3600 < -6: continue
   title=clean(field(block,'title')); summary=clean(field(block,'description','summary','content'))[:600]
   if not title: continue
   key=re.sub(r'[^a-z0-9]+',' ',title.lower()).strip()
   if key in seen: continue
   seen.add(key)
   uid=hashlib.sha256(f'{source}|{key}'.encode()).hexdigest()[:16]
   rows.append({'id':uid,'source':source,'published':d.isoformat(),'title':title,'summary':summary})
 rows.sort(key=lambda x:x['published'],reverse=True)
 Path(args.json_out).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 with Path(args.text_out).open('w',encoding='utf-8') as f:
  for x in rows:
   f.write(f"[{x['id']}] [{x['published'][:16].replace('T',' ')}] {x['source']}: {x['title']}\n")
   if x['summary']: f.write(f"    {x['summary']}\n")
   f.write('\n')
 print(json.dumps({'entries':len(rows),'status':'ok' if rows else 'empty'},ensure_ascii=False))
 return 0
if __name__=='__main__': raise SystemExit(main())
