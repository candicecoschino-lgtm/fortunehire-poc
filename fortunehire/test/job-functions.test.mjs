import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_FUNCTIONS,classifyJobFunctions} from '../public/job-functions.js';
import {filterJobs,readJobFilters,serializeJobFilters} from '../public/jobs.js';

test('clear role titles map to job functions independently of company industry',()=>{
 for(const [title,key] of [
  ['Sales Associate','sales'],['Account Executive','sales'],['Marketing Manager','marketing'],
  ['Human Resources Generalist','hr'],['HR Business Partner','hr'],['Software Engineer','it'],
  ['IT Systems Administrator','it'],['Operations Manager','operations'],['Customer Service Representative','service'],
  ['Administrative Assistant','admin'],['Admin Coordinator','admin'],['Executive Assistant','admin'],
  ['Corporate Counsel','legal'],['Payroll Analyst','finance'],['Mechanical Engineer','engineering'],
  ['Registered Nurse','healthcare'],['Supply Chain Analyst','logistics'],['Welder','manufacturing'],
  ['Research Scientist','research'],['Program Manager','projects']
 ])assert.ok(classifyJobFunctions(title).includes(key),title);
 assert.equal(new Set(Object.keys(JOB_FUNCTIONS)).size,16);
});

test('word boundaries and unclear titles do not invent functions',()=>{
 for(const title of ['Specialist II','Associate','President','Salesforce Consultant','Wholesale Specialist','Support Specialist'])assert.deepEqual(classifyJobFunctions(title),['other']);
 assert.deepEqual(classifyJobFunctions(null),['other']);
 assert.ok(!classifyJobFunctions('Software Engineer').includes('engineering'));
 assert.ok(!classifyJobFunctions('Technical Support Engineer').includes('service'));
 assert.ok(!classifyJobFunctions('Pharmacy Technician').includes('manufacturing'));
 assert.deepEqual(classifyJobFunctions('Systems Admin'),['it']);
});

test('cross-functional titles appear in each relevant category without duplicate labels',()=>{
 assert.deepEqual(classifyJobFunctions('Sales Operations Analyst'),['sales','operations']);
 assert.deepEqual(classifyJobFunctions('Marketing Communications Manager'),['marketing']);
});

test('job function intersects other filters while unspecified employment type stays independent',()=>{
 const j={id:'example',title:'Sales Operations Analyst',companyName:'Example',companyId:'example',industry:'Commercial Banks',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'on-site',locations:[{city:'Austin',state:'Texas'}],employmentType:'Not specified',travelRequired:null};
 const f=extra=>({...readJobFilters(''),...extra});
 for(const fn of ['sales','operations'])assert.equal(filterJobs([j],f({function:fn,type:'Not specified',state:'Texas'}),'2026-11-17').length,1);
 assert.equal(filterJobs([j],f({function:'admin'}),'2026-11-17').length,0);
 assert.equal(filterJobs([j],f({function:'sales',type:'Full-time'}),'2026-11-17').length,0);
 assert.equal(j.employmentType,'Not specified');
 assert.equal(filterJobs([{...j,title:'Specialist II'}],f({function:'other'}),'2026-11-17').length,1);
});

test('job function links round trip and empty filters clear the selection',()=>{
 const f=readJobFilters('?function=admin&state=New+York&type=Not+specified');
 assert.equal(f.function,'admin');assert.deepEqual(readJobFilters('?'+serializeJobFilters(f)),f);
 assert.equal(readJobFilters('').function,'');assert.equal(serializeJobFilters(readJobFilters('')),'');
 assert.equal(readJobFilters('?sector=Technology').function,'');
});
