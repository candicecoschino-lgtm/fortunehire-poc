// Search categories inferred only from explicit role-title wording. A role may
// span functions; these labels are not employer-supplied employment types.
export const JOB_FUNCTIONS = {
 sales:'Sales',marketing:'Marketing & Communications',hr:'Human Resources',it:'IT & Software',
 operations:'Operations',service:'Customer Service',admin:'Administrative',legal:'Legal & Compliance',
 finance:'Finance & Accounting',engineering:'Engineering & Design',healthcare:'Healthcare & Clinical',
 logistics:'Supply Chain & Logistics',manufacturing:'Manufacturing & Skilled Trades',
 research:'Research & Science',projects:'Project & Program Management',other:'Other / Unclassified'
};
const rules = {
 sales:/\b(?:sales|account executive|business development|client executive|relationship banker|mortgage loan officer)\b/i,
 marketing:/\b(?:marketing|communications?|public relations|social media|copywriter|brand manager|content strategist|content creator)\b/i,
 hr:/\b(?:human resources|HR|recruit(?:er|ing|ment)|talent acquisition|people operations|employee relations|human capital|compensation|benefits (?:analyst|specialist|manager))\b/i,
 it:/\b(?:IT|information technology|software|developer|cyber(?:security)?|data (?:engineer|scientist)|systems? (?:administrator|admin|analyst|engineer)|network (?:engineer|administrator)|technical support|application support|cloud|devops|database|technology)\b/i,
 operations:/\b(?:operations?|store (?:manager|leader)|branch manager|facilities|facility|maintenance|security (?:officer|guard)|property manager)\b/i,
 service:/\b(?:customer (?:service|support|care)|call center|contact center|member (?:service|support)|patient service|guest service|client service)\b/i,
 admin:/\b(?:admin(?:istrative|istration)?|executive assistant|office (?:assistant|manager|coordinator)|receptionist|data entry|secretary|clerical|scheduler)\b/i,
 legal:/\b(?:legal|attorney|counsel|paralegal|compliance|regulatory affairs|ethics)\b/i,
 finance:/\b(?:financ(?:e|ial)|account(?:ant|ing)|audit(?:or|ing)?|tax|treasury|controller|bookkeeper|payroll|accounts (?:payable|receivable)|FP&A)\b/i,
 engineering:/\b(?:engineer(?:ing)?|industrial designer|mechanical designer|design engineer)\b/i,
 healthcare:/\b(?:nurs(?:e|ing)|RN|LPN|LVN|physician|pharmac(?:ist|y)|clinical|therapist|medical|dental|paramedic|patient care|healthcare|care (?:manager|coordinator))\b/i,
 logistics:/\b(?:supply chain|logistics|warehouse|procurement|purchasing|buyer|inventory|distribution|shipping|receiving|package handler|material handler|truck driver|delivery driver|transportation)\b/i,
 manufacturing:/\b(?:manufacturing|production|machinist|assembler|assembly|welder|electrician|mechanic|machine operator)\b/i,
 research:/\b(?:research(?:er)?|scientist|laboratory|chemist|biologist)\b/i,
 projects:/\b(?:project|program) (?:manager|management|coordinator|director|lead)\b/i
};
export function classifyJobFunctions(title){
 if(typeof title!=='string')return ['other'];
 const matches=Object.entries(rules).filter(([key,rule])=>rule.test(title)&&!(key==='engineering'&&rules.it.test(title))&&!(key==='admin'&&/\b(?:systems?|network|database|IT) admin(?:istrator|istration)?\b/i.test(title))).map(([key])=>key);
 return matches.length?matches:['other'];
}
