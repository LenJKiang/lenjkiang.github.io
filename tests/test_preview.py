import hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,dump
from build_local_preview import preview_assets,build_preview
class LocalPreviewSafety(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='preview-test-',dir=ROOT/'workspace/working');self.r=Path(self.temp.name);(self.r/'workspace/inbox').mkdir(parents=True);(self.r/'workspace/review').mkdir()
  self.f=self.r/'workspace/inbox/test.pdf';self.f.write_bytes(b'SYNTHETIC LOCAL TEST ONLY');self.a=dict(id='test',kind='paper',source_file='workspace/inbox/test.pdf',filename='test.pdf',sha256=hashlib.sha256(self.f.read_bytes()).hexdigest(),permission_scope='local-preview-only')
 def tearDown(self):self.temp.cleanup()
 def check(self,a):dump(self.r/'workspace/review/local-preview.yml',[a]);return preview_assets(self.r)
 def test_local_scope_valid(self):self.assertEqual(len(self.check(self.a)),1)
 def test_public_scope_never_inferred(self):
  with self.assertRaises(AssertionError):self.check(dict(self.a,permission_scope='approved'))
 def test_changed_source_rejected(self):
  self.f.write_bytes(b'changed')
  with self.assertRaises(AssertionError):self.check(self.a)
 def test_ppt_rejected(self):
  f=self.f.with_suffix('.pptx');f.write_bytes(self.f.read_bytes());a=dict(self.a,kind='teaching',source_file='workspace/inbox/test.pptx',filename='test.pptx')
  with self.assertRaises(AssertionError):self.check(a)
 def test_unsafe_filename_rejected(self):
  with self.assertRaises(AssertionError):self.check(dict(self.a,filename='../private.pdf'))
 def test_repeat_overlay_preserves_readonly_pdf_and_removes_stale_files(self):
  import json,stat
  from common import sha
  (self.r/'dist').mkdir();(self.r/'dist/index.html').write_text('<html><head></head><body><main></main></body></html>',encoding='utf-8')
  (self.r/'workspace/reports').mkdir();(self.r/'workspace/reports/build-report.json').write_text(json.dumps({'base_path':'/'}),encoding='utf-8')
  photo=self.r/'workspace/inbox/test.jpg';photo.write_bytes(b'SYNTHETIC PHOTO FOR COPY TEST')
  dump(self.r/'workspace/review/local-preview.yml',[dict(self.a,related='test'),dict(id='photo',kind='photo',source_file='workspace/inbox/test.jpg',filename='photo.jpg',sha256=sha(photo),permission_scope='local-preview-only')])
  out=build_preview(self.r);pdf=out/'_local/test.pdf';pdf.chmod(stat.S_IREAD)
  try:
   (out/'stale-private.txt').write_text('SYNTHETIC STALE FILE',encoding='utf-8')
   build_preview(self.r)
   self.assertEqual(sha(pdf),self.a['sha256']);self.assertFalse((out/'stale-private.txt').exists())
   self.assertEqual(list((self.r/'dist').rglob('*.pdf')),[])
  finally:pdf.chmod(stat.S_IWRITE|stat.S_IREAD)
if __name__=='__main__':unittest.main(verbosity=2)
