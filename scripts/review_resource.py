"""Explicit hash-bound asset decision. Never invokes Git or any remote operation."""
import argparse, datetime, shutil, re
from pathlib import Path
from common import ROOT, dump, load, sha, inside, public_file, ASSET_EXT, validate

def decide(root,source,resource_id,status,expected_hash,related,version='unknown',language='unknown',license=None,evidence=None,approver=None,confirmed=False,chapter=None):
 root=Path(root); src=inside(root/'workspace/inbox',root/source); assert src.is_file(),'Source missing'
 assert re.fullmatch('[a-z0-9][a-z0-9-]*',resource_id),'Invalid resource ID'
 assert status in {'pending_review','approved','private_only','external_link_only','rejected'},'Invalid decision'
 assert sha(src)==expected_hash,'Source hash changed; rescan and obtain fresh approval'
 assert src.suffix.lower() in ASSET_EXT,'Unsupported public format'
 records=load(root/'workspace/review/approvals.yml') or []
 assert not any(r['resource_id']==resource_id for r in records),'Resource ID already reviewed; use a new version ID'
 now=datetime.date.today().isoformat(); ref=f'{resource_id}-{expected_hash[:12]}'
 private=dict(resource_id=resource_id,source_file=src.relative_to(root).as_posix(),sha256=expected_hash,status=status,approval_reference=ref,approved_by=approver,evidence=evidence,last_updated=now)
 if status=='approved':
  validate(root)
  assert confirmed and approver and license and evidence,'Explicit user confirmation, named approver, license and evidence are required'
  assert version in {'submitted_manuscript','accepted_manuscript','version_of_record','unknown'},'Invalid version'
  resources=load(root/'data/resources.yml'); pubs=load(root/'data/publications.yml'); courses=load(root/'data/courses.yml'); profile=load(root/'data/profile.yml')
  pub=next((p for p in pubs if p['id']==related),None); course=next((c for c in courses if c['course_id']==related),None)
  assert pub or course or related==profile['id'],'Unknown related record'
  category='papers' if pub else ('teaching' if course else 'images')
  formats={'papers':{'.pdf'},'teaching':{'.'+x for x in load(root/'config/site.yml').get('teaching_public_formats',['pdf'])},'images':{'.png','.jpg','.jpeg','.webp'}}
  assert src.suffix.lower() in formats[category],'Format incompatible with related record'
  assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|workspace[/\\]|file://',evidence),'Public evidence must not contain private paths'
  if pub: assert src.suffix.lower()=='.pdf' and version!='unknown','Paper approval requires PDF and verified manuscript version'
  if chapter: assert course and any(c['id']==chapter for c in course['chapters']),'Unknown course chapter'
  rel=f'public/{category}/{resource_id}{src.suffix.lower()}'; dest=public_file(root,rel); assert not dest.exists(),'Will not overwrite existing public file'
  assert not any(a['resource_id']==resource_id for a in resources),'Duplicate resource ID'
  assert src.stat().st_size <= load(root/'config/site.yml')['asset_limit_mb']*1024**2,'Asset too large'
  asset=dict(resource_id=resource_id,resource_type='paper' if pub else ('teaching' if course else 'image'),related_publication_or_course=related,sha256=expected_hash,format=src.suffix[1:].lower(),size=src.stat().st_size,language=language,version=version,license=license,permission_status='approved',approval_reference=ref,public_path=rel,last_updated=now)
  if chapter:asset['chapter_id']=chapter
  manifests=load(root/'config/public-assets.yml') or []
  manifests.append(dict(resource_id=resource_id,sha256=expected_hash,public_path=rel,approved_by=approver,approval_reference=ref,evidence=evidence,scope='website-public-distribution',approved_date=now))
  resources.append(asset)
  if pub:pub.update(pdf_version=version,pdf_permission_status='approved',pdf_public_path=rel)
  if course:
   course['resources'].append(resource_id);course['publication_status']='published'
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  dump(root/'data/resources.yml',resources);dump(root/'config/public-assets.yml',manifests);dump(root/'data/publications.yml',pubs);dump(root/'data/courses.yml',courses)
 records.append(private);dump(root/'workspace/review/approvals.yml',records)
 if status=='approved':validate(root)
 return ref
if __name__=='__main__':
 p=argparse.ArgumentParser(description='仅在已获得用户逐文件明确批准后使用 approved。该命令不构成用户批准。')
 for key in ['source','resource-id','status','sha256','related']:p.add_argument('--'+key,required=True)
 for key in ['version','language']:p.add_argument('--'+key,default='unknown')
 for key in ['license','evidence','approver','chapter']:p.add_argument('--'+key)
 p.add_argument('--confirm-public',action='store_true');a=p.parse_args()
 try:print('Decision recorded:',decide(ROOT,a.source,a.resource_id,a.status,a.sha256,a.related,a.version,a.language,a.license,a.evidence,a.approver,a.confirm_public,a.chapter))
 except (AssertionError,ValueError) as e:p.exit(1,str(e)+'\n')
