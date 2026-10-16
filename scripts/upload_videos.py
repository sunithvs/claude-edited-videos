#!/usr/bin/env python3
"""Resume uploading complete local MP4s to a draft/published GitHub Release."""
import argparse, concurrent.futures, json, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('library',type=Path);p.add_argument('--repo',default='sunithvs/claude-edited-videos');p.add_argument('--tag',default='videos-v1');p.add_argument('--workers',type=int,default=8);a=p.parse_args()
def gh(*args):
 return subprocess.check_output(['gh',*args],text=True)
release=next(r for r in json.loads(gh('api',f'repos/{a.repo}/releases?per_page=100')) if r['tag_name']==a.tag)
existing={r['name']:r for r in map(json.loads,gh('api','--paginate',f'repos/{a.repo}/releases/{release["id"]}/assets?per_page=100','--jq','.[] | {name,size,digest,state}').splitlines())}
rows=json.loads((a.library/'catalog.json').read_text());items=[]
for post in rows:
 for video in post['videos']:
  path=Path(video['local_path']);assert path.is_file() and path.stat().st_size==video['bytes'],path.name
  items.append((path,video))
manifest=[{'id':v['id'],'postId':v['post_id'],'filename':p.name,'bytes':v['bytes'],'sha256':v['sha256'],'url':f'https://github.com/{a.repo}/releases/download/{a.tag}/{p.name}'} for p,v in items]
root=Path(__file__).resolve().parents[1]
(root/'docs/data/video-files.json').write_text(json.dumps(manifest,indent=2))
todo=[(p,v) for p,v in items if p.name not in existing or existing[p.name]['size']!=v['bytes'] or existing[p.name].get('state')!='uploaded']
print(f'Already uploaded: {len(items)-len(todo)}. Remaining: {len(todo)}.',flush=True)
def upload(item):
 path,video=item
 for attempt in range(3):
  run=subprocess.run(['gh','release','upload',a.tag,str(path),'--repo',a.repo,'--clobber'],capture_output=True,text=True)
  if run.returncode==0:return path.name,None
  time.sleep(2**attempt)
 return path.name,run.stderr[-500:]
failed=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
 for n,(name,error) in enumerate(pool.map(upload,todo),1):
  if error:failed.append((name,error));print('FAILED',name,error,flush=True)
  if n%20==0 or n==len(todo):print(f'Uploaded {len(items)-len(todo)+n}/{len(items)}',flush=True)
if failed:raise SystemExit(f'{len(failed)} uploads failed. Re-run to resume.')
remote={r['name']:r for r in map(json.loads,gh('api','--paginate',f'repos/{a.repo}/releases/{release["id"]}/assets?per_page=100','--jq','.[] | {name,size,digest,state}').splitlines())}
for path,video in items:
 asset=remote[path.name];assert asset['size']==video['bytes'],path.name
 if asset.get('digest'):assert asset['digest']=='sha256:'+video['sha256'],path.name
print(f'Verified all {len(items)} remote asset sizes and available SHA-256 digests.',flush=True)
subprocess.run(['gh','release','upload',a.tag,str(root/'docs/data/video-files.json'),'--repo',a.repo,'--clobber'],check=True)
