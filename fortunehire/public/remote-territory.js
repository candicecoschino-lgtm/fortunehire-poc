import {normalize} from './directory.js';
const words=value=>normalize(value).replace(/[^a-z0-9]+/g,' ').trim();

// User-selected fallback for Humana's remote roles with a named title territory.
// An office address by itself does not establish remote eligibility. Explicit
// nationwide or state eligibility always takes precedence over this inference.
export function applyRemoteTerritory(job){
 if(job.companyId!=='humana'||job.arrangement!=='remote'||job.remoteScope!=='unknown'||job.eligibleStates?.length)return job;
 const title=words(job.title),locations=job.locations||[];
 if(/\b(?:nationwide|anywhere|all states|united states)\b/.test(title))return job;
 const cities=locations.filter(loc=>{
  const city=words(loc.city);
  return city.length>=3&&!/\b(?:remote|various|multiple|unknown)\b/.test(city)&&(' '+title+' ').includes(' '+city+' ');
 });
 // Field-sales territory names (e.g. Orange County or Inland Empire) need not
 // equal a city. Their specific posting's listed locations establish the states.
 const territory=/\bmedicare\s+field\s+sales\s*[-\u2010-\u2015]\s*([a-z].*)/i.exec(job.title)?.[1]||'';
 const fieldTerritory=!!territory&&!/^(?:remote|virtual|bilingual|spanish|english|full.time|part.time)\b/i.test(territory);
 const candidates=fieldTerritory?locations:cities;
 const states=[...new Set(candidates.map(loc=>loc.state))].sort();
 if(!states.length)return job;
 return {...job,remoteScope:'states',eligibleStates:states,remoteEligibilityBasis:'title-geography',
  locationNote:'Remote in '+states.join(', ')+'. State restriction inferred from the title territory and employer-listed job locations; confirm residence and local travel requirements with the employer.'};
}
