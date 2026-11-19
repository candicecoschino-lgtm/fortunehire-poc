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
  data: /\b(?:statistical (?:model(?:ing)?|analysis)|predictive (?:analytics|model(?:ing)?)|machine learning|artificial intelligence|data science|data scientist|data analytics|data analyst|data engineer|experimentation|A\/B testing|causal inference|econometrics|data visualization|business intelligence|data pipelines?|analytics platforms?|TensorFlow|PyTorch|pandas|scikit-learn|R programming)\b/i,
  software: /\b(?:software (?:engineer|engineering|developer|development|test)|application developer|programmer|write code|build software|develop applications|API development|RESTful web services|object-oriented programming|frontend|front-end|backend|back-end|full[- ]stack|mobile app development|firmware development|CI\/CD engineering|distributed systems|application architecture|software platform engineering|automation engineering)\b/i,
  cyber: /\b(?:cybersecurity|information security|security operations center|threat (?:hunting|detection|intelligence)|penetration test|incident response|vulnerability management|identity and access management|security architecture|security engineering|SIEM|Splunk|Nessus|SOC)\b/i,
  it: /\b(?:IT infrastructure|information technology|cloud infrastructure|network (?:administrator|engineer|operations|deployment)|systems administrator|database administrator|technical support|help desk|service desk|endpoint management|IT service management|desktop support|systems integration|enterprise integrations|platform APIs|workforce management|time and attendance systems?|cloud operations|DevOps|site reliability|AWS|Azure|GCP|Cisco|Kubernetes|Linux|Terraform|VMware)\b/i,
  success: /\b(?:customer success|client success|account management|manage customer accounts|renewal strategy|customer adoption|client relationship management)\b/i,
  service: /\b(?:customer service|customer support|member support|call center|contact center|resolve customer (?:issues|complaints)|answer customer inquiries|patient access support|technical customer support)\b/i,
  healthcareAdmin: /\b(?:healthcare operations|clinical operations|patient access|medical records|provider relations|utilization management|healthcare administration|care coordination operations|credentialing|revenue cycle)\b/i,
  healthcare: /\b(?:patient care|clinical care|nursing care|diagnose|treat patients|administer medication|clinical assessment|physical therapy|registered nurse|licensed practical nurse|pharmacist|therapist|medical assistant)\b/i,
  sales: /\b(?:sell (?:products|services|solutions)|sales quota|sales targets|sales pipeline|close (?:new )?(?:sales|deals)|negotiate sales contracts|business development|generate new business|acquire new customers|account executive|sales representative|team-based selling|managing a large product portfolio|customer relationships|selling to (?:physician offices|healthcare providers)|presenting to C-suite|gross profit and margin performance|value-based solutions)\b/i,
  marketing: /\b(?:marketing campaign|marketing strategy|brand strategy|advertising campaign|media planning|search engine marketing|demand generation|content marketing|social media campaign|market research|product marketing|client acquisition|prospect events?)\b/i,
  communications: /\b(?:public relations|press release|corporate communications|internal communications|media relations|community relations|executive communications|public affairs)\b/i,
  creative: /\b(?:graphic design|user experience design|UX design|user interface design|creative direction|visual design|art direction|video production|animation|copywriting|content design)\b/i,
  hr: /\b(?:recruit(?:ment|ing|er)|talent acquisition|employee relations|human resources|compensation and benefits|workforce planning|people operations|employee training|learning and development|HR policies)\b/i,
  finance: /\b(?:financial statements|financial analysis|accounting|accounts payable|accounts receivable|payroll|tax returns|tax advisor|indirect tax|treasury|budgeting|budget variance|cost baselines?|cost estimating|cost estimator|reconcile actual spend|financial models?|financial audit|internal audit|underwrite (?:loans|insurance)|insurance claims|actuarial|investment analysis|equity research|fund financing|portfolio and asset analysis|cash flow modeling|LTV migration|risk-based audit plan|risk and control environment|financial and operational audits?)\b/i,
  legal: /\b(?:legal advice|legal counsel|draft legal|review contracts|litigation|regulatory compliance|compliance investigations|government affairs|legal research|paralegal)\b/i,
  engineering: /\b(?:design|develop|test|analy[sz]e|validate|prototype|model)\b.{0,60}\b(?:mechanical|electrical|hardware|circuits?|structural|robotics|avionics|CAD|engineering drawings?)\b|\b(?:mechanical engineering|electrical engineering|civil engineering|hardware engineering|avionics engineering)\b/i,
  manufacturing: /\b(?:manufacturing operations|production line|operate production equipment|assemble components|CNC machining|welding|fabrication|manufacturing process|production scheduling)\b/i,
  trades: /\b(?:repair equipment|install electrical|HVAC maintenance|field service|plumbing|electrician|mechanic|equipment maintenance|construction trades|on-site repairs)\b/i,
  logistics: /\b(?:supply chain|inventory management|inventory control|warehouse operations|distribution cent(?:er|re)|cycle counting|shipping|coordinate shipments|freight|distribution|material planning|logistics operations|transportation planning|fleet operations)\b/i,
  procurement: /\b(?:procurement|purchasing|source suppliers|supplier sourcing|negotiate supplier contracts|purchase orders|vendor selection|strategic sourcing)\b/i,
  operations: /\b(?:business operations|daily operations|facility operations|facilities management|operational processes|process improvement|branch operations|store operations|service delivery model|operational excellence|continuous improvement|Lean Six Sigma|Kaizen|Value Stream Mapping|DMAIC|PDCA|A3 problem solving|operational KPIs?|performance metrics?|distribution network optimization|process mapping|labor planning)\b/i,
  admin: /\b(?:administrative support|executive calendar|office administration|schedule appointments|clerical duties|data entry|receptionist|office supplies|travel arrangements)\b/i,
  projects: /\b(?:project timeline|project budget|program delivery|project plan|coordinate project|manage project|portfolio delivery|project management office|PMO|integrated product team|programmatic execution|control account plans?|resource-loaded schedules?|work breakdown structure|feature-development lifecycle)\b/i,
  product: /\b(?:product roadmap|product direction|product requirements|product strategy|prioritize product backlog|product management|product owner|product lifecycle|pricing and packaging|launch readiness|launch portfolios?)\b/i,
  business: /\b(?:business strategy|strategic planning|business case|business requirements|market opportunity|corporate development|business performance|business process analysis|business development strategy|enterprise strategy|strategic priorities|business direction)\b/i,
  research: /\b(?:scientific research|laboratory experiments|research study|experimental design|research and development|R&D|clinical research|research methods|scientific publication)\b/i,
  quality: /\b(?:quality assurance|quality inspection|safety inspection|quality control|batch quality|environmental health and safety|EHS|product compliance|safety program|audit quality systems|quality control testing|radiation safety)\b/i,
  retail: /\b(?:retail store|retail sales|cashier|stock shelves|store inventory|merchandising|personal shopper|checkout|grocery|store associate|store manager|store shift supervisor|stocking coach)\b/i,
  hospitality: /\b(?:prepare food|cook meals|serve food|restaurant operations|hotel housekeeping|guest services|barista|bartender|food service|hotel operations)\b/i
};

const titleRules = {
  data: /\b(?:data scientist|data analyst|data engineer|analytics (?:engineer|manager|analyst)|bi analyst|business intelligence analyst|statistician|quantitative analyst|forecasting (?:manager|analyst)|demand forecast(?:ing)? (?:manager|analyst))\b/i,
  software: /\b(?:software engineer|software development engineer|software developer|application developer|programmer|frontend engineer|backend engineer|full[- ]stack engineer|mobile developer|robotics software development engineer|robotics SW engineer|AI-native software engineer|software test architect|senior test architect|(?:java|python|C\+\+|golang|ruby|javascript) developer)\b/i,
  cyber: /\b(?:cybersecurity|information security|security engineer|security analyst|penetration tester|threat analyst)\b/i,
  it: /\b(?:IT support|help desk|network administrator|network developer|network deployment planner|NW deployment planner|systems administrator|system integration lead|database administrator|computer operator|cloud administrator|cloud engineer|DevOps engineer|site reliability engineer|technical support|core infrastructure (?:engineer|lead)|data center technician|data center infrastructure engineer|application analyst|application platform manager|workforce management (?:and )?time & attendance solutions? manager|Epic environments?)\b/i,
  success: /\b(?:customer success|client success|account manager|customer adoption)\b/i,
  service: /\b(?:customer service|customer support|call center|contact center|member services|tech support representative|technical support representative)\b/i,
  healthcareAdmin: /\b(?:clinical operations|healthcare administrator|patient access|field reimbursement|practice management|practice manager|medical records|utilization review|provider relations|grievance.{0,10}appeals|care coordinator|care navigator|care manager|behavioral health liaison|member care liaison)\b/i,
  healthcare: /\b(?:registered nurse|\bRN\b|\bLPN\b|nurse|physician|anesthesiologist|surgeon|doctor|pharmac(?:ist|y intern|y technician)|clinical (?:lab|laboratory) scientist|clinician|physical therapist assistant|\bPTA\b|therapist|medical assistant|patient care|clinical specialist|medical social worker|home health aide)\b/i,
  sales: /\b(?:business sales|field sales|Medicare sales|sales representative|sales res?presentative|sales specialist|sales account|sales manager|sales executive|sales consultant|account executive|business development|business development representative)\b/i,
  marketing: /\b(?:marketing|marketer|brand manager|digital marketing|content marketing|advertising)\b/i,
  communications: /\b(?:communications? (?:specialist|manager|director|coordinator|representative|intern)|public relations|media relations|public affairs|copywriter)\b/i,
  creative: /\b(?:graphic designer|visual designer|product designer|learning experience designer|LXD|design director|UX|UI|creative|art director|animator|video producer|studio production coordinator)\b/i,
  hr: /\b(?:human resources|\bHR\b|recruiter|talent acquisition|people operations|employee relations|compensation|benefits)\b/i,
  finance: /\b(?:accountant|accounting|financial analyst|credit analyst|cost estimator|cost analyst|finance|auditor|internal audit|tax (?:analyst|advisor)|indirect tax|fund financing trader|equity research|portfolio analyst|payroll|underwriter|claims adjuster|actuary|relationship banker|wealth management client associate|registered wealth management)\b/i,
  legal: /\b(?:attorney|counsel|lawyer|paralegal|legal|compliance|regulatory affairs)\b/i,
  engineering: /\b(?:systems engineering manager|mechanical engineer|electrical engineer|electrical (?:technical )?designer|civil engineer|structural (?:&|and) payloads? design engineer|structural design engineer|design and release engineer|hardware engineer|post silicon engineer|electrophysics engineer|avionics engineer|drone avionics engineer|robotics engineer|manufacturing engineer|product engineering manager|process engineer|controls engineer|data center controls engineer|data center electrical field engineer|industrial engineer|engineering project team leader|optical systems liaison engineer|innovation and design engineer|test development engineer|test architect|3GPP standards engineer|guidance, navigation,? and control (?:\(GNC\) )?engineer|GNC engineer|environmental remediation engineer|thermal systems engineer|electromechanical engineer|engineering drawings?|CAD designer)\b/i,
  manufacturing: /\b(?:manufacturing|production (?:operator|associate|supervisor|manager)|machinist|assembler|welder|machine operator)\b/i,
  trades: /\b(?:electrician|mechanic|HVAC|plumber|field technician|maintenance technician|service technician|machine operator|supervisor lab service engineering|flight simulator maintenance supervisor|simulator technician|tire.{0,8}battery technician|automotive technician|instrumentation.{0,15}automation service engineer)\b/i,
  logistics: /\b(?:supply chain coordinator|supply chain|logistics|warehouse|inventory (?:control|coordinator|specialist)|driver|dispatcher|courier|fleet|shipping|distribution|freight flow associate|ground handler|MP&L)\b/i,
  procurement: /\b(?:procurement|purchasing|buyer|strategic sourcing|supplier sourcing|vendor manager)\b/i,
  operations: /\b(?:operations|facilities|facility manager|process improvement|branch manager|area manager|process assistant|physical security|security officer|target security specialist|loss prevention|asset protection)\b/i,
  admin: /\b(?:administrative assistant|executive assistant|office manager|receptionist|office coordinator|clerical)\b/i,
  projects: /\b(?:project manager|program manager|PMO|project coordinator|engineering project team leader|technical infrastructure program manager)\b/i,
  product: /\b(?:product manager|product owner|product management)\b/i,
  business: /\b(?:business strategist|strategy analyst|business analyst|business execution lead|enterprise strategy|strategic planning|corporate development)\b/i,
  research: /\b(?:researcher|research scientist|research associate|scientific researcher|chemist|biologist)\b/i,
  quality: /\b(?:quality|safety|EHS|environmental health)\b/i,
  retail: /\b(?:retail sales(?: consultant| associate| representative)?|retail (?:sales|store) (?:associate|manager|representative)|retail customer service associate|store associate|cashier|personal shopper|merchandis(?:er|ing)|stocker|stocking (?:coach|lead|supervisor)|member specialist|meat\s*\/?\s*clerk|meat cutter|bakery.?deli clerk|grocery(?: night)?\s*\/?\s*clerk|courtesy clerk|grocery bagger|store(?:\/night)? clerk|fulfillment associate|loader\/cart associate|online grocery|pro experience manager|store manager|assistant store manager|general merchandise team leader|member team lead|food & consumables coach|produce clerk|drug-gen mdse\/clerk|fuel center clerk|floral\/dept leader)\b/i,
  hospitality: /\b(?:barista|server|chef|cook|hospitality|housekeeping|food service)\b/i
};

const titlePriority = ['data','software','cyber','it','healthcareAdmin','healthcare','product','projects','procurement','sales','success','service','marketing','communications','creative','finance','legal','hr','engineering','manufacturing','trades','logistics','operations','admin','research','quality','retail','hospitality','business'];
export const JOB_FUNCTION_OPTIONS=Object.entries(JOB_FUNCTIONS).sort((a,b)=>a[1].localeCompare(b[1]));

function evidenceScores(values, source) {
  const keys = Object.keys(JOB_FUNCTIONS).filter(key => key !== 'other');
  const matcher = source === 'responsibilities'
    ? (key, value) => dutyMatches(key, value)
    : (key, value) => patterns[key]?.test(value) || false;
  return Object.fromEntries(keys.map(key => [key, values.reduce((score, value, index) => {
    if (!matcher(key, value)) return score;
    // Duties are already the primary evidence set; their list position is not
    // reliable enough to triple-weight the first few extracted sentences.
    const weight = 1;
    return score + weight;
  }, 0)]));
}

function decisive(scored, source) {
  const max = Math.max(0, ...Object.values(scored));
  if (!max) return null;
  const winners = Object.keys(scored).filter(key => scored[key] === max);
  if (winners.length !== 1) return { primaryFunction: 'other', basis: source, evidence: [], confidence: 'low', reviewRequired: true, ambiguous: true, candidates: winners };
  const key = winners[0];
  const runner = Math.max(0, ...Object.entries(scored).filter(([candidate]) => candidate !== key).map(([, score]) => score));
  const margin = max - runner;
  const confidence = source === 'responsibilities' && margin >= 2 && max >= 3 ? 'high' : source === 'responsibilities' && max >= 1 && margin >= 1 ? 'medium' : source === 'required skills' && max >= 2 && margin >= 1 ? 'medium' : 'low';
  // Keep weak responsibility matches visible. Falling through to a title or
  // employer category erased conflicting duty evidence and caused false wins.
  if (confidence === 'low') return { primaryFunction: 'other', basis: source, evidence: [], confidence: 'low', reviewRequired: true, ambiguous: true, candidates: winners };
  return { primaryFunction: key, basis: source, evidence: [], confidence, reviewRequired: false, candidates: [key] };
}

function titleCandidates(title) {
  const normalized = typeof title === 'string' ? title.replace(/\s+/g, ' ').replace(/[\u2010-\u2015]/g, '-') : '';
  if (/\bsales operations analyst\b/i.test(normalized)) return [];
  if (/\b(?:facilities project manager|project manager|program manager|project coordinator)\b/i.test(normalized)) return ['projects'];
  if (/\blead infrastructure engineer\b/i.test(normalized)) return ['it'];
  if (/\b(?:design and release|release) engineer\b/i.test(normalized)) return ['engineering'];
  if (/\btechnical product manager\b/i.test(normalized)) return ['product'];
  if (/\b(?:application platform|platforms? technology) director\b/i.test(normalized)) return ['software'];
  if (/\bsupervisor\b.{0,30}\bflight simulator maintenance\b/i.test(normalized)) return ['trades'];
  if (/\b(?:landing gear\b.{0,50}\bengineer|engineer\b.{0,50}\blanding gear)\b/i.test(normalized)) return ['engineering'];
  if (/\b(?:internal audit|audit manager)\b/i.test(normalized)) return ['finance'];
  if (/\b(?:healthcare )?sales account executive\b/i.test(normalized)) return ['sales'];
  if (/\bdirector\b.{0,70}\b(?:order fulfillment|dealer platforms?)\b/i.test(normalized)) return ['software'];
  if (/\b(?:business process improvement|operational excellence|continuous improvement)\b/i.test(normalized)) return ['operations'];
  if (/\bsupply chain coordinator\b/i.test(normalized)) return ['logistics'];
  if (/\b(?:business process improvement|operational excellence|continuous improvement)\b/i.test(normalized)) return ['operations'];
  if (/\b(?:creative director|design director|art director)\b/i.test(normalized)) return ['creative'];
  if (/\b(?:field sales|medicare field sales)\b/i.test(normalized)) return ['sales'];
  if (/\b(?:transportation coordinator|delivery dispatcher|driver dispatcher)\b/i.test(normalized)) return ['logistics'];
  if (/\b(?:field reimbursement|behavioral health liaison|care management liaison)\b/i.test(normalized)) return ['healthcareAdmin'];
  if (/\b(?:fund financing trader|indirect tax advisor|tax advisor)\b/i.test(normalized)) return ['finance'];
  if (/\b(?:assistant store manager|store manager|stocking coach|stocking supervisor)\b/i.test(normalized)) return ['retail'];
  if (/\bexecutive assistant\b/i.test(normalized)) return ['admin'];
  const matches = titlePriority.filter(key => titleRules[key]?.test(normalized));
  if (matches.includes('sales') && /\b(?:business sales|sales representative|sales account|sales manager|account executive|sales executive|sales consultant)\b/i.test(normalized) && !/\bretail sales\b/i.test(normalized)) return ['sales'];
  if (matches.includes('sales') && /\bretail sales\b/i.test(normalized) && /\bconsultant\b/i.test(normalized)) return ['retail'];
  if (matches.includes('retail') && /\b(?:retail sales|retail customer service|store sales|store associate|grocery|meat clerk|bakery.?deli|member specialist|merchandising service associate)\b/i.test(normalized)) return ['retail'];
  const specific = ['data','software','cyber'].filter(key => matches.includes(key));
  if (specific.length === 1) return specific;
  if (matches.includes('engineering') && /\b(?:engineer|engineering|technical designer|test architect)\b/i.test(normalized)) return ['engineering'];
  if (matches.includes('manufacturing') && /\b(?:manufacturing operations manager|production manager)\b/i.test(normalized)) return ['manufacturing'];
  if (matches.includes('operations') && /\barea manager\b/i.test(normalized) && !/\b(?:sales|account|territory)\b/i.test(normalized)) return ['operations'];
  return matches;
}

export function jobFunctionResult(job) {
  const context = job && typeof job === 'object' ? job.functionContext : null;
  if (validFunctionContext(context)) {
    const responsibilities = (context.duties || []).filter(text => typeof text === 'string' && text.trim());
    const skills = [...(context.requiredSkills || []), ...(context.preferredSkills || [])].filter(isUsableSkill);
    const responsibilityResult = decisive(evidenceScores(responsibilities, 'responsibilities'), 'responsibilities');
    const skillResult = decisive(evidenceScores(skills, 'required skills'), 'required skills');
    const titleKeys = titleCandidates(job?.title);
    if (responsibilityResult && !responsibilityResult.ambiguous) {
      responsibilityResult.evidence = responsibilities.filter(text => dutyMatches(responsibilityResult.primaryFunction, text)).slice(0, 4);
      return responsibilityResult;
    }
    if (responsibilityResult?.ambiguous) {
      const compatibleTitle = titleKeys.filter(key => responsibilityResult.candidates.includes(key));
      const skillSupportsTitle = !skillResult || compatibleTitle.some(key => skillResult.primaryFunction === key || skillResult.ambiguous && skillResult.candidates.length === 1 && skillResult.candidates[0] === key);
      if (compatibleTitle.length === 1 && skillSupportsTitle) return { primaryFunction: compatibleTitle[0], basis: 'responsibilities', evidence: [...responsibilities.filter(text => dutyMatches(compatibleTitle[0], text)).slice(0, 3), job.title].slice(0, 4), confidence: 'medium', reviewRequired: true };
      if (skillResult && !skillResult.ambiguous && responsibilityResult.candidates.includes(skillResult.primaryFunction)) {
        return { primaryFunction: skillResult.primaryFunction, basis: 'responsibilities', evidence: [...responsibilities.filter(text => dutyMatches(skillResult.primaryFunction, text)).slice(0, 3), ...skills.filter(text => patterns[skillResult.primaryFunction]?.test(text)).slice(0, 2)].slice(0, 4), confidence: 'medium', reviewRequired: true };
      }
      return { primaryFunction: 'other', basis: 'responsibilities', evidence: responsibilities.slice(0, 4), confidence: 'low', reviewRequired: true };
    }
    if (skillResult && !skillResult.ambiguous) {
      if (titleKeys.length && !titleKeys.includes(skillResult.primaryFunction)) return { primaryFunction: 'other', basis: 'required skills', evidence: skills.slice(0, 4), confidence: 'low', reviewRequired: true };
      skillResult.evidence = skills.filter(text => patterns[skillResult.primaryFunction]?.test(text)).slice(0, 4);
      return skillResult;
    }
    if (skillResult?.ambiguous) {
      const compatibleTitle = titleKeys.filter(key => skillResult.candidates.includes(key));
      if (compatibleTitle.length === 1) return { primaryFunction: compatibleTitle[0], basis: 'required skills', evidence: [...skills.filter(text => patterns[compatibleTitle[0]]?.test(text)).slice(0, 3), job.title].slice(0, 4), confidence: 'medium', reviewRequired: true };
      return { primaryFunction: 'other', basis: 'required skills', evidence: skills.slice(0, 4), confidence: 'low', reviewRequired: true };
    }
    const category = typeof context.category === 'string' ? context.category : '';
    return classifyTitle(job?.title, category);
  }
  return classifyTitle(typeof job === 'string' ? job : job?.title, '');
}

function isUsableSkill(value) {
  return typeof value === 'string' && value.trim().length >= 3
    && !/\b(?:degree|bachelor|master|diploma|education|minimum requirements?|years? of experience|hours per week|pay transparency|salary|benefits?|shift|work location|relocation|authorized to work|accommodation)\b/i.test(value);
}

function classifyTitle(title, category) {
  const normalized = typeof title === 'string' ? title.replace(/\s+/g, ' ').replace(/[\u2010-\u2015]/g, '-') : '';
  const matches = titleCandidates(normalized);
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
