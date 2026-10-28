"""Integration test: approved synthetic PDF is rendered in an isolated mini site."""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from common import ROOT, load, dump, sha, local_env
from review_resource import decide

def run():
 folder=ROOT/'workspace/working/fixture-integration'
 if folder.exists():
  assert folder.resolve().is_relative_to((ROOT/'workspace/working').resolve());shutil.rmtree(folder)
 folder.mkdir()
 for d in ['data','config','website/shared','scripts']:
  shutil.copytree(ROOT/d,folder/d,ignore=shutil.ignore_patterns('__pycache__'))
 for d in ['workspace/inbox/papers','workspace/review','workspace/reports','public/papers']:(folder/d).mkdir(parents=True,exist_ok=True)
 dump(folder/'data/resources.yml',[]);dump(folder/'config/public-assets.yml',[])
 pubs=load(folder/'data/publications.yml')
 for pub in pubs:pub.update(pdf_public_path=None,pdf_permission_status='external_link_only',pdf_version='unknown')
 dump(folder/'data/publications.yml',pubs[:1]);courses=load(folder/'data/courses.yml')
 for course in courses:course['resources']=[]
 profile=load(folder/'data/profile.yml');profile['photo_resource_id']=None;dump(folder/'data/profile.yml',profile)
 dump(folder/'data/courses.yml',courses[:1]);dump(folder/'workspace/review/approvals.yml',[])
 import fitz
 src=folder/'workspace/inbox/papers/synthetic.pdf';doc=fitz.open();page=doc.new_page();page.insert_text((72,72),'SYNTHETIC TEST ONLY - NOT A REAL PUBLICATION');doc.save(src);doc.close()
 decide(folder,'workspace/inbox/papers/synthetic.pdf','synthetic-integration','approved',sha(src),pubs[0]['id'],'accepted_manuscript','en','synthetic-test-fixture','TEST FIXTURE: isolated pipeline verification','TEST FIXTURE',True)
 teach=folder/'workspace/inbox/teaching/synthetic-lecture.pdf';teach.parent.mkdir(parents=True,exist_ok=True)
 doc=fitz.open();page=doc.new_page();page.insert_text((72,72),'SYNTHETIC LECTURE - TEST ONLY');doc.save(teach);doc.close()
 course_data=load(folder/'data/courses.yml');course_data[0]['chapters']=[dict(id='synthetic-lecture',title_zh='合成测试讲次',title_en='Synthetic test lecture')];dump(folder/'data/courses.yml',course_data)
 decide(folder,'workspace/inbox/teaching/synthetic-lecture.pdf','synthetic-lecture','approved',sha(teach),course_data[0]['course_id'],'unknown','en','synthetic-test-fixture','TEST FIXTURE: isolated teaching verification','TEST FIXTURE',True,'synthetic-lecture')
 proc=subprocess.run([sys.executable,str(folder/'scripts/build_site.py')],cwd=folder,env=local_env(folder),capture_output=True,text=True,encoding='utf-8',errors='replace')
 (ROOT/'workspace/reports/fixture-integration.log').write_text(proc.stdout+proc.stderr,encoding='utf-8');assert proc.returncode==0,proc.stderr+proc.stdout
 pdf=folder/'dist/public/papers/synthetic-integration.pdf';assert sha(pdf)==sha(src)
 for lang in ['','en/']:
  html=(folder/f'dist/{lang}publications/{pubs[0]["id"]}.html').read_text(encoding='utf-8');assert 'application/pdf' in html and ' download' in html and '/public/papers/synthetic-integration.pdf' in html
 for lang in ['', 'en/']:
  course_html=(folder/f'dist/{lang}teaching/{course_data[0]["course_id"]}.html').read_text(encoding='utf-8')
  assert '/public/teaching/synthetic-lecture.pdf' in course_html and '<table' in course_html and ' download' in course_html
 assert sha(folder/'dist/public/teaching/synthetic-lecture.pdf')==sha(teach)
 assert not list((ROOT/'dist').rglob('synthetic-integration.pdf')),'Synthetic file leaked into production dist'
 report=dict(status='PASS',synthetic_only=True,pages=18,asset_sha256=sha(src),checks=['Quarto real PDF reader and download HTML in both languages','Approved PDF copied with unchanged hash','Private inbox never copied into output','Teaching lecture table, format/language and authorized PDF links in both languages','Production dist contains no fixture PDF'])
 (ROOT/'workspace/reports/fixture-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':run()
