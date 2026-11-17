import test from 'node:test';
import assert from 'node:assert/strict';
import {postedLabel,locationSummary,paySummary} from '../public/job-presentation.js';
test('posting age uses the employer date, including across daylight saving changes',()=>{
 assert.equal(postedLabel('2026-11-17','2026-11-17'),'Posted today');
 assert.equal(postedLabel('2026-11-16','2026-11-17'),'Posted yesterday');
 assert.equal(postedLabel('2026-10-31','2026-11-02'),'Posted 2 days ago');
 assert.equal(postedLabel(null,'2026-11-17'),'Posting date unavailable');
});
test('location summaries prioritize the selected state without inventing remote eligibility',()=>{
 const job={arrangement:'hybrid',locations:[{city:'Seattle',state:'Washington'},{city:'Austin',state:'Texas'}]};
 assert.equal(locationSummary(job,'Texas'),'Austin, Texas + 1 more location');
 assert.equal(locationSummary({...job,arrangement:'remote',remoteScope:'unknown'}),'Remote - eligible states not specified');
 assert.equal(locationSummary({...job,arrangement:'remote',remoteScope:'states',eligibleStates:['Florida','Georgia','Texas']},'Texas'),'Remote in Texas, Florida + 1 more state');
 assert.equal(locationSummary({...job,arrangement:'remote',remoteScope:'nationwide'}),'Remote across the United States');
});
test('unstructured pay is disclosed without guessing a numeric range or dropping qualifications',()=>{
 const text='Annual base salary is $90,000 to $140,000 in the listed locations. The package also includes commission and location-specific terms.';
 const job={salary:null,publishedPay:{text,scopeStates:[]}};
 assert.deepEqual(paySummary(job),{text,detail:true,note:'Employer wording; see full terms'});
 assert.equal(job.publishedPay.text,text);
 assert.equal(paySummary({salary:null,publishedPay:null}).text,'Pay information unavailable');
});
test('a pay range never appears as applicable outside its published state scope',()=>{
 const job={salary:{min:90000,max:100000,currency:'USD',period:'year',scopeStates:['California']}};
 assert.equal(paySummary(job,'Florida').text,'Pay unavailable for this state');
 assert.equal(paySummary(job,'California').text,'$90,000.00\u2013$100,000.00 / year');
 assert.equal(paySummary(job).note,'Location-specific pay; see details');
});
