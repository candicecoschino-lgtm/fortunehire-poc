import { normalize } from './directory.js';
export const US_STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'];
export const ARRANGEMENTS = {'on-site':'On-site',hybrid:'Hybrid',remote:'Remote',unknown:'Not specified'};
export const JOB_KEYS = ['q','state','arrangement','company','industry','sector','type','pay','travel','sort','page'];
export function todayInNewYork(date = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(p=>[p.type,p.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}
export function readJobFilters(search) {
  const p = new URLSearchParams(search);
  const f = Object.fromEntries(JOB_KEYS.map(k=>[k,(p.get(k)||'').slice(0,160)]));
  f.sort = ['title','company'].includes(f.sort) ? f.sort : 'newest';
  f.travel = f.travel === 'exclude' ? 'exclude' : 'include';
  f.page = /^\d+$/.test(f.page) ? String(Math.min(10000,Math.max(1,Number(f.page)))) : '1';
  return f;
}
export function serializeJobFilters(f) {
  const p=new URLSearchParams();
  for(const k of JOB_KEYS) if(f[k] && !((k==='sort'&&f[k]==='newest')||(k==='travel'&&f[k]==='include')||(k==='page'&&String(f[k])==='1'))) p.set(k,f[k]);
  return p.toString();
}
export function isCurrent(job, today = todayInNewYork()) {
  const age=(Date.parse(today+'T12:00:00Z')-Date.parse(job.reviewedAt+'T12:00:00Z'))/86400000;
  const postingAge=job.postedAt?(Date.parse(today+'T12:00:00Z')-Date.parse(job.postedAt+'T12:00:00Z'))/86400000:NaN;
  return job.status==='reviewed' && age>=0 && age<=7 && postingAge>=0 && postingAge<=14 && (!job.closesAt || job.closesAt>=today);
}
export function matchesState(job,state) {
  if(!state) return true;
  if(!US_STATES.includes(state)) return false;
  if(job.arrangement==='remote') return job.remoteScope==='nationwide' || job.eligibleStates.includes(state);
  return job.locations.some(location=>location.state===state);
}
export function filterJobs(jobs,f,today = todayInNewYork()) {
  return jobs.filter(j=>isCurrent(j,today) && (!normalize(f.q)||normalize(j.title+' '+j.companyName).includes(normalize(f.q))) && matchesState(j,f.state) && (!f.arrangement||j.arrangement===f.arrangement) && (!f.company||j.companyId===f.company) && (!f.industry||j.industry===f.industry) && (!f.sector||j.sector===f.sector) && (!f.type||j.employmentType===f.type) && (f.travel!=='exclude'||j.travelRequired!==true) && (!f.pay || matchesPay(j,f.pay,f.state))).sort((a,b)=>f.sort==='title'?a.title.localeCompare(b.title):f.sort==='company'?a.companyName.localeCompare(b.companyName)||a.title.localeCompare(b.title):(b.postedAt||'').localeCompare(a.postedAt||'')||a.title.localeCompare(b.title));
}
export function matchesPay(job,value,state='') {
  const match=/^(year|hour):(\d+)$/.exec(value);
  return Boolean(match && job.salary && (!state||!job.salary.scopeStates?.length||job.salary.scopeStates.includes(state)) && job.salary.currency==='USD' && job.salary.period===match[1] && job.salary.min>=Number(match[2]));
}
export function paginateJobs(jobs,page,size=12) {
  const pages=Math.max(1,Math.ceil(jobs.length/size)); const current=Math.min(pages,Math.max(1,Number(page)||1));
  return {items:jobs.slice((current-1)*size,current*size),page:current,pages,total:jobs.length};
}
export function salaryText(job) {
  if(!job.salary) return job.publishedPay?.text || 'Pay not verified';
  const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:job.salary.currency,maximumFractionDigits:2}).format(n);
  return `${money(job.salary.min)}–${money(job.salary.max)} / ${job.salary.period==='year'?'year':'hour'}`;
}
function validDate(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value))&&new Date(value+'T12:00:00Z').toISOString().slice(0,10)===value;}
export function validateJobs(data,companies) {
  if(data.schemaVersion!==1||!Array.isArray(data.jobs))throw Error('Invalid job dataset');
  const ids=new Set(),urls=new Set(),employers=new Map(companies.map(c=>[c.id,c]));
  for(const j of data.jobs){
    if(!/^[a-z0-9-]+$/.test(j.id)||ids.has(j.id)||urls.has(j.url))throw Error('Duplicate/invalid job'); ids.add(j.id);urls.add(j.url);
    const c=employers.get(j.companyId);if(!c)throw Error('Unknown employer');
    for(const v of [j.title,j.requisitionId,j.locationNote,j.sourceNote,j.sector])if(typeof v!=='string'||!v.trim())throw Error('Missing job field');
    if(!Object.hasOwn(ARRANGEMENTS,j.arrangement)||!['Full-time','Part-time','Contract','Temporary','Internship','Not specified'].includes(j.employmentType)||![true,false,null].includes(j.travelRequired))throw Error('Invalid job category');
    if(!['nationwide','states','unknown'].includes(j.remoteScope)||!Array.isArray(j.eligibleStates)||!Array.isArray(j.locations))throw Error('Invalid eligibility');
    for(const s of j.eligibleStates)if(!US_STATES.includes(s))throw Error('Invalid eligible state');
    for(const loc of j.locations)if(!loc.city||!US_STATES.includes(loc.state))throw Error('Invalid job location');
    if(j.arrangement!=='remote'&&j.remoteScope!=='unknown')throw Error('Remote eligibility on office job');
    if(j.arrangement!=='remote'&&!j.locations.length)throw Error('Missing office location');
    if(j.remoteScope==='states'&&!j.eligibleStates.length)throw Error('Empty remote eligibility');
    if(j.remoteScope!=='states'&&j.eligibleStates.length)throw Error('Conflicting eligibility');
    if(!validDate(j.reviewedAt)||(j.postedAt!==null&&!validDate(j.postedAt))||(j.closesAt!==null&&!validDate(j.closesAt)))throw Error('Invalid job dates');
    const officialHost=new URL(c.careerUrl).hostname;
    const url=new URL(j.url);if(url.protocol!=='https:'||url.username||url.password||url.hostname!==officialHost||!/\/jobs?\/[^/]+|\/search\/jobdetails\/[^/]+\/[0-9a-f-]{36}\/?$|\/en-us\/job-detail\/[^/]+/i.test(url.pathname))throw Error('Invalid official job URL');
    if(!['reviewed','closed','needs-review'].includes(j.status))throw Error('Invalid review status');
    if(j.salary && (!Number.isFinite(j.salary.min)||!Number.isFinite(j.salary.max)||j.salary.min<=0||j.salary.max<j.salary.min||j.salary.currency!=='USD'||!['year','hour'].includes(j.salary.period)))throw Error('Invalid pay');
    if(j.salary?.scopeStates && (!Array.isArray(j.salary.scopeStates)||j.salary.scopeStates.some(s=>!US_STATES.includes(s))))throw Error('Invalid pay geography');
    if(j.publishedPay && (typeof j.publishedPay.text!=='string'||!j.publishedPay.text.trim()||j.publishedPay.text.length>1000||typeof j.publishedPay.note!=='string'||!Array.isArray(j.publishedPay.scopeStates)||j.publishedPay.scopeStates.some(s=>!US_STATES.includes(s))))throw Error('Invalid published pay');
  }
  return data.jobs.map(j=>({...j,companyName:employers.get(j.companyId).name,industry:employers.get(j.companyId).industry,companySource:employers.get(j.companyId).profileSource}));
}
