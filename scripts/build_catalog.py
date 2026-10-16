#!/usr/bin/env python3
"""Build the portable Pages catalog and thumbnails from collect.py's output."""
import argparse, concurrent.futures, io, json, re, sqlite3, subprocess
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('library',type=Path);p.add_argument('--release-tag',default='videos-v1');a=p.parse_args()
source=json.loads((a.library/'catalog.json').read_text())
originals={r['slug']:r for r in json.loads((a.library/'source.json').read_text())}
def public_text(text):
 """Do not republish machine paths embedded in source prompt/post text."""
 if not text:return text
 return re.sub(r'(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^\s\"\x27<>]+','[local file path removed]',text)
thumbs=ROOT/'docs/assets/thumbs';thumbs.mkdir(parents=True,exist_ok=True)
def title(row):
 if row.get('title'):return row['title']
 text=re.sub(r'https?://\S+','',row['prompt']).strip()
 line=next((s.strip(' #*\"「') for s in text.splitlines() if len(s.strip())>12),text)
 return line[:74].rstrip()+('…' if len(line)>74 else '')
def thumb(row):
 videos=row['videos'];out=thumbs/(row['slug']+'.webp')
 if not out.exists() and videos:
  v=next((v for v in videos if v.get('local_path')),None)
  if v:
   seconds=min(4,max(.2,(v.get('duration') or 10)*.2))
   run=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(seconds),'-i',v['local_path'],'-frames:v','1','-vf','scale=640:400:force_original_aspect_ratio=decrease,pad=640:400:(ow-iw)/2:(oh-ih)/2:color=0x16181b','-f','image2pipe','-vcodec','png','pipe:1'],capture_output=True)
   if run.returncode:print('Thumbnail unavailable:',row['slug'],flush=True)
   else:Image.open(io.BytesIO(run.stdout)).save(out,'WEBP',quality=76)
 return row['slug'],out.exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 available=dict(pool.map(thumb,source))
posts=[]
for r in source:
 videos=[]
 for v in r['videos']:
  raw=json.loads(v.get('variants_json') or '{}')
  archive_url='https://github.com/sunithvs/claude-edited-videos/releases/download/'+a.release_tag+'/'+Path(v['local_path']).name
  videos.append({'id':v['id'],'url':archive_url,'originalUrl':v['source_url'],'duration':v.get('duration'),'sourcePost':raw.get('source_post_url',r['post_url']),'relationship':raw.get('relationship','attached video'),'fallbacks':list(dict.fromkeys([v.get('selected_url') or v['source_url']]+([('https://media.skillry.dev/opus-5-5/'+r['slug']+'/original.mp4')] if originals[r['slug']].get('skillry_url') and len(r['videos'])==1 else [])+[v['source_url']]))})
 posts.append({'id':r['id'],'slug':r['slug'],'author':r['author'],'title':public_text(title(r)),'editorialTitle':bool(r.get('title')),'category':r['category'],'tags':r['tech_tags'],'prompt':public_text(r['prompt']),'partial':r['prompt_partial'],'postText':public_text(r['post_text']),'postUrl':r['post_url'],'thumbnail':'assets/thumbs/'+r['slug']+'.webp' if available[r['slug']] else None,'videos':videos})
posts.sort(key=lambda p:int(p['id']),reverse=True)
(ROOT/'docs/data/catalog.json').write_text(json.dumps(posts,ensure_ascii=False,separators=(',',':')))
dbpath=ROOT/'docs/data/videos.sqlite';dbpath.unlink(missing_ok=True);db=sqlite3.connect(dbpath)
db.executescript('CREATE TABLE posts(id TEXT PRIMARY KEY,slug TEXT,author TEXT,title TEXT,category TEXT,tags TEXT,prompt TEXT,prompt_partial INTEGER,post_text TEXT,post_url TEXT,thumbnail TEXT); CREATE TABLE videos(id TEXT PRIMARY KEY,post_id TEXT REFERENCES posts(id),url TEXT,original_url TEXT,duration REAL,source_post TEXT,relationship TEXT);CREATE INDEX video_post ON videos(post_id);')
for r in posts:
 db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?)',(r['id'],r['slug'],r['author'],r['title'],r['category'],json.dumps(r['tags']),r['prompt'],r['partial'],r['postText'],r['postUrl'],r['thumbnail']))
 for v in r['videos']:db.execute('INSERT INTO videos VALUES(?,?,?,?,?,?,?)',(v['id'],r['id'],v['url'],v['originalUrl'],v['duration'],v['sourcePost'],v['relationship']))
db.commit();db.close()
print('Built',len(posts),'posts,',sum(len(p['videos']) for p in posts),'videos,',sum(available.values()),'thumbnails.')
