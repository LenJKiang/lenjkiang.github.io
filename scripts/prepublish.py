"""Pre-commit/pre-publish local guard. No upload, staging, commit or push."""
import argparse, re, subprocess, sys
from common import ROOT, validate, load, sha

def check_staged():
 validate()
 result=subprocess.run(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'],cwd=ROOT,capture_output=True,check=True)
 files=[x for x in result.stdout.decode('utf-8').split('\0') if x]
 allowed={a['public_path']:a for a in load(ROOT/'data/resources.yml')}
 for name in files:
  normalized=name.replace('\\','/');parts=normalized.split('/')
  assert not any(p in {'workspace','dist','.venv','__pycache__','.quarto','.env'} for p in parts),'Private/generated file staged: '+normalized
  assert not re.search(r'(^|/)(\.env[^/]*|credentials[^/]*|id_rsa|.*\.(pem|key|p12))$',normalized,re.I),'Possible secret staged'
  blob=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
  if normalized.startswith('public/'):
   import hashlib
   assert normalized in allowed,'Unapproved public file staged';assert hashlib.sha256(blob).hexdigest()==allowed[normalized]['sha256'],'Staged asset hash mismatch'
  elif normalized.lower().endswith(('.pdf','.pptx','.png','.jpg','.jpeg','.zip')):raise AssertionError('Binary outside approved public area staged: '+normalized)
  if len(blob)<2*1024**2 and not normalized.startswith('public/'):
   text=blob.decode('utf-8',errors='ignore')
   assert not re.search(r'(?:ghp_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',text),'Possible credential in staged content'
 all_changes=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT)
 # Validate the complete staged tree, not only the working copy.
 # Snapshot consists only of Git-tracked bytes and must stand alone without workspace/.
 if all_changes:
  import tempfile, pathlib
  with tempfile.TemporaryDirectory(prefix='staged-check-',dir=ROOT/'workspace/working') as tmp:
   dest=pathlib.Path(tmp)
   paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0')
   for name in filter(None,paths):
    parts=name.replace('\\','/').split('/')
    assert not any(p in {'workspace','dist','.venv','.env'} for p in parts),'Private tree entry staged'
    target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(subprocess.check_output(['git','show',':'+name],cwd=ROOT))
   validate(dest)
 print('PASS staged guard:',len(files),'staged changes; no changes were staged by this command')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');a=p.parse_args()
 try:
  if a.staged:check_staged()
  else:
   validate();from validate_site import validate_output
   print(validate_output(ROOT/'dist',load(ROOT/'config/site.yml')))
 except (AssertionError,subprocess.CalledProcessError) as e:p.exit(1,'PREPUBLISH FAILED: '+str(e)+'\n')
