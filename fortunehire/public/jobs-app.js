import {JOB_FUNCTIONS,classifyJobFunctions} from './job-functions.js';
import {mountSavedSearches} from './saved-searches.js';
import { JOB_KEYS, US_STATES, ARRANGEMENTS, todayInNewYork, readJobFilters, serializeJobFilters, isCurrent, filterJobs, paginateJobs, salaryText, validateJobs } from './jobs.js';
import {postedLabel,locationSummary,paySummary} from './job-presentation.js';
const $=id=>document.getElementById(id);
const e=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const link=(text,url)=>{const a=e('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
let jobs=[],ready=false,currentPage='1',pending,renderedDay='',collection=null,logos={};
const labelDate=value=>new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
function card(j,f){
  const article=e('article',undefined,'card job-card');
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
  if(j.employmentType!=='Not specified')badges.append(e('span',j.employmentType,'job-badge'));
  if(j.travelRequired===true)badges.append(e('span','Travel required','job-badge'));
  meta.append(e('p',locationSummary(j,f.state),'job-location'),badges);
  const details=e('details',undefined,'job-details');const summary=e('summary','Job details & sources');const body=e('div',undefined,'job-detail-body');
  const dl=e('dl');for(const [key,val]of [['Posted',labelDate(j.postedAt)],['Last successfully checked',labelDate(j.reviewedAt)],['Employment type',j.employmentType],['Industry',j.industry],['Job function (from title)',classifyJobFunctions(j.title).map(key=>JOB_FUNCTIONS[key]).join(', ')],[j.identifierType==='posting-id'?'Employer posting ID':'Employer requisition',j.requisitionId],['Employer deadline',j.closesAt?labelDate(j.closesAt):'Not specified']])dl.append(e('dt',key),e('dd',val));
  if(j.arrangement==='remote'&&j.remoteScope==='states')dl.append(e('dt','Eligible remote states'),e('dd',j.eligibleStates.join(', ')));
  const payScope=j.salary?.scopeStates||j.publishedPay?.scopeStates||[];const payApplies=!f.state||!payScope.length||payScope.includes(f.state);
  body.append(e('p','Location & eligibility: '+j.locationNote));
  if(j.arrangementBasis==='listed-location')body.append(e('p','Work arrangement: On-site, classified from the listed city/state. The employer did not explicitly state a work arrangement.'));
  if(payApplies&&(j.salary||j.publishedPay))body.append(e('p','Employer-published pay: '+salaryText(j)));
  else if(!payApplies)body.append(e('p','Published pay does not have verified applicability to the selected state. Open the employer posting for its location-specific terms.'));
  for(const note of new Set([j.salaryNote,j.publishedPay?.note].filter(Boolean)))body.append(e('p',note));
  body.append(e('p',j.travelRequired===true?`Travel required: ${j.travelNote}`:j.travelRequired===false?'Travel: employer states none':'Travel requirements not specified'),dl,e('p',j.sourceNote),link('Official posting & application \u2197',j.url),e('br'),link('Employer classification source \u2197',j.companySource));
  details.append(summary,body);
  const pay=e('div',undefined,'job-pay');const presentation=paySummary(j,f.state);
  if(presentation.detail){pay.append(e('p',presentation.text,'job-salary'));const button=e('button','Full pay details \u2193','inline-detail');button.type='button';button.setAttribute('aria-label',`View published pay for ${j.title} at ${j.companyName}`);button.addEventListener('click',()=>{details.open=true;summary.focus();});pay.append(button);}
  else pay.append(e('p',presentation.text,'job-salary'+(!j.salary&&!j.publishedPay||!payApplies?' unavailable':'')));
  if(presentation.note)pay.append(e('p',presentation.note,'pay-context'));
  const actions=e('div',undefined,'job-actions');const apply=link('Apply at employer \u2197',j.url);apply.className='career-link';apply.setAttribute('aria-label',`View role and apply: ${j.title} at ${j.companyName} (opens in a new tab)`);actions.append(apply);
  article.append(top,meta,pay,actions,details);return article;
}

function renderFilterChips(f){
  const active=[];
  for(const key of ['state','arrangement','company','industry','function','type','pay'])if(f[key]){const control=$(key);active.push([key,control.options[control.selectedIndex].textContent]);}
  if(f.q.trim())active.push(['q',`Search: ${f.q.trim()}`]);
  if(f.travel==='exclude')active.push(['travel','Exclude travel-required roles']);
  $('active-filters').replaceChildren(...active.map(([key,label])=>{
    const button=e('button',label+' \u00d7','filter-chip');button.type='button';button.setAttribute('aria-label',`Remove filter: ${label}`);
    button.addEventListener('click',()=>{const index=[...$('active-filters').children].indexOf(button);if(key==='travel')$('include-travel').checked=true;else $(key).value='';change();const remaining=$('active-filters').children;if(remaining.length)remaining[Math.min(index,remaining.length-1)].focus();else $('q').focus();});return button;
  }));
  $('active-filters').hidden=!active.length;$('reset').hidden=!active.length;
  const count=['company','industry','function','type','pay'].filter(key=>f[key]).length+(f.travel==='exclude'?1:0);
  $('more-filter-count').textContent=`${count} selected`;$('more-filter-count').hidden=!count;
  return active.length;
}

function setOptions(id,values){const select=$(id);select.replaceChildren(select.options[0]);for(const [value,label]of values){const o=e('option',label);o.value=value;select.append(o);}select.disabled=false;}
function restore(){
  applyFilterValues(readJobFilters(location.search));
}
function applyFilterValues(f){
  currentPage=f.page;
  for(const k of JOB_KEYS.filter(k=>!['page','travel'].includes(k))){const control=$(k);if(k!=='q'&&f[k]&&![...control.options].some(o=>o.value===f[k])){const o=e('option',`Unavailable: ${f[k]}`);o.value=f[k];control.append(o);}control.value=f[k];}
  $('include-travel').checked=f.travel!=='exclude';
  document.querySelector('.more-filters').open=['company','industry','function','type','pay'].some(k=>f[k])||f.travel==='exclude';
}
function selected(){return {...Object.fromEntries(JOB_KEYS.filter(k=>!['page','travel'].includes(k)).map(k=>[k,$(k).value])),travel:$('include-travel').checked?'include':'exclude',page:currentPage};}
function render(sync=true){
  if(!ready)return;
  const f=selected();const today=todayInNewYork();renderedDay=today;const visible=jobs.filter(j=>isCurrent(j,today));const matches=filterJobs(jobs,f,today);const page=paginateJobs(matches,currentPage);currentPage=String(page.page);f.page=currentPage;
  $('results').replaceChildren(...page.items.map(j=>card(j,f)));
  const activeCount=renderFilterChips(f);
  $('count').textContent=activeCount?`${matches.length} matching ${matches.length===1?'job':'jobs'}`:`${visible.length} recent jobs`;
  $('coverage').textContent=`${visible.length} jobs · ${new Set(visible.map(j=>j.companyId)).size} employers`;
  const last=[...jobs].map(j=>j.reviewedAt).sort().at(-1);
  const failures=Object.values(collection?.sources||{}).filter(s=>s.errors?.length).length;
  $('scope-note').textContent=collection?`${Object.keys(collection.sources||{}).length} employers · Posted within 14 days · Latest successful check ${last?labelDate(last):'unavailable'} · Sampled coverage.${failures?' Some employer updates were unavailable; last successful dates remain in job details.':''}`:`Starter collection · Posted within 14 days · Last checked ${last?labelDate(last):'date unavailable'} · Not a complete job feed.`;
  $('empty').hidden=matches.length>0;$('pagination').hidden=page.pages<=1;$('previous-page').disabled=page.page<=1;$('next-page').disabled=page.page>=page.pages;$('page-label').textContent=`Page ${page.page} of ${page.pages}`;
  if(sync){const query=serializeJobFilters(f);history.replaceState(null,'',`${location.pathname}${query?'?'+query:''}${location.hash}`);}
}
function change(){clearTimeout(pending);currentPage='1';render();}
function reset(){clearTimeout(pending);for(const k of JOB_KEYS.filter(k=>!['page','travel'].includes(k)))$(k).value=k==='sort'?'newest':'';$('include-travel').checked=true;document.querySelector('.more-filters').open=false;currentPage='1';render();}
async function load(){
  ready=false;$('error').hidden=true;$('empty').hidden=true;$('results').setAttribute('aria-busy','true');$('count').textContent='Loading jobs…';
  try{
    const responses=await Promise.all(['jobs','companies'].map(name=>fetch(new URL(`./data/${name}.json`,import.meta.url))));if(responses.some(r=>!r.ok))throw Error('Unavailable data');
    const [data,employers,logoData]=await Promise.all([...responses.map(r=>r.json()),fetch(new URL('./data/company-logos.json',import.meta.url)).then(r=>r.ok?r.json():null).catch(()=>null)]);jobs=validateJobs(data,employers.companies);collection=data.automation||null;logos=logoData?.schemaVersion===1?logoData.logos||{}:{};
    setOptions('state',US_STATES.map(s=>[s,s]));
    const companies=[...new Map(jobs.map(j=>[j.companyId,j.companyName]))].sort((a,b)=>a[1].localeCompare(b[1]));setOptions('company',companies);
    setOptions('industry',[...new Set(jobs.map(j=>j.industry))].sort().map(s=>[s,s]));
    setOptions('function',Object.entries(JOB_FUNCTIONS));
    restore();ready=true;render(false);savedSearches.refresh();
  }catch{$('results').replaceChildren();$('error').hidden=false;$('coverage').textContent='Job data unavailable';$('count').textContent='Unable to load jobs';$('pagination').hidden=true;}
  finally{$('results').setAttribute('aria-busy','false');}
}
$('filters').addEventListener('submit',event=>{event.preventDefault();change();});$('q').addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(change,120);});
for(const k of JOB_KEYS.filter(k=>!['q','travel','page'].includes(k)))$(k).addEventListener('change',change);
$('include-travel').addEventListener('change',change);$('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',()=>{reset();$('q').focus();});$('retry').addEventListener('click',load);
for(const [id,delta]of [['previous-page',-1],['next-page',1]])$(id).addEventListener('click',()=>{currentPage=String(Number(currentPage)+delta);render();$('count').tabIndex=-1;$('count').focus();});
window.addEventListener('popstate',()=>{if(ready){clearTimeout(pending);restore();render(false);}});
function refreshFreshness(){if(ready&&todayInNewYork()!==renderedDay)render();}
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refreshFreshness();});setInterval(refreshFreshness,60000);
const savedSearches=mountSavedSearches({getFilters:selected,isReady:()=>ready,applyFilters:f=>{clearTimeout(pending);applyFilterValues(f);render();}});
load();
