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

const patterns = {
  data: /\b(?:statistical (?:model(?:ing)?|analysis)|predictive (?:analytics|model(?:ing)?)|machine learning|artificial intelligence|data science|data scientist|data analytics|data analyst|data engineer|experimentation|A\/B testing|causal inference|econometrics|data visualization|business intelligence|SQL|Python|Tableau|Power ?BI|TensorFlow|PyTorch|Spark|pandas|scikit-learn|SAS|R programming)\b/i,
  software: /\b(?:software (?:engineer|engineering|developer|development)|application developer|programmer|write code|build software|develop applications|API development|frontend|front-end|backend|back-end|full[- ]stack|mobile app development|firmware development)\b/i,
  cyber: /\b(?:cybersecurity|information security|security operations center|threat (?:hunting|detection|intelligence)|penetration test|incident response|vulnerability management|identity and access management|security architecture|security engineering|SIEM|Splunk|Nessus|SOC)\b/i,
  it: /\b(?:IT infrastructure|information technology|cloud infrastructure|network (?:administrator|engineer|operations)|systems administrator|database administrator|technical support|help desk|service desk|endpoint management|IT service management|desktop support|systems integration|cloud operations|DevOps|site reliability|AWS|Azure|GCP|Cisco|Kubernetes|Linux|Terraform|VMware)\b/i,
  success: /\b(?:customer success|client success|account management|manage customer accounts|renewal strategy|customer adoption|client relationship management)\b/i,
  service: /\b(?:customer service|customer support|member support|call center|contact center|resolve customer (?:issues|complaints)|answer customer inquiries|patient access support|technical customer support)\b/i,
  healthcareAdmin: /\b(?:healthcare operations|clinical operations|patient access|medical records|provider relations|utilization management|healthcare administration|care coordination operations|credentialing|revenue cycle)\b/i,
  healthcare: /\b(?:patient care|clinical care|nursing care|diagnose|treat patients|administer medication|clinical assessment|physical therapy|registered nurse|licensed practical nurse|physician|pharmacist|therapist|medical assistant)\b/i,
  sales: /\b(?:sell (?:products|services|solutions)|sales quota|sales targets|sales pipeline|close (?:new )?(?:sales|deals)|negotiate sales contracts|business development|generate new business|acquire new customers|account executive|sales representative)\b/i,
  marketing: /\b(?:marketing campaign|marketing strategy|brand strategy|advertising campaign|media planning|search engine marketing|demand generation|content marketing|social media campaign|market research|product marketing)\b/i,
  communications: /\b(?:public relations|press release|corporate communications|internal communications|media relations|community relations|executive communications|public affairs)\b/i,
  creative: /\b(?:graphic design|user experience design|UX design|user interface design|creative direction|visual design|art direction|video production|animation|copywriting|content design)\b/i,
  hr: /\b(?:recruit(?:ment|ing|er)|talent acquisition|employee relations|human resources|compensation and benefits|workforce planning|people operations|employee training|learning and development|HR policies)\b/i,
  finance: /\b(?:financial statements|financial analysis|accounting|accounts payable|accounts receivable|payroll|tax returns|treasury|budgeting|financial audit|underwrite (?:loans|insurance)|insurance claims|actuarial|investment analysis)\b/i,
  legal: /\b(?:legal advice|legal counsel|draft legal|review contracts|litigation|regulatory compliance|compliance investigations|government affairs|legal research|paralegal)\b/i,
  engineering: /\b(?:design|develop|test|analy[sz]e|validate|prototype|model)\b.{0,60}\b(?:mechanical|electrical|hardware|circuits?|structural|robotics|avionics|CAD|engineering drawings?)\b|\b(?:mechanical engineering|electrical engineering|civil engineering|hardware engineering|avionics engineering)\b/i,
  manufacturing: /\b(?:manufacturing operations|production line|operate production equipment|assemble components|CNC machining|welding|fabrication|manufacturing process|production scheduling)\b/i,
  trades: /\b(?:repair equipment|install electrical|HVAC maintenance|field service|plumbing|electrician|mechanic|equipment maintenance|construction trades|on-site repairs)\b/i,
  logistics: /\b(?:supply chain|inventory management|warehouse operations|coordinate shipments|freight|distribution|material planning|logistics operations|transportation planning|fleet operations)\b/i,
  procurement: /\b(?:procurement|purchasing|source suppliers|supplier sourcing|negotiate supplier contracts|purchase orders|vendor selection|strategic sourcing)\b/i,
  operations: /\b(?:business operations|daily operations|facility operations|facilities management|operational processes|process improvement|branch operations|store operations|continuous improvement)\b/i,
  admin: /\b(?:administrative support|executive calendar|office administration|schedule appointments|clerical duties|data entry|receptionist|office supplies|travel arrangements)\b/i,
  projects: /\b(?:project timeline|project budget|program delivery|project plan|coordinate project|manage project|portfolio delivery|project management office|PMO)\b/i,
  product: /\b(?:product roadmap|product requirements|product strategy|prioritize product backlog|product management|product owner|product lifecycle)\b/i,
  business: /\b(?:business strategy|strategic planning|business case|business requirements|market opportunity|corporate development|business performance|business process analysis)\b/i,
  research: /\b(?:scientific research|laboratory experiments|research study|experimental design|research and development|R&D|clinical research|research methods|scientific publication)\b/i,
  quality: /\b(?:quality assurance|quality inspection|safety inspection|quality control|environmental health and safety|EHS|product compliance|safety program|audit quality systems)\b/i,
  retail: /\b(?:retail store|cashier|stock shelves|store inventory|merchandising|personal shopper|checkout|grocery|store associate|store manager)\b/i,
  hospitality: /\b(?:prepare food|cook meals|serve food|restaurant operations|hotel housekeeping|guest services|barista|bartender|food service|hotel operations)\b/i
};

const titleRules = {
  data: /\b(?:data scientist|data analyst|data engineer|analytics (?:engineer|manager|analyst)|bi analyst|business intelligence analyst|statistician|quantitative analyst)\b/i,
  software: /\b(?:software engineer|software development engineer|software developer|application developer|programmer|frontend engineer|backend engineer|full[- ]stack engineer|mobile developer|robotics SW engineer|(?:java|python|C\+\+|golang|ruby|javascript) developer)\b/i,
  cyber: /\b(?:cybersecurity|information security|security engineer|security analyst|penetration tester|threat analyst)\b/i,
  it: /\b(?:IT support|help desk|network administrator|network developer|systems administrator|system integration lead|database administrator|computer operator|cloud administrator|cloud engineer|DevOps engineer|site reliability engineer|technical support|core infrastructure engineer|data center technician|data center infrastructure engineer|application analyst|Epic environments?)\b/i,
  success: /\b(?:customer success|client success|account manager|customer adoption)\b/i,
  service: /\b(?:customer service|customer support|call center|contact center|member services)\b/i,
  healthcareAdmin: /\b(?:clinical operations|healthcare administrator|patient access|medical records|utilization review|provider relations|grievance.{0,10}appeals|care coordinator|care navigator|care manager)\b/i,
  healthcare: /\b(?:nurse|physician|doctor|pharmac(?:ist|y intern|y technician)|clinician|therapist|medical assistant|patient care|clinical specialist|medical social worker|home health aide)\b/i,
  sales: /\b(?:sales|account executive|business development|sales representative|business development representative)\b/i,
  marketing: /\b(?:marketing|marketer|brand manager|digital marketing|content marketing|advertising)\b/i,
  communications: /\b(?:communications|public relations|media relations|public affairs|copywriter)\b/i,
  creative: /\b(?:designer|design director|UX|UI|creative|art director|animator|video producer)\b/i,
  hr: /\b(?:human resources|\bHR\b|recruiter|talent acquisition|people operations|employee relations|compensation|benefits)\b/i,
  finance: /\b(?:accountant|accounting|financial analyst|finance|auditor|tax analyst|payroll|underwriter|claims adjuster|actuary|relationship banker|wealth management client associate|registered wealth management)\b/i,
  legal: /\b(?:attorney|counsel|lawyer|paralegal|legal|compliance|regulatory affairs)\b/i,
  engineering: /\b(?:mechanical engineer|electrical engineer|civil engineer|structural engineer|hardware engineer|avionics engineer|robotics engineer|manufacturing engineer|process engineer|controls engineer|industrial engineer|engineering project team leader|3GPP standards engineer|engineering drawings?|CAD designer)\b/i,
  manufacturing: /\b(?:manufacturing|production|machinist|assembler|welder|machine operator)\b/i,
  trades: /\b(?:electrician|mechanic|HVAC|plumber|field technician|maintenance technician|service technician|tire.{0,8}battery technician|automotive technician|instrumentation.{0,15}automation service engineer)\b/i,
  logistics: /\b(?:supply chain|logistics|warehouse|inventory|driver|courier|fleet|shipping|distribution|freight flow associate|ground handler|MP&L)\b/i,
  procurement: /\b(?:procurement|purchasing|buyer|strategic sourcing|supplier sourcing|vendor manager)\b/i,
  operations: /\b(?:operations|facilities|facility manager|process improvement|branch manager|physical security|security officer|target security specialist|loss prevention|asset protection)\b/i,
  admin: /\b(?:administrative assistant|executive assistant|office manager|receptionist|office coordinator|clerical)\b/i,
  projects: /\b(?:project manager|program manager|PMO|project coordinator)\b/i,
  product: /\b(?:product manager|product owner|product management)\b/i,
  business: /\b(?:business strategist|strategy analyst|business analyst|strategic planning|corporate development)\b/i,
  research: /\b(?:researcher|research scientist|scientist|laboratory|chemist|biologist)\b/i,
  quality: /\b(?:quality|safety|EHS|environmental health)\b/i,
  retail: /\b(?:retail|store associate|cashier|personal shopper|merchandis(?:er|ing)|stocker|member specialist|meat\s*\/?\s*clerk|meat cutter|bakery.?deli clerk|grocery(?: night)?\s*\/?\s*clerk|courtesy clerk|grocery bagger|store(?:\/night)? clerk|fulfillment associate|loader\/cart associate|online grocery|pro experience manager|store manager|store supervisor|general merchandise team leader|member team lead|food & consumables coach|produce clerk|drug-gen mdse\/clerk|fuel center clerk|floral\/dept leader)\b/i,
  hospitality: /\b(?:barista|server|chef|cook|hospitality|housekeeping|food service)\b/i
};

const titlePriority = ['data','software','cyber','it','healthcareAdmin','healthcare','product','projects','procurement','sales','success','service','marketing','communications','creative','finance','legal','hr','engineering','manufacturing','trades','logistics','operations','admin','research','quality','retail','hospitality','business'];
export const JOB_FUNCTION_OPTIONS=Object.entries(JOB_FUNCTIONS).sort((a,b)=>a[1].localeCompare(b[1]));

function countMatches(key, values) {
  return values.filter(value => patterns[key]?.test(value) || dutyRules[key] && dutyMatches(key, value)).length;
}

function decisive(scored, source) {
  const max = Math.max(0, ...Object.values(scored));
  if (!max) return null;
  const winners = Object.keys(scored).filter(key => scored[key] === max);
  if (winners.length !== 1) return { primaryFunction: 'other', basis: source, evidence: [], confidence: 'low', reviewRequired: true, ambiguous: true };
  const key = winners[0];
  const runner = Math.max(0, ...Object.entries(scored).filter(([candidate]) => candidate !== key).map(([, score]) => score));
  const margin = max - runner;
  const confidence = source === 'responsibilities' && margin >= 1 ? 'high' : source === 'required skills' && max >= 2 && margin >= 1 ? 'medium' : source === 'job title' && margin >= 1 ? 'medium' : 'low';
  if(confidence==='low')return null;
  return { primaryFunction: key, basis: source, evidence: [], confidence, reviewRequired: confidence === 'low' };
}

function classifyByEvidence(values, source) {
  const keys = Object.keys(JOB_FUNCTIONS).filter(key => key !== 'other');
  return decisive(Object.fromEntries(keys.map(key => [key, countMatches(key, values)])), source);
}

export function jobFunctionResult(job) {
  const context = job && typeof job === 'object' ? job.functionContext : null;
  if (validFunctionContext(context)) {
    const responsibilities = context.duties || [];
    let result = classifyByEvidence(responsibilities, 'responsibilities');
    if (result && result.primaryFunction !== 'other') {
      result.evidence = responsibilities.filter(text => patterns[result.primaryFunction]?.test(text) || dutyRules[result.primaryFunction] && dutyMatches(result.primaryFunction, text)).slice(0, 4);
      return result;
    }
    if(result?.primaryFunction==='other'){result.evidence=responsibilities.slice(0,4);return result;}
    const skills = [...(context.requiredSkills || []), ...(context.preferredSkills || [])];
    result = classifyByEvidence(skills, 'required skills');
    if (result && result.primaryFunction !== 'other') {
      result.evidence = skills.filter(text => patterns[result.primaryFunction]?.test(text) || dutyRules[result.primaryFunction] && dutyMatches(result.primaryFunction,text)).slice(0, 4);
      return result;
    }
    // A real tie in role duties or skills is intentionally not broken by title.
    if (result?.primaryFunction === 'other'){result.evidence=skills.slice(0,4);return result;}
    const category = typeof context.category === 'string' ? context.category : '';
    return classifyTitle(job?.title, category);
  }
  return classifyTitle(typeof job === 'string' ? job : job?.title, '');
}

function classifyTitle(title, category) {
  const normalized = typeof title === 'string' ? title.replace(/\s+/g, ' ').replace(/[\u2010-\u2015]/g, '-') : '';
  const matches=titlePriority.filter(key=>titleRules[key]?.test(normalized));
  if(matches.includes('retail')&&/\b(?:retail sales|retail customer service|store sales|store associate|grocery|meat clerk|bakery.?deli|member specialist|merchandising service associate)\b/i.test(normalized))return {primaryFunction:'retail',basis:'job title',evidence:[normalized],confidence:'medium',reviewRequired:false};
  if(matches.includes('sales')&&/\b(?:business sales|sales representative|sales account|sales manager|account executive)\b/i.test(normalized))return {primaryFunction:'sales',basis:'job title',evidence:[normalized],confidence:'medium',reviewRequired:false};
  const specific=['data','software','cyber'].filter(key=>matches.includes(key));
  if(specific.length===1)return { primaryFunction:specific[0],basis:'job title',evidence:[normalized],confidence:'medium',reviewRequired:false };
  if(matches.length===1)return { primaryFunction:matches[0],basis:'job title',evidence:[normalized],confidence:'medium',reviewRequired:false };
  if(matches.length>1)return { primaryFunction:'other',basis:'job title',evidence:[normalized],confidence:'low',reviewRequired:true };
  if (category) {
    const categoryMatches=titlePriority.filter(key=>titleRules[key]?.test(category));
    if(categoryMatches.length===1)return { primaryFunction:categoryMatches[0],basis:'employer category',evidence:[category],confidence:'low',reviewRequired:true};
    if(categoryMatches.length>1)return {primaryFunction:'other',basis:'employer category',evidence:[category],confidence:'low',reviewRequired:true};
  }
  return { primaryFunction: 'other', basis: normalized ? 'job title' : 'insufficient evidence', evidence: [], confidence: 'low', reviewRequired: true };
}

export function classifyJobFunctions(job) {
  return [jobFunctionResult(job).primaryFunction];
}

export function isValidJobFunction(value) {
  return typeof value === 'string' && Object.hasOwn(JOB_FUNCTIONS, value);
}
