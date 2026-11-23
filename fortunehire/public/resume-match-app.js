import {ARRANGEMENTS, US_STATES, validateJobs} from './jobs.js';
import {locationSummary} from './job-presentation.js';
import {extractResume, ResumeFileError} from './resume-files.js';
import {FEEDBACK_LABELS, MAX_PROFILE_LENGTH, rankMatches, readProfile, summarizeFeedback} from './resume-match.js';

const get = id => document.getElementById(id);
const create = (tag, text) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
};
const fileInput = get('resume-file');
const profileInput = get('profile');
const stateInput = get('match-state');
const arrangementInput = get('match-arrangement');
const findButton = get('find-matches');
const feedback = new Map();
let matches = [];
let catalog;
let extraction;
let run = 0;
for (const state of US_STATES) {
  const option = create('option', state);
  option.value = state;
  stateInput.append(option);
}

async function loadCatalog() {
  catalog ??= Promise.all(['jobs', 'companies'].map(async name => {
    const response = await fetch(new URL(`./data/${name}.json`, import.meta.url), {credentials: 'omit'});
    if (!response.ok) throw new Error('Catalog unavailable');
    return response.json();
  })).then(([jobs, companies]) => validateJobs(jobs, companies.companies)).catch(error => {
    catalog = undefined;
    throw error;
  });
  return catalog;
}

function updateSummary() {
  const {counts, reviewed, topFiveRelevant, beyondTitleRelevant} = summarizeFeedback(matches, feedback);
  get('feedback-summary').textContent = `${reviewed} of ${matches.length} reviewed. ${counts.Relevant} Relevant, ${counts.Maybe} Maybe, ${counts['Not Relevant']} Not Relevant. ${topFiveRelevant} relevant in the first ${Math.min(5, matches.length)}. ${beyondTitleRelevant} relevant outside your past titles.`;
}

function feedbackControls(job) {
  const fieldset = create('fieldset');
  fieldset.className = 'match-feedback';
  fieldset.append(create('legend', `Your feedback for ${job.title}`));
  const ratingLabel = create('label', 'Relevance');
  const rating = create('select');
  rating.autocomplete = 'off';
  const empty = create('option', 'Unrated');
  empty.value = '';
  rating.append(empty);
  for (const label of FEEDBACK_LABELS) rating.append(create('option', label));
  ratingLabel.append(rating);
  const reasonLabel = create('label', 'Reason (optional)');
  const reason = create('input');
  reason.type = 'text';
  reason.autocomplete = 'off';
  reason.spellcheck = false;
  reason.maxLength = 300;
  reasonLabel.append(reason);
  const titleLabel = create('label');
  const beyondTitle = create('input');
  beyondTitle.type = 'checkbox';
  beyondTitle.autocomplete = 'off';
  titleLabel.append(beyondTitle, ' Outside my past job titles');
  const record = () => {
    feedback.set(job.id, {label: rating.value, reason: reason.value, beyondTitle: beyondTitle.checked});
    updateSummary();
  };
  rating.addEventListener('change', record);
  reason.addEventListener('input', () => {
    feedback.set(job.id, {label: rating.value, reason: reason.value, beyondTitle: beyondTitle.checked});
  });
  beyondTitle.addEventListener('change', record);
  fieldset.append(ratingLabel, reasonLabel, titleLabel);
  return fieldset;
}

function evidenceList(items, render) {
  const list = create('ul');
  list.className = 'match-evidence';
  for (const item of items) {
    const li = create('li');
    render(item, li);
    list.append(li);
  }
  return list;
}

function matchCard({job, category, duties, requirements, preferred}) {
  const li = create('li');
  const card = create('article');
  card.className = 'match-card';
  const title = create('h3', job.title);
  const arrangement = job.arrangementBasis === 'listed-location'
    ? 'On-site inferred from the listed location'
    : ARRANGEMENTS[job.arrangement];
  const badge = create('p', category);
  badge.className = 'match-category';
  card.append(title, create('p', job.companyName), create('p', locationSummary(job, stateInput.value)),
    create('p', arrangement), badge, create('h4', 'Why this matches'));
  if (duties.length) {
    card.append(evidenceList(duties, (pair, item) => {
      const labels = [...pair.shared, ...pair.phrases];
      item.append(create('strong', labels.slice(0, 3).join(' · ')),
        create('span', `Your experience — ${pair.fact}`),
        create('span', `Employer duty — ${pair.posting}`));
    }));
  } else {
    card.append(create('p', 'A listed skill is supported by your profile. The available duties do not establish a broader match.'));
  }
  const details = create('details');
  details.append(create('summary', 'Qualifications to review'));
  if (requirements.length) {
    details.append(evidenceList(requirements, (requirement, item) => {
      item.append(create('strong', requirement.status + ' — '), requirement.posting);
      if (requirement.fact) item.append(create('span', `Your profile — ${requirement.fact}`));
    }));
  } else {
    details.append(create('p', 'Employer requirements are unclear in the available listing data.'));
  }
  if (preferred.length) {
    details.append(create('h4', 'Preferred skills supported by your profile'),
      evidenceList(preferred, (item, li) => li.append(item.posting, create('span', `Your profile — ${item.fact}`))));
  }
  details.append(create('p', 'Review the official posting for the full requirements.'));
  const apply = create('a', 'View posting and apply at employer ↗');
  apply.href = job.url;
  apply.target = '_blank';
  apply.rel = 'noopener noreferrer';
  const link = create('p');
  link.append(apply);
  card.append(details, link, feedbackControls(job));
  li.append(card);
  return li;
}

function clearResults() {
  matches = [];
  feedback.clear();
  get('match-list').replaceChildren();
  get('feedback-summary').textContent = '';
  get('match-results').hidden = true;
}

function clearSession() {
  run++;
  extraction?.abort();
  extraction = undefined;
  fileInput.value = '';
  profileInput.value = '';
  stateInput.value = '';
  arrangementInput.value = '';
  findButton.disabled = false;
  get('file-status').textContent = '';
  get('match-status').textContent = '';
  clearResults();
}

fileInput.addEventListener('change', async () => {
  extraction?.abort();
  const file = fileInput.files[0];
  fileInput.value = '';
  if (!file) return;
  const controller = new AbortController();
  extraction = controller;
  const timeout = setTimeout(() => controller.abort(new DOMException('Read timed out', 'TimeoutError')), 15_000);
  get('file-status').textContent = 'Reading the file on this device…';
  findButton.disabled = true;
  try {
    const text = await extractResume(file, controller.signal);
    if (controller.signal.aborted || extraction !== controller) return;
    profileInput.value = text.slice(0, MAX_PROFILE_LENGTH);
    get('file-status').textContent = text.length > MAX_PROFILE_LENGTH
      ? 'Only the first 60,000 characters are shown. Check the text before matching.'
      : 'Text extracted. Check it for missing text or lines out of order before matching.';
    profileInput.focus();
  } catch (error) {
    if (extraction !== controller) return;
    get('file-status').textContent = error.name === 'TimeoutError'
      ? 'Reading took too long. Paste your experience below.'
      : error instanceof ResumeFileError ? error.message : 'This file could not be read. Paste your experience below.';
  } finally {
    clearTimeout(timeout);
    if (extraction === controller) {
      extraction = undefined;
      findButton.disabled = false;
    }
  }
});

findButton.addEventListener('click', async () => {
  if (!profileInput.value.trim()) {
    get('match-status').textContent = 'Choose a résumé or paste your experience first.';
    profileInput.focus();
    return;
  }
  if (feedback.size && !window.confirm('Start a new match run and clear feedback from this run?')) return;
  const current = ++run;
  clearResults();
  findButton.disabled = true;
  get('match-status').textContent = 'Checking the verified job catalog…';
  try {
    const jobs = await loadCatalog();
    if (current !== run) return;
    matches = rankMatches(jobs, readProfile(profileInput.value), {
      state: stateInput.value, arrangement: arrangementInput.value,
    });
    if (!matches.length) {
      get('match-status').textContent = 'No current jobs had enough matching evidence. Try adding concrete duties or widening your location preferences.';
      return;
    }
    get('match-status').textContent = matches.length < 20
      ? `Only ${matches.length} current jobs had enough evidence to recommend.` : 'Found 20 evidence-based recommendations.';
    get('match-list').append(...matches.map(matchCard));
    updateSummary();
    get('match-results').hidden = false;
    get('results-heading').focus();
  } catch {
    if (current === run) get('match-status').textContent = 'The jobs could not be loaded or matched. Try again.';
  } finally {
    if (current === run) findButton.disabled = Boolean(extraction);
  }
});

get('clear-session').addEventListener('click', () => {
  clearSession();
  get('file-status').textContent = 'Session cleared.';
  fileInput.focus();
});
window.addEventListener('pagehide', clearSession);
window.addEventListener('pageshow', event => {
  if (event.persisted) clearSession();
});
