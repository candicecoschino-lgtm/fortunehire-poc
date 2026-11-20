import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {jobFunctionResult,isValidJobFunction} from '../public/job-functions.js';

const defaultRoot=resolve(fileURLToPath(new URL('..',import.meta.url)));
const rootArg=process.argv.indexOf('--root');
const root=resolve(rootArg>=0?process.argv[rootArg+1]:defaultRoot);
const path=resolve(root,'public/data/jobs.json');
const data=JSON.parse(await readFile(path,'utf8'));
const before=data.jobs.map(job=>({
  id:job.id,url:job.url,postedAt:job.postedAt,reviewedAt:job.reviewedAt,
  checkedAt:job.checkedAt,closesAt:job.closesAt,status:job.status,
  sourceHash:job.sourceHash,primaryJobFunction:job.primaryJobFunction
}));
const rows=[];
for(const job of data.jobs){
  const result=jobFunctionResult(job);
  if(!isValidJobFunction(result.primaryFunction))throw Error(`No valid primary function for ${job.id}`);
  rows.push({id:job.id,url:job.url,oldFunction:job.primaryJobFunction||'',newFunction:result.primaryFunction,basis:result.basis,confidence:result.confidence,reviewRequired:result.reviewRequired,evidence:result.evidence.slice(0,4).join(' | ')});
  job.primaryJobFunction=result.primaryFunction;
  job.jobFunctionBasis=result.basis;
  job.jobFunctionConfidence=result.confidence;
  job.jobFunctionReviewRequired=result.reviewRequired;
  job.jobFunctionEvidence=result.evidence.slice(0,4);
}
data.schemaVersion=2;
if(process.argv.includes('--write')){
  if(new Set(data.jobs.map(job=>job.id)).size!==data.jobs.length)throw Error('Classification found duplicate job IDs');
  if(new Set(data.jobs.map(job=>job.url)).size!==data.jobs.length)throw Error('Classification found duplicate job URLs');
  const after=new Map(data.jobs.map(job=>[job.id,job]));
  for(const old of before){
    const current=after.get(old.id);
    if(!current||current.url!==old.url||['postedAt','reviewedAt','checkedAt','closesAt','status','sourceHash'].some(key=>current[key]!==old[key]))throw Error(`Classification changed protected posting data: ${old.id}`);
  }
  await writeFile(path,JSON.stringify(data,null,2)+'\n');
  const outputDir=resolve(root,'outputs/job-function-audit/post-correction');
  await mkdir(outputDir,{recursive:true});
  const escape=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const columns=['id','url','oldFunction','newFunction','basis','confidence','reviewRequired','evidence'];
  const csv=[columns.join(','),...rows.map(row=>columns.map(key=>escape(row[key])).join(','))].join('\n')+'\n';
  const counts=values=>Object.fromEntries([...new Set(values)].sort().map(key=>[key,values.filter(value=>value===key).length]));
  const summary={generatedAt:new Date().toISOString(),jobs:data.jobs.length,changed:rows.filter(row=>row.oldFunction!==row.newFunction).length,oldOther:before.filter(row=>row.primaryJobFunction==='other').length,newOther:rows.filter(row=>row.newFunction==='other').length,reviewRequired:rows.filter(row=>row.reviewRequired).length,oldCounts:counts(before.map(row=>row.primaryJobFunction||'missing')),newCounts:counts(rows.map(row=>row.newFunction)),protectedPostingFieldsPreserved:true,stableIDsAndURLsPreserved:true};
  await Promise.all([
    writeFile(resolve(outputDir,'reclassification.csv'),csv),
    writeFile(resolve(outputDir,'summary.json'),JSON.stringify(summary,null,2)+'\n')
  ]);
  console.log(JSON.stringify(summary,null,2));
}
console.log(`Classified ${data.jobs.length} jobs with exactly one primary function.`);
