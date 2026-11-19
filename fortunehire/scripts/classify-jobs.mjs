import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {jobFunctionResult,isValidJobFunction} from '../public/job-functions.js';

const defaultRoot=resolve(fileURLToPath(new URL('..',import.meta.url)));
const rootArg=process.argv.indexOf('--root');
const root=resolve(rootArg>=0?process.argv[rootArg+1]:defaultRoot);
const path=resolve(root,'public/data/jobs.json');
const data=JSON.parse(await readFile(path,'utf8'));
for(const job of data.jobs){
  const result=jobFunctionResult(job);
  if(!isValidJobFunction(result.primaryFunction))throw Error(`No valid primary function for ${job.id}`);
  job.primaryJobFunction=result.primaryFunction;
  job.jobFunctionBasis=result.basis;
  job.jobFunctionConfidence=result.confidence;
  job.jobFunctionReviewRequired=result.reviewRequired;
  job.jobFunctionEvidence=result.evidence.slice(0,4);
}
data.schemaVersion=2;
if(process.argv.includes('--write'))await writeFile(path,JSON.stringify(data,null,2)+'\n');
console.log(`Classified ${data.jobs.length} jobs with exactly one primary function.`);
