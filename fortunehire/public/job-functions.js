import { dutyRules, dutyMatches, validFunctionContext } from './function-duties.js';

// Stable keys keep existing filter URLs and saved searches usable. Labels are
// intentionally alphabetized by display text in the filter component.
export const JOB_FUNCTIONS = {
  admin: 'Administrative & Office Support',
  business: 'Business Strategy & Planning',
  communications: 'Communications & Public Relations',
  service: 'Customer Service & Support',
  success: 'Customer Success & Account Management',
  data: 'Data & Analytics',
  creative: 'Design & Creative',
  engineering: 'Engineering',
  finance: 'Finance & Accounting',
  hospitality: 'Food Service & Hospitality',
  healthcareAdmin: 'Healthcare Administration & Operations',
  healthcare: 'Healthcare & Clinical Care',
  hr: 'Human Resources & Talent',
  it: 'IT Infrastructure & Support',
  legal: 'Legal & Compliance',
  manufacturing: 'Manufacturing & Production',
  marketing: 'Marketing & Advertising',
  operations: 'Operations & Facilities',
  product: 'Product Management',
  projects: 'Program & Project Management',
  procurement: 'Purchasing & Procurement',
  quality: 'Quality & Safety',
  research: 'Research & Science',
  retail: 'Retail & Store Operations',
  sales: 'Sales & Business Development',
  software: 'Software Engineering & Development',
  logistics: 'Supply Chain & Logistics',
  trades: 'Trades & Field Service',
  cyber: 'Cybersecurity & Information Security',
  other: 'Other / Unclassified'
};

// First match is the clearest named occupation family. Keep these patterns specific
// and ordered so a modifier such as “marketing” cannot displace “data scientist”.
const titleRules = [
  ['data', /\b(?:data scientist|data analyst|data engineer|analytics (?:engineer|manager|analyst)|business intelligence (?:analyst|engineer)|business intel(?:ligence)? engineer|BI analyst|laboratory analytics|statistician|quantitative analyst|machine learning (?:engineer|scientist)|AI\/ML (?:engineer|scientist))\b/i],
  ['cyber', /\b(?:cybersecurity|cyber security|information security|penetration tester|threat analyst|security operations analyst)\b/i],
  ['healthcareAdmin', /\b(?:medical receptionist|patient access|care coordinator|care navigator|medical records|provider relations|utilization review|healthcare administrator|clinical operations|health economics|reimbursement director)\b/i],
  ['healthcare', /\b(?:registered nurse|\bRN\b|\bLPN\b|nurse|physician|doctor|pharmacist|pharmacy technician|pharmacy manager|medical dosimetrist|PRN laboratory technician|medical laboratory technician|therapist|medical assistant|optician|hearing aid dispenser|IV technician|clinical scientist|clinical lab scientist|clinical specialist|oncology specialist|home health aide)\b/i],
  ['retail', /\b(?:retail|store associate|store manager|assistant manager.{0,30}store|store.{0,30}assistant manager|cashier|personal shopper|merchandiser|stocker|stocking coach|meat cutter|grocery clerk|member specialist)\b/i],
  ['finance', /\b(?:accountant|accounting|financial analyst|finance manager|finance analyst|financial planning (?:and|&) analysis|FP&A|commercial credit analyst|credit analyst|financial advisor|financial solutions advisor|private wealth client associate|wealth client associate|trust officer|consumer investments|treasury sales client officer|private bank|real estate sales associate|(?:business )?banking relationship manager|pricing analyst|pricing specialist|estimating and pricing specialist|auditor|internal audit|tax advisor|payroll|underwriter|claims adjuster|actuary|banker|relationship banker|wealth management)\b/i],
  ['sales', /\b(?:sales (?:representative|res?presentative|specialist|manager|executive|consultant|account manager|program|engineer|development representative)|inside sales|field sales|account executive|business development (?:representative|manager)|customer solutions representative|global sales accounts director)\b/i],
  ['success', /\b(?:customer success|client success|customer adoption|digital adoption representative|account manager|client relationship manager)\b/i],
  ['service', /\b(?:customer service|customer support|call center|contact center|member services|technical support representative)\b/i],
  ['product', /\b(?:product manager|product owner|product management|product mgmt|technical product manager|digital product manager|manager.{0,20}digital product)\b/i],
  ['projects', /\b(?:project manager|program manager|project coordinator|program coordinator|project management|program management|project controls|project planner|program planner|integrated product team lead|IPT lead|integrated planning and scheduling|planning and scheduling specialist)\b/i],
  ['procurement', /\b(?:procurement|purchasing|buyer|strategic sourcing|supplier sourcing)\b/i],
  ['marketing', /\b(?:marketing|brand manager|social media manager|advertising|demand generation)\b/i],
  ['communications', /\b(?:communications? (?:specialist|manager|director|coordinator|lead analyst|senior advisor|associate manager)|corporate communications|CEO communications|social media communications|public relations|media relations|public affairs)\b/i],
  ['creative', /\b(?:graphic designer|UX designer|UI designer|user experience designer|visual designer|art director|video producer|animator|creative director|studio.{0,12}production coordinator)\b/i],
  ['hr', /\b(?:human resources|HR (?:specialist|manager|business partner)|recruiter|talent acquisition|employee (?:relations|development)|benefits specialist)\b/i],
  ['legal', /\b(?:attorney|lawyer|paralegal|legal counsel|compliance (?:analyst|officer|specialist|manager)|regulatory affairs)\b/i],
  ['software', /\b(?:software (?:engineer|developer|architect|program manager|asset management)|software development engineer|robotics SW engineer|senior test architect|test architect|application developer|programmer|frontend engineer|backend engineer|full[- ]stack engineer|mobile developer)\b/i],
  ['it', /\b(?:IT (?:manager|support|business partner|core infrastructure|service|portfolio management analyst)|information technology business partner|help desk|support engineer|network (?:administrator|engineer|deployment planner|deploy technician)|infra delivery technician|NW deployment planner|systems administrator|system integration lead|core infrastructure lead|database administrator|cloud (?:administrator|engineer)|cloud application architect(?:ure)?|solutions architect|DevOps engineer|site reliability engineer|data center (?:infrastructure )?(?:engineer|technician)|ML infrastructure engineer|(?:hardware )?asset management specialist|business systems analyst|application analyst|IT operations engineer)\b/i],
  ['quality', /\b(?:quality (?:assurance|control|inspector|engineer|specialist|manager)|product acceptance|test and evaluation|test & evaluation|electromagnetic compatibility technician|functional safety|safety (?:specialist|manager|officer)|EHS|environmental health and safety)\b/i],
  ['manufacturing', /\b(?:manufacturing (?:engineer|technician|operator|associate|supervisor|manager|technology analyst)|engineer.{0,25}manufacturing|production (?:operator|associate|supervisor|manager)|assembler|machinist|machine operator|welder)\b/i],
  ['trades', /\b(?:electrician|mechanic|HVAC technician|maintenance (?:technician|specialist|mechanic)|facilities plant maintenance|equipment maintenance|field technician|service technician|service engineer|aircraft painter|custom painter|plumber|installer|avionics technician)\b/i],
  ['engineering', /\b(?:(?:mechanical|electrical|civil|structural|hardware|avionics|robotics|industrial|process|controls|design and release|RF|vehicle design|instrumentation|automation|test development|systems?) engineer|RF systems? integration engineer|RF design engineer|systems? integration engineer|engineering (?:manager|specialist|analyst|team leader|project team leader)|systems engineering analyst|electrical (?:technical )?designer|engineer(?:ing)? II|engineer|HW regulatory compliance engineer|CPU microarchitect|RTL design engineer|phased array RF front end architect|robotics (?:and )?autonomy validation architect|CAD designer|microarchitect)\b/i],
  ['logistics', /\b(?:supply chain|logistics|warehouse|ground handler|transportation analyst|inventory (?:control|coordinator|specialist|management|associate)|stores controller|driver|dispatcher|fleet|shipping|distribution|freight)\b/i],
  ['operations', /\b(?:operations (?:manager|analyst|specialist|supervisor)|ops manager|custody operations|facilities manager|facility manager|branch manager|area manager|process assistant|process improvement|continuous improvement|government property management|property management|value chain designer)\b/i],
  ['admin', /\b(?:administrative assistant|executive assistant|office manager|office coordinator|receptionist|clerical)\b/i],
  ['research', /\b(?:researcher|research scientist|research associate|chemist|biologist|laboratory scientist|labs? internship)\b/i],
  ['hospitality', /\b(?:barista|server|chef|cook|housekeeper|hospitality|food service)\b/i],
  ['business', /\b(?:business analyst|strategy analyst|business strategist|corporate development|strategic planning|chief of staff)\b/i]
];

const skillRules = {
  data: /\b(?:statistical modeling|machine learning|predictive analytics|econometrics|TensorFlow|PyTorch|scikit-learn|data pipelines|business intelligence)\b/i,
  software: /\b(?:software development|programming languages?|object-oriented programming|application architecture|CI\/CD)\b/i,
  cyber: /\b(?:penetration testing|incident response|vulnerability management|SIEM|identity and access management)\b/i,
  it: /\b(?:cloud infrastructure|network administration|Linux administration|Kubernetes|Terraform|VMware)\b/i,
  finance: /\b(?:GAAP|financial accounting|tax accounting|financial modeling|accounts payable|accounts receivable)\b/i,
  engineering: /\b(?:CAD|mechanical design|electrical design|circuit design|systems engineering)\b/i,
  healthcare: /\b(?:patient care|clinical assessment|medication administration|phlebotomy|patient treatment)\b/i,
  healthcareAdmin: /\b(?:medical coding|medical records|patient scheduling|revenue cycle|utilization management)\b/i,
  hr: /\b(?:talent acquisition|employee relations|benefits administration|payroll administration|HRIS)\b/i,
  sales: /\b(?:sales pipeline|sales quota|CRM|negotiation|account planning)\b/i,
  marketing: /\b(?:campaign management|brand strategy|search engine marketing|content marketing|media planning)\b/i,
  legal: /\b(?:legal research|contract drafting|litigation|regulatory compliance|paralegal studies)\b/i,
  logistics: /\b(?:inventory control|freight management|warehouse management|transportation planning|fleet management)\b/i,
  procurement: /\b(?:strategic sourcing|vendor selection|purchase order management|supplier negotiation)\b/i,
  quality: /\b(?:quality assurance|quality control|safety auditing|root cause analysis|ISO 9001)\b/i,
  manufacturing: /\b(?:CNC machining|production operations|assembly|welding|manufacturing processes)\b/i,
  trades: /\b(?:HVAC|electrical repair|plumbing|equipment maintenance|field service)\b/i,
  projects: /\b(?:project management|program management|schedule management|project budgeting|PMP)\b/i,
  product: /\b(?:product roadmap|product management|product requirements|user stories|backlog prioritization)\b/i,
  research: /\b(?:laboratory research|experimental design|scientific research|clinical research)\b/i,
  retail: /\b(?:retail operations|merchandising|point of sale|store operations)\b/i,
  hospitality: /\b(?:food preparation|food safety|guest services|restaurant operations)\b/i,
  communications: /\b(?:public relations|media relations|press releases|corporate communications)\b/i,
  creative: /\b(?:graphic design|UX design|visual design|video production|Adobe Creative Suite)\b/i,
  service: /\b(?:customer support|call center|contact center|service recovery)\b/i,
  success: /\b(?:customer success|customer adoption|account renewals|client success)\b/i,
  operations: /\b(?:process improvement|Lean Six Sigma|operational excellence|facility operations)\b/i,
  admin: /\b(?:administrative support|calendar management|office administration|records management)\b/i,
  business: /\b(?:business strategy|strategic planning|business analysis|corporate strategy)\b/i
};

export const JOB_FUNCTION_OPTIONS=Object.entries(JOB_FUNCTIONS).sort((a,b)=>a[1].localeCompare(b[1]));

function makeResult(primaryFunction, basis, evidence, reviewRequired=false) {
  return {primaryFunction,basis,evidence:evidence.slice(0,4),confidence:reviewRequired?'low':'medium',reviewRequired};
}

function matchingFunctions(values, matcher) {
  const found=new Set();
  for(const value of values) for(const [key,rule] of Object.entries(matcher)) if(rule.test(value)) found.add(key);
  return [...found];
}

function classifyTitle(title) {
  const normalized=typeof title==='string'?title.replace(/\s+/g,' ').replace(/[\u2010-\u2015]/g,'-').trim():'';
  if(!normalized)return null;
  return titleRules.find(([,rule])=>rule.test(normalized))?.[0]||null;
}

function cleanEvidence(values) {
  return values.filter(value=>typeof value==='string'&&value.trim().length>=8&&!/\b(?:salary|pay transparency|benefits|shift schedule|work location|equal opportunity|accommodation)\b/i.test(value));
}

export function jobFunctionResult(job) {
  const title=typeof job==='string'?job:job?.title;
  const context=typeof job==='object'&&validFunctionContext(job.functionContext)?job.functionContext:null;
  const duties=cleanEvidence(context?.duties||[]);
  const skills=cleanEvidence(context?.requiredSkills||[]);
  const titleFunction=classifyTitle(title);
  const dutyFunctions=matchingFunctions(duties,dutyRules);
  const skillFunctions=matchingFunctions(skills,skillRules);

  if(titleFunction){
    const disagreement=dutyFunctions.length===1&&dutyFunctions[0]!==titleFunction;
    const support=duties.filter(duty=>dutyMatches(titleFunction,duty));
    return makeResult(titleFunction,'job title',[title,...support],disagreement);
  }
  if(dutyFunctions.length===1){
    const key=dutyFunctions[0];
    return makeResult(key,'responsibilities',duties.filter(duty=>dutyMatches(key,duty)));
  }
  if(dutyFunctions.length>1){
    const overlap=dutyFunctions.filter(key=>skillFunctions.includes(key));
    if(overlap.length===1){const key=overlap[0];return makeResult(key,'responsibilities',[...duties.filter(duty=>dutyMatches(key,duty)),...skills.filter(skill=>skillRules[key]?.test(skill))],true);}
    return makeResult('other','responsibilities',duties,true);
  }
  if(skillFunctions.length===1){const key=skillFunctions[0];return makeResult(key,'required skills',skills.filter(skill=>skillRules[key]?.test(skill)),true);}
  return makeResult('other',title?'job title':'insufficient evidence',title?[title]:[],true);
}

export function classifyJobFunctions(job) {
  return [jobFunctionResult(job).primaryFunction];
}

export function isValidJobFunction(value) {
  return typeof value === 'string' && Object.hasOwn(JOB_FUNCTIONS, value);
}
