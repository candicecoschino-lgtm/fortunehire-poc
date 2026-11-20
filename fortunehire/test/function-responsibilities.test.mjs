import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_FUNCTIONS,jobFunctionResult} from '../public/job-functions.js';
import {filterJobs,readJobFilters} from '../public/jobs.js';
import {validFunctionContext} from '../public/function-duties.js';

const context=(duties=[],requiredSkills=[],category='')=>({version:2,duties,requiredSkills,preferredSkills:[],category});
test('a clear title remains primary over department wording and incidental duties',()=>{
 const result=jobFunctionResult({title:'Data Scientist, Marketing',functionContext:context(['Coordinate project meetings for the marketing team.'],['Python'],'Marketing')});
 assert.equal(result.primaryFunction,'data');assert.equal(result.basis,'job title');
});

test('each existing taxonomy category is still valid',()=>{
 assert.equal(Object.keys(JOB_FUNCTIONS).length,30);
 for(const key of Object.keys(JOB_FUNCTIONS))assert.equal(typeof key,'string');
});

test('specific duty evidence is used only when the title is generic',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context(['Resolve customer inquiries and service issues.'])});
 assert.equal(result.primaryFunction,'service');assert.equal(result.basis,'responsibilities');
});

test('multiple conflicting duty families remain Other / Unclassified',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context(['Develop marketing campaigns.','Prepare financial statements.'])});
 assert.equal(result.primaryFunction,'other');assert.equal(result.reviewRequired,true);
});

test('skills provide a fallback for an unrecognized title',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context([],['Machine learning','Statistical modeling'])});
 assert.equal(result.primaryFunction,'data');assert.equal(result.basis,'required skills');
});

test('function evidence validation continues to reject malformed context',()=>{
 assert.equal(validFunctionContext(context(['Build predictive models.'],['Python'])),true);
 assert.equal(validFunctionContext({version:2,duties:[],requiredSkills:['x'.repeat(501)],preferredSkills:[],category:''}),false);
});

test('a single persisted primary function remains filterable by stable job ID',()=>{
 const job={id:'saved-job-id',title:'Sales Analyst',companyName:'Example',companyId:'example',industry:'Technology',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'hybrid',remoteScope:'unknown',eligibleStates:[],locations:[{city:'Austin',state:'Texas'}],employmentType:'Full-time',travelRequired:null,primaryJobFunction:'data'};
 assert.equal(filterJobs([job],readJobFilters('?function=data'),'2026-11-17').length,1);
 assert.equal(filterJobs([job],readJobFilters('?function=sales'),'2026-11-17').length,0);
 assert.equal(job.id,'saved-job-id');
});
