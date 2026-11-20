export function installMultiFilterBehavior(document){
  const dropdowns=[...document.querySelectorAll('details.multi-filter')];
  document.addEventListener('pointerdown',event=>{
    for(const dropdown of dropdowns)if(dropdown.open&&!dropdown.contains(event.target))dropdown.open=false;
  });
  document.addEventListener('toggle',event=>{
    if(!dropdowns.includes(event.target)||!event.target.open)return;
    for(const dropdown of dropdowns)if(dropdown!==event.target)dropdown.open=false;
  },true);
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape')for(const dropdown of dropdowns)dropdown.open=false;
  });
}
