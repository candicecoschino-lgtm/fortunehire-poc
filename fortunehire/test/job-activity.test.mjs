import test from 'node:test';
import assert from 'node:assert/strict';
import {ACTIVITY_KEY,readJobActivity,setJobActivity,activityFlags,activityView,trackedJobs} from '../public/job-activity.js';
import {filterJobs,readJobFilters,matchesPosted,hasPostedPay} from '../public/jobs.js';
const storage=()=>{const values=new Map();return {getItem:key=>values.get(key)||null,setItem:(key,value)=>values.set(key,value)};};
const today='2026-11-17';
const job={id:'example-1',title:'Software Engineer',companyName:'Example',companyId:'example',status:'reviewed',postedAt:today,reviewedAt:today,closesAt:null,arrangement:'on-site',locations:[{city:'Austin',state:'Texas'}],employmentType:'Full-time',travelRequired:null,salary:null,publishedPay:null};

test('saved, hidden, and applied states persist independently and can be undone',()=>{
 const s=storage();s.setItem('other-key','keep');
 setJobActivity(s,job,'saved',true);setJobActivity(s,job,'applied',true);setJobActivity(s,job,'hidden',true);
 let records=readJobActivity(s);assert.equal(records.length,1);
 for(const flag of ['saved','applied','hidden'])assert.equal(activityFlags(records,job.id)[flag],true);
 records=setJobActivity(s,job,'hidden',false);assert.equal(records[0].saved,true);assert.equal(records[0].applied,true);
 setJobActivity(s,job,'applied',false);assert.deepEqual(setJobActivity(s,job,'saved',false),[]);
 assert.equal(s.getItem('other-key'),'keep');
});

test('hidden jobs leave All jobs but remain available in personal views',()=>{
 const records=[{id:job.id,saved:true,hidden:true,applied:true}];
 assert.equal(activityView([job],records,'').length,0);
 for(const view of ['saved','applied','hidden'])assert.equal(activityView([job],records,view).length,1);
 assert.equal(activityView([job],[],'saved').length,0);
});

test('latest employer data replaces a saved snapshot and absent or closed jobs are labeled unavailable',()=>{
 const s=storage();setJobActivity(s,job,'saved',true);const records=readJobActivity(s);
 let result=trackedJobs([{...job,title:'Updated role',status:'closed'}],records,snapshot=>snapshot,today);
 assert.equal(result.length,1);assert.equal(result[0].title,'Updated role');assert.equal(result[0].organizerUnavailable,true);
 result=trackedJobs([],records,snapshot=>snapshot,today);assert.equal(result[0].organizerUnavailable,true);
 assert.equal(filterJobs(result,readJobFilters(''),today).length,0); // Missing snapshots cannot reappear as live jobs.
 assert.equal(activityView([],records,'').length,0);
 const old=trackedJobs([],[{...records[0],job:{...job,postedAt:'2026-10-01'}}],snapshot=>snapshot,today);
 assert.equal(filterJobs(old,readJobFilters(''),today).length,0);
 assert.equal(filterJobs(old,readJobFilters(''),today,true).length,1);
 assert.equal(filterJobs(old,readJobFilters('?posted=7'),today,true).length,0);
});

test('invalid snapshots cannot produce links and current live jobs remain authoritative',()=>{
 const records=[{id:job.id,saved:true,job:{...job,url:'javascript:alert(1)'}}];
 assert.deepEqual(trackedJobs([],records,()=>{throw Error('Invalid official URL');},today),[]);
 const live=trackedJobs([job],records,()=>{throw Error('Do not use snapshot');},today);assert.equal(live.length,1);assert.equal(live[0].organizerUnavailable,false);
});

test('corrupt activity, duplicate IDs, invalid actions, and storage failures are handled safely',()=>{
 const s=storage();s.setItem(ACTIVITY_KEY,'{bad');assert.deepEqual(readJobActivity(s),[]);
 s.setItem(ACTIVITY_KEY,JSON.stringify({version:1,jobs:[null,{id:'__proto__',saved:true},{id:job.id,saved:true,job}, {id:job.id,hidden:true,job}]}));
 assert.equal(readJobActivity(s).length,1);
 assert.throws(()=>setJobActivity(s,job,'unknown',true),/Invalid/);
 const previous=s.getItem(ACTIVITY_KEY);s.setItem=()=>{throw Error('Storage full');};
 assert.throws(()=>setJobActivity(s,job,'applied',true),/Storage full/);assert.equal(s.getItem(ACTIVITY_KEY),previous);
});

test('posting-date windows use employer dates, preserve the two-week feed rule, and round-trip',()=>{
 assert.equal(matchesPosted(job,'today',today),true);
 assert.equal(matchesPosted({...job,postedAt:'2026-11-16'},'today',today),false);
 for(const [window,boundary,outside] of [['3','2026-11-14','2026-11-13'],['7','2026-11-10','2026-11-09'],['14','2026-11-03','2026-11-02']]){
  assert.equal(matchesPosted({...job,postedAt:boundary},window,today),true);
  assert.equal(matchesPosted({...job,postedAt:outside},window,today),false);
 }
 assert.equal(matchesPosted({...job,postedAt:null},'today',today),false);
 assert.equal(matchesPosted({...job,postedAt:'2026-11-18'},'7',today),false);
 assert.equal(filterJobs([{...job,postedAt:'2026-10-01'}],readJobFilters(''),today).length,0);
 const f=readJobFilters('?posted=3&payPosted=1&view=saved');assert.equal(f.posted,'3');assert.equal(f.payPosted,'1');assert.equal(f.view,'saved');
 assert.equal(readJobFilters('?posted=bogus&payPosted=false&view=other').posted,'');
});

test('Pay posted includes text-only ranges while respecting geography and numeric pay filters',()=>{
 const pay={...job,publishedPay:{text:'Employer range $80,000 to $120,000',scopeStates:['Texas'],note:'Period unspecified.'}};
 assert.equal(hasPostedPay(pay),true);assert.equal(hasPostedPay(pay,'Florida'),false);assert.equal(hasPostedPay(job),false);
 assert.equal(filterJobs([pay,job],readJobFilters('?payPosted=1'),today).length,1);
 assert.equal(filterJobs([pay],readJobFilters('?payPosted=1&state=Florida'),today).length,0);
 assert.equal(filterJobs([pay],readJobFilters('?payPosted=1&pay=year:50000'),today).length,0);
});
