import {readJobFilters,serializeJobFilters} from './jobs.js';

export const SAVED_SEARCH_KEY='fortunehire.saved-searches.v1';
export const MAX_SAVED_SEARCHES=20;
export function savedQuery(filters){
 const query=typeof filters==='string'?filters:serializeJobFilters(filters);
 return serializeJobFilters({...readJobFilters(query),page:'1'});
}
export function readSavedSearches(storage){
 const raw=storage.getItem(SAVED_SEARCH_KEY);
 if(!raw||raw.length>64000)return [];
 let data;try{data=JSON.parse(raw);}catch{return [];}
 if(data?.version!==1||!Array.isArray(data.searches))return [];
 const names=new Set(),searches=[];
 for(const entry of data.searches){
  if(typeof entry?.name!=='string'||typeof entry.query!=='string'||entry.query.length>4096)continue;
  const name=entry.name.trim();
  if(!name||name.length>60||names.has(name.toLowerCase()))continue;
  names.add(name.toLowerCase());searches.push({name,query:savedQuery(entry.query)});
  if(searches.length===MAX_SAVED_SEARCHES)break;
 }
 return searches;
}
export function saveSearch(storage,name,filters){
 name=name.trim();
 if(!name||name.length>60)throw Error('Choose a name between 1 and 60 characters.');
 const searches=readSavedSearches(storage),index=searches.findIndex(s=>s.name.toLowerCase()===name.toLowerCase());
 if(index<0&&searches.length>=MAX_SAVED_SEARCHES)throw Error('You have 20 saved searches. Remove one to save another.');
 const entry={name,query:savedQuery(filters)};
 if(index<0)searches.push(entry);else searches[index]=entry;
 storage.setItem(SAVED_SEARCH_KEY,JSON.stringify({version:1,searches}));
 return {searches,updated:index>=0};
}
export function removeSearch(storage,name){
 const searches=readSavedSearches(storage).filter(s=>s.name!==name);
 storage.setItem(SAVED_SEARCH_KEY,JSON.stringify({version:1,searches}));
 return searches;
}

export function mountSavedSearches({getFilters,applyFilters,isReady}){
 const $=id=>document.getElementById(id),editor=$('save-search-form'),nameInput=$('search-name');
 const status=message=>{$('saved-search-status').textContent=message;};
 let storage,searches=[],available=true;
 try{storage=window.localStorage;searches=readSavedSearches(storage);}catch{available=false;}
 const storageError=()=>status('Your browser could not save this change. Allow site storage or try again; your job filters still work.');
 function closeEditor(){editor.hidden=true;$('save-filters').setAttribute('aria-expanded','false');}
 function refresh(){
  $('save-filters').disabled=!available||!isReady();
  $('saved-search-count').textContent=searches.length?` (${searches.length})`:'';
  const list=$('saved-search-list');list.replaceChildren();
  if(!searches.length){const p=document.createElement('p');p.className='small';p.textContent='No saved searches yet. Choose your filters, then select Save filters.';list.append(p);}
  for(const search of searches){
   const row=document.createElement('div');row.className='saved-search-row';
   const load=document.createElement('button');load.type='button';load.className='saved-search-load';load.textContent=search.name;load.disabled=!isReady();load.setAttribute('aria-label',`Load saved search: ${search.name}`);
   load.addEventListener('click',()=>{if(!isReady())return;closeEditor();applyFilters(readJobFilters(search.query));status(`Loaded “${search.name}” with the latest available jobs.`);$('count').tabIndex=-1;$('count').focus();});
   const remove=document.createElement('button');remove.type='button';remove.className='saved-search-remove';remove.textContent='Remove';remove.setAttribute('aria-label',`Remove saved search: ${search.name}`);
   remove.addEventListener('click',()=>{try{searches=removeSearch(storage,search.name);refresh();status(`Removed “${search.name}”.`);const next=$('saved-search-list').querySelector('button');(next||$('save-filters')).focus();}catch{storageError();}});
   row.append(load,remove);list.append(row);
  }
 }
 $('save-filters').addEventListener('click',()=>{
  if(!available||!isReady())return;
  if(!editor.hidden){closeEditor();return;}
  editor.hidden=false;$('save-filters').setAttribute('aria-expanded','true');
  const query=savedQuery(getFilters()),match=searches.find(s=>s.query===query);nameInput.value=match?.name||'';
  status('');nameInput.focus();nameInput.select();
 });
 $('cancel-save-search').addEventListener('click',()=>{closeEditor();$('save-filters').focus();});
 editor.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();closeEditor();$('save-filters').focus();}});
 editor.addEventListener('submit',event=>{
  event.preventDefault();if(!available||!isReady()||!editor.reportValidity())return;
  try{
   const result=saveSearch(storage,nameInput.value,getFilters());searches=result.searches;
   closeEditor();refresh();$('saved-searches').open=true;status(`${result.updated?'Updated':'Saved'} “${nameInput.value.trim()}”.`);$('save-filters').focus();
  }catch(error){status(error.message.startsWith('Choose a name')||error.message.startsWith('You have 20')?error.message:'Your browser could not save this search. It has not been saved; allow site storage or try again.');}
 });
 window.addEventListener('storage',event=>{
  if(event.key!==SAVED_SEARCH_KEY&&event.key!==null)return;
  try{searches=readSavedSearches(storage);refresh();}catch{storageError();}
 });
 refresh();if(!available)status('Saved searches are unavailable because this browser blocks site storage. Your job filters still work.');
 return {refresh};
}
