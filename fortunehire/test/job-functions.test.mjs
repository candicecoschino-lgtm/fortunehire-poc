import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_FUNCTIONS,JOB_FUNCTION_OPTIONS,jobFunctionResult,classifyJobFunctions,isValidJobFunction} from '../public/job-functions.js';
import {filterJobs,readJobFilters,validateJobs} from '../public/jobs.js';

const context=(duties=[],requiredSkills=[],category='')=>({version:2,duties,requiredSkills,preferredSkills:[],category});
const job=(title,fn,extra={})=>({id:'test-job',title,companyId:'example',companyName:'Example',industry:'Technology',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'on-site',remoteScope:'unknown',eligibleStates:[],locations:[{city:'Austin',state:'Texas'}],employmentType:'Full-time',travelRequired:null,primaryJobFunction:fn,...extra});

test('taxonomy is unchanged, candidate-friendly, and alphabetized for display',()=>{
 const labels=JOB_FUNCTION_OPTIONS.map(([,label])=>label);
 assert.equal(labels.length,30);
 assert.deepEqual(labels.slice().sort((a,b)=>a.localeCompare(b)),labels);
 assert.equal(JOB_FUNCTIONS.data,'Data & Analytics');
});

test('specific job titles are the primary classification signal',()=>{
 for(const [title,expected] of [
  ['Data Scientist, Marketing','data'],['Finance Manager, Sales Finance','finance'],['IT Operations Engineer','it'],
  ['Senior Software Engineer','software'],['Retail Sales Consultant','retail'],['Customer Success Account Manager','success'],
  ['Medical Receptionist','healthcareAdmin'],['Registered Nurse','healthcare'],['Manufacturing Engineer I','manufacturing']
 ]){
  const result=jobFunctionResult({title,functionContext:context([],[], 'Unrelated Department')});
  assert.equal(result.primaryFunction,expected,title);
  assert.equal(result.basis,'job title');
  assert.equal(classifyJobFunctions({title}).length,1);
 }
});

test('specific sales, communications, IT, and operations titles no longer fall through to Other',()=>{
 for(const [title,expected] of [
  ['Sales Development Representative I','sales'],
  ['Global Sales Accounts Director','sales'],
  ['Business Communications Lead Analyst','communications'],
  ['Director of CEO Communications','communications'],
  ['Network Deploy Technician, Infra Delivery','it'],
  ['Lead IT Portfolio Management Analyst','it'],
  ['Prime Air Ops Manager','operations'],
  ['Head of Custody Operations','operations']
 ]) assert.equal(jobFunctionResult({title}).primaryFunction,expected,title);
 assert.equal(jobFunctionResult({title:'Communications Research and Impact Advisor',functionContext:context(['Lead quantitative and qualitative studies end to end.'])}).primaryFunction,'other');
});

test('recurring specific occupations resolve without broad department guesses',()=>{
 for(const [title,expected] of [
  ['Pharmacy Intern','healthcare'],['CNA Hospice Aide','healthcare'],
  ['Online Grocery Pick-Up Clerk','retail'],['Bakery/Deli Clerk','retail'],
  ['Merchandising Service Associate','retail'],
  ['Xfinity Outside Sales Professional','sales'],['Solar Sales Rep','sales'],
  ['Senior Network Developer','it'],['Tire & Battery Technician - Automotive','trades'],
  ['Operations Admin II','admin'],['Senior Tax Analyst','finance']
 ]) assert.equal(jobFunctionResult({title}).primaryFunction,expected,title);
 for(const title of ['Benefits Consultant','Merchandising Lead','Fulfillment Associate'])
  assert.equal(jobFunctionResult({title}).primaryFunction,'other',title);
});

test('responsibilities support a generic title and resolve one clear function',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context(['Prepare financial statements and reconcile accounts payable.'])});
 assert.equal(result.primaryFunction,'finance');
 assert.equal(result.basis,'responsibilities');
 assert.equal(result.reviewRequired,false);
});

test('required skills can classify when title and responsibilities do not',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context([],['Machine learning','Statistical modeling','PyTorch'])});
 assert.equal(result.primaryFunction,'data');
 assert.equal(result.basis,'required skills');
 assert.equal(result.reviewRequired,true);
});

test('ambiguous evidence falls back to Other / Unclassified',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context(['Develop marketing campaigns.','Prepare financial statements.'])});
 assert.equal(result.primaryFunction,'other');
 assert.equal(result.reviewRequired,true);
 assert.equal(result.confidence,'low');
});

test('a specific title wins but conflicting duties flag the listing for review',()=>{
 const result=jobFunctionResult({title:'Data Scientist, Marketing',functionContext:context(['Prepare financial statements and reconcile accounts payable.'])});
 assert.equal(result.primaryFunction,'data');
 assert.equal(result.basis,'job title');
 assert.equal(result.reviewRequired,true);
});

test('missing evidence stays unclassified and each result is exactly one valid key',()=>{
 for(const input of [{title:'Specialist II'},{title:''},{title:'Assistant'}]){
  const result=jobFunctionResult(input);
  assert.equal(result.primaryFunction,'other');
  assert.equal(result.reviewRequired,true);
  const functions=classifyJobFunctions(input);
  assert.equal(functions.length,1);
  assert.ok(isValidJobFunction(functions[0]));
 }
});

test('filtering reads the persisted single function and keeps stable job references',()=>{
 const dataJob=job('Data Scientist, Marketing','data',{id:'stable-saved-job'});
 assert.equal(filterJobs([dataJob],readJobFilters('?function=data'),'2026-11-17').length,1);
 assert.equal(filterJobs([dataJob],readJobFilters('?function=marketing'),'2026-11-17').length,0);
 assert.equal(dataJob.id,'stable-saved-job');
 const legacy={...dataJob};delete legacy.primaryJobFunction;
 assert.equal(filterJobs([legacy],readJobFilters('?function=data'),'2026-11-17').length,0);
});

test('legacy schema upgrade assigns one function without changing job ID or URL',()=>{
 const source=job('Data Scientist, Marketing',undefined);delete source.primaryJobFunction;
 const companies=[{id:'example',name:'Example',industry:'Technology',profileSource:'https://example.com',careerUrl:'https://example.com/careers'}];
 source.url='https://example.com/jobs/1';source.requisitionId='1';source.identifierType='requisition';source.locationNote='Austin, Texas';source.sector='Technology';source.sourceNote='Official posting';source.sourceHash='stable';source.collectionMethod='official';source.arrangementBasis=undefined;
 const normalized=validateJobs({schemaVersion:1,jobs:[source]},companies)[0];
 assert.equal(normalized.id,source.id);assert.equal(normalized.url,source.url);assert.equal(normalized.primaryJobFunction,'data');
 assert.throws(()=>validateJobs({schemaVersion:2,jobs:[{...normalized,primaryJobFunction:['data']}]},companies),/Invalid primary job function/);
});
