export const keys = ['q', 'company', 'industry', 'state', 'city', 'sort'];
export const normalize = value => String(value ?? '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim().toLocaleLowerCase('en-US');
export function readFilters(search) {
  const params = new URLSearchParams(search);
  return Object.fromEntries(keys.map(key => [key, key === 'sort' ? (params.get(key) === 'desc' ? 'desc' : 'asc') : (params.get(key) || '').slice(0, 120)]));
}
export function filterCompanies(companies, f) {
  return companies.filter(c => (!normalize(f.q) || normalize(c.name).includes(normalize(f.q))) && (!f.company || c.id === f.company) && (!f.industry || c.industry === f.industry) && (!f.state || c.headquarters.state === f.state) && (!f.city || c.headquarters.city === f.city)).sort((a,b) => (f.sort === 'desc' ? -1 : 1) * a.name.localeCompare(b.name, 'en-US'));
}
export function serializeFilters(filters) {
  const params = new URLSearchParams();
  for (const key of keys) if (filters[key] && !(key === 'sort' && filters[key] === 'asc')) params.set(key, filters[key]);
  return params.toString();
}
export function validateData(data) {
  if (data.schemaVersion !== 1 || !Array.isArray(data.companies) || !data.companies.length) throw new Error('Invalid directory');
  const ids = new Set();
  for (const c of data.companies) {
    if (!/^[a-z0-9-]+$/.test(c.id) || ids.has(c.id)) throw new Error('Invalid or duplicate ID');
    ids.add(c.id);
    for (const value of [c.name,c.industry,c.headquarters?.city,c.headquarters?.state,c.verificationNote]) if (typeof value !== 'string' || !value.trim()) throw new Error('Missing company field');
    if (!Number.isInteger(c.listYear) || c.listYear !== data.listYear || !/^\d{4}-\d{2}-\d{2}$/.test(c.reviewedAt)) throw new Error('Invalid date or list year');
    for (const field of ['careerUrl','profileSource','membershipSource']) {
      const url = new URL(c[field]);
      if (url.protocol !== 'https:' || url.username || url.password) throw new Error('Unsafe URL');
    }
    if (c.supportingSources !== undefined) {
      if (!Array.isArray(c.supportingSources)) throw new Error('Invalid supporting sources');
      for (const source of c.supportingSources) {
        const url = new URL(source.url);
        if (typeof source.label !== 'string' || !source.label.trim() || url.protocol !== 'https:' || url.username || url.password) throw new Error('Unsafe supporting source');
      }
    }
  }
  return data;
}
