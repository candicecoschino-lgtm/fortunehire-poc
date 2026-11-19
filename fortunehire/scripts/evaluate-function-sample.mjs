import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { jobFunctionResult, JOB_FUNCTIONS } from '../public/job-functions.js';

const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const outputDir=resolve(root,'outputs/job-function-audit/transition');
const csv=await readFile(resolve(outputDir,'manual-review-sample.csv'),'utf8');
const data=JSON.parse(await readFile(resolve(root,'public/data/jobs.json'),'utf8'));
const companies=JSON.parse(await readFile(resolve(root,'public/data/companies.json'),'utf8')).companies;
const companyById=new Map(companies.map(row=>[row.id,row.name]));

// Independent human judgments recorded from the sample's captured duty/skill
// evidence. Null means reasonable reviewers could not choose one function.
const expected={
  1:'admin',2:'logistics',4:'projects',5:'engineering',7:'engineering',8:'communications',10:null,
  12:'healthcare',16:'software',18:'data',21:'creative',22:'engineering',23:'engineering',24:'software',
  26:'finance',28:'hospitality',31:'healthcareAdmin',32:'healthcareAdmin',34:null,35:null,36:'quality',
  37:'manufacturing',38:'hr',39:'admin',40:'it',41:'it',44:'legal',48:'trades',50:'marketing',
  51:'marketing',54:'operations',55:'product',57:'engineering',58:'projects',61:'quality',62:'procurement',
  63:'procurement',64:'quality',65:'quality',66:'logistics',68:'engineering',69:null,71:'business',73:'sales',
  74:'service',76:'software',77:'software',78:'product',80:'logistics',81:'projects',83:'trades',84:'trades',
  85:'engineering',86:'cyber',87:'projects',89:'it',91:'legal',92:'sales',95:null,97:'sales',99:'trades',
  100:'healthcare',101:'logistics',102:'engineering',104:'operations',105:'engineering',107:'engineering',
  109:'operations',110:'operations',111:'projects',112:'finance',113:'operations',114:'sales',115:null,
  116:'operations',117:null,118:'operations',119:'engineering',120:'engineering',121:null,122:'operations',
  123:'software',128:'sales',131:'product',132:'software',133:'software',134:'software',135:'software',
  136:'software',137:'software',138:'sales',141:'sales',142:'sales',143:'sales',144:'sales',145:'sales',
  146:'sales',147:'projects',148:'sales',150:'finance'
};
const labelToKey=new Map(Object.entries(JOB_FUNCTIONS).map(([key,label])=>[label,key]));
function parseCsv(text){
  const rows=[];let row=[],field='',quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(quoted){if(c==='"'&&text[i+1]==='"'){field+='"';i++;}else if(c==='"')quoted=false;else field+=c;}
    else if(c==='"')quoted=true;
    else if(c===','){row.push(field);field='';}
    else if(c==='\n'){row.push(field);rows.push(row);row=[];field='';}
    else if(c!=='\r')field+=c;
  }
  if(field||row.length){row.push(field);rows.push(row);}
  const [headers,...records]=rows;
  return records.map(record=>Object.fromEntries(headers.map((header,index)=>[header,record[index]??''])));
}

const sample=parseCsv(csv);
const jobByUrl=new Map(data.jobs.map(job=>[job.url,job]));
const rows=sample.map((prior,index)=>{
  const sampleRow=index+1;
  const key=expected[sampleRow];
  const current=jobByUrl.get(prior.officialUrl);
  if(!current)throw new Error(`Sample URL no longer maps to an active record: ${prior.officialUrl}`);
  const result=jobFunctionResult(current);
  return {
    sampleRow,employer:companyById.get(current.companyId)||current.companyId,title:current.title,
    priorFunction:labelToKey.get(prior.functionLabel)||prior.functionLabel,
    updatedFunction:result.primaryFunction,expectedFunction:key??'',adjudicable:key!==undefined&&key!==null,
    confidence:result.confidence,reviewRequired:result.reviewRequired,
    sampleEvidenceAvailability:prior.evidenceAvailability,
    evidence:result.evidence.join(' | '),independentEvidence:current.functionContext?.duties?.join(' | ')||current.functionContext?.requiredSkills?.join(' | ')||prior.evidence||''
  };
});
const reviewed=rows.filter(row=>row.adjudicable);
const unresolved=rows.filter(row=>!row.adjudicable);
const previousCorrect=reviewed.filter(row=>row.priorFunction===row.expectedFunction).length;
const updatedCorrect=reviewed.filter(row=>row.updatedFunction===row.expectedFunction).length;
const summary={sampleSize:rows.length,adjudicableCases:reviewed.length,unresolvedCases:unresolved.length,
  prior:{correct:previousCorrect,accuracy:previousCorrect/reviewed.length},
  updated:{correct:updatedCorrect,accuracy:updatedCorrect/reviewed.length},
  changedCategories:rows.filter(row=>row.priorFunction!==row.updatedFunction).length,
  ambiguousWithDutyOrSkillEvidence:unresolved.filter(row=>['responsibilities','required skills'].includes(row.sampleEvidenceAvailability)).length,
  unresolvedWithoutDutyOrSkillEvidence:unresolved.filter(row=>row.sampleEvidenceAvailability==='title fallback').length,
  sampleTitleFallbackCount:rows.filter(row=>row.sampleEvidenceAvailability==='title fallback').length,
  updatedOther:rows.filter(row=>row.updatedFunction==='other').length,
  evaluationType:'In-sample review after tuning rules against this same review cohort; this is not an independent holdout estimate.',
  limitation:'Expected functions are human judgments from the captured duty/skill excerpts. The sample is stratified, several roles repeat, and 50 records lack usable duty/skill evidence; results should not be generalized to all postings.'};
const esc=value=>'"'+String(value??'').replaceAll('"','""')+'"';
const columns=['sampleRow','employer','title','priorFunction','updatedFunction','expectedFunction','adjudicable','confidence','reviewRequired','sampleEvidenceAvailability','independentEvidence','evidence'];
await writeFile(resolve(outputDir,'review-sample-comparison.csv'),[columns.join(','),...rows.map(row=>columns.map(key=>esc(row[key])).join(','))].join('\n')+'\n');
await writeFile(resolve(outputDir,'review-sample-summary.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));
