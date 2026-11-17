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
 assert.deepEqual(paySummary(job),{text:'$90,000\u2013$140,000 / year',detail:true,note:''});
 assert.equal(job.publishedPay.text,text);
 assert.equal(paySummary({salary:null,publishedPay:null}).text,'Pay information unavailable');
});
test('a pay range never appears as applicable outside its published state scope',()=>{
 const job={salary:{min:90000,max:100000,currency:'USD',period:'year',scopeStates:['California']}};
 assert.equal(paySummary(job,'Florida').text,'Pay unavailable for this state');
 assert.equal(paySummary(job,'California').text,'$90,000\u2013$100,000 / year');
 assert.equal(paySummary(job).note,'');
});

test('projected starting-range boilerplate becomes only the stated range without guessing a period',()=>{
 const text='The starting salary range posted for this position is $77,300.00 to $97,900.00 and reflects the projected salary range for new hires in this position in U.S. and/or Canada locations, not including incentive compensation, equity, or benefits.';
 const job={salary:null,publishedPay:{text,scopeStates:['California']}};
 assert.deepEqual(paySummary(job),{text:'$77,300\u2013$97,900',detail:true,note:''});
 assert.equal(job.publishedPay.text,text);
});

test('distinct published ranges stay separate rather than inventing a combined range',()=>{
 const job={publishedPay:{text:'Salary range for this position is $208,180 - $278,460 / year | Pay range for those locations is $228,970 - $306,250 per year.',scopeStates:[]}};
 assert.equal(paySummary(job).text,'$208,180\u2013$278,460 / year · $228,970\u2013$306,250 / year');
});

test('duplicate text does not repeat a range and hourly cents remain intact',()=>{
 const text='Hourly pay range is $21.50 - $27.34 | Hourly pay range is $21.50 - $27.34';
 assert.equal(paySummary({publishedPay:{text,scopeStates:[]}}).text,'$21.50\u2013$27.34 / hour');
 assert.equal(paySummary({salary:{min:21.5,max:21.5,period:'hour',scopeStates:[]}}).text,'$21.50 / hour');
});

test('text without a clear range links to details without placing prose or a guessed amount in the header',()=>{
 for(const text of ['Competitive salary, subject to experience.','Total target compensation is $81,585 including salary and commission.','Salary range is $90k-$120k.']){
  assert.deepEqual(paySummary({publishedPay:{text,scopeStates:[]}}),{text:'See pay details',detail:true,note:''});
 }
});
