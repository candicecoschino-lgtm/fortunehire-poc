import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {jobFunctionResult,isValidJobFunction} from '../public/job-functions.js';

const jobs=JSON.parse(readFileSync(new URL('../public/data/jobs.json',import.meta.url),'utf8')).jobs;
const lines=readFileSync(new URL('../outputs/job-function-audit/final-independent-validation/sample.csv',import.meta.url),'utf8').trim().split(/\r?\n/);
function parseCsv(line){const cells=[];let value='',quoted=false;for(let i=0;i<line.length;i++){const char=line[i];if(char==='"'&&quoted&&line[i+1]==='"'){value+='"';i++;}else if(char==='"')quoted=!quoted;else if(char===','&&!quoted){cells.push(value);value='';}else value+=char;}cells.push(value);return cells;}
const headers=parseCsv(lines[0]);
const sample=lines.slice(1).map(line=>Object.fromEntries(parseCsv(line).map((value,index)=>[headers[index],value])));

test('previously reviewed cases remain a development regression set, not a held-out accuracy claim',()=>{
 assert.equal(sample.length,150);const byId=new Map(jobs.map(job=>[job.id,job]));let active=0, historicalOnly=0;
 for(const row of sample){
  const job=byId.get(row.jobId);
  // The fixture is historical; listings may legitimately close or leave the active feed.
  // Reconstruct the classifier input from the saved adjudication evidence when absent.
  const evidenceJob=job||{id:row.jobId,title:row.title,functionContext:{duties:row.duties?row.duties.split(' | '):[],requiredSkills:row.skills?row.skills.split(' | '):[]}};
  if(job)active++;else historicalOnly++;
  const first=jobFunctionResult(evidenceJob),second=jobFunctionResult(evidenceJob);
  assert.ok(isValidJobFunction(first.primaryFunction),row.jobId);
  assert.deepEqual(first,second,`classification changed for identical evidence: ${row.jobId}`);
 }
 assert.equal(active+historicalOnly,150);
});
