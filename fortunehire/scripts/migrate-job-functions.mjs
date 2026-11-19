import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {jobFunctionResult,JOB_FUNCTIONS} from '../public/job-functions.js';

const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const dataPath=resolve(root,'public/data/jobs.json');
const auditPath=resolve(root,'outputs/job-function-audit/enriched-context.json');
const baselinePath=resolve(root,'outputs/job-function-audit/transition/baseline.json');
const outputDir=resolve(root,'outputs/job-function-audit/transition');
const data=JSON.parse(await readFile(dataPath,'utf8'));
const audit=JSON.parse(await readFile(auditPath,'utf8'));
const baseline=JSON.parse(await readFile(baselinePath,'utf8'));
const companies=JSON.parse(await readFile(resolve(root,'public/data/companies.json'),'utf8')).companies;
const companyById=new Map(companies.map(company=>[company.id,company]));
const previous=new Map(baseline.map(row=>[row.jobId,row.functions]));
const oldLabels={sales:'Sales',marketing:'Marketing & Communications',hr:'Human Resources',it:'IT & Software',operations:'Operations',service:'Customer Service',admin:'Administrative',legal:'Legal & Compliance',finance:'Finance & Accounting',engineering:'Engineering & Design',healthcare:'Healthcare & Clinical',logistics:'Supply Chain & Logistics',manufacturing:'Manufacturing & Skilled Trades',research:'Research & Science',projects:'Product, Project & Program Management',business:'Business & Strategy',retail:'Retail & Store Roles',hospitality:'Food & Hospitality',quality:'Quality & Safety',other:'Other / Unclassified'};
const original=data.jobs.map(job=>({id:job.id,url:job.url,postedAt:job.postedAt,reviewedAt:job.reviewedAt,checkedAt:job.checkedAt,closesAt:job.closesAt,status:job.status,sourceHash:job.sourceHash}));
const rows=[];
let contextMatches=0,contextUrlMismatch=0;

for(const job of data.jobs){
  const context=audit.jobs?.[job.id];
  if(context){
    if(context.source?.url===job.url){
      job.functionContext={version:2,duties:(context.responsibilities||[]).slice(0,16),requiredSkills:(context.requiredSkills||[]).slice(0,16),preferredSkills:(context.preferredSkills||[]).slice(0,16),category:String(context.department||context.occupationalCategory||'').slice(0,120)};
      contextMatches++;
    }else contextUrlMismatch++;
  }
  const result=jobFunctionResult(job);
  job.primaryJobFunction=result.primaryFunction;
  job.jobFunctionBasis=result.basis;
  job.jobFunctionConfidence=result.confidence;
  job.jobFunctionReviewRequired=result.reviewRequired;
  job.jobFunctionEvidence=result.evidence.slice(0,4);
  const company=companyById.get(job.companyId);
  rows.push({
    jobId:job.id,employer:company?.name||job.companyId,title:job.title,officialUrl:job.url,
    previousFunction:(previous.get(job.id)||[]).map(key=>oldLabels[key]||key).join(' | '),
    previousPrimary:oldLabels[(previous.get(job.id)||[])[0]]||(previous.get(job.id)||[])[0]||'',
    primaryFunction:job.primaryJobFunction,functionLabel:JOB_FUNCTIONS[job.primaryJobFunction],
    evidenceSource:job.jobFunctionBasis,confidence:job.jobFunctionConfidence,
    reviewRequired:job.jobFunctionReviewRequired?'yes':'no',
    evidence:job.jobFunctionEvidence.join(' | '),
    evidenceAvailability:job.functionContext?.duties?.length?'responsibilities':job.functionContext?.requiredSkills?.length?'required skills':job.jobFunctionBasis==='job title'?'title fallback':'insufficient',
    status:job.status
  });
}

if(new Set(data.jobs.map(job=>job.id)).size!==data.jobs.length)throw Error('Migration found duplicate job IDs');
if(new Set(data.jobs.map(job=>job.url)).size!==data.jobs.length)throw Error('Migration found duplicate job URLs');
const after=new Map(data.jobs.map(job=>[job.id,job]));
for(const prior of original){
  const job=after.get(prior.id);
  if(!job||job.url!==prior.url||['postedAt','reviewedAt','checkedAt','closesAt','status','sourceHash'].some(key=>job[key]!==prior[key]))throw Error(`Migration changed protected posting data: ${prior.id}`);
}
data.schemaVersion=2;

const escape=value=>'"'+String(value??'').replaceAll('"','""')+'"';
const columns=['employer','title','officialUrl','previousFunction','previousPrimary','functionLabel','evidenceSource','confidence','reviewRequired','evidence','evidenceAvailability','status'];
const csv=[columns.join(','),...rows.map(row=>columns.map(key=>escape(row[key])).join(','))].join('\n')+'\n';
const reviewRows=rows.filter(row=>row.reviewRequired==='yes');
const sample=[];
for(const key of Object.keys(JOB_FUNCTIONS)){
  const group=rows.filter(row=>row.primaryFunction===key).sort((a,b)=>a.employer.localeCompare(b.employer)||a.jobId.localeCompare(b.jobId));
  const employersSeen=new Set();
  for(const row of group){if(employersSeen.has(row.employer))continue;sample.push(row);employersSeen.add(row.employer);if(employersSeen.size===3)break;}
}
for(const row of reviewRows){if(sample.length>=150)break;if(!sample.some(item=>item.jobId===row.jobId))sample.push(row);}
const counts=Object.fromEntries(Object.keys(JOB_FUNCTIONS).map(key=>[JOB_FUNCTIONS[key],rows.filter(row=>row.primaryFunction===key).length]).filter(([,count])=>count));
const originalCounts={};
for(const row of baseline)for(const key of new Set(row.functions||[])){const label=oldLabels[key]||key;originalCounts[label]=(originalCounts[label]||0)+1;}
const unchangedEquivalent=rows.filter(row=>(previous.get(row.jobId)||[]).includes(row.primaryFunction)).length;
const summary={generatedAt:new Date().toISOString(),jobs:rows.length,classifiedExactlyOnce:rows.filter(row=>Object.hasOwn(JOB_FUNCTIONS,row.primaryFunction)).length,reviewRequired:reviewRows.length,contextMatches,contextUrlMismatch,auditContextsAvailable:Object.keys(audit.jobs||{}).length,confidence:Object.fromEntries(['high','medium','low'].map(level=>[level,rows.filter(row=>row.confidence===level).length])),classificationBasisCounts:Object.fromEntries([...new Set(rows.map(row=>row.evidenceSource))].map(basis=>[basis,rows.filter(row=>row.evidenceSource===basis).length])),originalFunctionCounts:originalCounts,primaryFunctionCounts:counts,comparison:{unchangedEquivalent,changed:rows.length-unchangedEquivalent,previouslyMultiFunction:baseline.filter(row=>(row.functions||[]).length>1).length},sampleSize:sample.length,manualAccuracy:'Not measured; sample is provided for human review.'};
const sampleColumns=[...columns,'manualReview','reviewedPrimaryFunction','reviewerNotes'];
await mkdir(outputDir,{recursive:true});
await writeFile(dataPath,JSON.stringify(data,null,2)+'\n');
await Promise.all([
  writeFile(resolve(outputDir,'before-after.csv'),csv),
  writeFile(resolve(outputDir,'review-required.csv'),[columns.join(','),...reviewRows.map(row=>columns.map(key=>escape(row[key])).join(','))].join('\n')+'\n'),
  writeFile(resolve(outputDir,'manual-review-sample.csv'),[sampleColumns.join(','),...sample.map(row=>[...columns.map(key=>escape(row[key])),'','',''].join(','))].join('\n')+'\n'),
  writeFile(resolve(outputDir,'summary.json'),JSON.stringify(summary,null,2)+'\n'),
  writeFile(resolve(outputDir,'README.md'),`# Job function reclassification\n\nGenerated ${summary.generatedAt}. All ${summary.jobs} postings received exactly one primary function. Existing IDs, official URLs, dates, status, and source hashes were checked and preserved.\n\n${summary.contextMatches} audit description contexts matched existing job IDs and official URLs. Other jobs use the documented title fallback or remain Other / Unclassified and flagged for review. No descriptions were fetched during migration.\n\nThe deterministic sample spans the proposed functions and employers. Use the blank manualReview, reviewedPrimaryFunction, and reviewerNotes columns to record a human check. Accuracy has not been measured and no 90% result is claimed.\n`)
]);
console.log(JSON.stringify(summary,null,2));
