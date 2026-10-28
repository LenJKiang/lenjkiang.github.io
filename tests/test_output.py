import json,re,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,load
from validate_site import validate_output
class OutputSafety(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='output-test-',dir=ROOT/'workspace/working');self.dist=Path(self.temp.name)/'dist';shutil.copytree(ROOT/'dist',self.dist)
  self.cfg=load(ROOT/'config/site.yml');self.cfg['base_path']=json.loads((ROOT/'workspace/reports/build-report.json').read_text(encoding='utf-8'))['base_path']
 def tearDown(self):self.temp.cleanup()
 def fails(self):
  with self.assertRaises(AssertionError):validate_output(self.dist,self.cfg)
 def test_clean_build(self):
  expected=2*(7+len(load(ROOT/'data/publications.yml'))+len(load(ROOT/'data/courses.yml')))
  self.assertEqual(validate_output(self.dist,self.cfg)['pages'],expected)
 def test_unapproved_pdf_rejected(self):(self.dist/'private.pdf').write_bytes(b'private');self.fails()
 def test_private_text_rejected(self):(self.dist/'private-inventory.txt').write_text('private',encoding='utf-8');self.fails()
 def test_workspace_rejected(self):
  (self.dist/'workspace').mkdir();(self.dist/'workspace/secret.txt').write_text('private',encoding='utf-8');self.fails()
 def test_missing_local_script_rejected(self):(self.dist/'assets/filters.js').unlink();self.fails()
 def test_broken_language_switch_rejected(self):
  p=self.dist/'index.html';s=p.read_text(encoding='utf-8');s=s.replace('class="language-switch"','class="broken-switch"');p.write_text(s,encoding='utf-8');self.fails()
 def test_missing_canonical_rejected(self):
  p=self.dist/'index.html';s=re.sub(r'<link rel="canonical"[^>]+>','',p.read_text(encoding='utf-8'));p.write_text(s,encoding='utf-8');self.fails()
 def test_private_path_in_search_index_rejected(self):
  (self.dist/'search.json').write_text('["E:/private/person.pdf"]',encoding='utf-8');self.fails()
 def test_capacity_limit_enforced(self):self.cfg['capacity_limit_mb']=0.0001;self.fails()
 def test_wrong_base_path_rejected(self):self.cfg['base_path']='/wrong-project/';self.fails()
if __name__=='__main__':unittest.main(verbosity=2)
