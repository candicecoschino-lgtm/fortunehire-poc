import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
test('every enabled feed belongs to a reviewed directory employer and career host',async()=>{
  const data=new URL('../public/data/',import.meta.url);
  const registry=JSON.parse(await readFile(new URL('job-sources.json',data),'utf8'));
  const companies=JSON.parse(await readFile(new URL('companies.json',data),'utf8')).companies;
  assert.equal(registry.schemaVersion,1);
  for(const [id,source] of Object.entries(registry.sources)){
    const company=companies.find(c=>c.id===id);assert.ok(company,id);
    assert.equal(source.host,new URL(company.careerUrl).hostname);
    assert.ok(typeof source.sector==='string'&&source.sector.trim());
  }
});
