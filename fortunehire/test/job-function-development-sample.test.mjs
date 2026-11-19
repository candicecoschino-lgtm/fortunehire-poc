import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {jobFunctionResult,isValidJobFunction} from '../public/job-functions.js';

const jobs=JSON.parse(readFileSync(new URL('../public/data/jobs.json',import.meta.url),'utf8')).jobs;
const lines=readFileSync(new URL('../outputs/job-function-audit/final-independent-validation/sample.csv',import.meta.url),'utf8').trim().split(/\r?\n/);
function parseCsv(line){
  const cells=[];let value='',quoted=false;
  for(let i=0;i<line.length;i++){
    const char=line[i];
    if(char==='"'&&quoted&&line[i+1]==='"'){value+='"';i++;}
    else if(char==='"')quoted=!quoted;
    else if(char===','&&!quoted){cells.push(value);value='';}
    else value+=char;
  }
  cells.push(value);return cells;
}
const headers=parseCsv(lines[0]);
const sample=lines.slice(1).map(line=>Object.fromEntries(parseCsv(line).map((value,index)=>[headers[index],value])));

test('the previous independent sample remains a development regression set, not a holdout',()=>{
  assert.equal(sample.length,150);
  const byId=new Map(jobs.map(job=>[job.id,job]));
  let judged=0,correct=0;
  for(const row of sample){
    const job=byId.get(row.jobId);
    assert.ok(job,`missing development record ${row.jobId}`);
    const result=jobFunctionResult(job);
    assert.ok(isValidJobFunction(result.primaryFunction),row.jobId);
    assert.equal(result.primaryFunction.length>0,true,row.jobId);
    if(row.adjudication==='correct'||row.adjudication==='incorrect'){
      judged++;
      if(result.primaryFunction===row.independentFunction)correct++;
    }
  }
  assert.equal(judged,96);
  assert.ok(correct/judged>=0.9,`development accuracy ${(correct/judged*100).toFixed(1)}% fell below 90%`);
});
