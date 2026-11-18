import test from 'node:test';
import assert from 'node:assert/strict';
import {applyRemoteTerritory} from '../public/remote-territory.js';
import {filterJobs,readJobFilters,validateJobs} from '../public/jobs.js';
import {locationSummary} from '../public/job-presentation.js';
import fs from 'node:fs';
const today='2026-11-18';
const base={id:'humana-synthetic',companyId:'humana',title:'Medicare Field Sales-San Diego, CA',arrangement:'remote',remoteScope:'unknown',eligibleStates:[],locations:[{city:'San Diego',state:'California'},{city:'Carlsbad',state:'California'}],status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',companyName:'Humana'};
test('title territory adds a disclosed state restriction without changing arrangement or dates',()=>{
 for(const title of ['Medicare Field Sales-San Diego, CA','Medicare Field Sales-San Diego CA','Care Coordinator - San Diego, CA']){
  const job=applyRemoteTerritory({...base,title});
  assert.equal(job.remoteScope,'states');assert.deepEqual(job.eligibleStates,['California']);assert.equal(job.arrangement,'remote');
  assert.equal(job.postedAt,base.postedAt);assert.equal(job.reviewedAt,base.reviewedAt);assert.match(job.locationNote,/inferred/);
  assert.equal(locationSummary(job),'Remote in California (from title)');
  assert.equal(filterJobs([job],readJobFilters('?state=California&arrangement=remote-state'),today).length,1);
  assert.equal(filterJobs([job],readJobFilters('?state=Michigan&arrangement=remote'),today).length,0);
 }
 assert.equal(base.remoteScope,'unknown');assert.deepEqual(base.eligibleStates,[]);
});
test('regional field-sales titles use all listed states, including later locations, without guessing a state from the territory name',()=>{
 const job=applyRemoteTerritory({...base,title:'Medicare Field Sales-Kansas City',locations:[{city:'Kansas City',state:'Missouri'},{city:'Olathe',state:'Kansas'}]});
 assert.deepEqual(job.eligibleStates,['Kansas','Missouri']);
 assert.deepEqual(applyRemoteTerritory({...base,title:'Medicare Field Sales-Washington',locations:[{city:'St. George',state:'Utah'}]}).eligibleStates,['Utah']);
});
test('explicit eligibility, nonremote roles and unqualified titles are preserved',()=>{
 for(const patch of [{remoteScope:'nationwide'},{remoteScope:'states',eligibleStates:['Texas']},{arrangement:'hybrid'},{arrangement:'on-site'},{companyId:'other'},{title:'Senior DevOps Platform Engineer'},{title:'Medicare Field Sales-Nationwide'},{title:'Medicare Field Sales-Remote'},{locations:[]}]){
  const job={...base,...patch};assert.equal(applyRemoteTerritory(job),job,JSON.stringify(patch));
 }
});
test('publication validation applies the policy to existing and future records without a manual ID list',()=>{
 const data=JSON.parse(fs.readFileSync(new URL('../public/data/jobs.json',import.meta.url),'utf8'));
 const companies=JSON.parse(fs.readFileSync(new URL('../public/data/companies.json',import.meta.url),'utf8')).companies;
 const sample=data.jobs.find(j=>j.companyId==='humana');assert.ok(sample);
 const synthetic={...sample,id:'humana-synthetic-new-role',title:base.title,locations:base.locations,arrangement:'remote',remoteScope:'unknown',eligibleStates:[]};
 delete synthetic.arrangementBasis;delete synthetic.arrangementNote;
 const [job]=validateJobs({schemaVersion:1,jobs:[synthetic]},companies);
 assert.ok(job);assert.equal(job.remoteScope,'states');assert.deepEqual(job.eligibleStates,['California']);
 assert.equal(applyRemoteTerritory(job),job);
});
