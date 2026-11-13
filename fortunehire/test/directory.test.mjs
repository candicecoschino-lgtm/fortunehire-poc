import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {filterCompanies, normalize, readFilters, serializeFilters, validateData} from '../public/directory.js';
const data=JSON.parse(await readFile(new URL('../public/data/companies.json',import.meta.url),'utf8'));
test('production records have complete provenance, safe URLs and unique identifiers',()=>{
  assert.equal(validateData(data),data);
  assert.equal(data.companies.length,12);
  for(const c of data.companies){assert.equal(new URL(c.profileSource).hostname,'fortune.com');assert.equal(c.listYear,2026);}
});
test('search ignores surrounding spaces, case and diacritics',()=>{
  assert.equal(normalize('  Résumé  '),'resume');
  assert.deepEqual(filterCompanies(data.companies,{q:'  MICROSOFT  '}).map(c=>c.id),['microsoft']);
});
test('company, industry, city and state filters intersect',()=>{
  assert.deepEqual(filterCompanies(data.companies,{industry:'General Merchandisers',state:'Washington'}).map(c=>c.id),['costco']);
  assert.equal(filterCompanies(data.companies,{company:'target',state:'Washington'}).length,0);
  assert.equal(filterCompanies(data.companies,{city:'Atlanta',state:'Georgia'}).length,2);
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
  for(const modify of [d=>d.companies.push(d.companies[0]),d=>d.companies[0].careerUrl='javascript:alert(1)',d=>d.companies[0].headquarters=null,d=>d.companies[0].listYear=2025]){
    const copy=structuredClone(data);modify(copy);assert.throws(()=>validateData(copy));
  }
});
