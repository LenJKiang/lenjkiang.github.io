"""Shared contracts; public metadata never contains private source inventories."""
from pathlib import Path
import hashlib, os, re, shutil, json, sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
STATUSES={'pending_review','approved','private_only','external_link_only','rejected'}
BINARY_EXT={'.pdf','.pptx','.png','.jpg','.jpeg','.webp','.svg','.gif','.zip'}
ASSET_EXT={'.pdf','.pptx','.png','.jpg','.jpeg','.webp','.md','.qmd'}
def load(p):
 with open(p,encoding='utf-8-sig') as f: return yaml.safe_load(f)
def dump(p,value):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(yaml.safe_dump(value,allow_unicode=True,sort_keys=False),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()
def inside(root,p):
 root=Path(root).resolve(); p=Path(p)
 assert not p.is_symlink(),f'Symlink forbidden: {p.name}'
 p=p.resolve(); assert p.is_relative_to(root),f'Path escapes allowed directory: {p.name}'
 return p

def public_file(root,rel):
 assert isinstance(rel,str) and rel.startswith('public/'), 'Asset path must start with public/'
 assert '\\' not in rel and '..' not in Path(rel).parts, 'Unsafe asset path'
 return inside(Path(root)/'public',Path(root)/rel)
def base_path(value):
 assert re.fullmatch(r'/(?:[A-Za-z0-9_.-]+/)*',value or ''),'base_path must be / or /repository/'
 assert all(part not in {'.','..'} for part in value.split('/')), 'base_path may not traverse directories'
 return value

def metadata(root=ROOT):
 result={k:load(Path(root)/f'data/{k}.yml') for k in ['profile','research','publications','courses','resources','links']}
 file=Path(root)/'data/academic.yml'
 result['academic']=load(file) if file.exists() else dict(projects=[],honors=[],student_achievements=[],service=[])
 return result
def validate(root=ROOT):
 root=Path(root); d=metadata(root); cfg=load(root/'config/site.yml'); base_path(cfg['base_path'])
 origin=cfg.get('canonical_origin')
 assert origin is None or re.fullmatch(r'https://[A-Za-z0-9.-]+(?::\d+)?',origin),'canonical_origin must be an HTTPS origin'
 def required(obj,names):
  assert isinstance(obj,dict),'Expected mapping'
  for k in names: assert k in obj,f'Missing {k}'
 def text(obj,keys):
  for k in keys: assert isinstance(obj.get(k),str) and obj[k].strip(),f'Missing/invalid string {k}'
 def ident(value): assert isinstance(value,str) and re.fullmatch('[a-z0-9][a-z0-9-]*',value),f'Invalid ID {value}'
 def source(obj):
  required(obj,['verified_source','verified_date']); assert obj['verified_source'],'Missing source'
  assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(obj['verified_date'])),'Invalid verification date'
 p=d['profile']; text(p,['name_zh','name_en','role_zh','role_en','affiliation_zh','affiliation_en','summary_zh','summary_en','email']); source(p)
 for key in ['bio','research_overview','teaching_overview','about_intro','team_purpose','team_members','team_recruitment','team_contact']:
  if key+'_zh' in p or key+'_en' in p:text(p,[key+'_zh',key+'_en'])
 assert re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',p['email']),'Invalid email'
 for key,idkey in [('research','id'),('publications','id'),('courses','course_id'),('resources','resource_id'),('links','id')]:
  assert isinstance(d[key],list),f'{key} must be a list'
  seen=set()
  for item in d[key]:
   required(item,[idkey]); ident(item[idkey]); assert item[idkey] not in seen,f'Duplicate {key} ID'; seen.add(item[idkey])
 academic=d['academic'];assert isinstance(academic,dict),'Invalid academic data'
 for group in ['projects','honors','student_achievements','service']:
  assert isinstance(academic.get(group),list),'Missing academic list: '+group
  ids=set()
  for item in academic[group]:
   text(item,['id','title_zh','title_en']);ident(item['id']);source(item)
   assert item['id'] not in ids,'Duplicate academic ID';ids.add(item['id'])
   assert item.get('period') is None or isinstance(item['period'],str),'Invalid academic period'
   if group=='projects':
    if 'program_en' in item:text(item,['program_zh','program_en'])
    assert item['kind'] in {'research','teaching'} and item['role'] in {'principal_investigator','participant'},'Invalid project kind/role'
    assert item['status'] in {'active','completed','not_stated'},'Invalid project status'
   if group=='honors':assert item['recipient']=='self' and type(item['selected']) is bool,'Invalid personal award recipient'
   if group=='student_achievements':assert item['recipient']=='supervised_students','Student award must remain separate from personal award'
 areas={x['id'] for x in d['research']}; pubs={x['id'] for x in d['publications']}; courses={x['course_id'] for x in d['courses']}; resources={x['resource_id']:x for x in d['resources']}
 for x in d['research']: text(x,['title_zh','title_en','description_zh','description_en']); source(x)
 titles=set(); dois=set()
 for x in d['publications']:
  required(x,['id','title','authors','journal','year','doi','publisher_url','summary_zh','summary_en','research_category','selected','pdf_version','pdf_permission_status','pdf_public_path','publication_type']); source(x)
  text(x,['title','journal','publication_type']); assert isinstance(x['authors'],list) and x['authors'] and all(isinstance(a,str) and a for a in x['authors']),'Invalid authors'
  assert type(x['year']) is int and 1900<=x['year']<=2100,'Invalid publication year'
  assert type(x['selected']) is bool,'selected must be boolean'
  if 'selected_order' in x:assert type(x['selected_order']) is int and x['selected_order']>0,'Invalid selected publication order'
  assert x['research_category'] in areas,'Unknown research category'
  normalized=re.sub(r'\W','',x['title'].lower()); assert normalized not in titles,'Duplicate publication title'; titles.add(normalized)
  if x['doi']:
   assert re.fullmatch(r'10\.\d{4,9}/\S+',x['doi']),'Invalid DOI'
   doi=x['doi'].lower(); assert doi not in dois,'Duplicate DOI'; dois.add(doi)
  assert x['pdf_permission_status'] in STATUSES,'Invalid PDF permission status'
  assert type(x.get('pdf_links_enabled',True)) is bool,'pdf_links_enabled must be boolean'
  if not x.get('pdf_links_enabled',True):assert not x['pdf_public_path'],'Hidden PDF must not have a public asset path'
  assert x['pdf_version'] in {'unknown','submitted_manuscript','accepted_manuscript','version_of_record'},'Invalid PDF version'
  if x['pdf_public_path']:
   assert x['pdf_permission_status']=='approved','Publication PDF not approved'
   assert any(a['public_path']==x['pdf_public_path'] and a['related_publication_or_course']==x['id'] for a in resources.values()),'PDF missing resource manifest'
 for c in d['courses']:
  text(c,['title_zh','title_en','description_zh','description_en','language']); source(c)
  for key in ['audience','textbook']:
   if key+'_zh' in c or key+'_en' in c:text(c,[key+'_zh',key+'_en'])
  assert c['publication_status'] in {'metadata_only','published'},'Invalid course status'
  assert isinstance(c['chapters'],list) and isinstance(c['resources'],list),'Invalid course lists'
  chapter_ids=set()
  for chapter in c['chapters']:
   text(chapter,['id','title_zh','title_en']); ident(chapter['id']); assert chapter['id'] not in chapter_ids,'Duplicate chapter'; chapter_ids.add(chapter['id'])
  for rid in c['resources']:
   assert rid in resources and resources[rid]['related_publication_or_course']==c['course_id'],'Invalid course resource reference'
   chapter=resources[rid].get('chapter_id')
   if chapter: assert chapter in chapter_ids,'Invalid chapter reference'
 for link in d['links']:
  text(link,['title_zh','title_en','url']); source(link); assert link['url'].startswith('https://'),'External links require HTTPS'
 for a in resources.values():
  required(a,['resource_id','resource_type','related_publication_or_course','sha256','format','size','language','version','license','permission_status','approval_reference','public_path','last_updated'])
  assert 'source_file' not in a,'Private source_file must stay in workspace'
  assert a['resource_type'] in {'paper','teaching','image'},'Invalid resource type'
  formats={'paper':{'pdf'},'teaching':set(cfg.get('teaching_public_formats',['pdf'])),'image':{'png','jpg','jpeg','webp'}}
  assert a['format'] in formats[a['resource_type']],'Format incompatible with resource type'
  assert a['permission_status']=='approved','Public resource metadata must be approved'
  assert a['license'] and a['approval_reference'],'Missing permission evidence'
  assert re.fullmatch('[a-f0-9]{64}',a['sha256']),'Invalid SHA-256'
  assert type(a['size']) is int and a['size']>=0,'Invalid asset size'
  assert a['related_publication_or_course'] in pubs|courses|{p['id']},'Unknown related record'
  f=public_file(root,a['public_path']); assert f.is_file(),'Approved asset missing'; assert f.suffix.lower() in ASSET_EXT,'Asset format not allowed'
  assert f.suffix.lower().lstrip('.')==a['format'].lower(),'Format mismatch'
  assert sha(f)==a['sha256'] and f.stat().st_size==a['size'],'Approved asset hash/size changed'
  assert a['size']<=cfg['asset_limit_mb']*1024**2,'Asset exceeds configured size limit'
  ref=root/'config/public-assets.yml'
  manifests=load(ref) if ref.exists() else []
  matches=[v for v in manifests if v.get('resource_id')==a['resource_id']]
  assert len(matches)==1,'Missing or duplicated approval manifest'
  ap=matches[0]
  assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|workspace[/\\]|file://',str(ap.get('evidence',''))),'Private approval evidence path in public manifest'
  assert ap.get('sha256')==a['sha256'] and ap.get('public_path')==a['public_path'] and ap.get('scope')=='website-public-distribution' and ap.get('approved_by') and ap.get('evidence') and ap.get('approval_reference')==a['approval_reference'],'Invalid hash-bound approval'
  private=root/'workspace/review/approvals.yml'
  if private.exists():
   for review in load(private) or []:
    if review.get('resource_id')==a['resource_id'] and review.get('status')=='approved' and review.get('source_file'):
     src=inside(root/'workspace/inbox',root/review['source_file'])
     assert src.is_file() and sha(src)==a['sha256'],'Source changed: approval invalidated'
 actual={str(f.relative_to(root)).replace('\\','/') for f in (root/'public').rglob('*') if f.is_file()}
 expected={a['public_path'] for a in resources.values()}
 assert actual==expected,f'Public directory differs from allowlist: {actual^expected}'
 photo=p.get('photo_resource_id')
 if photo: assert photo in resources and resources[photo]['resource_type']=='image','Invalid photo resource'
 # Block local absolute paths and private directory references in public data.
 raw=json.dumps(d,ensure_ascii=False)
 assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|workspace[/\\]|file://|source_file',raw),'Private path in public metadata'
 return d

def quarto_exe():
 override=os.environ.get('QUARTO_PATH')
 choices=[override,shutil.which('quarto'),r'D:\Program Files\RStudio\resources\app\bin\quarto\bin\quarto.exe',r'C:\Program Files\RStudio\resources\app\bin\quarto\bin\quarto.exe']
 for c in choices:
  if c and Path(c).is_file(): return c
 raise RuntimeError('Quarto unavailable. Set QUARTO_PATH to quarto executable (RStudio bundled version supported).')
def local_env(root=ROOT):
 env=os.environ.copy(); work=Path(root)/'workspace'; tmp=work/'tmp'; tmp.mkdir(parents=True,exist_ok=True)
 for k in ['TMP','TEMP','TMPDIR']: env[k]=str(tmp)
 for k in ['XDG_CACHE_HOME','XDG_DATA_HOME','DENO_DIR','QUARTO_DENO_DIR','LOCALAPPDATA','APPDATA']:
  p=work/'cache'/k.lower(); p.mkdir(parents=True,exist_ok=True); env[k]=str(p)
 # Preserve read-only installed/user-site imports when APPDATA is redirected.
 env['PYTHONPATH']=os.pathsep.join(p for p in sys.path if p and Path(p).is_dir())
 env['PYTHONDONTWRITEBYTECODE']='1'
 return env

