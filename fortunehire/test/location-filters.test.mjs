import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_KEYS,readJobFilters,serializeJobFilters,filterJobs} from '../public/jobs.js';
import {savedQuery,readSavedSearches} from '../public/saved-searches.js';
import {locationSummary,todayPostingNote} from '../public/job-presentation.js';
const today='2026-11-18';
const job={id:'example',title:'Analyst',companyName:'Example',status:'reviewed',postedAt:today,reviewedAt:today,arrangement:'hybrid',locations:[{city:'Seattle',state:'Washington'},{city:'Detroit',state:'Michigan'}],salary:{min:100000,max:120000,currency:'USD',period:'year',scopeStates:['Washington']}};
test('old ZIP links and saved filters discard ZIP while preserving state, arrangement and other choices',()=>{
 const query='?city=48439&state=Michigan&arrangement=hybrid&function=it';
 const f=readJobFilters(query);
 assert.ok(!JOB_KEYS.includes('city'));assert.equal(f.city,undefined);
 assert.ok(!serializeJobFilters(f).includes('city='));assert.deepEqual(f.state,['Michigan']);assert.deepEqual(f.arrangement,['hybrid']);
 assert.deepEqual(readJobFilters(savedQuery(query)).function,['it']);
 const storage={getItem:()=>JSON.stringify({version:1,searches:[{name:'Michigan',query}]})};
 assert.ok(!readSavedSearches(storage)[0].query.includes('city='));
});
test('state and arrangement search include later-listed locations and preserve remote eligibility and pay scope',()=>{
 const f=readJobFilters('?city=48439&state=Michigan&arrangement=hybrid');
 assert.equal(filterJobs([job],f,today).length,1);
 assert.equal(locationSummary(job,'Michigan'),'Detroit, Michigan + 1 more location');
 assert.equal(filterJobs([job],{...f,payPosted:'1'},today).length,0);
 const remote={...job,arrangement:'remote',remoteScope:'states',eligibleStates:['Michigan']};
 assert.equal(filterJobs([remote],readJobFilters('?city=48439&state=Michigan&arrangement=remote'),today).length,1);
 assert.equal(filterJobs([remote],readJobFilters('?state=Texas&arrangement=remote'),today).length,0);
});
test('Posted today uses employer dates, independent of check dates, and explains when the whole feed lacks today',()=>{
 const yesterday={...job,postedAt:'2026-11-17'};
 const f=readJobFilters('?posted=today');
 assert.equal(filterJobs([yesterday],f,today).length,0);
 assert.equal(filterJobs([yesterday,job],f,today).length,1);
 assert.equal(filterJobs([yesterday],readJobFilters('?posted=3'),today).length,1);
 assert.match(todayPostingNote([yesterday],today),/No employer-dated postings for today/);
 assert.equal(todayPostingNote([yesterday,job],today),'');
 assert.equal(yesterday.postedAt,'2026-11-17');
});
