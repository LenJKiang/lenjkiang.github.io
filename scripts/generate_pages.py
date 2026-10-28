"""Generate bilingual Quarto pages from the shared academic data."""
import html, re
from pathlib import Path
from urllib.parse import quote
import yaml
from common import ROOT, dump

# Secondary pages retain stable URLs while the navbar has five main sections.
PAGES = [('index', '首页', 'Home'), ('research', '研究', 'Research'),
         ('publications', '论文', 'Publications'), ('teaching', '教学', 'Teaching'),
         ('team', '团队与招生', 'Team & Opportunities'), ('notes', '学术笔记', 'Notes'),
         ('about', '关于我', 'About Me')]
MAIN_PAGES = ['index', 'research', 'teaching', 'team', 'about']

def esc(value):
    return html.escape(str(value), quote=True)

def inline(value):
    """Allow journal-name emphasis while escaping all supplied HTML."""
    return re.sub(r'\*([^*\n]+)\*',r'<em>\1</em>',esc(value))

def publication_sort_key(p):
    roles={'first_author':0,'co_first_author':0,'corresponding_author':1,'co_corresponding_author':1}
    return (-p['year'],roles.get(p.get('owner_role'),2))

def generate(d, cfg, root=ROOT):
    root = Path(root)
    base = 'https://academic.invalid/'
    profile, papers, courses = d['profile'], d['publications'], d['courses']
    assets = {r['resource_id']: r for r in d['resources']}
    academic = d.get('academic', {})
    output_pages = []
    for lang in ['zh', 'en']:
        en = lang == 'en'
        folder = root/'website'/lang
        folder.mkdir(parents=True, exist_ok=True)
        def txt(z, e): return e if en else z
        def val(obj, key): return obj[key+'_'+lang]
        def url(rel): return base+('en/' if en else '')+rel
        def link(rel, title, cls=''):
            return f'<a class="{cls}" href="{esc(url(rel))}">{esc(title)}</a>'
        def public_url(rel): return base+rel
        def pdf_links(p):
            if not p.get('pdf_links_enabled', True): return ''
            if p.get('pdf_public_path'):
                u = esc(public_url(p['pdf_public_path']))
                return f'<a href="{u}">{txt("阅读 PDF", "Read PDF")}</a> · <a download href="{u}">{txt("下载 PDF", "Download PDF")}</a>'
            request = 'mailto:'+profile['email']+'?subject='+quote('PDF request: '+p['title'])
            return f'<a class="pdf-request" href="{esc(request)}">{txt("索取 PDF", "Request PDF")}</a>'
        def paper_card(p):
            doi = f'<a class="doi-link" href="https://doi.org/{esc(p["doi"])}">DOI ↗</a> · ' if p['doi'] else ''
            return (f'<article class="paper-card" data-paper="{p["id"]}" data-year="{p["year"]}" data-area="{p["research_category"]}" data-type="{p["publication_type"]}" data-owner-role="{esc(p.get("owner_role","coauthor"))}">'
                    f'<div class="eyebrow">{p["year"]} / {esc(p["journal"])}</div>'
                    f'<h3>{link("publications/"+p["id"]+".html", p["title"])}</h3>'
                    f'<p class="authors">{esc("; ".join(p["authors"]))}</p>'
                    f'<div class="card-bottom"><span>{doi}{pdf_links(p)}</span></div></article>')
        def academic_list(items, project=False):
            rows = []
            for item in items:
                info = []
                if item.get('period'): info.append(item['period'].replace('、', ', ') if en else item['period'])
                if project:
                    info.append(txt('主持','Principal investigator') if item['role']=='principal_investigator' else txt('参与','Participant'))
                    if item['status'] != 'not_stated':
                        info.append(txt('在研','Active') if item['status']=='active' else txt('已结题','Completed'))
                    if item.get('program_'+lang): info.append(val(item,'program'))
                    if item.get('project_number'): info.append(item['project_number'])
                meta = '<br><span class="academic-meta">'+esc(' · '.join(info))+'</span>' if info else ''
                rows.append('<li>'+esc(val(item,'title'))+meta+'</li>')
            return '<ul class="academic-list">'+''.join(rows)+'</ul>'
        def write(rel, title, description, body):
            path = folder/(rel+'.qmd')
            path.parent.mkdir(parents=True, exist_ok=True)
            twin = base+('' if en else 'en/')+rel+'.html'
            switch = f'<div class="language-bar"><a class="language-switch" href="{twin}" lang="{txt("en","zh-CN")}" hreflang="{txt("en","zh-CN")}">{txt("English →","中文 →")}</a></div>\n'
            header = {'title':title,'description':description,'lang':'en' if en else 'zh-CN','toc':False,'page-layout':'full'}
            path.write_text('---\n'+yaml.safe_dump(header,allow_unicode=True,sort_keys=False)+'---\n\n```{=html}\n'+switch+body+'\n```\n',encoding='utf-8')
            output_pages.append((('en/' if en else '')+rel+'.html',lang,description))
        def project_section(kind):
            items = [p for p in academic.get('projects',[]) if p['kind']==kind]
            if not items: return ''
            id_ = 'projects' if kind=='research' else 'teaching-projects'
            title = txt('科研项目','Research projects') if kind=='research' else txt('教研项目','Teaching projects')
            return f'<section id="{id_}"><h2>{title}</h2>'+academic_list(items,True)+'</section>'
        def publication_list():
            return '<div class="publication-list">'+''.join(paper_card(p) for p in sorted(papers,key=publication_sort_key))+'</div>'
        def course_resources(c):
            rows = ''
            for rid in c['resources']:
                a = assets[rid]; u = public_url(a['public_path'])
                rows += f'<tr><td>{esc(a.get("chapter_id",rid))}</td><td>{a["format"].upper()}</td><td>{esc(a["language"])}</td><td><a href="{u}">{txt("阅读","Read")}</a> · <a href="{u}" download>{txt("下载","Download")}</a></td></tr>'
            content = '<table><thead><tr>'+''.join('<th>'+t+'</th>' for t in [txt('章节 / 资源','Chapter / resource'),txt('格式','Format'),txt('语言','Language'),txt('访问','Access')])+'</tr></thead><tbody>'+rows+'</tbody></table>' if rows else f'<p class="empty-state">{txt("课件陆续更新。","Course materials will be added here.")}</p>'
            return f'<div class="course-resources" data-course="{c["course_id"]}">{content}</div>'
        def course_intro(c):
            s = f'<p>{esc(val(c,"description"))}</p>'
            if c.get('audience_'+lang): s += '<p>'+txt('授课对象：','Audience: ')+esc(val(c,'audience'))+'</p>'
            if c.get('textbook_'+lang): s += '<p>'+txt('教材：','Textbook: ')+esc(val(c,'textbook'))+'</p>'
            return s

        directions = '<p>'+esc(profile.get('research_overview_'+lang) or val(profile,'summary'))+'</p>'
        selected = ''.join(paper_card(p) for p in sorted([p for p in papers if p['selected']],key=lambda p:p.get('selected_order',999))[:5])
        photo = profile.get('photo_resource_id')
        portrait = f'<img class="profile-photo" src="{public_url(assets[photo]["public_path"])}" alt="{esc(profile["name_zh"])} / {esc(profile["name_en"])}">' if photo else '<div class="portrait-placeholder" aria-hidden="true"><span>ZL</span></div>'
        bio = profile.get('bio_'+lang) or val(profile,'summary')
        course_links = ' · '.join(link('teaching/'+c['course_id']+'.html',val(c,'title')) for c in courses)
        home = f'<section class="profile-intro">{portrait}<div><p class="name-secondary">{esc(profile["name_zh"] if en else profile["name_en"])}</p><p>{esc(val(profile,"role"))}<br>{esc(val(profile,"affiliation"))}</p><p><a href="mailto:{profile["email"]}">{profile["email"]}</a></p></div></section>'
        home += f'<section id="biography"><h2>{txt("个人简介","Biography")}</h2><p>{inline(bio)}</p></section><section id="research-interests"><h2>{txt("研究方向","Research interests")}</h2>{directions}</section>'
        home += f'<section id="selected-publications"><h2>{txt("代表性论文","Selected publications")}</h2>{selected}<p>{link("research.html#publications",txt("全部论文 →","All publications →"))}</p></section><section><h2>{txt("教学课程","Teaching")}</h2><p>{course_links}</p></section>'
        write('index',profile['name_en'] if en else profile['name_zh'],val(profile,'summary'),home)

        research = f'<p class="lead">{esc(val(profile,"summary"))}</p><section id="research-interests"><h2>{txt("研究方向","Research interests")}</h2>{directions}</section>'
        research += project_section('research')+f'<section id="publications"><h2>{txt("发表论文","Publications")}</h2>'+publication_list()+'</section>'
        write('research',txt('研究','Research'),val(profile,'summary'),research)
        write('publications',txt('发表论文','Publications'),txt('发表论文列表。','Publication list.'),publication_list())
        for p in papers:
            doi = f'<a class="doi-link" href="https://doi.org/{esc(p["doi"])}">DOI: {esc(p["doi"])}</a> · ' if p['doi'] else ''
            external = f'<a href="{esc(p["publisher_url"])}">Publisher ↗</a> · ' if p.get('publisher_url') and not p['doi'] else ''
            viewer = f'<object class="pdf-reader" data="{public_url(p["pdf_public_path"])}" type="application/pdf" aria-label="PDF"><a href="{public_url(p["pdf_public_path"])}">PDF</a></object>' if p.get('pdf_public_path') else ''
            abstract = '<p>'+esc(p.get('summary_'+lang))+'</p>' if p.get('summary_'+lang) else ''
            body = f'<p class="eyebrow">{p["year"]} / {esc(p["journal"])}</p><p class="authors">{esc("; ".join(p["authors"]))}</p>{abstract}<div class="actions">{doi}{external}{pdf_links(p)}</div>{viewer}'
            write('publications/'+p['id'],p['title'],p['title'],body+link('research.html#publications',txt('← 返回发表论文','← Back to publications')))

        teaching = '<p class="lead">'+esc(profile.get('teaching_overview_'+lang) or txt('课程与教学资料。','Courses and teaching materials.'))+'</p>'
        teaching += project_section('teaching')+f'<section id="courses"><h2>{txt("课程与课件","Courses and materials")}</h2><div class="course-grid">'
        for c in courses:
            teaching += f'<article class="course-card" id="course-{c["course_id"]}"><h2>{link("teaching/"+c["course_id"]+".html",val(c,"title"))}</h2>'+course_intro(c)+course_resources(c)+'</article>'
            chapters = ''.join('<li>'+esc(val(ch,'title'))+'</li>' for ch in c['chapters'])
            body = course_intro(c)
            if chapters: body += '<h2>'+txt('课程内容','Course content')+'</h2><ol>'+chapters+'</ol>'
            body += '<h2>'+txt('课程 PDF','Course PDFs')+'</h2>'+course_resources(c)
            write('teaching/'+c['course_id'],val(c,'title'),val(c,'description'),body+link('teaching.html',txt('← 返回教学','← Back to teaching')))
        write('teaching',txt('教学','Teaching'),txt('教学课程、教研项目和课程PDF。','Courses, teaching projects and course PDFs.'),teaching+'</div></section>')

        team = '<p class="lead">'+esc(profile.get('team_purpose_'+lang) or txt('重视学生科研训练。','We value student research training.'))+'</p>'
        if profile.get('team_members_'+lang): team += '<p class="team-members"><strong>'+esc(val(profile,'team_members'))+'</strong></p>'
        team += '<section><h2>'+txt('加入课题组','Join the group')+'</h2><p>'+esc(profile.get('team_recruitment_'+lang) or txt('欢迎通过邮件联系交流。','Please get in touch by email.'))+'</p><p>'+esc(profile.get('team_contact_'+lang) or '')+' <a href="mailto:'+profile['email']+'">'+profile['email']+'</a></p></section>'
        team += '<section id="student-achievements"><h2>'+txt('指导学生成果','Achievements of supervised students')+'</h2>'+academic_list(academic.get('student_achievements',[]))+'</section>'
        write('team',txt('团队与招生','Team & Opportunities'),txt('课题组、研究生培养与学生科研成果。','Our group, graduate supervision and student achievements.'),team)

        notes = '<p>'+txt('统计学、神经影像与科研实践中的方法和思考。','Methods and reflections on statistics, neuroimaging and research practice.')+'</p>'
        write('notes',txt('学术笔记','Notes'),txt('统计学、神经影像与科研实践。','Statistics, neuroimaging and research practice.'),notes)
        about = f'<p class="lead">{esc(profile.get("about_intro_"+lang) or val(profile,"role"))}<br>{esc(val(profile,"affiliation"))}</p>'
        about += '<section id="service"><h2>'+txt('兼职与学术服务','Appointments and academic service')+'</h2>'+academic_list(academic.get('service',[]))+'</section>'
        about += '<section id="honors"><h2>'+txt('荣誉与获奖','Honors and awards')+'</h2>'+academic_list(academic.get('honors',[]))+'</section>'
        about += '<section id="links"><h2>'+txt('学术链接','Academic links')+'</h2><ul>'+''.join(f'<li><a href="{esc(l["url"])}">{esc(val(l,"title"))} ↗</a></li>' for l in d['links'] if l['id']!='github')+'</ul></section>'
        about += f'<section id="contact"><h2>{txt("联系方式","Contact")}</h2><p><a href="mailto:{profile["email"]}">{profile["email"]}</a></p><p>'+txt('微信公众号：','WeChat official account: ')+esc(profile['wechat'])+'</p></section>'
        write('about',txt('关于我','About Me'),txt('学术服务、荣誉获奖与联系方式。','Academic service, honors, awards and contact information.'),about)

        nav = [{'href':n+'.qmd','text':e if en else z} for n,z,e in PAGES if n in MAIN_PAGES]
        project = {'project':{'type':'website','output-dir':'../../workspace/build/'+lang,'render':[str(Path(p).relative_to('en') if en else Path(p)).replace('.html','.qmd') for p,l,_ in output_pages if l==lang]},'website':{'title':profile['name_en'] if en else profile['name_zh'],'search':False,'navbar':{'background':'#FFFFFF','foreground':'#16324F','left':nav,'collapse-below':'lg'},'page-footer':{'left':'© '+profile['name_en'],'right':txt('统计学 · 脑科学 · 科研实践','Statistics · Brain science · Research practice')}},'format':{'html':{'theme':'cosmo','css':'styles.css','lang':'en' if en else 'zh-CN','toc':False,'anchor-sections':True,'smooth-scroll':False}},'filters':['windows-paths.lua'],'execute':{'enabled':False}}
        dump(folder/'_quarto.yml',project)
        (folder/'windows-paths.lua').write_text((root/'website/shared/windows-paths.lua').read_text(encoding='utf-8-sig'),encoding='utf-8')
        (folder/'styles.css').write_text((root/'website/shared/styles.css').read_text(encoding='utf-8'),encoding='utf-8')
    return output_pages
