import {readFile} from 'node:fs/promises';
import {validateJobs} from '../public/jobs.js';
const root=new URL('../public/data/',import.meta.url);
const data=JSON.parse(await readFile(new URL('jobs.json',root),'utf8'));
const companies=JSON.parse(await readFile(new URL('companies.json',root),'utf8')).companies;
const jobs=validateJobs(data,companies);
console.log(`Validated ${jobs.length} official job records.`);

