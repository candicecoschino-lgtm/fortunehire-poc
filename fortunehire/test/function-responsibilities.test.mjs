import test from 'node:test';
import assert from 'node:assert/strict';
import {jobFunctionResult,classifyJobFunctions} from '../public/job-functions.js';
import {filterJobs,readJobFilters} from '../public/jobs.js';
import {dutyRules} from '../public/function-duties.js';
const context=(duties,category='')=>({version:1,duties,category});
test('responsibilities override title and employer department without using incidental sales or medical words',()=>{
 const job={title:'Sales Operations Analyst',functionContext:context(['Build databases for the sales team.','Develop software for medical billing reports.'],'Sales')};
 assert.deepEqual(classifyJobFunctions(job),['it']);
 assert.equal(jobFunctionResult(job).basis,'responsibilities');
 assert.equal(jobFunctionResult(job).evidence.length,2);
});
test('specific responsibilities identify every function for generic titles',()=>{
 const examples={sales:'Meet sales targets.',marketing:'Develop marketing campaigns.',hr:'Manage employee relations.',it:'Build software for customers.',operations:'Oversee daily operations.',service:'Resolve customer complaints.',admin:'Manage executive calendars.',legal:'Provide legal advice.',finance:'Process payroll for employees.',engineering:'Design mechanical systems.',healthcare:'Provide direct patient care.',logistics:'Coordinate shipments.',manufacturing:'Operate production equipment.',research:'Conduct laboratory experiments.',projects:'Manage project timelines.',business:'Analyze business requirements.',retail:'Stock store shelves.',hospitality:'Prepare meals for customers.',quality:'Perform safety inspections.'};
 assert.deepEqual(Object.keys(examples).sort(),Object.keys(dutyRules).sort());
 for(const [key,duty] of Object.entries(examples))assert.deepEqual(classifyJobFunctions({title:'Specialist',functionContext:context([duty])}),[key],duty);
});
test('repeated core duties outweigh an incidental task; genuinely mixed duties can match multiple functions',()=>{
 const job={title:'Specialist',functionContext:context(['Develop software for operations.','Maintain databases for users.','Coordinate meetings.'])};
 assert.deepEqual(classifyJobFunctions(job),['it']);
 job.functionContext=context(['Process payroll for employees.','Manage employee relations.']);
 assert.deepEqual(new Set(classifyJobFunctions(job)),new Set(['hr','finance']));
});
test('category supports unclear descriptions; missing or malformed evidence safely falls back to title',()=>{
 assert.deepEqual(classifyJobFunctions({title:'Specialist',functionContext:context([],'Human Resources')}),['hr']);
 for(const functionContext of [undefined,{version:9},context([]),context(['Work with sales and HR. Support medical professionals.'])]){
  const result=jobFunctionResult({title:'Software Engineer',functionContext});assert.deepEqual(result.keys,['it']);assert.equal(result.basis,'title');
 }
});
test('filters use the same description result as details and preserve saved/older title-only jobs',()=>{
 const job={id:'test',title:'Sales Analyst',companyName:'Test',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',arrangement:'hybrid',locations:[],functionContext:context(['Build databases for the sales team.'])};
 const f=fn=>readJobFilters('?function='+fn);
 assert.equal(filterJobs([job],f('it'),'2026-11-17').length,1);
 assert.equal(filterJobs([job],f('sales'),'2026-11-17').length,0);
 const {functionContext,...older}=job;
 assert.equal(filterJobs([older],f('sales'),'2026-11-17').length,1);
 assert.deepEqual(classifyJobFunctions({title:'Specialist'}),['other']);
});

test('inflected actions and role-specific language resolve functions without their title',()=>{
 for(const [duty,key] of [
  ['Develops software for users.','it'],['Handles member calls in a friendly manner.','service'],
  ['Performs Failsafe Analyses for aircraft parts.','engineering'],['Operates handheld scanner to update inventory.','logistics'],
  ['Analyzes financial information to qualify customers for a lending solution.','finance'],
  ['Drives the prioritization and execution of product roadmap.','projects'],
  ['Provides clinical consultation to customers.','healthcare']
 ])assert.deepEqual(classifyJobFunctions({title:'Specialist',functionContext:context([duty])}),[key],duty);
});
