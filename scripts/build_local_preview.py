"""Local test overlay. This never approves redistribution or changes dist/public."""
import argparse,hashlib,html,json,re,shutil,stat
from pathlib import Path
from urllib.parse import urlsplit,unquote
from common import ROOT,load,sha,inside
from validate_site import Page

def preview_assets(root=ROOT):
 root=Path(root);items=load(root/'workspace/review/local-preview.yml');names=set()
 for a in items:
  assert a['permission_scope']=='local-preview-only','Preview scope required'
  assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',a['filename']),'Unsafe filename'
  assert a['filename'] not in names,'Duplicate preview filename';names.add(a['filename'])
  src=inside(root/'workspace',root/a['source_file']);assert src.is_file() and sha(src)==a['sha256'],'Local source changed; rescan'
  assert src.suffix.lower() in ({'.jpg','.jpeg','.png','.webp'} if a['kind']=='photo' else {'.pdf'}),'Only PDF course/paper files allowed'
  if a.get('original_file'):assert sha(inside(root/'workspace/inbox',root/a['original_file']))==a['sha256'],'Original changed'
 return items

def build_preview(root=ROOT):
 root=Path(root);items=preview_assets(root);dist=root/'dist';before={p.relative_to(dist).as_posix():sha(p) for p in dist.rglob('*') if p.is_file()}
 report=json.loads((root/'workspace/reports/build-report.json').read_text(encoding='utf-8'));base=report['base_path'];out=root/'workspace/preview-site'
 courses_path=root/'data/courses.yml'
 course_data={c['course_id']:c for c in load(courses_path)} if courses_path.exists() else {}
 inside(root/'workspace',out);out.mkdir(exist_ok=True)
 # Preserve identical PDFs: browsers may hold them open on Windows. Remove stale
 # generated files explicitly so this overlay still has an exact file allowlist.
 expected=set(before)|{'_local/'+a['filename'] for a in items}
 for f in out.rglob('*'):
  if f.is_file() and f.relative_to(out).as_posix() not in expected:
   inside(out,f);f.chmod(f.stat().st_mode|stat.S_IWRITE);f.unlink()
 shutil.copytree(dist,out,dirs_exist_ok=True);(out/'_local').mkdir(exist_ok=True);papers={a['related']:a for a in items if a['kind']=='paper'};lessons=[a for a in items if a['kind']=='teaching'];photo=next(a for a in items if a['kind']=='photo')
 for a in items:
  target=out/'_local'/a['filename']
  if not target.exists() or sha(target)!=a['sha256']:
   if target.exists():target.chmod(target.stat().st_mode|stat.S_IWRITE)
   shutil.copy2(root/a['source_file'],target)
 def links(a,en):
  u=base+'_local/'+a['filename'];return f'<a class="local-pdf" href="{u}" target="_blank" rel="noopener">'+('Read PDF' if en else '阅读 PDF')+f'</a> · <a class="local-download" href="{u}?download=1" download="{a["filename"]}">'+('Download' if en else '下载')+'</a>'
 for f in out.rglob('*.html'):
  rel=f.relative_to(out).as_posix();en=rel.startswith('en/');s=f.read_text(encoding='utf-8')
  img=f'<img class="profile-photo" src="{base}_local/{photo["filename"]}" alt="林李泽强 / Ze-Qiang Linli">'
  s=re.sub(r'<div class="portrait-placeholder".*?</div>',img,s,flags=re.S)
  def add_card(m):
   block=m.group(0)
   for id,a in papers.items():
    if 'publications/'+id+'.html' in block:return re.sub(r'<a class="pdf-request"[^>]*>.*?</a>',links(a,en),block)
   return block
  s=re.sub(r'<article class="paper-card".*?</article>',add_card,s,flags=re.S)
  for id,a in papers.items():
   if rel in {'publications/'+id+'.html','en/publications/'+id+'.html'}:
    s=re.sub(r'<a class="pdf-request"[^>]*>.*?</a>',links(a,en),s,count=1,flags=re.S)
  def add_lessons(m):
   course_id=m.group(1);course_lessons=[a for a in lessons if a['related']==course_id]
   if not course_lessons:return m.group(0)
   chapters={c['id']:c for c in course_data.get(course_id,{}).get('chapters',[])}
   tables=[]
   for chapter_id in dict.fromkeys(a.get('chapter_id','chapter-01') for a in course_lessons):
    group=[a for a in course_lessons if a.get('chapter_id','chapter-01')==chapter_id]
    rows=''.join(f'<tr><td>{html.escape(a["section"]+" "+a["title_en" if en else "title_zh"])}</td><td>PDF</td><td>'+('Chinese' if en else '中文')+f'</td><td>{a["page_count"]}</td><td>{links(a,en)}</td></tr>' for a in group)
    caption=chapters.get(chapter_id,{}).get('title_en' if en else 'title_zh', 'Course materials' if en else '课程课件')
    tables.append(f'<table class="local-lessons" data-chapter="{html.escape(chapter_id)}"><caption>{html.escape(caption)}</caption><thead><tr>'+''.join('<th>'+x+'</th>' for x in (['Section','Format','Language','Pages','Access'] if en else ['小节','格式','语言','页数','访问']))+'</tr></thead><tbody>'+rows+'</tbody></table>')
   return '<div class="course-resources" data-course="'+course_id+'">'+''.join(tables)+'</div>'
  s=re.sub(r'<div class="course-resources" data-course="([a-z0-9-]+)">.*?</div>',add_lessons,s,flags=re.S)
  s=s.replace('</head>','<meta name="robots" content="noindex,nofollow"></head>');f.write_text(s,encoding='utf-8')
 errors=[];count=0
 for f in out.rglob('*.html'):
  page=Page(f.read_text(encoding='utf-8'))
  for href,tag,attr in page.links:
   u=urlsplit(href)
   if u.scheme or u.netloc:continue
   p=unquote(u.path)
   dest=out/p[len(base):] if p.startswith(base) else (f.parent/p if p else f)
   dest=inside(out,dest)
   if dest.is_dir():dest=dest/'index.html'
   if not dest.is_file():errors.append(f.name+': '+href)
   count+=1
 for a in items:assert sha(out/'_local'/a['filename'])==a['sha256'],'Preview asset hash mismatch'
 assert {p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}==expected,'Unexpected preview output file'
 assert not list(out.rglob('*.ppt')) and not list(out.rglob('*.pptx')),'PPT files must never enter preview'
 assert not errors,'Broken preview links: '+str(errors[:10])
 assert before=={p.relative_to(dist).as_posix():sha(p) for p in dist.rglob('*') if p.is_file()},'Production dist changed'
 result=dict(status='PASS',scope='local-preview-only',pages=len(list(out.rglob('*.html'))),papers=len(papers),teaching_pdfs=len(lessons),photos=1,internal_references=count,production_dist_unchanged=True,ppt_files=0)
 (root/'workspace/reports/local-preview-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result));return out
if __name__=='__main__':build_preview()
