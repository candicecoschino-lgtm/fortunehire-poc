import {isSearchCurrent} from './jobs.js';
export const ACTIVITY_KEY='fortunehire.job-activity.v1';
export const MAX_TRACKED_JOBS=500;
const FLAGS=['saved','hidden','applied'];
export function readJobActivity(storage){
 const raw=storage.getItem(ACTIVITY_KEY);if(!raw||raw.length>4000000)return [];
 let data;try{data=JSON.parse(raw);}catch{return [];}
 if(data?.version!==1||!Array.isArray(data.jobs))return [];
 const ids=new Set(),records=[];
 for(const row of data.jobs){
  if(!row||typeof row.id!=='string'||!/^[a-z0-9-]+$/.test(row.id)||ids.has(row.id)||!FLAGS.some(flag=>row[flag]===true))continue;
  ids.add(row.id);records.push({id:row.id,...Object.fromEntries(FLAGS.map(flag=>[flag,row[flag]===true])),job:row.job?.id===row.id?row.job:null});
  if(records.length===MAX_TRACKED_JOBS)break;
 }
 return records;
}
export function setJobActivity(storage,job,flag,value){
 if(!FLAGS.includes(flag)||typeof value!=='boolean'||!job||!/^[a-z0-9-]+$/.test(job.id))throw Error('Invalid job action');
 const records=readJobActivity(storage),index=records.findIndex(row=>row.id===job.id);
 const record={id:job.id,saved:false,hidden:false,applied:false,...(index>=0?records[index]:{}),[flag]:value,job:{...job}};
 delete record.job.organizerUnavailable;
 if(!FLAGS.some(key=>record[key])){if(index>=0)records.splice(index,1);}
 else if(index>=0)records[index]=record;
 else{if(records.length>=MAX_TRACKED_JOBS)throw Error('Your browser list holds 500 jobs. Remove a saved, applied, or hidden choice before adding another.');records.push(record);}
 storage.setItem(ACTIVITY_KEY,JSON.stringify({version:1,jobs:records}));
 return records;
}
export function activityFlags(records,id){return records.find(row=>row.id===id)||{saved:false,hidden:false,applied:false};}
export function activityView(jobs,records,view=''){
 const byId=new Map(records.map(row=>[row.id,row]));
 return jobs.filter(job=>view?byId.get(job.id)?.[view]===true:!byId.get(job.id)?.hidden);
}
export function trackedJobs(liveJobs,records,validateSnapshot,today){
 const byId=new Map(liveJobs.map(job=>[job.id,job])),liveIds=new Set(byId.keys());
 for(const row of records){
  if(byId.has(row.id)||!row.job)continue;
  try{const job=validateSnapshot(row.job);if(job?.id===row.id)byId.set(row.id,job);}catch{/* Untrusted or obsolete snapshots cannot create job links. */}
 }
 return [...byId.values()].map(job=>({...job,organizerUnavailable:!liveIds.has(job.id)||!isSearchCurrent(job,today)}));
}
