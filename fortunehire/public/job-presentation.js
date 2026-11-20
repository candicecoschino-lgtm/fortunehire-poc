const money=value=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:value%1?2:0,maximumFractionDigits:2}).format(value);
export function todayPostingNote(jobs,today){
 return jobs.some(job=>job.postedAt===today)?'':'No employer-dated postings for today are in our current collection yet. Try Past 3 days or check again after the next refresh. This does not mean employers have no new openings.';
}
function publishedRanges(text){
 const ranges=[];
 for(const match of text.matchAll(/\$\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(?:to|[-\u2010-\u2015])\s*\$?\s*(\d[\d,]*(?:\.\d{1,2})?)(?![\d,.]|\s*[kKmM]\b)/g)){
  const low=Number(match[1].replaceAll(',','')),high=Number(match[2].replaceAll(',',''));
  if(!Number.isFinite(low)||!Number.isFinite(high)||low<=0||high<low)continue;
  const before=text.slice(Math.max(text.lastIndexOf('|',match.index)+1,match.index-65),match.index);
  const after=text.slice(match.index+match[0].length);
  const suffix=/^\s*(?:\/\s*|per\s+|an?\s+)?(year|annum|annually|annual|hour|hr|hourly)\b/i.exec(after)?.[1];
  const annual=/\b(?:annual|annually|yearly|per year|per annum)\b/i.test(before);
  const hourly=/\b(?:hourly|per hour)\b/i.test(before);
  const period=suffix?(/^(?:hour|hr)/i.test(suffix)?'hour':'year'):annual!==hourly?(annual?'year':'hour'):'';
  const range=`${money(low)}\u2013${money(high)}${period?' / '+period:''}`;
  if(!ranges.includes(range))ranges.push(range);
 }
 return ranges;
}
export function postedLabel(postedAt,today){
  const days=(Date.parse(today+'T12:00:00Z')-Date.parse(postedAt+'T12:00:00Z'))/86400000;
  if(!Number.isFinite(days)||days<0)return 'Posting date unavailable';
  return days===0?'Posted today':days===1?'Posted yesterday':`Posted ${days} days ago`;
}
export function locationSummary(job,state=''){
  const selected=Array.isArray(state)?state:state?[state]:[];
  if(job.arrangement==='remote'){
    if(job.remoteScope==='nationwide')return 'Remote across the United States';
    if(job.remoteScope==='states'){
      const preferred=selected.find(value=>job.eligibleStates.includes(value))||state;
      const states=preferred&&job.eligibleStates.includes(preferred)?[preferred,...job.eligibleStates.filter(s=>s!==preferred)]:job.eligibleStates;
      return `Remote in ${states.slice(0,2).join(', ')}${states.length>2?` + ${states.length-2} more ${states.length===3?'state':'states'}`:''}${job.remoteEligibilityBasis==='title-geography'?' (from title)':''}`;
    }
    return 'Remote - eligible states not specified';
  }
  const first=job.locations.find(location=>selected.includes(location.state))||job.locations.find(location=>location.state===state)||job.locations[0];
  if(!first)return job.locationNote;
  return `${first.city}, ${first.state}${job.locations.length>1?` + ${job.locations.length-1} more ${job.locations.length===2?'location':'locations'}`:''}`;
}
export function paySummary(job,state=''){
  const selected=Array.isArray(state)?state:state?[state]:[];
  const scope=job.salary?.scopeStates||job.publishedPay?.scopeStates||[];
  if(selected.length&&scope.length&&!selected.some(value=>scope.includes(value)))return {text:selected.length===1?'Pay unavailable for this state':'Pay unavailable for these states',detail:false,note:''};
  const applicable=selected.filter(value=>!scope.length||scope.includes(value));
  const scopeNote=selected.length&&scope.length&&applicable.length<selected.length?`Published pay is verified only for ${applicable.join(', ')}.`:'';
  if(!job.salary&&!job.publishedPay)return {text:'Pay information unavailable',detail:false,note:''};
  if(job.salary){
    const salary=job.salary;
    return {text:`${money(salary.min)}${salary.min===salary.max?'':'\u2013'+money(salary.max)} / ${salary.period==='year'?'year':'hour'}`,detail:false,note:scopeNote};
  }
  const ranges=publishedRanges(job.publishedPay.text);
  return {text:ranges.length?ranges.join(' · '):'See pay details',detail:true,note:scopeNote};
}
