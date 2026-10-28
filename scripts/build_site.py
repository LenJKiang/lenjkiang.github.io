"""Reproducible local Quarto build; all temporary state remains inside project."""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path
from html import escape
from xml.sax.saxutils import escape as xml_escape
from common import ROOT, load, validate, quarto_exe, local_env, inside, base_path
from generate_pages import generate
from validate_site import validate_output

def build(base=None,canonical_origin=None):
 d=validate();cfg=load(ROOT/'config/site.yml')
 if base is not None:cfg['base_path']=base_path(base)
 if canonical_origin is not None:
  assert re.fullmatch(r'https://[A-Za-z0-9.-]+(?::\d+)?',canonical_origin),'canonical origin must be an HTTPS origin'
  cfg['canonical_origin']=canonical_origin
 exe=quarto_exe();pages=generate(d,cfg)
 env=local_env();logs=[]
 for lang in ['zh','en']:
  command=[exe,'render','.']
  for key in ['TMP','TEMP','TMPDIR']:env[key]='../../workspace/tmp'
  proc=subprocess.run(command,cwd=ROOT/'website'/lang,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
  (ROOT/f'workspace/reports/quarto-{lang}.log').write_text(proc.stdout,encoding='utf-8');logs.append(proc.stdout)
  if proc.returncode:raise RuntimeError(f'Quarto {lang} failed; see workspace/reports/quarto-{lang}.log\n'+proc.stdout[-3500:])
 # Owned generated outputs only; never delete input or public originals.
 candidate=ROOT/'workspace/build/assembled'
 if candidate.exists():shutil.rmtree(inside(ROOT/'workspace/build',candidate))
 shutil.copytree(ROOT/'workspace/build/zh',candidate,ignore=shutil.ignore_patterns('en'))
 shutil.copytree(ROOT/'workspace/build/en',candidate/'en')
 (candidate/'assets').mkdir(exist_ok=True);shutil.copy2(ROOT/'website/shared/filters.js',candidate/'assets/filters.js')
 for asset in d['resources']:
  src=ROOT/asset['public_path'];dest=candidate/asset['public_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 base=cfg['base_path'];origin=cfg.get('canonical_origin') or 'http://127.0.0.1:8000'
 page_paths={r for r,_,_ in pages}
 # Remove any obsolete HTML Quarto retained from previous content generations.
 for f in list(candidate.rglob('*.html')):
  if f.relative_to(candidate).as_posix() not in page_paths:f.unlink()
 for rel,lang,description in pages:
  target=candidate/rel;raw=target.read_text(encoding='utf-8').replace('https://academic.invalid/',base);twin=rel[3:] if rel.startswith('en/') else 'en/'+rel;url=origin+base+rel
  raw=re.sub(r'<link[^>]+rel="(?:canonical|alternate)"[^>]*>','',raw)
  meta=f'<link rel="canonical" href="{escape(url,quote=True)}">\n'
  for code,path in [('en',rel if lang=='en' else twin),('zh-CN',rel if lang=='zh' else twin)]:meta+=f'<link rel="alternate" hreflang="{code}" href="{escape(origin+base+path,quote=True)}">\n'
  title=re.search(r'<title>(.*?)</title>',raw,re.S).group(1)
  meta+=f'<meta property="og:title" content="{escape(title,quote=True)}"><meta property="og:description" content="{escape(description,quote=True)}"><meta property="og:url" content="{escape(url,quote=True)}"><meta property="og:type" content="website"><meta property="og:locale" content="{lang}">'
  if not cfg.get('canonical_origin'):meta+='<meta name="robots" content="noindex, nofollow">'
  raw=raw.replace('</head>',meta+'\n</head>');raw=raw.replace('</body>',f'<script src="{base}assets/filters.js" defer></script>\n</body>')
  target.write_text(raw,encoding='utf-8')
 sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+xml_escape(origin+base+rel)+'</loc></url>' for rel,_,_ in pages)+'</urlset>'
 (candidate/'sitemap.xml').write_text(sitemap,encoding='utf-8');(candidate/'robots.txt').write_text('User-agent: *\n'+('Allow: '+base if cfg.get('canonical_origin') else 'Disallow: /')+'\nSitemap: '+origin+base+'sitemap.xml\n',encoding='utf-8');(candidate/'.nojekyll').touch()
 report=validate_output(candidate,cfg,d)
 out=ROOT/'dist'
 if out.exists():shutil.rmtree(inside(ROOT,out))
 shutil.copytree(candidate,out)
 report['quarto_version']=subprocess.check_output([exe,'--version'],env=env,text=True).strip()
 report['output']='dist/'
 report['external_network_links']='not asserted by local validation'
 (ROOT/'workspace/reports/build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base-path');p.add_argument('--canonical-origin');a=p.parse_args()
 try:build(a.base_path,a.canonical_origin)
 except Exception as e:p.exit(1,'BUILD FAILED: '+str(e)+'\n')
