import { JOB_KEYS, US_STATES, ARRANGEMENTS, todayInNewYork, readJobFilters, serializeJobFilters, isCurrent, filterJobs, paginateJobs, salaryText, validateJobs } from './jobs.js';
const $=id=>document.getElementById(id);
const e=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const link=(text,url)=>{const a=e('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
let jobs=[],ready=false,currentPage='1',pending;
const labelDate=value=>new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
function card(j,f){
  const a=e('article',undefined,'card job-card');
  const top=e('div',undefined,'card-top');const monogram=e('span',j.companyName.split(/\s+/).map(s=>s[0]).slice(0,2).join(''),'monogram');monogram.setAttribute('aria-hidden','true');
  const text=e('div');const title=e('h3',undefined,'job-title');const titleLink=link(j.title,j.url);titleLink.setAttribute('aria-label',`${j.title} at ${j.companyName} (opens employer posting in a new tab)`);title.append(titleLink);text.append(title,e('div',j.companyName,'job-company'));top.append(monogram,text);
  const badges=e('div',undefined,'job-badges');badges.append(e('span',ARRANGEMENTS[j.arrangement],`job-badge ${j.arrangement}`),e('span',j.employmentType==='Not specified'?'Job type not verified':j.employmentType,'job-badge'));
  const payApplies=!f.state||!j.salary?.scopeStates?.length||j.salary.scopeStates.includes(f.state);
  const pay=e('p',payApplies?salaryText(j):'Pay not verified for this location','job-salary');
  const travel=e('p',j.travelRequired===true?`Travel required · ${j.travelNote}`:j.travelRequired===false?'Travel: employer states none':'Travel: not specified','job-travel');
  const apply=link('View role & apply ↗',j.url);apply.className='career-link';apply.setAttribute('aria-label',`View role and apply: ${j.title} at ${j.companyName} (opens in a new tab)`);
  const details=e('details');details.append(e('summary','Posting details & sources'));
  const dl=e('dl');for(const [key,val]of [['Industry',j.industry],['Sector',j.sector],['Employer requisition',j.requisitionId],['Posted',j.postedAt?labelDate(j.postedAt):'Not specified'],['Reviewed',labelDate(j.reviewedAt)],['Employer deadline',j.closesAt?labelDate(j.closesAt):'Not specified']])dl.append(e('dt',key),e('dd',val));
  details.append(dl,e('p',j.salaryNote),e('p',j.sourceNote),link('Official posting & application ↗',j.url),e('br'),link('Employer classification source ↗',j.companySource));
  a.append(top,badges,e('p',j.locationNote,'job-location'),pay,travel,apply,details);return a;
}
function setOptions(id,values){const select=$(id);select.replaceChildren(select.options[0]);for(const [value,label]of values){const o=e('option',label);o.value=value;select.append(o);}select.disabled=false;}
function restore(){
  const f=readJobFilters(location.search);currentPage=f.page;
  for(const k of JOB_KEYS.filter(k=>!['page','travel'].includes(k))){const control=$(k);if(k!=='q'&&f[k]&&![...control.options].some(o=>o.value===f[k])){const o=e('option',`Unavailable: ${f[k]}`);o.value=f[k];control.append(o);}control.value=f[k];}
  $('include-travel').checked=f.travel!=='exclude';
  if(['company','industry','sector','type','pay'].some(k=>f[k]))document.querySelector('.more-filters').open=true;
}
function selected(){return {...Object.fromEntries(JOB_KEYS.filter(k=>!['page','travel'].includes(k)).map(k=>[k,$(k).value])),travel:$('include-travel').checked?'include':'exclude',page:currentPage};}
function render(sync=true){
  if(!ready)return;
  const f=selected();const today=todayInNewYork();const visible=jobs.filter(j=>isCurrent(j,today));const matches=filterJobs(jobs,f,today);const page=paginateJobs(matches,currentPage);currentPage=String(page.page);f.page=currentPage;
  $('results').replaceChildren(...page.items.map(j=>card(j,f)));
  $('count').textContent=`${matches.length} matching ${matches.length===1?'job':'jobs'} · ${visible.length} reviewed postings available`;
  $('coverage').textContent=`${visible.length} jobs · ${new Set(visible.map(j=>j.companyId)).size} employers`;
  const last=[...jobs].map(j=>j.reviewedAt).sort().at(-1);$('scope-note').textContent=`Manually curated starter collection · Last reviewed ${last?labelDate(last):'date unavailable'} · Not a complete job feed.`;
  $('empty').hidden=matches.length>0;$('pagination').hidden=page.pages<=1;$('previous-page').disabled=page.page<=1;$('next-page').disabled=page.page>=page.pages;$('page-label').textContent=`Page ${page.page} of ${page.pages}`;
  const active=[];for(const key of ['state','arrangement','company','industry','sector','type','pay'])if(f[key]){const control=$(key);active.push(control.options[control.selectedIndex].textContent);}if(f.q.trim())active.push(`Search: ${f.q.trim()}`);if(f.travel==='exclude')active.push('Confirmed travel-required roles excluded');
  $('active-filters').textContent=active.join(' · ');$('active-filters').hidden=!active.length;
  if(sync){const query=serializeJobFilters(f);history.replaceState(null,'',`${location.pathname}${query?'?'+query:''}${location.hash}`);}
}
function change(){clearTimeout(pending);currentPage='1';render();}
function reset(){clearTimeout(pending);for(const k of JOB_KEYS.filter(k=>!['page','travel'].includes(k)))$(k).value=k==='sort'?'newest':'';$('include-travel').checked=true;currentPage='1';render();}
async function load(){
  ready=false;$('error').hidden=true;$('empty').hidden=true;$('results').setAttribute('aria-busy','true');$('count').textContent='Loading jobs…';
  try{
    const responses=await Promise.all(['jobs','companies'].map(name=>fetch(new URL(`./data/${name}.json`,import.meta.url))));if(responses.some(r=>!r.ok))throw Error('Unavailable data');
    const [data,employers]=await Promise.all(responses.map(r=>r.json()));jobs=validateJobs(data,employers.companies);
    setOptions('state',US_STATES.map(s=>[s,s]));
    const companies=[...new Map(jobs.map(j=>[j.companyId,j.companyName]))].sort((a,b)=>a[1].localeCompare(b[1]));setOptions('company',companies);
    for(const k of ['industry','sector'])setOptions(k,[...new Set(jobs.map(j=>j[k]))].sort().map(s=>[s,s]));
    restore();ready=true;render(false);
  }catch{$('results').replaceChildren();$('error').hidden=false;$('coverage').textContent='Job data unavailable';$('count').textContent='Unable to load jobs';$('pagination').hidden=true;}
  finally{$('results').setAttribute('aria-busy','false');}
}
$('filters').addEventListener('submit',event=>{event.preventDefault();change();});$('q').addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(change,120);});
for(const k of JOB_KEYS.filter(k=>!['q','travel','page'].includes(k)))$(k).addEventListener('change',change);
$('include-travel').addEventListener('change',change);$('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',()=>{reset();$('q').focus();});$('retry').addEventListener('click',load);
for(const [id,delta]of [['previous-page',-1],['next-page',1]])$(id).addEventListener('click',()=>{currentPage=String(Number(currentPage)+delta);render();$('count').tabIndex=-1;$('count').focus();});
window.addEventListener('popstate',()=>{if(ready){clearTimeout(pending);restore();render(false);}});document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')render();});setInterval(()=>render(),60000);
load();
