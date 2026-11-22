import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const companies=JSON.parse(await readFile(new URL('../public/data/companies.json',import.meta.url),'utf8')).companies;
const manifest=JSON.parse(await readFile(new URL('../public/data/company-logos.json',import.meta.url),'utf8'));

test('local company logos have official-source metadata and valid image files',async()=>{
  assert.equal(manifest.schemaVersion,1);
  assert.equal(Object.keys(manifest.logos).length,72);
  const companyIds=new Set(companies.map(company=>company.id));
  for(const [id,logo] of Object.entries(manifest.logos)){
    assert.ok(companyIds.has(id),id);
    assert.match(logo.src,new RegExp(`^\\./assets/company-logos/${id}\\.(?:png|ico|jpg|svg)$`));
    assert.equal(new URL(logo.sourceUrl).protocol,'https:');
    assert.equal(new URL(logo.companyUrl).protocol,'https:');
    assert.match(logo.reviewedAt,/^\d{4}-\d{2}-\d{2}$/);
    const bytes=await readFile(new URL('../public/'+logo.src.slice(2),import.meta.url));
    const png=bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
    const ico=bytes.subarray(0,4).equals(Buffer.from([0,0,1,0]));
    const jpg=bytes.subarray(0,3).equals(Buffer.from([255,216,255]));
    const svg=/<(?:\w+:)?svg\b/.test(bytes.toString('utf8',0,200));
    assert.ok(png||ico||jpg||svg,`${id} is not a supported image`);
  }
  assert.deepEqual(companies.map(c=>c.id).filter(id=>!manifest.logos[id]).sort(),['adobe','intel','warner-bros-discovery']);
});
