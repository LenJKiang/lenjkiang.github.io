// Real Edge browser checks. All browser profile/output files remain in workspace/.
const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..');process.env.TEMP=path.join(root,'workspace/tmp');process.env.TMP=process.env.TEMP;process.env.TMPDIR=process.env.TEMP;
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
async function main(){
 const base=process.argv[2]||'/';const origin=process.env.PREVIEW_ORIGIN||'http://127.0.0.1:8000';const out=path.join(root,'workspace/reports/browser');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launchPersistentContext(path.join(root,'workspace/working/browser-profile'),{headless:true,acceptDownloads:true,downloadsPath:path.join(out,'downloads'),executablePath:process.env.EDGE_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',viewport:{width:1440,height:1000},env:{...process.env,TEMP:path.join(root,'workspace/tmp'),TMP:path.join(root,'workspace/tmp')},args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 let checks=[];let errors=[];let warnings=[];const page=browser.pages()[0];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().startsWith(origin)&&r.status()>=400)errors.push(r.status()+' '+r.url());});
 const check=(ok,name)=>{if(!ok)throw new Error(name);checks.push(name);};
 try{
 for(const lang of ['','en/']){
  let response=await page.goto(origin+base+lang+'index.html',{waitUntil:'networkidle'});check(response.status()===200,'HTTP 200 '+lang+'home');
  check(await page.locator('h1').count()===1,'Semantic heading '+lang);check((await page.locator('html').getAttribute('lang'))===(lang?'en':'zh-CN'),'HTML language '+lang);
  check(await page.locator('.navbar-nav .nav-item').count()===5,'Five primary navigation items '+lang);
  check(await page.locator('.paper-card').count()===5,'Five selected publications on home '+lang);
  check(JSON.stringify(await page.locator('.paper-card').evaluateAll(xs=>xs.map(x=>x.dataset.paper)))===JSON.stringify(['gwm-hfn','brain-age-sngp','wm-lifespan','smoking-aging','wm-lateralization']),'Five owner-selected papers in requested order '+lang);
  check(await page.locator('a[href*="github.com"]').count()===0,'No GitHub link on home '+lang);
  check(await page.locator('#research-interests p').count()===1&&await page.locator('#research-interests h3').count()===0,'One research paragraph on home '+lang);
  await page.screenshot({path:path.join(out,(lang?'en':'zh')+'-desktop.png'),fullPage:true});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Desktop no horizontal overflow '+lang);
  await page.locator('.language-switch').click();await page.waitForLoadState('networkidle');check([origin+base+(lang?'':'en/')+'index.html',origin+base+(lang?'':'en/')].includes(page.url()),'Language switch '+lang+' actual='+page.url());
 }
 await page.goto(origin+base+'publications.html',{waitUntil:'networkidle'});check(await page.locator('select,.year-group').count()===0,'Flat publication list without year groups or filters');
 await page.locator('.paper-card h3 a').first().click();await page.waitForLoadState('networkidle');check(page.url().includes('/publications/'),'Publication details navigation');
 const detail=page.url();await page.locator('.language-switch').click();await page.waitForLoadState('networkidle');check(page.url()===detail.replace(origin+base,origin+base+'en/'),'Detail language counterpart');
 await page.goto(origin+base+'teaching.html',{waitUntil:'networkidle'});check(await page.locator('.course-card').count()===5,'Five verified course records');await page.locator('.course-card h2 a').first().click();await page.waitForLoadState('networkidle');if(process.env.CHECK_LOCAL_RESOURCES==='1'){check(await page.locator('.local-lessons tbody tr').count()===7,'Seven PDF lessons in chapters 1 and 2');check(await page.locator('[data-chapter="chapter-01"] tbody tr').count()===5&&await page.locator('[data-chapter="chapter-02"] tbody tr').count()===2,'Five chapter 1 lessons and two chapter 2 lessons');check(await page.locator('a[href$=".ppt"],a[href$=".pptx"]').count()===0,'No PPT download links');}else{check(await page.locator('.empty-state').isVisible(),'Course truthfully states no resources');}
 for(const lang of ['','en/']){
 await page.setViewportSize({width:390,height:844});await page.goto(origin+base+lang+'index.html',{waitUntil:'networkidle'});
 check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Mobile no horizontal overflow '+lang);await page.screenshot({path:path.join(out,(lang?'en':'zh')+'-mobile.png'),fullPage:true});
 const toggle=page.locator('.navbar-toggler');check(await toggle.isVisible(),'Mobile menu toggle visible '+lang);await toggle.click();await page.locator('.navbar-collapse').waitFor({state:'visible'});check(await page.locator('.navbar-collapse').isVisible(),'Mobile menu opens '+lang);await toggle.click();
 }
 await page.setViewportSize({width:1440,height:1000});await page.goto(origin+base+'index.html',{waitUntil:'networkidle'});await page.keyboard.press('Tab');check(await page.locator(':focus').count()===1,'Keyboard focus available');
 await page.goto(origin+base+'research.html',{waitUntil:'networkidle'});check(await page.locator('#projects li').count()===7,'Seven research projects, active and completed');await page.screenshot({path:path.join(out,'zh-research.png'),fullPage:true});
 await page.goto(origin+base+'teaching.html',{waitUntil:'networkidle'});check(await page.locator('#teaching-projects li').count()===3,'Three teaching projects with roles');
 await page.goto(origin+base+'about.html',{waitUntil:'networkidle'});check(await page.locator('#honors li').count()===14,'Fourteen personal honors');await page.screenshot({path:path.join(out,'zh-about.png'),fullPage:true});
 await page.goto(origin+base+'team.html',{waitUntil:'networkidle'});check(await page.locator('#student-achievements li').count()===11,'All eleven student achievement records');
 for(const lang of ['','en/']){
  await page.goto(origin+base+lang+'research.html',{waitUntil:'networkidle'});check(await page.locator('.paper-card').count()===22,'Research contains all 22 papers '+lang);check(await page.locator('.paper-card .doi-link').count()===20,'20 verified DOI links '+lang);
  check(await page.locator('select,.year-group,.paper-card .tag').count()===0,'No filters, year groups or area tags '+lang);
  const records=await page.locator('.paper-card').evaluateAll(xs=>xs.map(x=>({...x.dataset})));const ranks={first_author:0,co_first_author:0,corresponding_author:1,co_corresponding_author:1};const sorted=[...records].sort((a,b)=>Number(b.year)-Number(a.year)||(ranks[a.ownerRole]??2)-(ranks[b.ownerRole]??2));check(JSON.stringify(records.map(x=>x.paper))===JSON.stringify(sorted.map(x=>x.paper)),'Publication order: year then first/corresponding/other author '+lang);
  await page.goto(origin+base+lang+'teaching.html',{waitUntil:'networkidle'});check(await page.evaluate(()=>!!(document.querySelector('#teaching-projects').compareDocumentPosition(document.querySelector('#courses'))&Node.DOCUMENT_POSITION_FOLLOWING)),'Teaching projects precede course materials '+lang);
  if(process.env.CHECK_LOCAL_RESOURCES==='1')check(await page.locator('#course-probability .local-pdf').count()===7,'Seven PDF lessons accessible directly on teaching overview '+lang);
  await page.goto(origin+base+lang+'team.html',{waitUntil:'networkidle'});check((await page.locator('.team-members').innerText()).includes(lang?'six master':'6名统计学'),'Confirmed team membership '+lang);check(await page.locator('.team-members strong').count()===1,'Team membership emphasized '+lang);
  await page.goto(origin+base+lang+'about.html',{waitUntil:'networkidle'});check(await page.locator('a[href*="github.com"]').count()===0,'No GitHub link on about '+lang);check(await page.locator('#service li').count()===5,'Five appointments and service records '+lang);check((await page.locator('#service li').nth(1).innerText()).includes(lang?'Council Member':'理事'),'Council membership second '+lang);
  for(const name of ['index','research','teaching','team','about']){
   await page.setViewportSize({width:390,height:844});await page.goto(origin+base+lang+name+'.html',{waitUntil:'networkidle'});
   check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Mobile no horizontal overflow '+lang+name);
   const main=await page.locator('main').innerText();check(!/公开信息核验于|本地测试预览|以上为本人提供的|获奖对象为指导学生|Local test preview|Public information checked on/.test(main),'No internal audit notices '+lang+name);
   await page.screenshot({path:path.join(out,(lang?'en':'zh')+'-'+name+'-mobile-v04.png'),fullPage:true});
  }
 }
 if(process.env.CHECK_LOCAL_RESOURCES==='1'){
 await page.goto(origin+base+'index.html',{waitUntil:'networkidle'});check(await page.locator('.profile-photo').evaluate(x=>x.complete&&x.naturalWidth>0),'Real profile photo loads');
 await page.goto(origin+base+'publications.html',{waitUntil:'networkidle'});const paperUrls=await page.locator('.local-pdf').evaluateAll(xs=>xs.map(a=>a.href));check(paperUrls.length===20,'Twenty papers with PDF links; two metadata-only records');check(await page.locator('.pdf-request').count()===0,'No PDF request links for the two opted-out records');
 await page.goto(origin+base+'teaching/probability.html',{waitUntil:'networkidle'});const lessonUrls=await page.locator('.local-pdf').evaluateAll(xs=>xs.map(a=>a.href));
 for(const u of [...paperUrls,...lessonUrls]){const response=await page.request.get(u);check(response.status()===200&&(await response.body()).subarray(0,5).toString()==='%PDF-','Real PDF response '+u.split('/').pop());}
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('.local-download').first().click()]);const save=path.join(out,'download-test.pdf');const crypto=require('node:crypto');const hash=x=>crypto.createHash('sha256').update(x).digest('hex');try{await download.saveAs(save);check(hash(fs.readFileSync(save))===hash(fs.readFileSync(path.join(root,'workspace/preview-site/_local',download.suggestedFilename()))),'Actual browser download preserves SHA-256');}catch(e){warnings.push('Edge automation canceled file save; actual browser save remains unverified. HTTP attachment response and bytes are checked separately.');const r=await page.request.get(download.url());check(r.status()===200&&(r.headers()['content-disposition']||'').startsWith('attachment;'),'HTTP attachment response');check(hash(await r.body())===hash(fs.readFileSync(path.join(root,'workspace/preview-site/_local',download.suggestedFilename()))),'HTTP download payload preserves SHA-256');}
 }
 check(errors.length===0,'No browser JS errors or failed local responses');
 const report={status:warnings.length?'PASS_WITH_LIMITATION':'PASS',warnings,base_path:base,browser:await browser.browser().version(),checks,errors};fs.writeFileSync(path.join(out,process.env.CHECK_LOCAL_RESOURCES==='1'?(base==='/'?'local-root-report.json':'local-project-report.json'):(base==='/'?'root-report.json':'project-report.json')),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
