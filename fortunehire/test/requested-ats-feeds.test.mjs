import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateJobs} from '../public/jobs.js';

const root = new URL('../public/data/', import.meta.url);
const read = name => readFile(new URL(name + '.json', root), 'utf8').then(JSON.parse);

test('public ATS job URLs are limited to the employer board and individual role', async () => {
  const [data, directory] = await Promise.all([read('jobs'), read('companies')]);
  for (const [company, other] of [['openai', 'Perplexity'], ['perplexity', 'openai'], ['anthropic', 'other']]) {
    const job = data.jobs.find(row => row.companyId === company);
    assert.ok(job, company);
    const validated = {schemaVersion: data.schemaVersion, jobs: [job]};
    assert.equal(validateJobs(validated, directory.companies)[0].id, job.id);
    const url = new URL(job.url);
    const [, , ...jobPath] = url.pathname.split('/');
    const invalid = [
      job.url + '/application', job.url + '?session=1',
      url.origin + '/' + [other, ...jobPath].join('/'),
    ];
    for (const bad of invalid) {
      assert.throws(() => validateJobs({...validated, jobs: [{...job, url: bad}]}, directory.companies),
        /Invalid official job URL/);
    }
  }
});
