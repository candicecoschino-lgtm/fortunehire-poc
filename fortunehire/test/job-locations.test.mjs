import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {normalizeCity,zipPrefix,resolveCitySearch,matchingOfficeLocations,locationPayState} from '../public/job-locations.js';
import {STATE_NAMES,US_STATES} from '../public/us-geography.js';
import {filterJobs,readJobFilters,serializeJobFilters} from '../public/jobs.js';
import {locationSummary,paySummary} from '../public/job-presentation.js';
import {savedQuery} from '../public/saved-searches.js';
const today='2026-11-17';
const job={id:'example-1',title:'Analyst',companyName:'Example',companyId:'example',status:'reviewed',postedAt:today,reviewedAt:today,closesAt:null,arrangement:'hybrid',locations:[{city:'Seattle',state:'Washington'},{city:'Austin',state:'Texas'},{city:'Dallas',state:'Texas'}],employmentType:'Full-time',travelRequired:null,salary:null,publishedPay:null};
const shard=code=>JSON.parse(fs.readFileSync(new URL(`../public/data/zip/${code.slice(0,2)}.json`,import.meta.url),'utf8'));

test('city matching normalizes case, accents, common place-name abbreviations, and state qualifiers',()=>{
 assert.equal(normalizeCity('ST. LOUIS'),normalizeCity('Saint Louis'));
 assert.equal(normalizeCity('Ft. Worth'),normalizeCity('Fort Worth'));
 assert.equal(normalizeCity('Mt. Juliet'),normalizeCity('Mount Juliet'));
 assert.equal(normalizeCity('New York City'),normalizeCity('New York'));
 assert.equal(normalizeCity('Cañon City'),'canon city');
 for(const query of ['Austin, TX','Austin TX','Austin, Texas'])assert.deepEqual(resolveCitySearch(query).places,[{city:'Austin',state:'Texas'}]);
 assert.equal(resolveCitySearch('Austin, invalid').status,'invalid');
});

test('real ZIP data preserves leading zeroes and resolves to documented postal cities',()=>{
 for(const [zip,city,state] of [['01803','Burlington','Massachusetts'],['02108','Boston','Massachusetts'],['78701','Austin','Texas'],['10001','New York','New York'],['94105','San Francisco','California']]){
  const result=resolveCitySearch(zip,shard(zip));assert.equal(result.status,'valid');assert.ok(result.places.some(place=>place.city===city&&place.state===state));
 }
 assert.equal(resolveCitySearch('01803-1234',shard('01803')).zip,'01803');assert.equal(zipPrefix('01803'),'01');
});

test('unknown, loading, incomplete, malformed, and failed ZIP lookups never broaden to a whole state',()=>{
 for(const [query,data,status] of [['01803',undefined,'loading'],['01803',null,'unavailable'],['00000',{schemaVersion:1,prefix:'00',places:{}},'not-found'],['0180',undefined,'invalid'],['Remote',undefined,'invalid']])assert.equal(resolveCitySearch(query,data).status,status);
 const invalid={schemaVersion:1,prefix:'01',places:{'01803':[['Fake','__proto__']]}};
 assert.equal(resolveCitySearch('01803',invalid).status,'not-found');
 assert.equal(filterJobs([job],readJobFilters('?city=01803'),today).length,0);
});

test('city/state restrictions match the same location and include later-listed cities',()=>{
 for(const city of ['Austin','Austin, TX','Dallas, Texas'])assert.equal(filterJobs([job],readJobFilters('?city='+encodeURIComponent(city)),today).length,1);
 assert.equal(filterJobs([job],readJobFilters('?city=Austin&state=Washington'),today).length,0);
 assert.equal(filterJobs([job],readJobFilters('?city=Austin%2C+WA'),today).length,0);
 const zip=resolveCitySearch('78701',shard('78701'));
 assert.equal(filterJobs([job],readJobFilters('?city=78701'),today,false,zip).length,1);
 assert.equal(filterJobs([job],readJobFilters('?city=78701&state=Washington'),today,false,zip).length,0);
 assert.equal(filterJobs([job],readJobFilters('?city=Aust'),today).length,0); // Suggestions guide exact cities; no substring geography.
});

test('city search targets on-site/hybrid offices without reinterpreting remote eligibility',()=>{
 for(const arrangement of ['on-site','hybrid'])assert.equal(matchingOfficeLocations({...job,arrangement},resolveCitySearch('Austin')).length,1);
 for(const arrangement of ['remote','unknown'])assert.equal(matchingOfficeLocations({...job,arrangement},resolveCitySearch('Austin')).length,0);
 const remote={...job,arrangement:'remote',remoteScope:'nationwide',eligibleStates:[]};
 assert.equal(filterJobs([remote],readJobFilters('?state=Texas&arrangement=remote'),today).length,1);
 assert.equal(filterJobs([remote],readJobFilters('?city=Austin&arrangement=remote'),today).length,0);
});

test('matched city appears first on cards, even when another city shares its state',()=>{
 const search=resolveCitySearch('Dallas, TX');
 assert.equal(locationSummary(job,'Texas',search),'Dallas, Texas + 2 more locations');
 assert.equal(locationSummary(job,'Washington'),'Seattle, Washington + 2 more locations');
});

test('ZIP and city searches retain pay-state restrictions even when the State select is empty',()=>{
 const j={...job,salary:{min:90000,max:120000,period:'year',currency:'USD',scopeStates:['Washington']}};
 const search=resolveCitySearch('78701',shard('78701'));
 assert.equal(locationPayState(j,search),'Texas');assert.equal(paySummary(j,locationPayState(j,search)).text,'Pay unavailable for this state');
 for(const filter of ['payPosted=1','pay=year:50000'])assert.equal(filterJobs([j],readJobFilters('?city=78701&'+filter),today,false,search).length,0);
 assert.equal(filterJobs([{...j,salary:{...j.salary,scopeStates:['Texas']}}],readJobFilters('?city=78701&payPosted=1'),today,false,search).length,1);
});

test('city/ZIP round-trips through shared links and saved searches, including future and older saved roles',()=>{
 const f=readJobFilters('?city=01803&state=Massachusetts&arrangement=hybrid');assert.equal(f.city,'01803');assert.deepEqual(readJobFilters('?'+serializeJobFilters(f)),f);assert.equal(readJobFilters(savedQuery(f)).city,'01803');
 const future={...job,locations:[{city:'Tempe',state:'Arizona'}]};assert.equal(filterJobs([future],readJobFilters('?city=Tempe%2C+AZ'),today).length,1);
 const old={...job,postedAt:'2026-10-01',organizerUnavailable:true};
 assert.equal(filterJobs([old],readJobFilters('?city=Austin'),today).length,0);assert.equal(filterJobs([old],readJobFilters('?city=Austin&view=saved'),today,true).length,1);
});

test('bundled ZIP shards have complete provenance, valid state codes, and consistent counts',()=>{
 const dir=new URL('../public/data/zip/',import.meta.url),metadata=JSON.parse(fs.readFileSync(new URL('../public/data/zip-source.json',import.meta.url),'utf8'));
 let count=0;
 for(const file of fs.readdirSync(dir)){
  const data=JSON.parse(fs.readFileSync(new URL(file,dir),'utf8'));assert.equal(data.prefix,file.slice(0,2));
  for(const [zip,places] of Object.entries(data.places)){assert.match(zip,/^\d{5}$/);assert.ok(zip.startsWith(data.prefix));assert.ok(places.length>0);for(const [city,state] of places){assert.ok(city.trim());assert.ok(Object.hasOwn(STATE_NAMES,state));}count++;}
 }
 assert.equal(count,metadata.zipCount);assert.equal(metadata.license,'CC BY 4.0');assert.equal(US_STATES.length,51);
});
