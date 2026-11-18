// Deliberately specific action/object phrases, not generic words such as
// "sales", "training", "health", "it", or "compliance" anywhere in a page.
export const dutyRules={
 sales:/\b(?:sell(?:ing)? (?:products|services|solutions)|(?:close|win|negotiate) (?:new )?(?:sales|deals|contracts)|(?:develop|manage|build|grow) (?:a |the )?(?:sales pipeline|client portfolio)|(?:meet|exceed|achieve) (?:sales |revenue )?(?:quotas|sales targets))\b/i,
 marketing:/\b(?:(?:develop|manage|execute|create|design|lead) (?:the |our )?(?:marketing campaigns|marketing strategy|brand strategy|advertising campaigns|social media content)|(?:write|produce|create) (?:marketing content|press releases))\b/i,
 hr:/\b(?:(?:recruit|hire|onboard) (?:new )?(?:employees|candidates|staff)|(?:manage|administer|resolve|investigate|oversee) (?:employee relations|employee benefits|compensation programs|HR policies)|(?:design|deliver|develop) (?:employee training|learning programs))\b/i,
 it:/\b(?:(?:design|develop|build|maintain|test|deploy|write) (?:and (?:maintain|develop|test|deploy) )?(?:the |our )?(?:software|applications|APIs|code|databases|data pipelines|cloud infrastructure)|(?:manage|administer|maintain|secure) (?:the |our )?(?:databases|computer networks|IT systems|cloud platforms)|(?:analyze|analyse|resolve|investigate) (?:cyber threats|security incidents|software defects))\b/i,
 operations:/\b(?:(?:manage|oversee|improve|coordinate|supervise|optimize) (?:the |daily |day-to-day )?(?:business operations|operational processes|facility operations|branch operations|daily operations)|(?:maintain|repair|manage) (?:building systems|facilities|equipment maintenance))\b/i,
 service:/\b(?:(?:resolve|handle|respond to|answer) (?:customer|client|member) (?:inquiries|complaints|questions|issues)|(?:provide|deliver) (?:customer service|customer support|member support)|(?:assist|help) customers with)\b/i,
 admin:/\b(?:(?:manage|coordinate|maintain|schedule|organize|arrange) (?:executive calendars|office supplies|travel arrangements|appointments|meetings)|(?:perform|provide) (?:data entry|administrative support|clerical duties)|(?:greet|welcome) (?:visitors|guests))\b/i,
 legal:/\b(?:(?:draft|review|negotiate) (?:legal documents|legal contracts|commercial agreements)|(?:provide|deliver) legal (?:advice|counsel)|(?:manage|conduct|oversee|investigate) (?:litigation|regulatory filings|compliance investigations|compliance audits))\b/i,
 finance:/\b(?:(?:prepare|analyze|analyse|review|reconcile|manage|process) (?:financial statements|financial reports|tax returns|accounts payable|accounts receivable|journal entries|payroll|invoices)|(?:perform|conduct) (?:financial audits|financial analysis)|(?:underwrite|adjudicate|process) (?:insurance claims|loans))\b/i,
 engineering:/\b(?:(?:design|develop|test|analyze|analyse) (?:mechanical systems|electrical systems|electronic circuits|aircraft systems|hardware|structural components)|(?:create|prepare|review) (?:engineering drawings|CAD models|technical drawings))\b/i,
 healthcare:/\b(?:(?:provide|deliver|coordinate|assess|evaluate|manage) (?:direct )?(?:patient care|clinical care|nursing care|treatment plans)|(?:diagnose|treat|assess|examine) patients|(?:administer|dispense) (?:medications|medication|prescriptions)|(?:conduct|perform) (?:clinical assessments|patient assessments))\b/i,
 logistics:/\b(?:(?:manage|coordinate|optimize|plan) (?:supply chains|supply chain|logistics|shipments|inventory levels)|(?:pick|pack|ship|receive|load|unload) (?:orders|freight|packages|merchandise)|(?:negotiate|manage) (?:supplier contracts|vendor contracts)|(?:deliver|transport) (?:packages|freight|goods))\b/i,
 manufacturing:/\b(?:(?:operate|maintain|repair|set up) (?:production equipment|manufacturing equipment|CNC machines|industrial machinery)|(?:assemble|weld|fabricate|machine) (?:parts|components|metal|products))\b/i,
 research:/\b(?:(?:conduct|design|perform|lead) (?:scientific research|laboratory experiments|clinical research|research studies)|(?:analyze|analyse|interpret) (?:experimental data|laboratory results)|(?:develop|validate) (?:scientific methods|laboratory methods))\b/i,
 projects:/\b(?:(?:manage|coordinate|lead|oversee|develop|track) (?:project timelines|project budgets|project plans|program delivery|product roadmaps|product strategy)|(?:define|prioritize) (?:product requirements|product backlog))\b/i,
 business:/\b(?:(?:analyze|analyse|evaluate|develop|create|document) (?:business requirements|business performance|business strategy|market opportunities|business cases|business processes)|(?:build|develop|maintain|create) (?:dashboards|business reports|reporting dashboards))\b/i,
 retail:/\b(?:(?:stock|replenish|merchandise) (?:shelves|store shelves|store inventory|displays)|(?:operate|manage) (?:cash registers|checkout lanes)|(?:assist|help) (?:shoppers|customers) (?:with purchases|in store))\b/i,
 hospitality:/\b(?:(?:prepare|cook|serve) (?:food|meals|beverages)|(?:clean|maintain) (?:guest rooms|hotel rooms)|(?:take|serve) (?:food orders|drink orders)|(?:manage|oversee) (?:restaurant operations|food service))\b/i,
 quality:/\b(?:(?:perform|conduct|lead) (?:quality inspections|safety inspections|quality audits|safety audits)|(?:develop|implement|manage) (?:quality assurance programs|safety programs)|(?:inspect|test) (?:products|components) for (?:defects|quality))\b/i
};

export function validFunctionContext(value){
 return value?.version===1&&Array.isArray(value.duties)&&value.duties.length<=16&&value.duties.every(s=>typeof s==='string'&&s.length<=500)&&typeof value.category==='string'&&value.category.length<=120;
}

// Normalize action inflections only, preserving domain nouns and word boundaries.
export function dutyText(value){
 return value.replace(/^(you(?: will|[’']ll) )?(develop|build|maintain|manage|lead|deliver|provide|support|analyze|analyse|prepare|process|perform|coordinate|execute|implement|monitor|resolve|sell|drive|negotiate|recruit|administer|conduct|operate|repair|inspect|ensure|assist|create|oversee|evaluate|review|plan|schedule|greet|stock|serve|cook|test|write|respond|handle|advise|represent|optimize|supervise|diagnose|treat|assess|dispense|weld|assemble)s\b/i,'$1$2');
}

const additional={
 engineering:/\b(?:perform|conduct|lead|develop|ensure)\b.{0,90}\b(?:stress analysis|DaDT analysis|finite element|failsafe analyses|structural requirements)\b/i,
 logistics:/\b(?:provide movement of packages|operate handheld scanner|scan(?:ning)?[ /-]load methods)\b/i,
 finance:/\b(?:analyze financial information|advise customers)\b.{0,160}\b(?:lending solution|lending solutions|mortgage)\b/i,
 service:/\bhandle(?:s)? (?:customer|member|client) calls\b/i,
 projects:/\b(?:drive|provide|support|manage)\b.{0,95}\b(?:product roadmap|product management practices)\b/i,
 healthcare:/\b(?:provide clinical consultation|evaluate healthcare products|deliver clinical education|supervise home health aide|ensure the plan of care)\b/i
};
export function dutyMatches(key,text){
 const normalized=dutyText(text);
 return dutyRules[key].test(normalized)||!!additional[key]?.test(normalized);
}
