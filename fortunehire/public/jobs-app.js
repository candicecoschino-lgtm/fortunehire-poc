import {JOB_FUNCTIONS,JOB_FUNCTION_OPTIONS} from './job-functions.js';
import {mountSavedSearches} from './saved-searches.js';
import {ACTIVITY_KEY,readJobActivity,setJobActivity,activityFlags,activityView,trackedJobs} from './job-activity.js';
import { JOB_KEYS, MULTI_FILTER_KEYS, US_STATES, ARRANGEMENTS, todayInNewYork, readJobFilters, serializeJobFilters, isCurrent, filterJobs, paginateJobs, salaryText, validateJobs } from './jobs.js';
import {postedLabel,locationSummary,paySummary,todayPostingNote} from './job-presentation.js';
import {installMultiFilterBehavior} from './multi-filter-behavior.js';
const $=id=>document.getElementById(id);
const e=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const link=(text,url)=>{const a=e('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
let jobs=[],ready=false,currentPage='1',pending,renderedDay='',collection=null,logos={};
let activity=[],activityStorage,activityAvailable=true,companyDirectory=[],undoAction=null;
const FILTER_CONTROLS=JOB_KEYS.filter(k=>!['page','travel','payPosted'].includes(k));
installMultiFilterBehavior(document);
try{activityStorage=window.localStorage;activity=readJobActivity(activityStorage);}catch{activityAvailable=false;}
const labelDate=value=>new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
function card(j,f){
  const employmentType=j.employmentTypeBasis==='assumed-full-time'?'Not specified':j.employmentType;
  const selectedStates=Array.isArray(f.state)?f.state:f.state?[f.state]:[];
  const applicablePayStates=j.salary?.scopeStates||j.publishedPay?.scopeStates||[];
  const selectedEligible=selectedStates.filter(state=>j.arrangement==='remote'?j.remoteScope==='nationwide'||j.eligibleStates.includes(state):j.locations.some(location=>location.state===state));
  const cardState=selectedEligible.find(state=>!applicablePayStates.length||applicablePayStates.includes(state))||selectedEligible[0]||'';
  const article=e('article',undefined,'card job-card');
  article.dataset.jobId=j.id;
  const top=e('div',undefined,'card-top');const mark=e('span',undefined,'company-mark');mark.setAttribute('aria-hidden','true');const monogram=e('span',j.companyName.split(/\s+/).map(s=>s[0]).slice(0,2).join(''),'monogram');mark.append(monogram);
  const logo=logos[j.companyId];
  if(logo&&new RegExp(`^\\./assets/company-logos/${j.companyId}\\.(png|ico|jpg|svg)$`).test(logo.src)){
    const img=e('img',undefined,'company-logo');img.alt='';img.width=40;img.height=40;img.loading='lazy';img.decoding='async';
    img.addEventListener('load',()=>{monogram.hidden=true;img.classList.add('is-loaded');},{once:true});
    img.addEventListener('error',()=>{img.remove();monogram.hidden=false;},{once:true});mark.append(img);img.src=new URL(logo.src,import.meta.url).href;
  }
  const identity=e('div');const title=e('h3',undefined,'job-title');const titleLink=link(j.title,j.url);titleLink.setAttribute('aria-label',`${j.title} at ${j.companyName} (opens employer posting in a new tab)`);title.append(titleLink);
  const byline=e('div',undefined,'job-byline');const posted=e('time',postedLabel(j.postedAt,todayInNewYork()),'job-posted');posted.dateTime=j.postedAt;posted.title=`Employer posting date: ${labelDate(j.postedAt)}`;byline.append(e('span',j.companyName,'job-company'),e('span','\u00b7'),posted);identity.append(title,byline);top.append(mark,identity);
  const meta=e('div',undefined,'job-meta');const badges=e('div',undefined,'job-badges');
  badges.append(e('span',j.arrangement==='remote'&&j.remoteScope==='states'?'Remote \u00b7 State restricted':j.arrangement==='unknown'?'Work arrangement not specified':ARRANGEMENTS[j.arrangement],`job-badge ${j.arrangement}`));
  if(employmentType!=='Not specified')badges.append(e('span',employmentType,'job-badge'));
  if(j.travelRequired===true)badges.append(e('span','Travel required','job-badge'));
  meta.append(e('p',locationSummary(j,f.state),'job-location'),badges);
  if(j.organizerUnavailable)meta.append(e('p',j.status==='closed'?'This posting was marked closed.':'Outside the current job feed; availability is not verified.','job-availability'));
  const details=e('details',undefined,'job-details');const summary=e('summary','Job details & sources');const body=e('div',undefined,'job-detail-body');
  const fn={primaryFunction:j.primaryJobFunction,basis:j.jobFunctionBasis,confidence:j.jobFunctionConfidence,evidence:j.jobFunctionEvidence||[],reviewRequired:j.jobFunctionReviewRequired};
  const fnSource=`Primary job function (${fn.basis} · ${fn.confidence} confidence${fn.reviewRequired?'; review suggested':''})`;
  const dl=e('dl');for(const [key,val]of [['Posted',labelDate(j.postedAt)],['Last successfully checked',labelDate(j.reviewedAt)],['Employment type',employmentType],['Industry',j.industry],[fnSource,JOB_FUNCTIONS[fn.primaryFunction]],[j.identifierType==='posting-id'?'Employer posting ID':'Employer requisition',j.requisitionId],['Employer deadline',j.closesAt?labelDate(j.closesAt):'Not specified']])dl.append(e('dt',key),e('dd',val));
  if(j.arrangement==='remote'&&j.remoteScope==='states')dl.append(e('dt','Eligible remote states'),e('dd',j.eligibleStates.join(', ')));
  const payScope=j.salary?.scopeStates||j.publishedPay?.scopeStates||[];const payApplies=!cardState||!payScope.length||payScope.includes(cardState);
  for(const excerpt of fn.evidence)body.append(e('p','Function evidence: '+excerpt));
  body.append(e('p','Location & eligibility: '+j.locationNote));
  if(j.arrangementBasis==='listed-location')body.append(e('p','Work arrangement: On-site, classified from the listed city/state. The employer did not explicitly state a work arrangement.'));
  if(payApplies&&(j.salary||j.publishedPay))body.append(e('p','Employer-published pay: '+salaryText(j)));
  else if(!payApplies)body.append(e('p','Published pay does not have verified applicability to the selected state. Open the employer posting for its location-specific terms.'));
  for(const note of new Set([j.salaryNote,j.publishedPay?.note].filter(Boolean)))body.append(e('p',note));
  body.append(e('p',j.travelRequired===true?`Travel required: ${j.travelNote}`:j.travelRequired===false?'Travel: employer states none':'Travel requirements not specified'),dl,e('p',j.sourceNote),link('Official posting & application \u2197',j.url),e('br'),link('Employer classification source \u2197',j.companySource));
  details.append(summary,body);
  const pay=e('div',undefined,'job-pay');const presentation=paySummary(j,selectedStates);
  if(presentation.detail){pay.append(e('p',presentation.text,'job-salary'));const button=e('button','Full pay details \u2193','inline-detail');button.type='button';button.setAttribute('aria-label',`View published pay for ${j.title} at ${j.companyName}`);button.addEventListener('click',()=>{details.open=true;summary.focus();});pay.append(button);}
  else pay.append(e('p',presentation.text,'job-salary'+(!j.salary&&!j.publishedPay||!payApplies?' unavailable':'')));
  if(presentation.note)pay.append(e('p',presentation.note,'pay-context'));
  const actions=e('div',undefined,'job-actions');const apply=link(j.organizerUnavailable?'View employer posting \u2197':'Apply at employer \u2197',j.url);apply.className='career-link';apply.setAttribute('aria-label',`${j.organizerUnavailable?'View employer posting':'View role and apply'}: ${j.title} at ${j.companyName} (opens in a new tab)`);actions.append(apply);
  const tools=e('div',undefined,'job-tools'),flags=activityFlags(activity,j.id);
  for(const [flag,on,off] of [['saved','Saved','Save'],['hidden','Unhide','Hide'],['applied','Applied','Mark applied']]){
    const button=e('button',flags[flag]?on:off,'job-tool');button.type='button';button.dataset.action=flag;button.disabled=!activityAvailable;
    button.setAttribute('aria-pressed',String(flags[flag]));button.setAttribute('aria-label',`${flags[flag]?on:off} job: ${j.title}`);
    button.addEventListener('click',()=>jobAction(j,flag,!activityFlags(activity,j.id)[flag]));tools.append(button);
  }
  article.append(top,meta,pay,actions,details,tools);return article;
}

function jobAction(job,flag,value,undo=false){
 const oldIndex=[...$('results').children].findIndex(node=>node.dataset.jobId===job.id);
 try{
  const previous=!!activityFlags(activity,job.id)[flag];activity=setJobActivity(activityStorage,job,flag,value);
  undoAction=undo?null:{job,flag,value:previous};render();
  $('job-action-status').textContent=undo?'Change undone.':`${flag==='saved'?(value?'Saved':'Unsaved'):flag==='hidden'?(value?'Hidden':'Unhidden'):(value?'Marked applied':'Removed applied mark')}: ${job.title}.`;
  $('undo-job-action').hidden=!undoAction;
  const cards=[...$('results').children],target=cards.find(node=>node.dataset.jobId===job.id)||cards[Math.max(0,oldIndex)];
  const focus=target?.querySelector(`[data-action="${flag}"]`)||$('count');focus.tabIndex=focus.tabIndex<0?0:focus.tabIndex;focus.focus();
 }catch(error){$('job-action-status').textContent=error.message.startsWith('Your browser list')?error.message:'Your browser could not remember this change. Allow site storage or try again.';}
}

function renderFilterChips(f){
  const active=[];
  for(const key of MULTI_FILTER_KEYS){
    const checked=key==='company'||key==='companyExclude'?companyInputs(key).filter(input=>input.checked):[...$(key).querySelectorAll('input[type="checkbox"]:checked')];
    for(const input of checked)active.push([key,input.value,key==='company'?`Include: ${input.dataset.label}`:key==='companyExclude'?`Exclude: ${input.dataset.label}`:input.parentElement.textContent.trim()]);
  }
  for(const key of ['industry','type','pay','posted'])if(f[key]){const control=$(key);active.push([key,'',control.options[control.selectedIndex]?.textContent||f[key]]);}
  if(f.q.trim())active.push(['q','',`Search: ${f.q.trim()}`]);
  if(f.travel==='exclude')active.push(['travel','','Exclude travel-required roles']);
  if(f.payPosted)active.push(['payPosted','','Pay posted']);
  $('active-filters').replaceChildren(...active.map(([key,value,label])=>{
    const button=e('button',label+' \u00d7','filter-chip');button.type='button';button.setAttribute('aria-label',`Remove filter: ${label}`);
    button.addEventListener('click',()=>{const index=[...$('active-filters').children].indexOf(button);if(key==='travel')$('include-travel').checked=true;else if(key==='payPosted')$('pay-posted').checked=false;else if(MULTI_FILTER_KEYS.includes(key)){const inputs=key==='company'||key==='companyExclude'?companyInputs(key):[...$(key).querySelectorAll('input[type="checkbox"]')];const input=inputs.find(option=>option.value===value);if(input)input.checked=false;updateMultiSummary(key);}else if(key==='q')$('q').value='';else $(key).value='';change();const remaining=$('active-filters').children;if(remaining.length)remaining[Math.min(index,remaining.length-1)].focus();else $('q').focus();});return button;
  }));
  $('active-filters').hidden=!active.length;$('reset').hidden=!active.length;
  const count=['industry','type','pay','posted','payPosted'].filter(key=>f[key]).length+MULTI_FILTER_KEYS.reduce((sum,key)=>sum+(Array.isArray(f[key])?f[key].length:f[key]?1:0),0)+(f.travel==='exclude'?1:0);
  $('more-filter-count').textContent=`${count} selected`;$('more-filter-count').hidden=!count;
  return active.length;
}

function setOptions(id,values){const select=$(id);select.replaceChildren(select.options[0]);for(const [value,label]of values){const o=e('option',label);o.value=value;select.append(o);}select.disabled=false;}
function setMultiOptions(id,values){
  const box=$(id);box.replaceChildren();
  for(const [value,label] of values){const row=e('label');const input=document.createElement('input');input.type='checkbox';input.value=value;row.append(input,e('span',label));box.append(row);}
  box.addEventListener('change',()=>updateMultiSummary(id));
  updateMultiSummary(id);
}
function companyInputs(id){return [...$('company-rows').querySelectorAll(`input[data-filter="${id}"]`)];}
function setCompanyOptions(values){
  const rows=$('company-rows');rows.replaceChildren();
  for(const [value,name] of values){
    const row=e('div',undefined,'company-filter-row');row.dataset.name=name.toLowerCase();
    const include=e('label');const yes=e('input');yes.type='checkbox';yes.value=value;yes.dataset.filter='company';yes.dataset.label=name;yes.setAttribute('aria-label',`Include ${name}`);include.append(yes);
    const exclude=e('label');const no=e('input');no.type='checkbox';no.value=value;no.dataset.filter='companyExclude';no.dataset.label=name;no.setAttribute('aria-label',`Exclude ${name}`);exclude.append(no);
    row.append(include,e('span',name),exclude);rows.append(row);
  }
  rows.addEventListener('change',event=>{const input=event.target;if(input.checked){const opposite=input.dataset.filter==='company'?'companyExclude':'company';const other=companyInputs(opposite).find(item=>item.value===input.value);if(other)other.checked=false;}updateMultiSummary('company');change();});
  $('company-search').addEventListener('input',()=>{const query=$('company-search').value.trim().toLowerCase();for(const row of rows.children)row.hidden=!row.dataset.name.includes(query);});
  updateMultiSummary('company');
}
function updateMultiSummary(id){
  if(id==='company'||id==='companyExclude'){const yes=companyInputs('company').filter(input=>input.checked).length,no=companyInputs('companyExclude').filter(input=>input.checked).length;$('company-summary').textContent=yes||no?`${yes} included · ${no} excluded`:'All companies';return;}
  const selected=[...$(id).querySelectorAll('input[type="checkbox"]:checked')].map(input=>input.parentElement.textContent.trim());
  const summary=$(`${id}-summary`);
  const empty={state:'Any state',arrangement:'Any arrangement',function:'Any function'}[id];
  summary.textContent=!selected.length?empty:selected.length===1?selected[0]:`${selected[0]} + ${selected.length-1} more`;
}
function multiValues(id){return (id==='company'||id==='companyExclude'?companyInputs(id):[...$(id).querySelectorAll('input[type="checkbox"]')]).filter(input=>input.checked).map(input=>input.value);}
function restore(){
  applyFilterValues(readJobFilters(location.search));
}
function applyFilterValues(f){
  currentPage=f.page;
  for(const k of FILTER_CONTROLS){
    if(MULTI_FILTER_KEYS.includes(k)){
      const values=Array.isArray(f[k])?f[k]:f[k]?[f[k]]:[];
      const box=$(k);const inputs=k==='company'||k==='companyExclude'?companyInputs(k):[...box.querySelectorAll('input[type="checkbox"]')];
      if(k!=='company'&&k!=='companyExclude')for(const value of values)if(!inputs.some(input=>input.value===value)){const row=e('label');const input=document.createElement('input');input.type='checkbox';input.value=value;row.append(input,e('span',`Unavailable: ${value}`));box.append(row);}
      for(const input of k==='company'||k==='companyExclude'?inputs:box.querySelectorAll('input[type="checkbox"]'))input.checked=values.includes(input.value);
      updateMultiSummary(k);continue;
    }
    const control=$(k);if(k!=='q'&&f[k]&&![...control.options].some(o=>o.value===f[k])){const o=e('option',`Unavailable: ${f[k]}`);o.value=f[k];control.append(o);}control.value=f[k];
  }
  $('include-travel').checked=f.travel!=='exclude';
  $('pay-posted').checked=f.payPosted==='1';
  document.querySelector('.more-filters').open=['company','industry','function','type','pay','posted','payPosted'].some(k=>Array.isArray(f[k])?f[k].length>0:Boolean(f[k]))||f.travel==='exclude';
}
function selected(){return {...Object.fromEntries(FILTER_CONTROLS.map(k=>[k,MULTI_FILTER_KEYS.includes(k)?multiValues(k):$(k).value])),payPosted:$('pay-posted').checked?'1':'',travel:$('include-travel').checked?'include':'exclude',page:currentPage};}
function render(sync=true){
  if(!ready)return;
  const f=selected();const today=todayInNewYork();renderedDay=today;const visible=jobs.filter(j=>isCurrent(j,today));
  const library=f.view?trackedJobs(jobs,activity,snapshot=>validateJobs({schemaVersion:1,jobs:[snapshot]},companyDirectory)[0],today):jobs;
  const candidates=activityView(library,activity,f.view),matches=filterJobs(candidates,f,today,!!f.view);const page=paginateJobs(matches,currentPage);currentPage=String(page.page);f.page=currentPage;
  $('results').replaceChildren(...page.items.map(j=>card(j,f)));
  const activeCount=renderFilterChips(f);
  const viewLabel=f.view?f.view+' ':activeCount?'matching ':'recent ';
  $('count').textContent=`${matches.length} ${viewLabel}${matches.length===1?'job':'jobs'}`;
  for(const view of ['saved','applied','hidden']){const option=$('view').querySelector(`option[value="${view}"]`);option.textContent=`${view[0].toUpperCase()+view.slice(1)} jobs (${activity.filter(row=>row[view]).length})`;}
  $('view-help').textContent=f.view==='hidden'?'Hidden jobs stay out of All jobs. Select Unhide to bring one back.':f.view?'Your lists stay in this browser. Older or closed jobs are labeled; filters still apply.':'Your lists stay in this browser. Mark applied tracks your progress; apply on the employer’s site.';
  $('empty-title').textContent=f.view?`No ${f.view} jobs match this view.`:'No jobs in our collection match yet.';
  const dateNote=f.posted==='today'?todayPostingNote(visible,today):'';
  $('empty-note').textContent=dateNote|| (f.view?'Use the job controls to build your lists, or clear filters to see more.':'Broaden your selection. This curated collection does not cover every employer or opening.');
  $('all-jobs').hidden=!f.view;
  $('coverage').textContent=`${visible.length} jobs · ${new Set(visible.map(j=>j.companyId)).size} employers`;
  const last=[...jobs].map(j=>j.reviewedAt).sort().at(-1);
  const failures=Object.values(collection?.sources||{}).filter(s=>s.errors?.length).length;
  $('scope-note').textContent=collection?`${Object.keys(collection.sources||{}).length} employers · Posted within 14 days · Latest successful check ${last?labelDate(last):'unavailable'} · Sampled coverage.${failures?' Some employer updates were unavailable; last successful dates remain in job details.':''}`:`Starter collection · Posted within 14 days · Last checked ${last?labelDate(last):'date unavailable'} · Not a complete job feed.`;
  $('empty').hidden=matches.length>0;$('pagination').hidden=page.pages<=1;$('previous-page').disabled=page.page<=1;$('next-page').disabled=page.page>=page.pages;$('page-label').textContent=`Page ${page.page} of ${page.pages}`;
  if(sync){const query=serializeJobFilters(f);history.replaceState(null,'',`${location.pathname}${query?'?'+query:''}${location.hash}`);}
}
function change(){clearTimeout(pending);currentPage='1';render();}
function reset(){clearTimeout(pending);for(const k of FILTER_CONTROLS.filter(k=>k!=='view')){if(MULTI_FILTER_KEYS.includes(k)){for(const input of k==='company'||k==='companyExclude'?companyInputs(k):$(k).querySelectorAll('input[type="checkbox"]'))input.checked=false;updateMultiSummary(k);}else $(k).value=k==='sort'?'newest':'';}$('company-search').value='';for(const row of $('company-rows').children)row.hidden=false;$('include-travel').checked=true;$('pay-posted').checked=false;document.querySelector('.more-filters').open=false;currentPage='1';render();}
async function load(){
  ready=false;$('error').hidden=true;$('empty').hidden=true;$('results').setAttribute('aria-busy','true');$('count').textContent='Loading jobs…';
  try{
    const responses=await Promise.all(['jobs','companies'].map(name=>fetch(new URL(`./data/${name}.json`,import.meta.url))));if(responses.some(r=>!r.ok))throw Error('Unavailable data');
    const [data,employers,logoData]=await Promise.all([...responses.map(r=>r.json()),fetch(new URL('./data/company-logos.json',import.meta.url)).then(r=>r.ok?r.json():null).catch(()=>null)]);companyDirectory=employers.companies;jobs=validateJobs(data,companyDirectory);collection=data.automation||null;logos=logoData?.schemaVersion===1?logoData.logos||{}:{};
    setMultiOptions('state',US_STATES.map(s=>[s,s]));
    setMultiOptions('arrangement',[['on-site','On-site'],['hybrid','Hybrid'],['remote','Remote'],['remote-state','State-restricted remote'],['unknown','Not specified']]);
    const companies=[...new Map(jobs.map(j=>[j.companyId,j.companyName]))].sort((a,b)=>a[1].localeCompare(b[1]));setCompanyOptions(companies);
    setOptions('industry',[...new Set(jobs.map(j=>j.industry))].sort().map(s=>[s,s]));
    setMultiOptions('function',JOB_FUNCTION_OPTIONS);
    restore();ready=true;render();savedSearches.refresh();
  }catch{$('results').replaceChildren();$('error').hidden=false;$('coverage').textContent='Job data unavailable';$('count').textContent='Unable to load jobs';$('pagination').hidden=true;}
  finally{$('results').setAttribute('aria-busy','false');}
}
$('filters').addEventListener('submit',event=>{event.preventDefault();change();});$('q').addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(change,120);});
for(const k of FILTER_CONTROLS.filter(k=>k!=='q'))$(k).addEventListener('change',change);
$('pay-posted').addEventListener('change',change);
$('all-jobs').addEventListener('click',()=>{$('view').value='';change();$('q').focus();});
$('undo-job-action').addEventListener('click',()=>{if(undoAction)jobAction(undoAction.job,undoAction.flag,undoAction.value,true);});
window.addEventListener('storage',event=>{if(event.key===ACTIVITY_KEY||event.key===null){try{activity=readJobActivity(activityStorage);if(ready)render();}catch{$('job-action-status').textContent='Your browser could not reload your job lists.';}}});
$('include-travel').addEventListener('change',change);$('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',()=>{reset();$('q').focus();});$('retry').addEventListener('click',load);
for(const [id,delta]of [['previous-page',-1],['next-page',1]])$(id).addEventListener('click',()=>{currentPage=String(Number(currentPage)+delta);render();$('count').tabIndex=-1;$('count').focus();});
window.addEventListener('popstate',()=>{if(ready){clearTimeout(pending);restore();render(false);}});
function refreshFreshness(){if(ready&&todayInNewYork()!==renderedDay)render();}
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refreshFreshness();});setInterval(refreshFreshness,60000);
const savedSearches=mountSavedSearches({getFilters:selected,isReady:()=>ready,applyFilters:f=>{clearTimeout(pending);applyFilterValues(f);render();}});
if(!activityAvailable)$('job-action-status').textContent='Your browser blocks site storage, so job lists are unavailable. Search and filters still work.';
load();
