"""Read-only inbox scan. Proposals never modify authoritative metadata or approvals."""
import argparse, collections, datetime, json, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from common import ROOT, load, sha, inside
DOI=re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+',re.I)
def scan(root=ROOT,kind='all'):
 root=Path(root); pubs=load(root/'data/publications.yml'); courses=load(root/'data/courses.yml'); items=[]
 for category in (['papers','teaching'] if kind=='all' else [kind]):
  inbox=root/'workspace/inbox'/category
  for f in sorted(inbox.rglob('*')):
   if not f.is_file(): continue
   inside(inbox,f)
   if f.suffix.lower() not in {'.pdf','.pptx','.md','.qmd'}: continue
   text=''; title=None; errors=[]; meta={}; slides=None
   try:
    if f.suffix.lower()=='.pdf':
     import fitz
     with fitz.open(f) as pdf:
      meta=pdf.metadata or {}; title=meta.get('title'); slides=len(pdf)
      text='\n'.join(pdf[i].get_text() for i in range(min(5,len(pdf))))
      if not text.strip(): errors.append('no_extractable_text: OCR not performed')
    elif f.suffix.lower()=='.pptx':
     with zipfile.ZipFile(f) as z:
      names=sorted(n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n))
      slides=len(names)
      for n in names[:5]:
       tree=ET.fromstring(z.read(n)); text+='\n'+' '.join(e.text or '' for e in tree.iter() if e.tag.endswith('}t'))
      if 'docProps/core.xml' in z.namelist():
       core=ET.fromstring(z.read('docProps/core.xml')); meta={n.tag.rsplit('}',1)[-1]:n.text for n in core}
       title=meta.get('title')
    else:
     text=f.read_text(encoding='utf-8-sig'); m=re.search(r'^#\s+(.+)$',text,re.M); title=m.group(1) if m else None
   except Exception as e: errors.append(f'{type(e).__name__}: extraction failed; review required')
   title=title.strip() if isinstance(title,str) and title.strip() else None
   if title and title.lower() in {'untitled','powerpoint presentation','presentation'}: title=None
   dois=sorted({m.group(0).rstrip('.,;') for m in DOI.finditer(text)})
   match=[p['id'] for p in pubs if p.get('doi') and p['doi'].lower() in [d.lower() for d in dois]]
   if not match and title:
    normalize=lambda s:re.sub(r'\W','',s.lower())
    match=[p['id'] for p in pubs if normalize(p['title'])==normalize(title)]
   hay=(f.as_posix()+' '+text[:3000]).lower()
   possible_courses=[c['course_id'] for c in courses if c['title_zh'] in hay or c['title_en'].lower() in hay or c['course_id'] in hay]
   chapter=re.search(r'(第\s*[一二三四五六七八九十\d]+\s*[章节讲]|(?:chapter|lecture)\s*\d+)',hay,re.I)
   hints=[]
   if re.search(r'accepted manuscript|author accepted',text,re.I): hints.append('possible_accepted_manuscript')
   if re.search(r'version of record|published by|©|copyright',text,re.I): hints.append('possible_publisher_version')
   h=sha(f)
   items.append(dict(resource_id='asset-'+h[:16],source_file=f.relative_to(root).as_posix(),resource_type='paper' if category=='papers' else 'teaching',sha256=h,format=f.suffix[1:].lower(),size=f.stat().st_size,title_candidate=title,doi_candidates=dois,matched_publications=match,possible_courses=possible_courses,chapter_candidate=chapter.group(0) if chapter else None,language_candidate='zh' if re.search(r'[\u4e00-\u9fff]',text) else ('en' if re.search('[a-zA-Z]',text) else 'unknown'),version='unknown',version_hints=hints,page_or_slide_count=slides,permission_status='pending_review',license=None,approval_reference=None,public_path=None,proposed_public_filename=h[:16]+f.suffix.lower(),proposed_record_changes={'related_record':match or possible_courses,'requires_human_review':True},errors=errors))
 hashes=collections.defaultdict(list); titles=collections.defaultdict(list)
 for i in items:
  hashes[i['sha256']].append(i['source_file'])
  if i['title_candidate']: titles[re.sub(r'\W','',i['title_candidate'].lower())].append(i['source_file'])
 return dict(scanned_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),items=items,exact_duplicates=[v for v in hashes.values() if len(v)>1],possible_metadata_duplicates=[v for v in titles.values() if len(v)>1],network_lookup='not_required: local DOI and title matching only; unavailable network cannot block scanning')
def main():
 p=argparse.ArgumentParser();p.add_argument('--type',choices=['papers','teaching','all'],default='all');a=p.parse_args(); result=scan(kind=a.type)
 out=ROOT/'workspace/reports'/('resource-scan-'+a.type+'.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 md=out.with_suffix('.md');md.write_text('# 资源扫描审核\n\n扫描条目：'+str(len(result['items']))+'；精确重复组：'+str(len(result['exact_duplicates']))+'\n\n详细候选、错误和哈希见同名 JSON。全部条目默认 pending_review；本命令不写 public/ 或 data/，不自动公开。\n',encoding='utf-8')
 print('Scanned',len(result['items']),'files;',len(result['exact_duplicates']),'exact duplicate groups;',out)
if __name__=='__main__':main()
