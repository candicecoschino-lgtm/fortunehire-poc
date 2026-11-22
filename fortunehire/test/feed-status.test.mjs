import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
test('all 75 directory companies have an honest feed status matching enabled sources',async()=>{
  const root=new URL('../public/data/',import.meta.url);
  const [companies,registry,audit]=await Promise.all(['companies','job-sources','company-feed-status'].map(async key=>JSON.parse(await readFile(new URL(key+'.json',root),'utf8'))));
  assert.equal(audit.companies.length,75);
  assert.deepEqual(audit.companies.map(c=>c.companyId).sort(),companies.companies.map(c=>c.id).sort());
  assert.equal(new Set(audit.companies.map(c=>c.companyId)).size,75);
  for(const row of audit.companies){
    assert.equal(row.status==='connected',Object.hasOwn(registry.sources,row.companyId));
    assert.ok(row.reason&&row.nextStep&&row.officialCareerUrl.startsWith('https://'));
  }
  for (const id of ['anthropic','brown-brown','openai','perplexity']) {
    const row = audit.companies.find(c => c.companyId === id);
    assert.equal(row.status,'verification-needed');
    assert.equal(row.officialCareerUrl,companies.companies.find(c => c.id === id).careerUrl);
  }
  assert.equal(audit.companies.find(c=>c.companyId==='rtx').status,'paused');
  assert.equal(audit.counts.connected,Object.keys(registry.sources).length);
  assert.equal(Object.values(audit.counts).reduce((n,v)=>n+v,0),75);
});
