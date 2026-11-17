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
 assert.ok(Object.keys(JOB_FUNCTIONS).length>=16);
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

test('reviewed gaps classify application development and other explicit technical vocabulary',()=>{
 for(const title of ['Application Development Advisor- Hybrid','Application Development Senior Analyst- Hybrid','Applications Development Sr Programmer Analyst - Assistant Vice President','Apps Dev Tech Lead Analyst - Vice President','Data Analyst - Optum Insight - Remote','Technical Staff, Network Architect','Senior Systems Architect - Datacenter','Lead (Oracle) SaaS Administrator','Applied AI/ML Lead Vice President','Senior Information Security Analyst','Principal Solution Architect','Long Range Server Planning'])assert.ok(classifyJobFunctions(title).includes('it'),title);
 assert.ok(!classifyJobFunctions('Avionics Technician - Line').includes('it'));
 assert.ok(classifyJobFunctions('Avionics Technician - Line').includes('engineering'));
});

test('reviewed non-IT gaps include functional and frontline titles',()=>{
 for(const [title,key] of [
  ['Customer Success Manager, Core - Commercial','service'],['Center Administrator','admin'],
  ['Personal Banker SAFE Act, One California Branch','finance'],['Underwriting Intern - Summer 2027','finance'],
  ['Behavioral Health Liaison (20% Travel: Macomb & Wayne)','healthcare'],['Licensed Optician','healthcare'],
  ['Optical Associate, Certified (ABO)','healthcare'],['Cashier Part Time','retail'],['Bakery/Deli Clerk','retail'],
  ['Starbucks Barista','hospitality'],['Food & Beverage Busser - Part Time','hospitality'],
  ['Courier/Non-DOT','logistics'],['Tractor Trailer Driver/RTD - Apprentice-2','logistics'],
  ['Mechanical Technician, Beaumont, TX','manufacturing'],['Senior Product Manager','projects'],
  ['Business Intelligence Analyst','business'],['Business\u00a0Information Consultant Senior','business'],
  ['Senior Manager - UX Design & Innovation','engineering'],['Quality Specialist II','quality'],['Manager, EHS','quality'],
  ['Employee Success Business Partner Director','hr'],['Training Consultant - Cold Planers','hr']
 ])assert.ok(classifyJobFunctions(title).includes(key),title);
});

test('broader vocabulary preserves ambiguous titles and separates physical and IT work',()=>{
 for(const title of ['Any Position','Field Specialist B','Assistant Manager','Senior Architect','Security Analyst Senior','Wellpoint Federal SME II'])assert.deepEqual(classifyJobFunctions(title),['other'],title);
 assert.ok(!classifyJobFunctions('Long Range Server Planning').includes('hospitality'));
 assert.ok(classifyJobFunctions('Restaurant Server').includes('hospitality'));
 assert.ok(!classifyJobFunctions('Optical Network Engineer').includes('healthcare'));
 assert.ok(!classifyJobFunctions('Human Resources Department Manager').includes('retail'));
});

test('brand-new listings receive rules without employer-specific IDs or saved manual labels',()=>{
 const base={id:'brand-new-listing-999',companyName:'New Employer',companyId:'new-employer',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'hybrid',locations:[{city:'Austin',state:'Texas'}],employmentType:'Not specified',travelRequired:null};
 for(const title of ['Application Development Senior Analyst - New Team','Applications Development Group Manager - New Office']){
  const j={...base,title};
  const f={...readJobFilters(''),function:'it',state:'Texas',type:'Not specified'};
  assert.equal(filterJobs([j],f,'2026-11-17').length,1);
  assert.equal(filterJobs([j],{...f,function:'other'},'2026-11-17').length,0);
  assert.equal(j.employmentType,'Not specified');assert.equal(j.reviewedAt,base.reviewedAt);
 }
});
