// Action plus work-object phrases: broad industry words alone are not evidence.
export const dutyRules = {
  data: /\b(?:build|develop|validate|deploy|evaluate|analyze|analyse|model|forecast|measure|interpret)\b.{0,100}\b(?:statistical models?|predictive models?|machine learning|datasets?|data pipelines?|experiments?|A\/B tests?|causal effects?|dashboards?|data quality|analytical models?)\b/i,
  software: /\b(?:design|write|build|develop|test|debug|maintain|deploy)\b.{0,80}\b(?:software|applications?|APIs|code|services|web platforms?|mobile apps?|firmware)\b/i,
  cyber: /\b(?:detect|investigate|respond to|mitigate|prevent|assess|monitor|secure)\b.{0,90}\b(?:cyber threats?|security incidents?|vulnerabilities|intrusions|access controls?|security risks?)\b/i,
  it: /\b(?:administer|operate|maintain|configure|troubleshoot|support|monitor)\b.{0,90}\b(?:networks?|cloud infrastructure|IT systems?|databases?|endpoints?|service desk|computer systems?)\b/i,
  success: /\b(?:improve|manage|drive|support|grow)\b.{0,80}\b(?:customer adoption|client relationships?|account renewals?|customer outcomes?|account portfolios?)\b/i,
  service: /\b(?:resolve|answer|handle|respond to)\b.{0,70}\b(?:customer inquiries|member questions|customer complaints|support requests|service issues|client concerns)\b/i,
  healthcareAdmin: /\b(?:coordinate|manage|review|process|improve)\b.{0,80}\b(?:patient access|clinical operations|provider records|utilization reviews?|medical records|care operations|healthcare services?)\b/i,
  healthcare: /\b(?:provide|deliver|coordinate|assess|evaluate|manage)\b.{0,70}\b(?:patient care|clinical care|nursing care|treatment plans?)\b|\b(?:diagnose|treat|examine) patients\b/i,
  sales: /\b(?:sell|negotiate|close|win|develop|manage|grow)\b.{0,80}\b(?:sales|customer accounts?|client portfolios?|sales pipeline|new business|revenue targets?)\b/i,
  marketing: /\b(?:develop|manage|execute|measure|optimize|create)\b.{0,80}\b(?:marketing campaigns?|brand strategy|advertising|content strategy|demand generation|product marketing)\b/i,
  communications: /\b(?:write|prepare|manage|deliver|coordinate)\b.{0,80}\b(?:press releases?|media relations?|internal communications?|public relations|executive communications?)\b/i,
  creative: /\b(?:design|create|produce|edit|illustrate)\b.{0,80}\b(?:visual assets?|user experiences?|user interfaces?|creative content|graphics|videos?|animations?)\b/i,
  hr: /\b(?:recruit|hire|onboard|administer|resolve|investigate|manage)\b.{0,80}\b(?:employees|candidates|employee relations|benefits programs?|compensation programs?|HR policies|talent pipelines?)\b/i,
  finance: /\b(?:prepare|analyze|analyse|review|reconcile|process|underwrite)\b.{0,80}\b(?:financial statements?|financial reports?|tax returns?|accounts payable|accounts receivable|payroll|insurance claims?|loan applications?)\b/i,
  legal: /\b(?:draft|review|negotiate|interpret)\b.{0,80}\b(?:legal documents?|contracts?|commercial agreements?|regulatory filings?)\b|\b(?:provide|deliver) legal (?:advice|counsel)\b/i,
  engineering: /\b(?:design|develop|test|analyze|analyse|validate)\b.{0,80}\b(?:mechanical systems?|electrical systems?|hardware|circuits?|structural components?|engineering drawings?|CAD models?)\b/i,
  manufacturing: /\b(?:operate|maintain|repair|set up|assemble|weld|fabricate|machine)\b.{0,80}\b(?:production equipment|manufacturing equipment|components?|parts|products|CNC machines?)\b/i,
  trades: /\b(?:install|repair|inspect|maintain|service)\b.{0,80}\b(?:electrical systems?|HVAC|plumbing|field equipment|building systems?|industrial equipment)\b/i,
  logistics: /\b(?:manage|coordinate|optimize|plan|pick|pack|ship|receive|deliver|transport)\b.{0,80}\b(?:supply chains?|shipments?|inventory levels?|order fulfillment|freight|packages?|goods|warehouse operations)\b/i,
  procurement: /\b(?:source|select|negotiate with|manage)\b.{0,80}\b(?:suppliers?|vendors?|purchase orders?|procurement contracts?)\b/i,
  operations: /\b(?:manage|oversee|improve|coordinate|supervise|optimize)\b.{0,80}\b(?:business operations|operational processes|facility operations|daily operations|branch operations|facilities|maintenance)\b/i,
  admin: /\b(?:manage|coordinate|maintain|schedule|organize|arrange)\b.{0,80}\b(?:executive calendars?|office supplies|travel arrangements?|appointments?|meetings?)\b|\b(?:perform|provide) (?:data entry|administrative support|clerical duties)\b/i,
  projects: /\b(?:manage|coordinate|lead|track|deliver)\b.{0,80}\b(?:project timelines?|project budgets?|project plans?|program delivery|project portfolios?)\b/i,
  product: /\b(?:define|prioritize|manage|develop)\b.{0,80}\b(?:product roadmaps?|product requirements?|product backlog|product strategy)\b/i,
  business: /\b(?:analyze|analyse|evaluate|develop|document)\b.{0,80}\b(?:business requirements?|business performance|business strategy|market opportunities|business cases?|business processes?)\b/i,
  research: /\b(?:conduct|design|perform|lead|interpret)\b.{0,80}\b(?:scientific research|laboratory experiments?|clinical research|research studies|experimental data|laboratory results?)\b/i,
  quality: /\b(?:perform|conduct|lead|inspect|audit|implement)\b.{0,80}\b(?:quality inspections?|safety inspections?|quality audits?|safety audits?|quality assurance|safety programs?)\b/i,
  retail: /\b(?:stock|replenish|merchandise|operate|manage)\b.{0,80}\b(?:store shelves|store inventory|cash registers?|checkout lanes?|retail displays?)\b/i,
  hospitality: /\b(?:prepare|cook|serve|clean|maintain|manage)\b.{0,80}\b(?:food|meals|beverages|guest rooms?|restaurant operations|hotel rooms?)\b/i
};

export function validFunctionContext(value) {
  return (value?.version === 1 || value?.version === 2)
    && Array.isArray(value.duties) && value.duties.length <= 16
    && value.duties.every(s => typeof s === 'string' && s.length <= 500)
    && (value.category === undefined || typeof value.category === 'string' && value.category.length <= 120)
    && (value.version === 1 || ['requiredSkills','preferredSkills'].every(key => Array.isArray(value[key]) && value[key].length <= 16 && value[key].every(s => typeof s === 'string' && s.length <= 500)));
}

export function dutyMatches(key, text) {
  return typeof text === 'string' && !!dutyRules[key]?.test(text);
}
