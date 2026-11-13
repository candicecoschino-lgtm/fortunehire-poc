import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {filterCompanies, normalize, readFilters, serializeFilters, validateData} from '../public/directory.js';
const data=JSON.parse(await readFile(new URL('../public/data/companies.json',import.meta.url),'utf8'));
test('production records have complete provenance, safe URLs and unique identifiers',()=>{
  assert.equal(validateData(data),data);
  assert.equal(data.companies.length,52);
  for(const c of data.companies){assert.equal(new URL(c.profileSource).hostname,'fortune.com');assert.equal(c.listYear,2026);}
});
test('search ignores surrounding spaces, case and diacritics',()=>{
  assert.equal(normalize('  Résumé  '),'resume');
  assert.deepEqual(filterCompanies(data.companies,{q:'  MICROSOFT  '}).map(c=>c.id),['microsoft']);
});

test('Google and Alphabet identify one parent company, Humana is included, and JPMorgan is not duplicated',()=>{
  assert.deepEqual(filterCompanies(data.companies,{q:'Google'}).map(c=>c.id),['alphabet']);
  assert.deepEqual(filterCompanies(data.companies,{q:'Alphabet'}).map(c=>c.id),['alphabet']);
  assert.deepEqual(filterCompanies(data.companies,{company:'humana',state:'Kentucky'}).map(c=>c.id),['humana']);
  assert.deepEqual(filterCompanies(data.companies,{q:'JPMorgan'}).map(c=>c.id),['jpmorgan-chase']);
});
test('company, industry, city and state filters intersect',()=>{
  assert.deepEqual(filterCompanies(data.companies,{industry:'General Merchandisers',state:'Washington'}).map(c=>c.id),['costco']);
  assert.equal(filterCompanies(data.companies,{company:'target',state:'Washington'}).length,0);
  assert.deepEqual(filterCompanies(data.companies,{city:'Atlanta',state:'Georgia'}).map(c=>c.id),['coca-cola','delta','home-depot','ups']);
  assert.equal(filterCompanies(data.companies,{company:'apple',q:'apple',city:'Cupertino',state:'California',industry:'Computers, Office Equipment'}).length,1);
});
test('empty results, reset and both alphabetical sorts',()=>{
  assert.equal(filterCompanies(data.companies,{q:'no such employer'}).length,0);
  const asc=filterCompanies(data.companies,{}).map(c=>c.name);
  assert.equal(asc.length,data.companies.length);
  assert.deepEqual(filterCompanies(data.companies,{sort:'desc'}).map(c=>c.name),[...asc].reverse());
});
test('URL filters round trip special characters and default sorting',()=>{
  const state=readFilters('?q=JPMorgan+Chase&industry=Health+Care%3A+Pharmacy+and+Other+Services&state=New+York&sort=desc');
  assert.deepEqual(readFilters('?'+serializeFilters(state)),state);
  assert.equal(serializeFilters(readFilters('')),'');
  assert.equal(readFilters('?sort=malicious').sort,'asc');
  assert.equal(readFilters('?q='+ 'a'.repeat(500)).q.length,120);
});
test('unknown URL selection yields no fabricated matches',()=>{
  assert.equal(filterCompanies(data.companies,readFilters('?company=unknown')).length,0);
});
test('malformed sources and duplicate companies are rejected',()=>{
  for(const modify of [d=>d.companies.push(d.companies[0]),d=>d.companies[0].careerUrl='javascript:alert(1)',d=>d.companies[0].headquarters=null,d=>d.companies[0].listYear=2025,d=>d.companies[0].supportingSources=[{label:'source',url:'javascript:alert(1)'}]]){
    const copy=structuredClone(data);modify(copy);assert.throws(()=>validateData(copy));
  }
});
test('new industry and headquarters combinations return reviewed additions',()=>{
  assert.deepEqual(filterCompanies(data.companies,{industry:'Airlines',state:'Illinois'}).map(c=>c.id),['united-airlines']);
  assert.deepEqual(filterCompanies(data.companies,{industry:'Petroleum Refining',state:'Texas'}).map(c=>c.id),['chevron','phillips-66','valero']);
  assert.equal(filterCompanies(data.companies,{company:'mckesson',city:'Irving'}).length,1);
  assert.equal(filterCompanies(data.companies,{company:'caterpillar',city:'Irvine'}).length,0);
});

