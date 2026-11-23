import test from 'node:test';
import assert from 'node:assert/strict';
import {jobFunctionResult} from '../public/job-functions.js';

const evidence = duties => ({version:2,duties,requiredSkills:[],preferredSkills:[],category:''});

test('ServiceNow application engineers need software duties for the software category',()=>{
  const job={companyId:'servicenow',title:'Senior Application Engineer'};
  const software=jobFunctionResult({...job,functionContext:evidence([
    'Build high-quality, clean, and reusable code while following software engineering practices.'
  ])});
  assert.equal(software.primaryFunction,'software');
  assert.equal(software.basis,'responsibilities');
  assert.equal(jobFunctionResult(job).primaryFunction,'engineering');
  assert.equal(jobFunctionResult({...job,companyId:'ge-vernova'}).primaryFunction,'engineering');
});

test('GE Vernova distinguishes tool inventory and process operations from general manufacturing',()=>{
  const companyId='ge-vernova';
  assert.equal(jobFunctionResult({companyId,title:'Tool Crib Attendant'}).primaryFunction,'logistics');
  const job={companyId,title:'GEV Cores and Castings Materials Internship – 2027',
    functionContext:evidence(['Draft standard work and work instructions for factory cost allocation.'])};
  const result=jobFunctionResult(job);
  assert.equal(result.primaryFunction,'operations');
  assert.equal(result.basis,'responsibilities');
});
