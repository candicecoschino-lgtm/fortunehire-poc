import test from 'node:test';
import assert from 'node:assert/strict';
import {readJobFilters,serializeJobFilters,filterJobs} from '../public/jobs.js';

const today='2026-11-20';
const make=(id,arrangement='on-site',state='Michigan',fn='sales')=>({id,companyId:id,title:'Sales role',companyName:id,postedAt:today,reviewedAt:today,status:'reviewed',closesAt:null,arrangement,remoteScope:arrangement==='remote'?'states':'unknown',eligibleStates:arrangement==='remote'?[state]:[],locations:[{state}],primaryJobFunction:fn,industry:'Health Care',employmentType:'Full-time',travelRequired:false});
const jobs=[make('centene'),make('cvs-health'),make('humana'),make('centene','remote','Michigan','data'),make('humana','remote','Ohio')];
const run=query=>filterJobs(jobs,readJobFilters(query),today).map(j=>j.companyId);

test('include uses OR and exclude removes Humana with or without an include list',()=>{
 assert.deepEqual(run('?company=centene&company=cvs-health'),['centene','cvs-health','centene']);
 assert.deepEqual(run('?companyExclude=humana'),['centene','cvs-health','centene']);
 assert.deepEqual(run('?company=centene&company=cvs-health&companyExclude=humana'),['centene','cvs-health','centene']);
});
test('conflicts resolve to exclusion and legacy single company links work',()=>{
 const f=readJobFilters('?company=humana&companyExclude=humana');assert.deepEqual(f.company,[]);assert.deepEqual(run('?company=centene'),['centene','centene']);
});
test('company filters combine with state, arrangement and functions',()=>{
 assert.deepEqual(run('?company=centene&company=cvs-health&companyExclude=humana&state=Michigan&arrangement=remote&function=data&function=sales'),['centene']);
});
test('include and exclude round-trip in shareable saved search URLs',()=>{
 const f=readJobFilters('?company=centene&company=cvs-health&companyExclude=humana');assert.deepEqual(readJobFilters('?'+serializeJobFilters(f)).company,f.company);assert.deepEqual(readJobFilters('?'+serializeJobFilters(f)).companyExclude,f.companyExclude);
});
