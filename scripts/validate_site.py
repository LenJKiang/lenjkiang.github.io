"""Static output validation, including language pairs, assets, metadata and capacity."""
import argparse, json, re
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
from common import ROOT, load, validate, sha, inside, base_path
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=True);self.links=[];self.ids=set();self.meta={};self.canonical=[];self.alternates=[];self.switches=[];self.lang=None;self.h1=0;self.images=[];self.title=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  if tag=='html':self.lang=a.get('lang')
  if tag=='h1':self.h1+=1
  if tag=='title':self.title=True
  if tag=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content')
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
  if tag=='link' and a.get('rel')=='alternate':self.alternates.append((a.get('hreflang'),a.get('href')))
  if tag=='a' and 'language-switch' in a.get('class',''):self.switches.append(a.get('href'))
  if tag=='img':self.images.append(a)
  for attr in ['href','src','data']:
   if a.get(attr):self.links.append((a[attr],tag,attr))

def validate_output(dist,cfg,d=None,root=ROOT):
 dist=Path(dist).resolve();root=Path(root);d=d or validate(root);base=base_path(cfg['base_path']);htmls={p.relative_to(dist).as_posix():Page(p.read_text(encoding='utf-8')) for p in dist.rglob('*.html')}
 assert htmls,'No HTML output'
 approved={a['public_path']:a for a in d['resources']};errors=[];checked=0
 from generate_pages import PAGES
 expected_html={prefix+name+'.html' for prefix in ['', 'en/'] for name in [p[0] for p in PAGES]+['publications/'+p['id'] for p in d['publications']]+['teaching/'+c['course_id'] for c in d['courses']]}
 assert set(htmls)==expected_html,'Unexpected or missing HTML page in output'
 generated_files={'styles.css','en/styles.css','search.json','en/search.json','sitemap.xml','robots.txt','.nojekyll','assets/filters.js'}
 for rel,page in htmls.items():
  assert page.lang==('en' if rel.startswith('en/') else 'zh-CN'),f'Wrong language {rel}'
  assert page.title and page.h1==1,f'Missing title or semantic h1 {rel}'
  assert page.meta.get('description') and page.meta.get('og:title') and page.meta.get('og:description') and page.meta.get('og:url'),f'Metadata missing {rel}'
  assert len(page.canonical)==1 and len(page.alternates)>=2,f'Canonical/hreflang missing {rel}'
  twin=rel[3:] if rel.startswith('en/') else 'en/'+rel
  assert twin in htmls and page.switches==[base+twin],f'Broken language pair {rel}'
  for img in page.images:assert img.get('alt'),f'Image alt missing {rel}'
  raw=(dist/rel).read_text(encoding='utf-8')
  assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|workspace[/\\]|file://|source_file|SYNTHETIC_PRIVATE_FIXTURE',raw),f'Private data leaked {rel}'
  for href,tag,attr in page.links:
   parsed=urlsplit(href)
   if parsed.scheme or parsed.netloc:continue
   path=unquote(parsed.path)
   if path.startswith('/'):
    if not path.startswith(base):errors.append(f'{rel}: outside base path {href}');continue
    target=dist/path[len(base):]
   else:target=(dist/rel).parent/path if path else dist/rel
   target=inside(dist,target)
   if target.is_dir():target=target/'index.html'
   if not target.is_file():errors.append(f'{rel}: missing {href}');continue
   if parsed.fragment and target.suffix=='.html':
    dest=target.relative_to(dist).as_posix();fragment=unquote(parsed.fragment)
    if fragment not in htmls[dest].ids:errors.append(f'{rel}: missing fragment {href}')
   checked+=1
   if target.suffix.lower() in {'.pdf','.pptx'}:
    key=target.relative_to(dist).as_posix();assert key in approved,f'Unauthorized resource link {key}'
 for f in dist.rglob('*'):
  if not f.is_file():continue
  inside(dist,f);rel=f.relative_to(dist).as_posix()
  runtime=(rel.startswith('site_libs/') or rel.startswith('en/site_libs/')) and f.suffix.lower() in {'.js','.css','.woff','.woff2','.ttf','.eot','.map'}
  assert rel in expected_html or rel in generated_files or rel in approved or runtime,f'Unexpected file in output: {rel}'
  if f.suffix in {'.json','.html'}:
   content=f.read_text(encoding='utf-8')
   assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|workspace[/\\]|file://|source_file|SYNTHETIC_PRIVATE_FIXTURE|https://academic.invalid/',content),f'Private or intermediate content in output {rel}'
  assert not any(part in {'workspace','data','tests','.git','.env','__pycache__'} for part in Path(rel).parts),f'Private output file {rel}'
  assert f.suffix.lower() not in {'.qmd','.py','.yml','.yaml','.md','.jsonl','.key','.pem'} or rel in approved,f'Source/private file in output {rel}'
  if rel in approved:assert sha(f)==approved[rel]['sha256'],f'Approved output hash mismatch {rel}'
  if f.suffix.lower() in {'.pdf','.pptx','.png','.jpg','.jpeg','.webp','.svg','.gif','.zip'}:
   assert rel in approved,f'Unapproved binary output {rel}'
   assert sha(f)==approved[rel]['sha256'],f'Output hash mismatch {rel}'
 for rel,a in approved.items():assert (dist/rel).is_file() and sha(dist/rel)==a['sha256'],f'Approved asset missing in output {rel}'
 for required in ['sitemap.xml','robots.txt','.nojekyll']:assert (dist/required).is_file(),f'Missing {required}'
 manifest=load(root/'config/public-assets.yml') or []
 assert len(manifest)==len(approved),'Stale asset approval manifest'
 total=sum(p.stat().st_size for p in dist.rglob('*') if p.is_file());assert total<=cfg['capacity_limit_mb']*1024**2,'Site exceeds configured maximum'
 assert not errors,'\n'.join(errors[:30])
 report=dict(status='PASS',pages=len(htmls),internal_links_checked=checked,base_path=base,approved_assets=len(approved),bytes=total,mb=round(total/1024**2,3),warning_threshold_mb=cfg['capacity_warning_mb'],capacity_warning=total>cfg['capacity_warning_mb']*1024**2,canonical_mode='public-configured' if cfg.get('canonical_origin') else 'local-preview-noindex')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dist',default=str(ROOT/'dist'));p.add_argument('--base-path');a=p.parse_args();cfg=load(ROOT/'config/site.yml')
 if a.base_path:cfg['base_path']=a.base_path
 try:
  report=validate_output(a.dist,cfg);(ROOT/'workspace/reports/site-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
 except (AssertionError,ValueError,KeyError) as e:p.exit(1,'FAIL site: '+str(e)+'\n')
