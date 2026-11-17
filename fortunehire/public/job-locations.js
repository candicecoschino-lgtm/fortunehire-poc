import {normalize} from './directory.js';
import {STATE_NAMES} from './us-geography.js';

export function normalizeCity(city){
 let value=normalize(city).replace(/[.'\u2019]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
 value=value.replace(/^st /,'saint ').replace(/^ft /,'fort ').replace(/^mt /,'mount ');
 return ['nyc','new york city'].includes(value)?'new york':value;
}
export function physicalCity(city){return !!city&&!/\b(?:remote|virtual|multiple|various|nationwide|anywhere|work\s+(?:at|from)\s+home)\b/i.test(city);}
export function zipPrefix(value){const match=/^(\d{5})(?:-\d{4})?$/.exec(value.trim());return match?match[1].slice(0,2):'';}
export function resolveCitySearch(value,shard){
 const query=String(value||'').trim();
 if(!query)return {status:'empty',places:[],message:''};
 const zip=/^(\d{5})(?:-\d{4})?$/.exec(query)?.[1];
 if(zip){
  if(shard===undefined)return {status:'loading',places:[],message:'Looking up ZIP '+zip+'…'};
  if(shard===null)return {status:'unavailable',places:[],message:'The ZIP lookup could not load. Please retry.'};
  const rows=shard.schemaVersion===1&&shard.prefix===zip.slice(0,2)&&Array.isArray(shard.places?.[zip])?shard.places[zip]:[];
  const places=rows.filter(row=>Array.isArray(row)&&typeof row[0]==='string'&&row[0].trim()&&Object.hasOwn(STATE_NAMES,row[1])).map(([city,state])=>({city,state:STATE_NAMES[state]}));
  if(!places.length)return {status:'not-found',places:[],message:'ZIP '+zip+' is not in our U.S. lookup. Check the ZIP or clear it.'};
  return {status:'valid',places,zip,message:'ZIP '+zip+': '+places.map(p=>p.city+', '+p.state).join('; ')+'.'};
 }
 return {status:'invalid',places:[],message:'Enter a five-digit U.S. ZIP code.'};
}
export function matchingOfficeLocations(job,search,selectedState=''){
 if(search.status!=='valid'||!['on-site','hybrid'].includes(job.arrangement))return [];
 return job.locations.filter(location=>physicalCity(location.city)&&(!selectedState||location.state===selectedState)&&search.places.some(place=>normalizeCity(location.city)===normalizeCity(place.city)&&(!place.state||location.state===place.state)));
}
export function locationPayState(job,search,selectedState=''){
 if(selectedState)return selectedState;
 const matches=matchingOfficeLocations(job,search),scope=job.salary?.scopeStates||job.publishedPay?.scopeStates||[];
 return (matches.find(location=>scope.includes(location.state))||matches[0])?.state||'';
}
