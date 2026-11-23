import {dutyRules} from './function-duties.js';
import {isCurrent, matchesState, todayInNewYork} from './jobs.js';

export const MATCH_LIMIT = 20;
export const FEEDBACK_LABELS = ['Relevant', 'Maybe', 'Not Relevant'];
export const MAX_PROFILE_LENGTH = 60_000;

// Task concepts describe work that can carry across occupations and industries.
const activities = {
  'Training and coaching': /\b(?:train\w* (?:\w+ ){0,3}(?:staff|employees|teams?|users?|customers?|clients?|personnel)|coach\w* (?:\w+ ){0,3}(?:teams?|staff|employees|reps|individuals|managers)|staff training|user training|training programs?|mentor\w* (?:\w+ ){0,3}(?:teams?|colleagues|staff|employees|engineers))\b/i,
  'People management': /\b(?:direct reports?|people management|supervis\w* (?:\w+ ){0,4}(?:staff|employees|personnel|associates)|manag\w* (?:\w+ ){0,3}teams? of \d+|performance reviews? for (?:\w+ ){0,3}(?:staff|employees|team members))\b/i,
  'Project delivery': /\b(?:project (?:plans?|delivery|milestones?|schedules?|timelines?)|coordinat\w* (?:\w+ ){0,3}(?:projects?|milestones?)|led (?:\w+ ){0,3}(?:projects?|initiatives)|cross-functional (?:projects?|delivery))\b/i,
  'Process improvement': /\b(?:process improvement|continuous improvement|workflow (?:improvement|redesign|optimization)|improv\w* (?:\w+ ){0,3}(?:processes|workflows|cycle time)|reduc\w* (?:\w+ ){0,3}(?:bottlenecks|rework|cycle times?)|standardiz\w* (?:\w+ ){0,3}(?:processes|workflows|procedures)|streamlin\w* (?:\w+ ){0,3}(?:processes|workflows|operations))\b/i,
  'Technology rollout and adoption': /\b(?:(?:software|systems?|technology|platform|CRM) rollout|technology adoption|product adoption|platform adoption|user adoption|customer adoption|roll(?:ed|ing)? out (?:\w+ ){0,4}(?:software|tools?|systems?|platforms?|CRM|technology)|implement\w* (?:\w+ ){0,4}(?:software|platforms?|CRM|systems?)|change management|go-live readiness)\b/i,
  'Customer relationship ownership': /\b(?:(?:customer|client|account) (?:relationships?|retention|renewals?|outcomes?)|account (?:plans?|portfolios?)|business reviews? (?:with|for) (?:customers?|clients?)|manag\w* (?:\w+ ){0,3}(?:customer|client) accounts?)\b/i,
  'Service onboarding': /\b(?:(?:customer|client|user|merchant|partner) onboarding|onboard\w* (?:\w+ ){0,3}(?:customers?|clients?|users?|merchants?|partners?)|implementation plans?)\b/i,
  'Operational performance': /\b(?:operational (?:metrics|performance|KPIs?)|performance metrics|key performance indicators|track\w* (?:\w+ ){0,3}(?:KPIs?|metrics|service levels?)|manag\w* (?:\w+ ){0,3}(?:daily operations|workflows|service levels?))\b/i,
  'Inventory and logistics': /\b(?:inventory (?:management|control|reconciliation|planning)|reconcil\w* (?:\w+ ){0,3}(?:inventory|stock)|coordinat\w* (?:\w+ ){0,3}(?:shipments?|deliveries|freight)|material planning)\b/i,
  'Quality assurance': /\b(?:quality (?:audits?|assurance|control|checks?)|root cause analysis|corrective actions?|inspect\w* (?:\w+ ){0,3}(?:equipment|products?|components?))\b/i,
  'Budget oversight': /\b(?:budget (?:planning|management|tracking|variance)|manag\w* (?:\w+ ){0,4}budgets?|forecast\w* (?:\w+ ){0,3}(?:costs?|expenses|spend))\b/i,
  'Safety procedures': /\b(?:safety (?:audits?|inspections?|training|procedures)|hazard assessments?|incident investigations?)\b/i,
  'Software engineering': /\b(?:writ\w*|wrote|cod\w*|debug\w*|develop\w*|build\w*|built|test\w*)\b.{0,45}\b(?:code|software|APIs?|web services?|firmware|backend|front[- ]?end|applications?)\b|\b(?:code reviews?|software architecture|CI\/CD|software development)\b/i,
};

const technicalActivities = {
  data: 'Data and analysis', it: 'IT systems',
  healthcare: 'Clinical care', engineering: 'Engineering design and validation',
  finance: 'Financial operations', legal: 'Legal work', cyber: 'Security operations',
  marketing: 'Marketing', communications: 'Communications', creative: 'Design and creative production',
};

const action = /\b(?:accountable|responsible|led|built|ran|grew|oversaw|taught|drove|wrote|tracked|deployed|trained|coached|managed|improved|launched|implemented|administered|designed|developed|delivered|supervised|organized|coordinated|supported|analyzed|reconciled|prepared|maintained|reduced|increased|created|operated|performed|standardized|mentored|negotiated|resolved|inspected|audited|owned|tested|executed|forecasted|processed|conducted|facilitated|partnered|worked|assessed|reported|rolling out|onboarded)\b/i;
const unverified = /\b(?:aspiring|interested in|seeking to|learning about|familiar with|exposure to|observed|no experience|never|not responsible|did not|didn.t|not certified|not licensed|in progress|expired)\b/i;
const ignoreLine = /https?:\/\/|www\.|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}\b/i;
const stopwords = new Set('about across after and applicable business company effectively from have into must other relevant required related strong support team teams that their them these they this through time under using will with work working years your ability skills experience preferred including within demonstrated knowledge position role responsibilities manage management lead leading provide develop ensure'.split(' '));
const baseVerbs = {
  led: 'lead', built: 'build', wrote: 'write', deployed: 'deploy', managed: 'manage', administered: 'administer',
  designed: 'design', developed: 'develop', delivered: 'deliver', coordinated: 'coordinate', supported: 'support',
  analyzed: 'analyze', reconciled: 'reconcile', prepared: 'prepare', maintained: 'maintain', created: 'create',
  operated: 'operate', performed: 'perform', negotiated: 'negotiate', resolved: 'resolve',
  audited: 'audit', tested: 'test', executed: 'execute', forecasted: 'forecast', processed: 'process',
  conducted: 'conduct', assessed: 'assess', implemented: 'implement',
};

function normalized(text) {
  return text.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}+#]+/gu, ' ').trim();
}

function terms(text) {
  const words = normalized(text).split(' ');
  const pairs = new Set();
  for (let i = 1; i < words.length; i++) {
    const pair = [words[i - 1], words[i]];
    if (pair.every(word => word.length >= 3 && !/^\d+$/.test(word) && !stopwords.has(word))) {
      pairs.add(pair.join(' '));
    }
  }
  return pairs;
}

function concepts(text) {
  const matches = Object.keys(activities).filter(key => activities[key].test(text));
  const baseText = text.replace(/\b\w+\b/g, word => Object.hasOwn(baseVerbs, word.toLowerCase()) ? baseVerbs[word.toLowerCase()] : word);
  for (const [key, label] of Object.entries(technicalActivities)) {
    if (dutyRules[key]?.test(baseText)) matches.push(label);
  }
  return matches;
}

export function readProfile(text) {
  const facts = [];
  const knownGaps = new Set();
  for (const line of text.slice(0, MAX_PROFILE_LENGTH).split(/[\r\n•]+/u)) {
    const fact = line.replace(/^[-*\s]+/, '').trim().slice(0, 500);
    if (fact.length < 5 || ignoreLine.test(fact)) continue;
    const gap = fact.match(/^do not have:\s*(.+)/i);
    if (gap) {
      knownGaps.add(normalized(gap[1]));
    } else if (!unverified.test(fact)) {
      const demonstrated = action.test(fact);
      facts.push({fact, normalized: normalized(fact), demonstrated, concepts: demonstrated ? concepts(fact) : [], terms: demonstrated ? terms(fact) : new Set()});
    }
  }
  return {facts, knownGaps};
}

function requirementStatus(posting, profile) {
  const phrase = normalized(posting);
  if (profile.knownGaps.has(phrase)) return {posting, status: 'Gap'};
  // Confirm simple skills named explicitly in the reviewed profile. Compound
  // requirements, credentials, and duration claims need fuller source evidence.
  const simple = phrase.split(' ').length <= 5
    && !/\d|\b(?:or|and|license|licensure|certified|certification|degree|equivalent|years?|authorization|clearance|registration|experience|proficiency)\b/i.test(phrase);
  const fact = simple && phrase.length >= 3 && profile.facts.find(item => {
    const text = item.normalized;
    return text === phrase || (item.demonstrated && (' ' + text + ' ').includes(' ' + phrase + ' '));
  });
  return fact ? {posting, status: 'Supported by your profile', fact: fact.fact} : {posting, status: 'Unverified'};
}

function pairEvidence(postings, profile, frequency, catalogSize) {
  const found = [];
  for (const posting of postings) {
    const postingConcepts = concepts(posting);
    const postingTerms = [...terms(posting)].filter(term => frequency.get(term) <= Math.max(5, catalogSize / 12));
    let best;
    for (const item of profile.facts) {
      if (!item.demonstrated) continue;
      const shared = postingConcepts.filter(concept => item.concepts.includes(concept));
      const phrases = postingTerms.filter(term => item.terms.has(term));
      if (!shared.length && !phrases.length) continue;
      const weight = Math.min(2, shared.length) * 3 + Math.min(2, phrases.length) * 3;
      if (!best || weight > best.weight) best = {posting, fact: item.fact, shared, phrases, weight};
    }
    if (best) found.push(best);
  }
  const pairs = [];
  const usedFacts = new Set();
  const usedConcepts = new Set();
  for (const pair of found.sort((a, b) => b.weight - a.weight)) {
    const evidence = [...pair.shared, ...pair.phrases];
    if (usedFacts.has(pair.fact) || evidence.every(item => usedConcepts.has(item))) continue;
    pairs.push(pair);
    usedFacts.add(pair.fact);
    for (const item of evidence) usedConcepts.add(item);
    if (pairs.length === 3) break;
  }
  return pairs;
}

function eligible(job, options, today) {
  if (job.organizerUnavailable || !isCurrent(job, today)) return false;
  if (options.arrangement && (job.arrangement !== options.arrangement || job.arrangementBasis === 'listed-location')) return false;
  if (options.state && !matchesState(job, options.state)) return false;
  return true;
}

export function rankMatches(jobs, profile, options = {}, today = todayInNewYork()) {
  const candidates = [...new Map(jobs.filter(job => eligible(job, options, today)).map(job => [job.id, job])).values()];
  const frequency = new Map();
  for (const job of candidates) {
    const phrases = new Set((job.functionContext?.duties || []).flatMap(duty => [...terms(duty)]));
    for (const phrase of phrases) frequency.set(phrase, (frequency.get(phrase) || 0) + 1);
  }
  const matches = [];
  for (const job of candidates) {
    const context = job.functionContext;
    if (!context) continue;
    const duties = pairEvidence(context.duties, profile, frequency, candidates.length);
    const requirements = (context.requiredSkills || []).map(item => requirementStatus(item, profile));
    const preferred = (context.preferredSkills || []).map(item => requirementStatus(item, profile))
      .filter(item => item.status === 'Supported by your profile');
    const supported = requirements.filter(item => item.status === 'Supported by your profile').length;
    const gaps = requirements.filter(item => item.status === 'Gap').length;
    if (!duties.length && !supported) continue;
    const direct = duties.some(duty => duty.phrases.length && duty.shared.length);
    const category = gaps || !requirements.length || !duties.length ? 'Needs verification'
      : direct || supported ? 'Strong evidence' : 'Transferable potential';
    const strength = duties.reduce((sum, duty) => sum + duty.weight, 0)
      + Math.min(3, supported) * 4 + Math.min(2, preferred.length);
    matches.push({job, duties, requirements, preferred, category, gaps, strength});
  }
  return matches.sort((a, b) => a.gaps - b.gaps || b.strength - a.strength
    || b.job.postedAt.localeCompare(a.job.postedAt) || a.job.id.localeCompare(b.job.id)).slice(0, MATCH_LIMIT);
}

export function summarizeFeedback(matches, feedback) {
  const counts = Object.fromEntries(FEEDBACK_LABELS.map(label => [label, 0]));
  let topFiveRelevant = 0;
  let beyondTitleRelevant = 0;
  matches.forEach(({job}, index) => {
    const entry = feedback.get(job.id);
    if (!entry || !FEEDBACK_LABELS.includes(entry.label)) return;
    counts[entry.label]++;
    if (entry.label === 'Relevant' && index < 5) topFiveRelevant++;
    if (entry.label === 'Relevant' && entry.beyondTitle) beyondTitleRelevant++;
  });
  return {counts, topFiveRelevant, beyondTitleRelevant, reviewed: Object.values(counts).reduce((a, b) => a + b, 0)};
}
