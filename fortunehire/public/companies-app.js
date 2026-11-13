import { keys, readFilters, filterCompanies, serializeFilters, validateData } from './directory.js';
const $ = id => document.getElementById(id);
let companies = [];
let ready = false;
let pending;
const element = (tag, text, className) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (className) e.className = className; return e; };
function link(text, url) { const a = element('a', text); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
function card(c) {
  const article = element('article', undefined, 'card');
  const top = element('div', undefined, 'card-top');
  const monogram = element('span', (c.name.match(/[A-Za-z0-9]+/g)||[]).map(s=>s[0]).slice(0,2).join(''), 'monogram'); monogram.setAttribute('aria-hidden','true');
  const title = element('div'); title.append(element('h3',c.name),element('div', `Fortune 500 · ${c.listYear}`, 'list-year')); top.append(monogram,title);
  const dl = element('dl'); dl.append(element('dt','Industry'),element('dd',c.industry),element('dt','Headquarters'),element('dd',`${c.headquarters.city}, ${c.headquarters.state}`));
  const career = link('Visit official careers ↗',c.careerUrl); career.className = 'career-link'; career.setAttribute('aria-label',`Visit ${c.name} official careers (opens in a new tab)`);
  const details = element('details'); const summary = element('summary','Sources & review date');
  const date = new Date(`${c.reviewedAt}T12:00:00Z`).toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric',timeZone:'UTC'});
  details.append(summary,element('p',`Reviewed ${date}. ${c.verificationNote}`),link('Company data source ↗',c.profileSource),element('br'),link(`${c.listYear} membership source ↗`,c.membershipSource),element('p',`Destination: ${new URL(c.careerUrl).hostname}`));
  for (const source of c.supportingSources || []) details.append(element('br'),link(`${source.label} ↗`,source.url));
  article.append(top,dl,career,details); return article;
}
function options(id, values) {
  const select = $(id); select.replaceChildren(select.options[0]);
  for (const [value,label] of values) { const option = element('option',label); option.value=value; select.append(option); }
  select.disabled = false;
}
function restore() {
  const f = readFilters(location.search);
  for (const key of keys) {
    if (key !== 'q' && f[key] && ![...$(key).options].some(o=>o.value === f[key])) { const option = element('option',`Unavailable: ${f[key]}`); option.value=f[key]; $(key).append(option); }
    $(key).value=f[key];
  }
}
function render(sync = true) {
  if (!ready) return;
  const f = Object.fromEntries(keys.map(key=>[key,$(key).value]));
  const result = filterCompanies(companies,f);
  $('results').replaceChildren(...result.map(card));
  $('count').textContent = `${result.length} of ${companies.length} companies`;
  $('empty').hidden = result.length !== 0;
  if (sync) { const query = serializeFilters(f); history.replaceState(null,'',`${location.pathname}${query ? '?' + query : ''}${location.hash}`); }
}
function reset() { clearTimeout(pending); for (const key of keys) $(key).value=key === 'sort' ? 'asc' : ''; render(); }
async function load() {
  ready = false; $('error').hidden = true; $('empty').hidden = true; $('results').setAttribute('aria-busy','true'); $('count').textContent='Loading companies…';
  try {
    const response = await fetch(new URL('./data/companies.json',import.meta.url));
    if (!response.ok) throw new Error('Data unavailable');
    const data = validateData(await response.json()); companies=data.companies;
    options('company', [...companies].sort((a,b)=>a.name.localeCompare(b.name)).map(c=>[c.id,c.name]));
    for (const key of ['industry','state','city']) options(key,[...new Set(companies.map(c=>key==='industry'?c.industry:c.headquarters[key]))].sort().map(s=>[s,s]));
    $('coverage').textContent=`${companies.length} of 500 employers reviewed`;
    restore(); ready = true; render(false);
  } catch {
    $('results').replaceChildren(); $('count').textContent='Directory unavailable'; $('coverage').textContent='Coverage unavailable'; $('error').hidden=false;
  } finally { $('results').setAttribute('aria-busy','false'); }
}
$('filters').addEventListener('submit',e=>{e.preventDefault();clearTimeout(pending);render();});
$('q').addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(()=>render(),120);});
for (const key of keys.filter(k=>k!=='q')) $(key).addEventListener('change',()=>{clearTimeout(pending);render();});
$('reset').addEventListener('click',reset); $('empty-reset').addEventListener('click',()=>{reset();$('q').focus();}); $('retry').addEventListener('click',load);
window.addEventListener('popstate',()=>{if(ready){clearTimeout(pending);restore();render(false);}});
load();

