import test from 'node:test';
import assert from 'node:assert/strict';
import {JOB_FUNCTIONS,JOB_FUNCTION_OPTIONS,jobFunctionResult,classifyJobFunctions} from '../public/job-functions.js';
import {filterJobs,readJobFilters,validateJobs} from '../public/jobs.js';

const context=(duties=[],requiredSkills=[],category='')=>({version:2,duties,requiredSkills,preferredSkills:[],category});
const job=(title,fn,extra={})=>({id:'test-job',title,companyId:'example',companyName:'Example',industry:'Technology',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'on-site',remoteScope:'unknown',eligibleStates:[],locations:[{city:'Austin',state:'Texas'}],employmentType:'Full-time',travelRequired:null,primaryJobFunction:fn,...extra});

test('taxonomy is a practical candidate-facing list with alphabetized labels',()=>{
 const labels=JOB_FUNCTION_OPTIONS.map(([,label])=>label);
 assert.ok(labels.length>=25&&labels.length<=32);
 assert.deepEqual(labels.slice().sort((a,b)=>a.localeCompare(b)),labels);
 assert.ok(Object.entries(JOB_FUNCTIONS).some(([key,label])=>key==='data'&&label==='Data & Analytics'));
});

test('responsibilities outrank title and employer department for a cross-functional role',()=>{
 const result=jobFunctionResult({title:'Data Scientist, Marketing',functionContext:context([
  'Build statistical models and predictive analytics for campaign performance.',
  'Develop machine learning models and validate experimental results.'
 ],['Python','SQL'],'Marketing')});
 assert.equal(result.primaryFunction,'data');
 assert.equal(result.basis,'responsibilities');
 assert.equal(result.confidence,'high');
 assert.equal(result.reviewRequired,false);
 assert.deepEqual(classifyJobFunctions({title:'Data Scientist, Marketing'}),['data']);
});

test('one clear responsibility function always produces one valid primary function',()=>{
 const examples={sales:'Close new deals and meet quarterly revenue targets.',marketing:'Develop marketing campaigns and measure demand generation.',hr:'Recruit candidates and manage employee relations.',it:'Administer cloud infrastructure and troubleshoot network services.',service:'Resolve customer inquiries and service complaints.',admin:'Schedule executive calendars and coordinate travel arrangements.',legal:'Review commercial agreements and provide legal advice.',finance:'Prepare financial statements and process payroll.',engineering:'Design electrical systems and validate hardware drawings.',healthcare:'Provide direct clinical care and assess patients.',logistics:'Coordinate shipments and optimize inventory operations.',manufacturing:'Operate production equipment and assemble products.',research:'Conduct laboratory experiments and analyze research results.',projects:'Manage project timelines and project budgets.',business:'Analyze business requirements and document business processes.',retail:'Replenish store shelves and manage retail displays.',hospitality:'Prepare meals and serve food to guests.',quality:'Conduct safety inspections and implement quality assurance programs.',procurement:'Select vendors and manage purchase orders.'};
 for(const [fn,duty] of Object.entries(examples)){
  const result=jobFunctionResult({title:'Specialist',functionContext:context([duty])});
  assert.equal(result.primaryFunction,fn,duty);
  assert.equal(classifyJobFunctions({title:'Specialist',functionContext:context([duty])}).length,1,duty);
 }
});

test('ambiguous responsibility evidence resolves to Other and is flagged',()=>{
 const result=jobFunctionResult({title:'Specialist',functionContext:context([
  'Develop marketing campaigns for customers.',
  'Prepare financial reports and analyze budgets.'
 ])});
 assert.equal(result.primaryFunction,'other');
 assert.equal(result.confidence,'low');
 assert.equal(result.reviewRequired,true);
});

test('skills are the next fallback; insufficient skills defer to an unambiguous title',()=>{
 assert.equal(jobFunctionResult({title:'Specialist',functionContext:context([],['Machine learning','Statistical modeling','Python'])}).primaryFunction,'data');
 assert.equal(jobFunctionResult({title:'Software Engineer',functionContext:context([],['Detail oriented'])}).primaryFunction,'software');
 const unclear=jobFunctionResult({title:'Specialist',functionContext:context([],['Detail oriented'])});
 assert.equal(unclear.primaryFunction,'other');assert.equal(unclear.reviewRequired,true);
});

test('employer category is only a fallback and does not override conflicting title evidence',()=>{
 const clear=jobFunctionResult({title:'Registered Nurse',functionContext:context([],[],'Marketing')});
 assert.equal(clear.primaryFunction,'healthcare');assert.equal(clear.basis,'job title');
 const conflict=jobFunctionResult({title:'Sales Operations Analyst',functionContext:context([],[],'Sales')});
 assert.equal(conflict.primaryFunction,'other');assert.equal(conflict.reviewRequired,true);
 const category=jobFunctionResult({title:'Specialist',functionContext:context([],[],'Human Resources')});
 assert.equal(category.primaryFunction,'hr');assert.equal(category.basis,'employer category');assert.equal(category.reviewRequired,true);
});

test('missing descriptions only use clear title fallback or flagged Other',()=>{
 assert.equal(jobFunctionResult({title:'Data Analyst'}).primaryFunction,'data');
 const unclear=jobFunctionResult({title:'Specialist II'});
 assert.equal(unclear.primaryFunction,'other');assert.equal(unclear.reviewRequired,true);
 const evidence={title:'Data Scientist, Marketing',functionContext:context(['Develop predictive analytics and validate statistical models.'],['Python','SQL'],'Marketing')};
 assert.deepEqual(jobFunctionResult(evidence),jobFunctionResult(evidence));
});

test('title fallbacks recognize clear frontline and regulated occupations without forcing generic titles',()=>{
 for(const [title,expected] of [
  ['Retail Sales Consultant','retail'],['Retail Customer Service Associate','retail'],['Meat Clerk','retail'],
  ['Relationship Banker','finance'],['Registered Wealth Management Client Associate','finance'],
  ['Pharmacy Technician','healthcare'],['Home Health Aide','healthcare'],['Software Development Engineer, AWS','software'],
  ['System Integration Lead','it'],['Target Security Specialist','operations'],['Tire & Battery Technician - Automotive','trades']
 ])assert.equal(jobFunctionResult({title}).primaryFunction,expected,title);
 assert.equal(jobFunctionResult({title:'Shift Supervisor'}).primaryFunction,'other');
});

test('filtering uses stored primary function and never includes cross-category duplicates',()=>{
 const dataJob=job('Data Scientist, Marketing','data');
 assert.equal(filterJobs([dataJob],readJobFilters('?function=data'),'2026-11-17').length,1);
 assert.equal(filterJobs([dataJob],readJobFilters('?function=marketing'),'2026-11-17').length,0);
 const legacy={...dataJob};delete legacy.primaryJobFunction;
 assert.equal(filterJobs([legacy],readJobFilters('?function=data'),'2026-11-17').length,0);
});

test('legacy schema upgrade assigns a primary function without changing job identity or saved references',()=>{
 const source=job('Data Scientist, Marketing',undefined);delete source.primaryJobFunction;
 const companies=[{id:'example',name:'Example',industry:'Technology',profileSource:'https://example.com',careerUrl:'https://example.com/careers'}];
 source.url='https://example.com/jobs/1';source.requisitionId='1';source.identifierType='requisition';source.locationNote='Austin, Texas';source.sector='Technology';source.sourceNote='Official posting';source.sourceHash='stable';source.collectionMethod='official';source.arrangementBasis=undefined;
 const normalized=validateJobs({schemaVersion:1,jobs:[source]},companies)[0];
 assert.equal(normalized.id,source.id);assert.equal(normalized.url,source.url);assert.equal(normalized.primaryJobFunction,'data');
 assert.throws(()=>validateJobs({schemaVersion:2,jobs:[{...normalized,primaryJobFunction:['data']}]},companies),/Invalid primary job function/);
});
