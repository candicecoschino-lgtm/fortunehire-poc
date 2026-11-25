import assert from 'node:assert/strict';
import {test} from 'node:test';
import {deflateRawSync} from 'node:zlib';
import {docxXml, fileKind, ResumeFileError} from '../public/resume-files.js';
import {qualificationIndex, rankMatches, readProfile, summarizeFeedback} from '../public/resume-match.js';

const today = '2026-11-22';
const job = (id, duties, overrides = {}) => ({
  id, title: id, postedAt: today, reviewedAt: today, status: 'reviewed',
  arrangement: 'on-site', locations: [{state: 'Washington'}],
  functionContext: {version: 2, duties, requiredSkills: [], preferredSkills: []},
  ...overrides,
});

test('qualification mode ranks demonstrated work on an Amazon equivalency path and skips stale or missing evidence', () => {
  const amazon = job('amazon-123', [], {sourceHash: 'current'});
  const stale = job('stale', ['Develop Python tools for data pipelines.'], {sourceHash: 'changed'});
  const uncovered = job('uncovered', ['Develop Python tools for data pipelines.']);
  const jobs = [amazon, stale, uncovered];
  const degree = 'Bachelor’s degree in computer science or equivalent professional experience building data pipelines.';
  const evidence = [
    {kind: 'required', text: degree},
    {kind: 'required', text: '5 years of enterprise experience'},
    {kind: 'preferred', text: 'Python'},
    {kind: 'ambiguous', text: 'Data pipelines'},
  ];
  const qualifications = qualificationIndex({version: 1, jobs: {
    [amazon.id]: {catalogSourceHash: 'current', evidence},
    [stale.id]: {catalogSourceHash: 'old', evidence},
  }}, jobs);
  const [match, ...others] = rankMatches(jobs, readProfile('Built data pipelines using Python.'), {qualifications}, today);
  assert.deepEqual(others, []);
  assert.equal(match.job.id, amazon.id);
  assert.deepEqual(match.requirements.map(({status}) => status), ['Related experience', 'Unverified']);
  assert.equal(match.requirements[0].posting, degree);
  assert.equal(match.preferred[0].posting, 'Python');
  assert.equal(match.category, 'Needs verification');
  assert.deepEqual(rankMatches(jobs, readProfile('Earned a Bachelor’s degree in computer science.'), {qualifications}, today), []);
});

test('baseline logistics and eligibility do not count as qualifications while role-specific transportation skills do', () => {
  const posting = job('amazon-456', [], {sourceHash: 'current'});
  const statements = [
    'Valid driver’s license', 'High school diploma or equivalent', 'Microsoft Office products and applications',
    'Can read and write fluently', 'Can bend or twist the body into unusual positions',
    'Can use hands to manipulate small wires', 'Can walk on uneven terrain',
    'Can work at heights and from ladders', 'Ability to lift 50 pounds', 'Fast-paced team environment',
    'Ability to travel up to 40%', 'Current RN license and ability to travel', 'Offsite training', 'U.S. citizen or permanent resident',
    'U.S. national or green card holder', 'Active Top Secret clearance', 'Reliable transportation',
    'Transportation planning experience', 'Commercial Driver’s License (CDL)',
  ];
  const qualifications = qualificationIndex({version: 1, jobs: {
    [posting.id]: {catalogSourceHash: 'current', evidence: statements.map(text => ({kind: 'required', text}))},
  }}, [posting]);
  assert.deepEqual(qualifications.get(posting.id).map(({text}) => text), statements.slice(-2));
  const profile = readProfile('Led transportation planning for regional distribution.\nDo not have: Valid driver’s license.');
  const [match] = rankMatches([posting], profile, {qualifications}, today);
  assert.equal(match.gaps, 0);
  assert.equal(match.requirements[0].status, 'Related experience');
  assert.equal(match.requirements[1].status, 'Unverified');
});

test('shared work across industries outranks a familiar title with unrelated duties', () => {
  const profile = readProfile('Warehouse supervisor\nReconciled stock and coordinated shipments.\nTrained warehouse staff.');
  const matches = rankMatches([
    job('same-title', ['Administer patient care.'], {title: 'Warehouse supervisor'}),
    job('adjacent', ['Manage inventory reconciliation.', 'Train client teams.']),
  ], profile, {}, today);
  assert.deepEqual(matches.map(result => result.job.id), ['adjacent']);
  assert.deepEqual(matches[0].duties.flatMap(pair => pair.shared).sort(), ['Inventory and logistics', 'Training and coaching']);
});

test('adoption evidence transfers to a new role, with credentials and durations unverified', () => {
  const profile = readProfile('Led a CRM rollout and trained store employees.\nStandardized workflows to reduce cycle time.');
  const context = {version: 2, duties: ['Drive customer adoption and train users.', 'Improve workflows.'],
    requiredSkills: ['PMP certification', '5 years of SaaS experience', 'CRM'], preferredSkills: ['Kubernetes']};
  const [result] = rankMatches([job('implementation', [], {functionContext: context})], profile, {}, today);
  assert.deepEqual(result.requirements.map(({status}) => status), ['Unverified', 'Unverified', 'Supported by your profile']);
  assert.equal(result.preferred.length, 0);
  assert.ok(result.duties.some(pair => pair.shared.includes('Technology rollout and adoption')));
});

test('mentions, qualifications in progress, negative evidence, and titles do not prove experience', () => {
  const profile = readProfile('Software Engineer\nDid not develop REST APIs.\nLearning about software architecture.\nManaged budgets.');
  assert.deepEqual(rankMatches([job('software', ['Develop REST APIs.'])], profile, {}, today), []);
});

test('rolling out software does not establish software engineering experience', () => {
  const profile = readProfile('Implemented new software and trained users.');
  const results = rankMatches([
    job('engineer', ['Develop APIs and debug application code.']),
    job('rollout', ['Drive platform adoption and train customers.']),
  ], profile, {}, today);
  assert.deepEqual(results.map(result => result.job.id), ['rollout']);
});

test('an explicit lack of a credential is a gap, while leading a project does not prove people management', () => {
  const profile = readProfile('Coordinated projects.\nDo not have: electrical license');
  const duties = ['Coordinate projects.', 'Supervise employees and conduct performance reviews.'];
  const [result] = rankMatches([job('coordinator', duties, {
    functionContext: {duties, requiredSkills: ['Electrical license']},
  })], profile, {}, today);
  assert.equal(result.requirements[0].status, 'Gap');
  assert.equal(result.category, 'Needs verification');
  assert.equal(result.duties.length, 1);
  assert.ok(!result.duties.flatMap(pair => pair.shared).includes('People management'));
});

test('missing employer requirements remain uncertain and title-only listings never pad the results', () => {
  const profile = readProfile('Coordinated freight deliveries.');
  const results = rankMatches([
    job('evidence-only', ['Coordinate shipments.']),
    job('title-only', [], {functionContext: undefined, title: 'Freight logistics manager'}),
  ], profile, {}, today);
  assert.equal(results.length, 1);
  assert.equal(results[0].category, 'Needs verification');
  assert.deepEqual(results[0].requirements, []);
});

test('current verified catalog rules apply and strict state selection excludes unknown remote eligibility', () => {
  const duty = ['Perform inventory reconciliation.'];
  const profile = readProfile('Performed inventory reconciliation.');
  const remote = {arrangement: 'remote', eligibleStates: []};
  const jobs = [
    job('verified-wa', duty),
    job('stale', duty, {reviewedAt: '2026-11-14'}),
    job('closed-status', duty, {status: 'closed'}),
    job('closed-date', duty, {closesAt: '2026-11-21'}),
    job('future', duty, {postedAt: '2026-11-23'}),
    job('saved-history', duty, {organizerUnavailable: true}),
    job('unknown-remote', duty, {...remote, remoteScope: 'unknown'}),
    job('other-remote', duty, {...remote, remoteScope: 'states', eligibleStates: ['Texas']}),
    job('nationwide', duty, {...remote, remoteScope: 'nationwide'}),
    job('inferred-wa', duty, {arrangementBasis: 'listed-location'}),
  ];
  assert.deepEqual(rankMatches(jobs, profile, {state: 'Washington'}, today).map(result => result.job.id),
    ['inferred-wa', 'nationwide', 'verified-wa']);
  assert.deepEqual(rankMatches(jobs, profile, {state: 'Washington', arrangement: 'on-site'}, today).map(result => result.job.id),
    ['verified-wa']);
});

test('ranking returns at most 20 unique jobs and feedback can be revised without changing rank', () => {
  const profile = readProfile('Created financial reports.\nPrepared financial statements.');
  const jobs = Array.from({length: 25}, (_, i) => job(`accounting-${i}`, ['Prepare financial statements.']));
  const matches = rankMatches([...jobs, jobs[0]], profile, {}, today);
  assert.equal(matches.length, 20);
  assert.equal(new Set(matches.map(result => result.job.id)).size, 20);
  const feedback = new Map([[matches[0].job.id, {label: 'Maybe', reason: 'Check seniority'}]]);
  assert.equal(summarizeFeedback(matches, feedback).counts.Maybe, 1);
  feedback.set(matches[0].job.id, {label: 'Relevant', beyondTitle: true});
  assert.deepEqual(summarizeFeedback(matches, feedback), {
    counts: {Relevant: 1, Maybe: 0, 'Not Relevant': 0}, topFiveRelevant: 1, beyondTitleRelevant: 1, reviewed: 1,
  });
  assert.deepEqual(rankMatches(jobs, profile, {}, today), matches);
});

test('file selection rejects unsupported or oversized files', () => {
  assert.equal(fileKind({name: 'RESUME.PDF', size: 100}), 'pdf');
  assert.throws(() => fileKind({name: 'resume.docm', size: 100}), ResumeFileError);
  assert.throws(() => fileKind({name: 'resume.docx', size: 12 * 1024 * 1024}), ResumeFileError);
});

function docxFixture(xml, declaredSize = Buffer.byteLength(xml)) {
  const records = [];
  const directory = [];
  let offset = 0;
  for (const [name, text] of [['[Content_Types].xml', '<Types/>'], ['word/document.xml', xml]]) {
    const filename = Buffer.from(name);
    const body = deflateRawSync(text);
    const size = name.startsWith('word/') ? declaredSize : Buffer.byteLength(text);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50);
    local.writeUInt16LE(8, 8);
    local.writeUInt32LE(body.length, 18);
    local.writeUInt32LE(size, 22);
    local.writeUInt16LE(filename.length, 26);
    records.push(local, filename, body);
    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50);
    central.writeUInt16LE(8, 10);
    central.writeUInt32LE(body.length, 20);
    central.writeUInt32LE(size, 24);
    central.writeUInt16LE(filename.length, 28);
    central.writeUInt32LE(offset, 42);
    directory.push(central, filename);
    offset += local.length + filename.length + body.length;
  }
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50);
  end.writeUInt16LE(2, 8);
  end.writeUInt16LE(2, 10);
  end.writeUInt32LE(directory.reduce((size, buffer) => size + buffer.length, 0), 12);
  end.writeUInt32LE(offset, 16);
  return Uint8Array.from(Buffer.concat([...records, ...directory, end])).buffer;
}

test('DOCX reader inflates only the bounded document body and rejects bad archives', async () => {
  const xml = '<w:document><w:p>Created financial reports</w:p></w:document>';
  assert.equal(await docxXml(docxFixture(xml)), xml);
  await assert.rejects(docxXml(docxFixture(xml, 12)), ResumeFileError);
  await assert.rejects(docxXml(docxFixture(xml, 3 * 1024 * 1024)), ResumeFileError);
  await assert.rejects(docxXml(new ArrayBuffer(4)), ResumeFileError);
});
