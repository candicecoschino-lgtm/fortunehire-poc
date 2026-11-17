import {salaryText} from './jobs.js';
export function postedLabel(postedAt,today){
  const days=(Date.parse(today+'T12:00:00Z')-Date.parse(postedAt+'T12:00:00Z'))/86400000;
  if(!Number.isFinite(days)||days<0)return 'Posting date unavailable';
  return days===0?'Posted today':days===1?'Posted yesterday':`Posted ${days} days ago`;
}
export function locationSummary(job,state=''){
  if(job.arrangement==='remote'){
    if(job.remoteScope==='nationwide')return 'Remote across the United States';
    if(job.remoteScope==='states'){
      const states=state&&job.eligibleStates.includes(state)?[state,...job.eligibleStates.filter(s=>s!==state)]:job.eligibleStates;
      return `Remote in ${states.slice(0,2).join(', ')}${states.length>2?` + ${states.length-2} more ${states.length===3?'state':'states'}`:''}`;
    }
    return 'Remote - eligible states not specified';
  }
  const first=job.locations.find(location=>location.state===state)||job.locations[0];
  if(!first)return job.locationNote;
  return `${first.city}, ${first.state}${job.locations.length>1?` + ${job.locations.length-1} more ${job.locations.length===2?'location':'locations'}`:''}`;
}
export function paySummary(job,state=''){
  const scope=job.salary?.scopeStates||job.publishedPay?.scopeStates||[];
  if(state&&scope.length&&!scope.includes(state))return {text:'Pay unavailable for this state',detail:false,note:''};
  if(!job.salary&&!job.publishedPay)return {text:'Pay information unavailable',detail:false,note:''};
  const text=salaryText(job);
  if(!job.salary&&text.length>95)return {text,detail:true,note:'Employer wording; see full terms'};
  return {text,detail:false,note:scope.length?'Location-specific pay; see details':''};
}
