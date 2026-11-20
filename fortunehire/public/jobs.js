import {jobFunctionResult,isValidJobFunction} from './job-functions.js';
import {validFunctionContext} from './function-duties.js';
import {applyRemoteTerritory} from './remote-territory.js';
import { normalize } from './directory.js';
import {US_STATES} from './us-geography.js';
export {US_STATES} from './us-geography.js';
export const ARRANGEMENTS = {'on-site':'On-site',hybrid:'Hybrid',remote:'Remote',unknown:'Not specified'};
export const JOB_KEYS = ['q','state','arrangement','company','companyExclude','industry','function','type','pay','posted','payPosted','view','travel','sort','page'];
export const MULTI_FILTER_KEYS = ['state','arrangement','function','company','companyExclude'];
const LEGACY_FUNCTIONS={it:'it',engineering:'engineering',manufacturing:'manufacturing',logistics:'logistics',projects:'projects',business:'business',other:'other',sales:'sales',marketing:'marketing',hr:'hr',operations:'operations',service:'service',admin:'admin',legal:'legal',finance:'finance',healthcare:'healthcare',research:'research',retail:'retail',hospitality:'hospitality',quality:'quality'};
export function normalizeLegacyFunction(value){return LEGACY_FUNCTIONS[value]||value;}
export function todayInNewYork(date = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(p=>[p.type,p.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}
export function readJobFilters(search) {
  const p = new URLSearchParams(search);
  const f = Object.fromEntries(JOB_KEYS.map(k=>[k,MULTI_FILTER_KEYS.includes(k)?[...new Set(p.getAll(k).flatMap(value=>value.split(',')).map(value=>value.trim()).filter(Boolean).map(value=>value.slice(0,160)))].slice(0,50):(p.get(k)||'').slice(0,160)]));
  f.company=f.company.filter(id=>!f.companyExclude.includes(id));
  f.sort = ['title','company'].includes(f.sort) ? f.sort : 'newest';
  f.travel = f.travel === 'exclude' ? 'exclude' : 'include';
  f.posted = ['today','3','7','14'].includes(f.posted)?f.posted:'';
  f.payPosted = f.payPosted==='1'?'1':'';
  f.view = ['saved','applied','hidden'].includes(f.view)?f.view:'';
  f.page = /^\d+$/.test(f.page) ? String(Math.min(10000,Math.max(1,Number(f.page)))) : '1';
  return f;
}
export function serializeJobFilters(f) {
  const p=new URLSearchParams();
  for(const k of JOB_KEYS){
    if(MULTI_FILTER_KEYS.includes(k)){
      const values=Array.isArray(f[k])?f[k]:f[k]?[f[k]]:[];
      for(const value of [...new Set(values)].filter(Boolean))p.append(k,String(value));
    }else if(f[k]&&!((k==='sort'&&f[k]==='newest')||(k==='travel'&&f[k]==='include')||(k==='page'&&String(f[k])==='1')))p.set(k,f[k]);
  }
  return p.toString();
}
export function isCurrent(job, today = todayInNewYork()) {
  const age=(Date.parse(today+'T12:00:00Z')-Date.parse(job.reviewedAt+'T12:00:00Z'))/86400000;
  const postingAge=job.postedAt?(Date.parse(today+'T12:00:00Z')-Date.parse(job.postedAt+'T12:00:00Z'))/86400000:NaN;
  return job.status==='reviewed' && age>=0 && age<=7 && postingAge>=0 && postingAge<=14 && (!job.closesAt || job.closesAt>=today);
}
export function matchesState(job,state) {
  const states=Array.isArray(state)?state:state?[state]:[];
  if(!states.length) return true;
  const valid=states.filter(value=>US_STATES.includes(value));
  if(!valid.length)return false;
  if(job.arrangement==='remote') return job.remoteScope==='nationwide' || valid.some(value=>job.eligibleStates.includes(value));
  return job.locations.some(location=>valid.includes(location.state));
}
function matchesArrangement(job,arrangements){
  const values=Array.isArray(arrangements)?arrangements:arrangements?[arrangements]:[];
  if(!values.length)return true;
  return values.some(value=>value==='remote-state'?job.arrangement==='remote'&&job.remoteScope==='states':job.arrangement===value);
}
function matchesCategory(value,selected){
  const values=Array.isArray(selected)?selected:selected?[selected]:[];
  return !values.length||values.includes(value);
}
function matchesStateScope(scope,states){
  const selected=Array.isArray(states)?states:states?[states]:[];
  return !selected.length||!scope?.length||selected.some(state=>scope.includes(state));
}
export function matchesPosted(job,window,today){
 if(!window)return true;
 const age=(Date.parse(today+'T12:00:00Z')-Date.parse(job.postedAt+'T12:00:00Z'))/86400000;
 return Number.isFinite(age)&&age>=0&&age<=(window==='today'?0:Number(window));
}
export function hasPostedPay(job,state=''){
 if(!job.salary&&!job.publishedPay)return false;
 const scope=job.salary?.scopeStates||job.publishedPay?.scopeStates||[];
 return matchesStateScope(scope,state);
}
export function filterJobs(jobs,f,today = todayInNewYork(),includeUnavailable=false) {
  return jobs.filter(j=>(includeUnavailable||!j.organizerUnavailable&&isCurrent(j,today)) && matchesPosted(j,f.posted,today) && (!f.payPosted||hasPostedPay(j,f.state)) && (!normalize(f.q)||normalize(j.title+' '+j.companyName).includes(normalize(f.q))) && matchesState(j,f.state) && matchesArrangement(j,f.arrangement) && matchesCategory(j.companyId,f.company) && !(Array.isArray(f.companyExclude)?f.companyExclude:f.companyExclude?[f.companyExclude]:[]).includes(j.companyId) && (!f.industry||j.industry===f.industry) && matchesCategory(j.primaryJobFunction,f.function) && (!f.type||j.employmentType===f.type) && (f.travel!=='exclude'||j.travelRequired!==true) && (!f.pay || matchesPay(j,f.pay,f.state))).sort((a,b)=>f.sort==='title'?a.title.localeCompare(b.title):f.sort==='company'?a.companyName.localeCompare(b.companyName)||a.title.localeCompare(b.title):(b.postedAt||'').localeCompare(a.postedAt||'')||a.title.localeCompare(b.title));
}
export function matchesPay(job,value,state='') {
  const match=/^(year|hour):(\d+)$/.exec(value);
  return Boolean(match && job.salary && matchesStateScope(job.salary.scopeStates,state) && job.salary.currency==='USD' && job.salary.period===match[1] && job.salary.min>=Number(match[2]));
}
export function paginateJobs(jobs,page,size=12) {
  const pages=Math.max(1,Math.ceil(jobs.length/size)); const current=Math.min(pages,Math.max(1,Number(page)||1));
  return {items:jobs.slice((current-1)*size,current*size),page:current,pages,total:jobs.length};
}
export function salaryText(job) {
  if(!job.salary) return job.publishedPay?.text || 'Pay not verified';
  const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:job.salary.currency,maximumFractionDigits:2}).format(n);
  return `${money(job.salary.min)}${job.salary.min===job.salary.max?'':'–'+money(job.salary.max)} / ${job.salary.period==='year'?'year':'hour'}`;
}
function validDate(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value))&&new Date(value+'T12:00:00Z').toISOString().slice(0,10)===value;}
export function validateJobs(data,companies) {
  if(![1,2].includes(data.schemaVersion)||!Array.isArray(data.jobs))throw Error('Invalid job dataset');
  const ids=new Set(),urls=new Set(),employers=new Map(companies.map(c=>[c.id,c]));
  for(const j of data.jobs){
    if(!/^[a-z0-9-]+$/.test(j.id)||ids.has(j.id)||urls.has(j.url))throw Error('Duplicate/invalid job'); ids.add(j.id);urls.add(j.url);
    const c=employers.get(j.companyId);if(!c)throw Error('Unknown employer');
    for(const v of [j.title,j.requisitionId,j.locationNote,j.sourceNote,j.sector])if(typeof v!=='string'||!v.trim())throw Error('Missing job field');
    if(!Object.hasOwn(ARRANGEMENTS,j.arrangement)||!['Full-time','Part-time','Contract','Temporary','Internship','Not specified'].includes(j.employmentType)||![true,false,null].includes(j.travelRequired))throw Error('Invalid job category');
    if(j.arrangementBasis!==undefined&&(j.arrangementBasis!=='listed-location'||j.arrangement!=='on-site'||typeof j.arrangementNote!=='string'||!j.arrangementNote.trim()))throw Error('Invalid location-based work arrangement');
    if(j.employmentTypeBasis!==undefined&&(j.employmentTypeBasis!=='assumed-full-time'||j.employmentType!=='Full-time'||typeof j.employmentTypeNote!=='string'||!j.employmentTypeNote.trim()))throw Error('Invalid assumed employment type');
    if(!['nationwide','states','unknown'].includes(j.remoteScope)||!Array.isArray(j.eligibleStates)||!Array.isArray(j.locations))throw Error('Invalid eligibility');
    for(const s of j.eligibleStates)if(!US_STATES.includes(s))throw Error('Invalid eligible state');
    for(const loc of j.locations)if(!loc.city||!US_STATES.includes(loc.state))throw Error('Invalid job location');
    if(j.arrangement!=='remote'&&j.remoteScope!=='unknown')throw Error('Remote eligibility on office job');
    if(j.arrangement!=='remote'&&!j.locations.length)throw Error('Missing office location');
    if(j.remoteScope==='states'&&!j.eligibleStates.length)throw Error('Empty remote eligibility');
    if(j.remoteScope!=='states'&&j.eligibleStates.length)throw Error('Conflicting eligibility');
    if(!validDate(j.reviewedAt)||(j.postedAt!==null&&!validDate(j.postedAt))||(j.closesAt!==null&&!validDate(j.closesAt)))throw Error('Invalid job dates');
    const officialHost=new URL(c.careerUrl).hostname;
    const url=new URL(j.url);
    const taleo=url.hostname==='valero.taleo.net'&&url.pathname==='/careersection/2/jobdetail.ftl'&&url.searchParams.getAll('job').length===1&&/^[A-Za-z0-9]{5,12}$/.test(url.searchParams.get('job'))&&Array.from(url.searchParams.keys()).every(key=>key==='job');
    const meta=url.hostname==='www.metacareers.com'&&/^\/profile\/job_details\/\d+\/?$/.test(url.pathname)&&!url.search&&!url.hash;
    const apple=url.hostname==='jobs.apple.com'&&/^\/en-us\/details\/\d+(?:-\d+)?\/[^/]+\/?$/.test(url.pathname)&&!url.search;
    if(url.protocol!=='https:'||url.username||url.password||url.hostname!==officialHost||(url.hostname==='www.metacareers.com'&&!meta)||(!taleo&&!apple&&!meta&&!/\/jobs?\/[^/]+|\/search\/jobdetails\/[^/]+\/[0-9a-f-]{36}\/?$|\/en-us\/job-detail\/[^/]+/i.test(url.pathname)))throw Error('Invalid official job URL');
    if(j.functionContext!==undefined&&!validFunctionContext(j.functionContext))throw Error('Invalid job function evidence');
    if(data.schemaVersion===2&&(!isValidJobFunction(j.primaryJobFunction)||!['responsibilities','required skills','job title','employer category','insufficient evidence'].includes(j.jobFunctionBasis)||!['high','medium','low'].includes(j.jobFunctionConfidence)||typeof j.jobFunctionReviewRequired!=='boolean'||!Array.isArray(j.jobFunctionEvidence)||j.jobFunctionEvidence.length>4||j.jobFunctionEvidence.some(text=>typeof text!=='string'||text.length>500)))throw Error('Invalid primary job function');
    if(!['reviewed','closed','needs-review'].includes(j.status))throw Error('Invalid review status');
    if(j.salary && (!Number.isFinite(j.salary.min)||!Number.isFinite(j.salary.max)||j.salary.min<=0||j.salary.max<j.salary.min||j.salary.currency!=='USD'||!['year','hour'].includes(j.salary.period)))throw Error('Invalid pay');
    if(j.salary?.scopeStates && (!Array.isArray(j.salary.scopeStates)||j.salary.scopeStates.some(s=>!US_STATES.includes(s))))throw Error('Invalid pay geography');
    if(j.publishedPay && (typeof j.publishedPay.text!=='string'||!j.publishedPay.text.trim()||j.publishedPay.text.length>1000||typeof j.publishedPay.note!=='string'||!Array.isArray(j.publishedPay.scopeStates)||j.publishedPay.scopeStates.some(s=>!US_STATES.includes(s))))throw Error('Invalid published pay');
  }
  return data.jobs.map(j=>{
    const upgraded=data.schemaVersion===1&&!isValidJobFunction(j.primaryJobFunction)?jobFunctionResult(j):null;
    const classified=upgraded?{...j,primaryJobFunction:upgraded.primaryFunction,jobFunctionBasis:upgraded.basis,jobFunctionConfidence:upgraded.confidence,jobFunctionReviewRequired:upgraded.reviewRequired,jobFunctionEvidence:upgraded.evidence}:j;
    return applyRemoteTerritory({...classified,companyName:employers.get(j.companyId).name,industry:employers.get(j.companyId).industry,companySource:employers.get(j.companyId).profileSource});
  });
}
