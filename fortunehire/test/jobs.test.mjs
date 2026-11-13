import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {readJobFilters,serializeJobFilters,filterJobs,validateJobs,matchesState,matchesPay,isCurrent,todayInNewYork,paginateJobs} from '../public/jobs.js';
const companies=JSON.parse(await readFile(new URL('../public/data/companies.json',import.meta.url),'utf8')).companies;
const data=JSON.parse(await readFile(new URL('./fixtures/reviewed-jobs.json',import.meta.url),'utf8'));
const jobs=validateJobs(data,companies),today='2026-11-13';
const filters=extra=>({...readJobFilters(''),...extra});

test('current publication dataset validates independently of historical regression fixtures',async()=>{
  const current=JSON.parse(await readFile(new URL('../public/data/jobs.json',import.meta.url),'utf8'));
  assert.ok(validateJobs(current,companies).length>0);
});
test('reviewed production jobs join real employers and cover all three arrangements',()=>{
  assert.equal(jobs.length,22);assert.deepEqual([...new Set(jobs.map(j=>j.arrangement))].sort(),['hybrid','on-site','remote']);
  for(const j of jobs){assert.ok(j.companyName);assert.ok(j.industry);assert.ok(j.sector);assert.ok(isCurrent(j,today));}
});
test('Florida work arrangements use actual job eligibility, not headquarters',()=>{
  assert.equal(filterJobs(jobs,filters({state:'Florida',arrangement:'on-site'}),today).length,2);
  assert.equal(filterJobs(jobs,filters({state:'Florida',arrangement:'hybrid'}),today).length,1);
  assert.equal(filterJobs(jobs,filters({state:'Florida',arrangement:'remote'}),today).length,4);
  const tampa=jobs.find(j=>j.requisitionId==='2395019');assert.ok(matchesState(tampa,'Florida'));assert.equal(matchesState(tampa,'Minnesota'),false);assert.match(tampa.locationNote,/20 miles/);
});
test('explicit nationwide remote eligibility matches any valid state; unknown does not',()=>{
  const nationwide=jobs.find(j=>j.requisitionId==='2401855');assert.ok(matchesState(nationwide,'Alaska'));assert.equal(matchesState(nationwide,'Atlantis'),false);
  assert.equal(matchesState({...nationwide,remoteScope:'unknown',eligibleStates:[]},'Florida'),false);
});
test('pay filters compare posted minimums within the same period and geographic scope',()=>{
  const hourly=jobs.find(j=>j.requisitionId==='2395019');assert.ok(matchesPay(hourly,'hour:15'));assert.equal(matchesPay(hourly,'hour:20'),false);assert.equal(matchesPay(hourly,'year:15000'),false);
  const ai=jobs.find(j=>j.requisitionId==='26995852');assert.ok(matchesPay(ai,'year:150000','New York'));assert.equal(matchesPay(ai,'year:150000','Texas'),false);assert.equal(matchesPay(ai,'year:200000'),false);
  assert.equal(matchesPay({...ai,salary:null},'year:50000'),false);
});
test('excluding travel-required jobs preserves unknowns without calling them travel-free',()=>{
  const result=filterJobs(jobs,filters({state:'Florida',travel:'exclude'}),today);assert.equal(result.length,3);assert.ok(result.some(j=>j.travelRequired===null));assert.ok(result.every(j=>j.travelRequired!==true));
});
test('company, industry, sector, job type, state, arrangement and title intersect',()=>{
  const result=filterJobs(jobs,filters({q:' SUPPORT ',company:'citigroup',industry:'Commercial Banks',sector:'Financials',type:'Full-time',state:'Florida',arrangement:'hybrid',pay:'year:50000'}),today);
  assert.equal(result.length,1);assert.equal(result[0].requisitionId,'261002688');
  assert.equal(filterJobs(jobs,filters({company:'citigroup',arrangement:'remote'}),today).length,0);
});
test('closed, expired, stale and future-reviewed records cannot appear',()=>{
  const j=jobs[0];assert.ok(isCurrent({...j,closesAt:today},today));assert.equal(isCurrent({...j,closesAt:'2026-11-12'},today),false);
  assert.equal(isCurrent({...j,status:'closed'},today),false);assert.equal(isCurrent({...j,reviewedAt:'2026-11-05'},today),false);assert.equal(isCurrent({...j,reviewedAt:'2026-11-14'},today),false);
  assert.equal(filterJobs(jobs,filters({}),'2026-11-21').length,0);
});
test('freshness uses New York date around midnight and daylight saving changes',()=>{
  assert.equal(todayInNewYork(new Date('2026-11-14T02:00:00Z')),'2026-11-13');assert.equal(todayInNewYork(new Date('2026-07-14T02:00:00Z')),'2026-07-13');
});
test('URL state preserves advanced selections and safe pagination defaults',()=>{
  const f=readJobFilters('?state=New+York&arrangement=hybrid&travel=exclude&pay=year%3A100000&page=2&sort=title');assert.deepEqual(readJobFilters('?'+serializeJobFilters(f)),f);assert.equal(serializeJobFilters(readJobFilters('')),'');assert.equal(readJobFilters('?page=-1').page,'1');assert.equal(readJobFilters('?page=999999999').page,'10000');
});
test('pagination has no duplicate/missing records and clamps out-of-range pages',()=>{
  const a=paginateJobs(jobs,1),b=paginateJobs(jobs,2);assert.equal(a.items.length,12);assert.equal(b.items.length,10);assert.equal(new Set([...a.items,...b.items].map(j=>j.id)).size,22);assert.equal(paginateJobs([],100).page,1);assert.equal(paginateJobs(jobs,900).page,2);
});
test('data validation rejects wrong-employer links, unsafe URLs, bogus dates and eligibility',()=>{
  for(const mutate of [d=>d.jobs.push(d.jobs[0]),d=>d.jobs[0].url='javascript:alert(1)',d=>d.jobs[0].url='https://jobs.boeing.com/job/wrong-employer',d=>d.jobs[0].reviewedAt='2026-02-31',d=>d.jobs[0].remoteScope='nationwide',d=>d.jobs[0].locations[0].state='Atlantis',d=>d.jobs[0].salary.min=-1]){const copy=structuredClone(data);mutate(copy);assert.throws(()=>validateJobs(copy,companies));}
});

