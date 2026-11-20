import test from 'node:test';
import assert from 'node:assert/strict';
import {filterJobs,readJobFilters,serializeJobFilters} from '../public/jobs.js';
import {savedQuery} from '../public/saved-searches.js';

const today='2026-11-18';
const base={companyId:'example',companyName:'Example',industry:'Technology',status:'reviewed',postedAt:today,reviewedAt:today,closesAt:null,employmentType:'Full-time',travelRequired:null};
const make=(id,title,fn,arrangement,locations,remoteScope='unknown',eligibleStates=[])=>({id,title,primaryJobFunction:fn,arrangement,locations,remoteScope,eligibleStates,...base});
const jobs=[
 make('sales-onsite','Sales Representative','sales','on-site',[{city:'Detroit',state:'Michigan'}]),
 make('it-remote-mi','IT Support Specialist','it','remote',[], 'states',['Michigan','Ohio']),
 make('finance-hybrid-wa','Financial Analyst','finance','hybrid',[{city:'Seattle',state:'Washington'}]),
 make('ops-onsite-wa','Operations Manager','operations','on-site',[{city:'Seattle',state:'Washington'}]),
 make('data-remote-unknown','Data Analyst','data','remote',[],'unknown',[]),
 make('data-remote-us','Data Scientist','data','remote',[],'nationwide',[]),
 make('sales-onsite-oh','Account Executive','sales','on-site',[{city:'Cleveland',state:'Ohio'}])
];

test('common job function searches return only the stored primary function',()=>{
 for(const fn of ['sales','it','finance','operations','data']){
  const results=filterJobs(jobs,readJobFilters(`?function=${fn}`),today);
  assert.ok(results.length>0,`no results for ${fn}`);
  assert.ok(results.every(job=>job.primaryJobFunction===fn),fn);
 }
});

test('multiple functions and arrangements use OR within categories and AND between categories',()=>{
 const filters=readJobFilters('?function=sales&function=data&arrangement=remote&arrangement=on-site&state=Michigan');
 assert.deepEqual(filterJobs(jobs,filters,today).map(job=>job.id).sort(),['data-remote-us','sales-onsite']);
});

test('multiple selected states match any supported location or remote eligibility',()=>{
 const filters=readJobFilters('?state=Michigan&state=Washington&arrangement=remote&arrangement=hybrid&arrangement=on-site');
 assert.deepEqual(filterJobs(jobs,filters,today).map(job=>job.id).sort(),['data-remote-us','finance-hybrid-wa','it-remote-mi','ops-onsite-wa','sales-onsite']);
});

test('state-specific remote roles require confirmed eligibility while nationwide roles remain valid',()=>{
 assert.deepEqual(filterJobs(jobs,readJobFilters('?state=Michigan&arrangement=remote'),today).map(job=>job.id).sort(),['data-remote-us','it-remote-mi']);
 assert.deepEqual(filterJobs(jobs,readJobFilters('?state=Washington&arrangement=remote'),today).map(job=>job.id),['data-remote-us']);
 assert.deepEqual(filterJobs(jobs,readJobFilters('?arrangement=remote-state'),today).map(job=>job.id),['it-remote-mi']);
});

test('new multi-value URLs round-trip and old single-value saved searches remain readable',()=>{
 const old=readJobFilters('?state=Michigan&arrangement=hybrid&function=it');
 assert.deepEqual(old.state,['Michigan']);assert.deepEqual(old.arrangement,['hybrid']);assert.deepEqual(old.function,['it']);
 const multi=readJobFilters('?state=Michigan&state=Washington&arrangement=remote&arrangement=on-site&function=sales&function=data');
 assert.deepEqual(readJobFilters('?'+serializeJobFilters(multi)),multi);
 assert.deepEqual(readJobFilters(savedQuery(multi)),{...multi,page:'1'});
});
