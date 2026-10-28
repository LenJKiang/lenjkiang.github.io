import json,os,re,subprocess,sys
from pathlib import Path
from common import ROOT,local_env,sha,load
commands=[['scripts/validate_content.py'],['-m','unittest','discover','-s','tests','-v'],['scripts/test_fixture_build.py'],['scripts/validate_site.py'],['scripts/prepublish.py'],['scripts/prepublish.py','--staged']]
env=local_env();env['PYTHONIOENCODING']='utf-8';results=[]
for i,args in enumerate(commands,1):
 p=subprocess.run([sys.executable]+args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace');log=p.stdout+p.stderr;filename=f'checks-{i}.log';(ROOT/'workspace/reports'/filename).write_text(log,encoding='utf-8');results.append(dict(command='python '+' '.join(args),status='PASS' if p.returncode==0 else 'FAIL',exit_code=p.returncode,log=filename));print(results[-1]['status'],results[-1]['command'],flush=True)
 if i==2:
  m=re.search(r'Ran (\d+) tests',log);count=int(m.group(1)) if m else 0
preview_manifest=ROOT/'workspace/review/local-preview.yml'
manifest=load(preview_manifest) if preview_manifest.exists() else []
for a in manifest:
 assert sha(ROOT/a['source_file'])==a['sha256']
 if a.get('original_file'):assert sha(ROOT/a['original_file'])==a['sha256']
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode('utf-8')
remotes=subprocess.check_output(['git','remote'],cwd=ROOT).decode('utf-8').splitlines()
result=dict(status='PASS' if all(x['status']=='PASS' for x in results) else 'FAIL',unit_tests=count,commands=results,local_source_hashes_unchanged=True,staged_files=len([x for x in staged.split('\0') if x]),git_remotes=len(remotes),public_binary_assets=len(load(ROOT/'data/resources.yml')),teaching_public_formats=load(ROOT/'config/site.yml')['teaching_public_formats'])
(ROOT/'workspace/reports/checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');sys.exit(0 if result['status']=='PASS' else 1)
