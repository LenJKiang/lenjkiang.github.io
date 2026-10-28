"""Acceptance checks against the actual bilingual build, not a template snapshot."""
import re, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT, load

class ContentPages(unittest.TestCase):
 def read(self, rel, en=False):
  return (ROOT/'dist'/('en' if en else '')/rel).read_text(encoding='utf-8')
 def test_home_has_five_selected_papers_and_biography(self):
  for en in [False,True]:
   text=self.read('index.html',en)
   self.assertEqual(len(re.findall(r'<article class="paper-card"',text)),5)
   self.assertIn('id="biography"',text)
   self.assertIn('2022',text)
   self.assertEqual(re.findall(r'<article class="paper-card" data-paper="([^"]+)"',text),['gwm-hfn','brain-age-sngp','wm-lifespan','smoking-aging','wm-lateralization'])
   self.assertIn('<em>Communications Biology</em>',text)
 def test_research_lists_every_publication_once_with_real_dois(self):
  papers=load(ROOT/'data/publications.yml')
  for en in [False,True]:
   text=self.read('research.html',en)
   for paper in papers:
    self.assertEqual(text.count('data-paper="'+paper['id']+'"'),1)
    if paper['doi']:self.assertIn('https://doi.org/'+paper['doi'],text)
   self.assertNotIn('10.1101/2025.03.05.25323471',text)
 def test_no_internal_audit_or_preview_notices_rendered(self):
  phrases=['公开信息核验于','官网记录可能随时间变化','本地测试预览，资料尚未公开发布','获奖对象为指导学生','以上为本人提供的','Record &amp; sources','Local test preview.','Public information checked on','Manuscript version and full-text redistribution']
  for f in (ROOT/'dist').rglob('*.html'):
   text=f.read_text(encoding='utf-8')
   for phrase in phrases:self.assertNotIn(phrase,text,f.name)
 def test_no_known_abbreviation_typo_or_encoding_damage(self):
  for f in (ROOT/'dist').rglob('*.html'):
   text=f.read_text(encoding='utf-8')
   self.assertNotRegex(text,r'\bCSD\b',f.name)
   self.assertNotIn('\ufffd',text,f.name)
  for en in [False,True]:self.assertIn('CSCD',self.read('about.html',en))
 def test_owner_excluded_papers_have_no_pdf_or_request_links(self):
  for en in [False,True]:
   for id_ in ['betel-alff-dfc','vr-moral-education']:
    text=self.read('publications/'+id_+'.html',en)
    self.assertNotIn('pdf-request',text)
    self.assertNotIn('application/pdf',text)
 def test_simple_research_and_publication_order(self):
  from generate_pages import publication_sort_key
  papers=load(ROOT/'data/publications.yml')
  expected=[p['id'] for p in sorted(papers,key=publication_sort_key)]
  for en in [False,True]:
   text=self.read('research.html',en)
   self.assertEqual(re.findall(r'<article class="paper-card" data-paper="([^"]+)"',text),expected)
   self.assertNotIn('<select',text)
   self.assertNotIn('class="year-group"',text)
   self.assertNotIn('class="direction"',text)
   self.assertNotIn('class="tag"',text)
 def test_year_precedes_author_role_in_sorting(self):
  from generate_pages import publication_sort_key
  records=[dict(id='old-first',year=2022,owner_role='first_author'),dict(id='new-other',year=2025,owner_role='coauthor'),dict(id='new-corresponding',year=2025,owner_role='corresponding_author'),dict(id='new-first',year=2025,owner_role='first_author')]
  self.assertEqual([p['id'] for p in sorted(records,key=publication_sort_key)],['new-first','new-corresponding','new-other','old-first'])
 def test_github_removed_from_home_and_about(self):
  from validate_site import Page
  for en in [False,True]:
   for rel in ['index.html','about.html']:
    for href,tag,attr in Page(self.read(rel,en)).links:
     if tag=='a':self.assertNotIn('github.com',href)
 def test_service_order_and_honors_chronology(self):
  import html
  academic=load(ROOT/'data/academic.yml')
  self.assertEqual([p['id'] for p in academic['service'][:3]],['editorial-board','guangdong-statistics-council','journal-review'])
  honors=academic['honors'];self.assertEqual(honors[0]['id'],'national-case')
  years=[max(map(int,re.findall(r'20\d{2}',h['period']))) for h in honors[1:]]
  self.assertEqual(years,sorted(years,reverse=True))
  for en in [False,True]:
   text=html.unescape(self.read('about.html',en));lang='en' if en else 'zh'
   positions=[text.index(p['title_'+lang]) for p in academic['service']]
   self.assertEqual(positions,sorted(positions))
 def test_teaching_projects_precede_courses(self):
  for en in [False,True]:
   text=self.read('teaching.html',en)
   self.assertLess(text.index('id="teaching-projects"'),text.index('id="courses"'))
   for course in load(ROOT/'data/courses.yml'):self.assertIn('data-course="'+course['course_id']+'"',text)
 def test_english_probability_matches_owner_scope(self):
  text=self.read('teaching/probability.html',True)
  for term in ['economics and management','Long Yonghong','random vectors','Chapter 3']:
   self.assertIn(term,text)
 def test_approved_resources_are_accessible_in_both_languages(self):
  from common import sha
  from validate_site import Page
  resources=load(ROOT/'data/resources.yml')
  for a in resources:
   self.assertEqual(sha(ROOT/'dist'/a['public_path']),a['sha256'])
   for en in [False,True]:
    if a['resource_type']=='paper':
     text=self.read('publications/'+a['related_publication_or_course']+'.html',en)
     self.assertIn('application/pdf',text)
     self.assertIn(a.get('license_url',''),text)
    elif a['resource_type']=='image':text=self.read('index.html',en)
    else:text=self.read('teaching/'+a['related_publication_or_course']+'.html',en)
    self.assertIn('/'+a['public_path'],[url for url,tag,attr in Page(text).links])
 def test_course_resources_have_titles_chapters_and_actual_language(self):
  import html
  resources={a['resource_id']:a for a in load(ROOT/'data/resources.yml')}
  for c in load(ROOT/'data/courses.yml'):
   for en in [False,True]:
    text=html.unescape(self.read('teaching/'+c['course_id']+'.html',en));lang='en' if en else 'zh'
    for rid in c['resources']:
     a=resources[rid]
     if a.get('title_'+lang):self.assertIn(a['title_'+lang],text)
     if a.get('chapter_id'):
      chapter=next(ch for ch in c['chapters'] if ch['id']==a['chapter_id'])
      self.assertIn(chapter['title_'+lang],text)
     if a['language']=='zh':self.assertIn('Chinese' if en else '中文',text)
 def test_team_members_and_all_student_achievements(self):
  profile=load(ROOT/'data/profile.yml');academic=load(ROOT/'data/academic.yml')
  import html
  for en in [False,True]:
   text=self.read('team.html',en);lang='en' if en else 'zh'
   self.assertIn(html.escape(profile['team_members_'+lang]),text)
   for v in academic['student_achievements']:self.assertIn(html.escape(v['title_'+lang]),text)
 def test_all_honors_and_service_are_visible_without_collapsing(self):
  import html
  academic=load(ROOT/'data/academic.yml')
  for en in [False,True]:
   text=self.read('about.html',en);lang='en' if en else 'zh'
   for v in academic['honors']+academic['service']:self.assertIn(v['title_'+lang],html.unescape(text))
   self.assertNotIn('<details>',text)

if __name__=='__main__':unittest.main(verbosity=2)
