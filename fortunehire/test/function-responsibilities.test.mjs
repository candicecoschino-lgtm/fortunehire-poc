import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_FUNCTIONS,jobFunctionResult} from '../public/job-functions.js';
import {filterJobs,readJobFilters} from '../public/jobs.js';
import {validFunctionContext} from '../public/function-duties.js';

const context=(duties=[],requiredSkills=[],category='')=>({version:2,duties,requiredSkills,preferredSkills:[],category});
test('role responsibilities beat incidental department and title vocabulary',()=>{
 const result=jobFunctionResult({title:'Sales Operations Analyst',functionContext:context([
  'Build data models and develop predictive analytics for account forecasting.',
  'Validate statistical results using machine learning methods.'
 ],['Python','SQL'],'Sales')});
 assert.equal(result.primaryFunction,'data');assert.equal(result.basis,'responsibilities');
});

test('each taxonomy function has bounded responsibility evidence coverage',()=>{
 const examples={admin:'Coordinate executive calendars and schedule appointments.',business:'Analyze business requirements and document business processes.',communications:'Prepare press releases and manage media relations.',service:'Resolve customer inquiries and service issues.',success:'Improve customer adoption and manage account renewals.',data:'Build predictive statistical models and validate datasets.',creative:'Design visual assets and create user experiences.',engineering:'Design mechanical systems and prepare engineering drawings.',finance:'Prepare financial statements and reconcile accounts payable.',hospitality:'Prepare meals and serve food to guests.',healthcareAdmin:'Coordinate patient access and manage clinical operations.',healthcare:'Provide patient care and assess treatment plans.',hr:'Recruit candidates and administer employee benefits.',it:'Administer cloud infrastructure and maintain computer networks.',legal:'Draft legal contracts and conduct compliance investigations.',manufacturing:'Operate production equipment and assemble components.',marketing:'Develop marketing campaigns and manage brand strategy.',operations:'Improve facility operations and manage daily operational processes.',product:'Prioritize product roadmaps and define product requirements.',projects:'Manage project plans and coordinate project timelines.',procurement:'Select vendors and manage purchasing plans.',quality:'Conduct safety inspections and implement quality assurance programs.',research:'Conduct laboratory experiments and interpret research results.',retail:'Stock store shelves and manage retail displays.',sales:'Close new sales and grow the sales pipeline.',software:'Develop software and write application code.',logistics:'Coordinate supply shipments and manage inventory.',trades:'Repair electrical systems and install HVAC equipment.',cyber:'Investigate security incidents and mitigate cyber threats.'};
 for(const key of Object.keys(JOB_FUNCTIONS).filter(key=>key!=='other')){
  const duty=examples[key];assert.ok(duty,`Missing example for ${key}`);
  const result=jobFunctionResult({title:'Specialist',functionContext:context([duty])});
  assert.equal(result.primaryFunction,key,duty);assert.equal(result.reviewRequired,false,duty);
 }
});

test('ambiguous evidence stays in Other while a clear skill set resolves when duties do not',()=>{
 const mixed=jobFunctionResult({title:'Specialist',functionContext:context(['Develop marketing campaigns.','Prepare financial statements.'])});
 assert.equal(mixed.primaryFunction,'other');assert.equal(mixed.reviewRequired,true);
 const skillOverride=jobFunctionResult({title:'Marketing Analyst',functionContext:context(['Develop marketing campaigns.','Prepare financial statements.'],['Machine learning','Statistical modeling','Python'])});
 assert.equal(skillOverride.primaryFunction,'other');assert.equal(skillOverride.basis,'responsibilities');
 const skills=jobFunctionResult({title:'Specialist',functionContext:context([],['Machine learning','Statistical modeling','Python'])});
 assert.equal(skills.primaryFunction,'data');assert.equal(skills.basis,'required skills');
});

test('job function validation accepts current context and rejects malformed evidence',()=>{
 assert.equal(validFunctionContext(context(['Build predictive models.'],['Python'])),true);
 assert.equal(validFunctionContext({version:2,duties:[],requiredSkills:['x'.repeat(501)],preferredSkills:[],category:''}),false);
});

test('job filter reads the persisted single function while saving and applying references by stable ID',()=>{
 const job={id:'saved-job-id',title:'Sales Analyst',companyName:'Example',companyId:'example',industry:'Technology',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'hybrid',remoteScope:'unknown',eligibleStates:[],locations:[{city:'Austin',state:'Texas'}],employmentType:'Full-time',travelRequired:null,primaryJobFunction:'data'};
 assert.equal(filterJobs([job],readJobFilters('?function=data'),'2026-11-17').length,1);
 assert.equal(filterJobs([job],readJobFilters('?function=sales'),'2026-11-17').length,0);
 assert.equal(job.id,'saved-job-id');
});
