import {dutyRules,dutyMatches,validFunctionContext} from './function-duties.js';
// Responsibilities first, employer category second, title fallback.
// These are search categories, not employer-supplied employment types.
export const JOB_FUNCTIONS = {
 sales:'Sales',marketing:'Marketing & Communications',hr:'Human Resources',it:'IT & Software',
 operations:'Operations',service:'Customer Service',admin:'Administrative',legal:'Legal & Compliance',
 finance:'Finance & Accounting',engineering:'Engineering & Design',healthcare:'Healthcare & Clinical',
 logistics:'Supply Chain & Logistics',manufacturing:'Manufacturing & Skilled Trades',
 research:'Research & Science',projects:'Product, Project & Program Management',business:'Business & Strategy',
 retail:'Retail & Store Roles',hospitality:'Food & Hospitality',quality:'Quality & Safety',other:'Other / Unclassified'
};
const rules = {
 sales:/\b(?:sales|selling|account executive|business development|client executive|relationship banker|mortgage loan officer|account (?:manager|director)|client partner|partner account)\b/i,
 marketing:/\b(?:marketing|marketer|communications?|comms|public relations|community relations|social media|copywriter|brand manager|content strategist|content creator|advertising|media planning|event coordinator|meeting planner|proposal writer)\b/i,
 hr:/\b(?:human resources|HR|HRLR|recruit(?:er|ing|ment)|talent|people (?:operations|analytics)|employee (?:relations|success|development)|associate relations|human capital|compensation|benefits (?:analyst|specialist|manager|consultant)|learning (?:experience|development)|training|L&D|workforce (?:experience|management))\b/i,
 it:/\b(?:IT|information technology|software|developer|programmer|applications? development|apps dev|applications? (?:analyst|architect|support)|cyber(?:security)?|information security|API security|product security|identity[ /-](?:access|aware)|AI|ML|artificial intelligence|machine learning|data (?:engineer|scientist|science|analyst|analytics|center|management)|datacenter|computer operator|systems? (?:administrator|admin|analyst|engineer|architect|integration)|network (?:engineer|administrator|architect|designer|planner|infrastructure|assurance)|networking|technical support|solutions? architect|platform (?:architect|infrastructure)|technical staff|SaaS|ITSM|ServiceNow|CRM|OCI|GCP|cloud|devops|database|technology|observability)\b/i,
 operations:/\b(?:operations?|operational|ops|store (?:manager|leader)|branch manager|area manager|shift supervisor|facilities|facility|maintenance|security (?:officer|guard|specialist|investigations|intelligence)|asset protection|property manag(?:er|ement)|sanitation|wastewater|utility manager|flight attendant|airport|seaman|marine terminals|operator trainee|process (?:coach|control|management|improvement)|continuous improvement)\b/i,
 service:/\b(?:customer (?:service|support|care|experience|success|solutions|engagement|enablement)|call center|contact center|member (?:service|support|advocate)|patient\s+service|guest (?:service|experience)|client service|account services|reservation agent|service & engagement)\b/i,
 admin:/\b(?:admin(?:istrative|istration)?|executive assistant|office (?:assistant|manager|coordinator|administrator)|center administrator|receptionist|data entry|secretary|clerical|schedul(?:er|e specialist)|correspondence)\b/i,
 legal:/\b(?:legal|LegalEdge|attorney|counsel|paralegal|compliance|regulatory|ethics|government affairs|state affairs|human rights)\b/i,
 finance:/\b(?:financ(?:e|ial|ing)|account(?:ant|ing)|audit(?:or|ing)?|tax|treasury|controller|CFO|bookkeeper|payroll|accounts (?:payable|receivable)|FP&A|bank(?:er|ing)|credit|loan officer|mortgage lending|wealth|investment|underwriting|actuar(?:y|ial)|claims|subrogation|securities|derivatives|trader|equities|trust officer|billing|reimbursement|revenue (?:cycle|integrity)|budget|cost (?:estimat(?:or|ing)|modeling|study)|estimating and pricing|insurance risk)\b/i,
 engineering:/\b(?:engineer(?:ing)?|designer|design|creative (?:director|assets|strategy|technologist)|art director|artist|animation|animatic|storyboard|video producer|producer.{0,12}ABC News|proofreader|audiovisual|avionics|control system|system integration|technical integrat(?:or|ion)|technical specialist|robotics|autonomy|perception|powertrain|suspension|battery recycling|electromagnetic|calibration|test architect)\b/i,
 healthcare:/\b(?:nurs(?:e|ing)|RN|LPN|LVN|CNA|PTA|physician|pharmac(?:ist|y)|clinical|clinician|therapist|therapy|medical|dental|paramedic|patient care|healthcare|care (?:manager|management|coordinator|coordination|navigator)|behavioral health|home health|hospice|hospital|optici(?:an|al)|hearing aid|dietitian|anesthesiologist|pathologist|radiology|ultrasound|utilization (?:management|review)|credentialing|coding (?:educat|education)|LTSS|oncology|health (?:coach|benefit)|DRG|IV technician|RX student|peer support.{0,25}foster care)\b/i,
 logistics:/\b(?:supply chain|supply planning|logistics|warehouse|procurement|purchasing|sourcing|buyer|inventory|distribution|shipping|receiv(?:ing|er)|package handler|material handler|driver|drvr|courier|delivery professional|transportation|freight|fulfillment|forklift|order selector|case picker|backroom|loader|ground handler|vehicle handler|dispatcher|demurrage|MP&L)\b/i,
 manufacturing:/\b(?:manufacturing|production|machinist|assembler|assembly|welder|electrician|mechanic|machine operator|electrical (?:journeyperson|technician)|instrumentation|HVAC|automotive technician|equipment technician|field technician|NGL field technician|tire|painter|plasterer|mold maker|grinder|blending|mixing operator|bindery|construction|installation.{0,15}technician|service tech|pipeline inspector|wastewater operator|board operator)\b/i,
 research:/\b(?:research(?:er)?|scientist|laboratory|labs?|chemist|biologist|microbiology|analytical science|meteorologist|flavor creation)\b/i,
 projects:/\b(?:product (?:manager|management|mgmt|owner)|(?:project|program) (?:manager|management|coordinator|director|lead|specialist|planner)|project technical specialist|proposal project specialist|technical program mgr)\b/i,
 business:/\b(?:business (?:analyst|analysis|manager|management|planner|information|insights|intelligence|process|controls|execution|strategy)|business and information analyst|strategy|strategic (?:planning|initiatives)|pricing|revenue (?:planning|growth)|capacity planning|forecasting|insights analyst|analytics|intelligence|planning.{0,5}scheduling|scheduling.{0,5}estimating|chief of staff|business & information analyst|risk.{0,5}controls)\b/i,
 retail:/\b(?:retail|store|cashier|personal shopper|merchandis(?:e|ing)|stocker|stocking|grocery|bakery|deli|produce|meat|seafood|floral|dairy|apparel.clerk|beer.wine|drug.gen mdse|e.commerce.clerk|membership|member (?:specialist|team lead)|pro experience|specialty ASM|beauty team leader|gas station attendant|gas attendant|fuel center)\b/i,
 hospitality:/\b(?:food|beverage|barista|starbucks|bartender|server|waithelp|sous chef|housekeeping|room attendant|cake decorator|costumer|landscaper|dining|resort rep|proprietor)\b/i,
 quality:/\b(?:quality|safety|EHS|environmental|environment|asset protection|firefighter|security investigations)\b/i
};
function classifyTitle(title){
 if(typeof title!=='string')return ['other'];
 title=title.replace(/\s+/g,' ').replace(/[\u2010-\u2015]/g,'-');
 const isIT=rules.it.test(title)||extensions.it.test(title);
 const isTechnicalAdmin=/\b(?:systems?|network|database|IT|SaaS) admin(?:istrator|istration)?\b/i.test(title);
 const matches=Object.entries(rules).filter(([key,rule])=>{
  if(!rule.test(title)&&!extensions[key]?.test(title))return false;
  if(key==='engineering'&&isIT)return false;
  if(key==='admin'&&isTechnicalAdmin)return false;
  if(key==='hospitality'&&isIT&&/\bserver\b/i.test(title))return false;
  return true;
 }).map(([key])=>key);
 return matches.length?matches:['other'];
}

// Additional explicit title vocabulary, shared by existing and future listings.
// Do not infer a function from the company name or from an unqualified title
// such as "Specialist", "Manager", or "Architect".
const extensions={
 it:/\b(?:enterprise architect|innovation tech lead|server (?:planning|administrator|engineer)|systems? lead analyst|compute|digital infrastructure|success architect.{0,15}(?:Agentforce|MuleSoft)|deployment planner.{0,15}GND)\b/i,
 finance:/\b(?:collateral risk|product control|quantitative|interest rate modeling|business risk|head of payments|consumer cards|trade support)\b/i,
 healthcare:/\b(?:optical associate|psychologist|coding educator|family care|case manager.{0,25}licensed BH|grievance.{0,5}appeals|SCA appeals|release of information|provider account management|carelon account management)\b/i,
 manufacturing:/\b(?:mechanical technician|electrical integration technician|measure technician|vending machine technician|E&I specialist)\b/i,
 engineering:/\b(?:EO\/IR|F\/A-18|systems leader|entry-level estimator)\b/i,
 logistics:/\b(?:CDL operator|vendor management)\b/i,
 retail:/\b(?:courtesy clerk|department manager.{0,15}Nike|(?:FT|PT) supervisor.{0,15}Converse|GM coach|omni-channel)\b/i,
 hr:/\bglobal mobility\b/i,
 projects:/\b(?:payment programs manager|manager, digital product|product renewals partner)\b/i,
 business:/\b(?:methods process analyst|contractor management|crisis management|digital change enablement|market readiness|change control)\b/i,
 quality:/\b(?:product acceptance|security investigative services|investigations lead, global security)\b/i,
 marketing:/\bevent broadcast\b/i
};

export function jobFunctionResult(job){
 if(typeof job==='string'||job==null)return {keys:classifyTitle(job),basis:'title',evidence:[]};
 const context=job.functionContext;
 if(validFunctionContext(context)){
  const scored=Object.keys(dutyRules).map(key=>({key,evidence:context.duties.filter(duty=>dutyMatches(key,duty))}));
  const highest=Math.max(0,...scored.map(match=>match.evidence.length));
  if(highest){
   // Prefer repeated core duties over a single ancillary task.
   const selected=scored.filter(match=>match.evidence.length===highest);
   return {keys:selected.map(match=>match.key),basis:'responsibilities',evidence:[...new Set(selected.flatMap(match=>match.evidence))].slice(0,4)};
  }
  const category=classifyTitle(context.category);
  if(!category.includes('other'))return {keys:category,basis:'employer category',evidence:[context.category]};
 }
 return {keys:classifyTitle(job.title),basis:'title',evidence:[]};
}
export function classifyJobFunctions(job){return jobFunctionResult(job).keys;}
