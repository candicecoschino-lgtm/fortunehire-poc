import test from 'node:test';
import assert from 'node:assert/strict';
import {SAVED_SEARCH_KEY,MAX_SAVED_SEARCHES,savedQuery,readSavedSearches,saveSearch,removeSearch} from '../public/saved-searches.js';
import {readJobFilters,filterJobs} from '../public/jobs.js';
function memoryStorage(){const data=new Map();return {getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,value)};}

test('saved filters retain every selection and sort while starting on page one',()=>{
 const f=readJobFilters('?q=Analyst&state=New+York&arrangement=remote-state&company=citigroup&industry=Commercial+Banks&function=it&type=Part-time&pay=hour%3A25&posted=7&payPosted=1&view=saved&travel=exclude&sort=title&page=4');
 const restored=readJobFilters(savedQuery(f));assert.deepEqual(restored,{...f,page:'1'});
 assert.equal(savedQuery(savedQuery(f)),savedQuery(f));
 assert.ok(!savedQuery('state=Florida&tracking=unrelated&page=8').includes('tracking'));
});

test('named searches persist and load independently of job data and other storage',()=>{
 const storage=memoryStorage();storage.setItem('unrelated','keep');
 saveSearch(storage,'  Florida IT  ',readJobFilters('?state=Florida&function=it'));
 const loaded=readSavedSearches(storage);assert.deepEqual(loaded,[{name:'Florida IT',query:'state=Florida&function=it'}]);
 assert.equal(storage.getItem('unrelated'),'keep');
 assert.deepEqual(Object.keys(JSON.parse(storage.getItem(SAVED_SEARCH_KEY)).searches[0]).sort(),['name','query']);
});

test('saving an existing name updates it without creating duplicates',()=>{
 const storage=memoryStorage();saveSearch(storage,'Remote roles','arrangement=remote');
 const result=saveSearch(storage,'REMOTE ROLES','arrangement=remote&function=it');
 assert.equal(result.updated,true);assert.equal(result.searches.length,1);
 assert.equal(readSavedSearches(storage)[0].query,'arrangement=remote&function=it');
});

test('removal deletes just the chosen saved search',()=>{
 const storage=memoryStorage();saveSearch(storage,'One','state=Texas');saveSearch(storage,'Two','state=Florida');
 assert.deepEqual(removeSearch(storage,'One'),[{name:'Two',query:'state=Florida'}]);
 assert.deepEqual(readSavedSearches(storage),[{name:'Two',query:'state=Florida'}]);
});

test('malformed, oversized, unsupported and duplicate stored entries are bounded',()=>{
 const storage=memoryStorage();
 for(const raw of ['{broken','null',JSON.stringify({version:2,searches:[]}),JSON.stringify({version:1,searches:{}}),'x'.repeat(64001)]){
  storage.setItem(SAVED_SEARCH_KEY,raw);assert.deepEqual(readSavedSearches(storage),[]);
 }
 storage.setItem(SAVED_SEARCH_KEY,JSON.stringify({version:1,searches:[null,{name:[],query:''},{name:' ',query:''},{name:'Good',query:'function=it&unknown=drop'},{name:'good',query:''},{name:'a'.repeat(61),query:''},{name:'Long query',query:'x'.repeat(4097)}]}));
 assert.deepEqual(readSavedSearches(storage),[{name:'Good',query:'function=it'}]);
});

test('names and limits are enforced while existing names can be updated at capacity',()=>{
 const storage=memoryStorage();
 for(const name of ['', ' ', 'x'.repeat(61)])assert.throws(()=>saveSearch(storage,name,''),/Choose a name/);
 for(let i=0;i<MAX_SAVED_SEARCHES;i++)saveSearch(storage,`Search ${i}`,'');
 assert.throws(()=>saveSearch(storage,'Extra',''),/20 saved searches/);
 assert.equal(saveSearch(storage,'Search 0','function=admin').searches.length,20);
});

test('blocked or full storage reports failure and preserves earlier saved data',()=>{
 const storage=memoryStorage();saveSearch(storage,'Existing','function=it');
 const before=storage.getItem(SAVED_SEARCH_KEY);
 storage.setItem=()=>{throw Error('Quota exceeded');};
 assert.throws(()=>saveSearch(storage,'Another','function=sales'),/Quota/);
 assert.throws(()=>removeSearch(storage,'Existing'),/Quota/);
 assert.equal(storage.getItem(SAVED_SEARCH_KEY),before);
 assert.throws(()=>readSavedSearches({getItem:()=>{throw Error('Storage blocked');}}),/blocked/);
});

test('loading a saved search includes newly received jobs rather than saved results',()=>{
 const storage=memoryStorage();saveSearch(storage,'New IT jobs','function=it&state=Texas');
 const filters=readJobFilters(readSavedSearches(storage)[0].query);
 const newJob={id:'received-later',title:'Application Development Analyst',status:'reviewed',postedAt:'2026-11-17',reviewedAt:'2026-11-17',closesAt:null,arrangement:'on-site',locations:[{city:'Austin',state:'Texas'}],employmentType:'Not specified',travelRequired:null};
 assert.equal(filterJobs([newJob],filters,'2026-11-17').length,1);
 assert.equal(filterJobs([{...newJob,status:'closed'}],filters,'2026-11-17').length,0);
});
