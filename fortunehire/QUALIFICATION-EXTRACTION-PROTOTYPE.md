# Qualification extraction prototype

## Scope

The offline Python extractor reads verified employer descriptions and dedicated
qualification fields. It scans every supplied block before applying independent
output caps of 24 required, preferred, and ambiguous statements. It preserves
whole statements, including alternatives, and records the employer URL, field,
section, block, and extraction confidence. Confidence describes the strength of
the source label. It does not verify a candidate's eligibility.

The prototype has no production callers. Feed adapters, job functions, public
data, search, and refresh publication are untouched. Source responses and
reviewed statement text were kept in the local audit workspace. This branch
contains aggregate findings and synthetic test inputs.

## November 23 validation

The comparison uses the catalog from main commit `59287dd`. We replayed 109
archived descriptions from the previous investigation and kept the 77 whose
source hash and legacy output both reproduced the published record. We also
read 22 official postings, including follow-up examples from Ashby, Greenhouse,
Oracle, Taleo, Disney, and other previously authorized sources. Of those, 21
reproduced both the published source hash and legacy output. After removing the
overlapping Ford posting, the broad comparison contains 97 jobs from 20
employers and nine source methods. It is a convenience sample, with 83 jobs
from the general JSON-LD method. Salesforce returned HTTP 429, Apple failed
to download, and Verizon's source hash differed. Apple field routing was
tested synthetically.

Twenty-one of these jobs were reviewed against their original employer
sections. A correct result must contain the complete source statement in the
right bucket after normalizing whitespace and list markers. The reviewer
retained shared list introductions and joined alternatives when the source
layout made the relationship explicit. The review includes examples used
to refine the prototype and one reviewer. It is a development benchmark.

| Measure | Existing function snippets | Dedicated extractor |
|---|---:|---:|
| Populated required field, broad sample | 43/97 (44%) | 55/97 (57%) |
| Populated preferred field, broad sample | 16/97 (16%) | 49/97 (51%) |
| Populated ambiguous field, broad sample | No field | 39/97 (40%) |
| At least one complete, correctly labeled required statement, reviewed jobs with required evidence | 1/15 (7%) | 15/15 (100%) |
| At least one complete, correctly labeled preferred statement, reviewed jobs with preferred evidence | 2/18 (11%) | 18/18 (100%) |
| Required source statements recovered completely | 7/81 | 75/81 |
| Preferred source statements recovered completely | 2/65 | 64/65 |
| Ambiguous source statements recovered completely | No field | 53/67 |
| Emitted statements or fragments | 129 | 193 |
| Complete, correctly labeled output | 9 | 192 |
| Complete statement in the wrong bucket | 4 | 1 |
| Fragment or other wording difference | 96 | 0 |
| Unsupported by the reviewed qualification statements | 20 | 0 |

The remaining classification error is a GE Vernova accepted-major criterion
that stayed ambiguous even though it qualified the preceding enrollment
requirement. The extractor still missed six required statements and one
preferred statement, and was more conservative on ambiguous statements.
The observed omissions came from extraction or labeling. No audited job hit
the output caps. The legacy wording differences include comma-separated
fragments that lost the scope of larger bullets. The prototype preserves
wording and punctuation while flattening whitespace and grouping linked list
items. The zero unsupported outputs in this reviewed set does not establish
a production false-positive rate.

### Employer coverage

These counts reflect the presence of a field in the 97-job replay. A drop in
required coverage can reflect both deliberate ambiguity and real omissions.

| Employer | Jobs | Required before → after | Preferred before → after | Ambiguous after |
|---|---:|---:|---:|---:|
| Amazon | 2 | 0 → 2 | 2 → 2 | 0 |
| Anthropic | 1 | 1 → 1 | 1 → 1 | 0 |
| AT&T | 16 | 1 → 4 | 0 → 1 | 1 |
| Boeing | 2 | 0 → 2 | 0 → 2 | 0 |
| Comcast | 16 | 15 → 3 | 1 → 1 | 15 |
| Disney | 1 | 1 → 1 | 0 → 1 | 0 |
| Ford | 11 | 3 → 8 | 2 → 8 | 2 |
| GE Vernova | 2 | 0 → 2 | 0 → 2 | 1 |
| General Motors | 8 | 2 → 5 | 1 → 4 | 1 |
| Intuit | 1 | 1 → 0 | 0 → 1 | 1 |
| Lowe’s | 9 | 8 → 9 | 8 → 9 | 1 |
| McKesson | 10 | 3 → 9 | 1 → 9 | 3 |
| Nike | 6 | 5 → 5 | 0 → 0 | 5 |
| OpenAI | 1 | 0 → 0 | 0 → 1 | 1 |
| Oracle | 1 | 0 → 0 | 0 → 1 | 1 |
| Perplexity | 1 | 1 → 0 | 0 → 1 | 1 |
| ServiceNow | 2 | 2 → 0 | 0 → 2 | 2 |
| Target | 4 | 0 → 1 | 0 → 0 | 4 |
| Valero | 1 | 0 → 1 | 0 → 1 | 0 |
| Walmart | 2 | 0 → 2 | 0 → 2 | 0 |

- Ford and McKesson examples recovered evidence after the old duty stop.
  Boeing and Walmart recovered both buckets after recognizing their
  parenthetical or punctuated headings.
- Comcast's generic **Skills** headings often produce ambiguous evidence.
  Its explicitly labeled retail requirements still produce required
  statements. Review more of the Comcast templates before interpreting the
  aggregate drop. Intuit and ServiceNow also expose general qualification
  headings alongside explicit preferred evidence.
- In the Oracle example, the dedicated qualifications field contained
  disclaimers and compensation. The relevant sections appeared in the
  responsibilities field under their own headings. The prototype discarded
  the disclaimer and kept qualifications under those nested headings.
  Valero recovered explicit inline requirements and preferences in its role
  description. A dedicated source field still benefits from content and
  boundary checks.

## Local testing

From this project's `fortunehire` directory:

```shell
python -B -m unittest discover -s test
node --test
node scripts/validate-jobs.mjs
python -B scripts/audit_qualifications.py archive-cases.json live-cases.json --references review-references.json
```

The audit command accepts local JSON arrays of cases with `id`, `employer`,
`url`, `source` (verified source fields), `before` (published function context),
`sameHash`, and `sameContext`. Keep only cases that match both checks. Optional
references map IDs to arrays of objects with `kind` and complete `text`.
The command outputs aggregates by employer and does not fetch, write, or print
individual qualification statements. The local test run passed 206 Python
tests (including 14 for this prototype), 103 JavaScript tests, and validation
of all 4,307 existing job records.

## Recommended integration

1. **Build a held-out review set.** Sample more postings per adapter, include
   explicit hard requirements and negative controls, and have a second
   reviewer adjudicate ambiguous language. Prioritize Comcast, Apple, the
   missing specialty criteria, conditional alternatives, and late sections.
2. **Run in shadow mode after approval.** Consume responses that the current
   collector has already authorized and verified. Store the extractor version,
   stable job ID and source hash with evidence outside the public job snapshot.
   Report coverage, omissions, unsupported statements and bucket errors by
   source. Make failure independent of the normal job refresh.
3. **Review accuracy before any publication.** Agree on per-source hard
   requirement precision and loss thresholds. Keep absent or ambiguous evidence
   visible as uncertainty. Sample the emitted wording and alternatives before
   enabling any résumé match logic to use it.
4. **Integrate as optional evidence for résumé matching.** After approval,
   join validated evidence by job ID and source hash. Ignore stale or
   mismatched evidence and preserve the existing searchable-job eligibility
   rules and direct employer application URLs.


## November 24 corrections

The incoming draft head was `1667bb6`. It already recognized credential
headings, dash-delimited inline headings, and standalone “must hold” and
“must maintain” statements. The remaining failures had four main causes.

- **Section scope leaked.** Expanded headings such as JPMorgan’s
  qualifications/capabilities/skills, Phillips 66’s label suffixes, and
  Verizon’s full “even better” heading now establish the correct scope. Nested
  headings end with their lists. Unknown HTML headings, job duties, and
  application and compensation sections close inherited qualification scope.
- **Labels and clauses were read in isolation.** Home Depot-style headings
  pair with numeric tenure values and empty placeholders are rejected. An
  explicit floor in a qualification section can establish a requirement at
  medium confidence. A floor in a preferred section stays preferred. Generic
  criteria stay ambiguous where the wording does not establish a requirement.
  Conflicting explicit labels for the same statement are retained as ambiguous.
- **Obligations were mixed with duties.** In the captured Cencora Pharmacist
  posting R2613180 the extractor now retains the pharmacy degree, resident-state
  license, active Pennsylvania license, and the obligation to obtain or maintain
  nonresident licenses as business needs dictate. It also retains complete
  documented disjunctions and nested choices, including the final Centene
  licensure option and Perplexity’s “at least one” technical list.
- **Nonqualification text inherited a bucket.** The extractor screens out
  application directions, salary ranges attached to qualifying text, employer
  marketing, equal-opportunity language, template labels, and operational
  actions ending in “when required.” These checks also apply to text supplied
  through the dedicated fields. The verified-input routing is unchanged.

## Before-and-after development replay

Both revisions ran against the same cached inputs and unedited references.
The original 21-case development set uses complete wording in the correct
bucket. The 136-case November 23 set spans 25 employers and 13 methods. That
set informed the changes below and is now development evidence. The
source-only reference was rule-assisted and received no independent human
adjudication. The separate blinded reference covers 11 usable jobs within
the same replayed set.

| Measure | Incoming draft `1667bb6` | Corrected |
|---|---:|---:|
| 21-case development required precision | 75/75 (100%) | 78/78 (100%) |
| 21-case development required recall | 75/81 (92.6%) | 78/81 (96.3%) |
| 21-case development preferred precision | 61/61 (100%) | 65/65 (100%) |
| 21-case development preferred recall | 61/65 (93.8%) | 65/65 (100%) |
| 136-case primary required precision | 288/312 (92.3%) | 409/426 (96.0%) |
| 136-case primary required recall | 288/575 (50.1%) | 409/575 (71.1%) |
| 136-case primary preferred precision | 334/392 (85.2%) | 426/440 (96.8%) |
| 136-case primary preferred recall | 334/605 (55.2%) | 426/605 (70.4%) |
| 136-case primary overall precision | 875/1,103 (79.3%) | 1,136/1,217 (93.3%) |
| 136-case primary overall recall | 875/1,619 (54.0%) | 1,136/1,619 (70.2%) |

| Primary replay error or coverage measure | Incoming draft | Corrected |
|---|---:|---:|
| Required missing, incomplete, or misclassified | 287 | 166 |
| Preferred missing, incomplete, or misclassified | 271 | 179 |
| Complete statements in the wrong bucket | 113 | 30 |
| Preferred-to-required promotions against the fixed labels | 10 | 0 |
| Partial wording or grouping differences | 35 | 17 |
| Source-like output without a reference label | 71 | 31 |
| Output without a literal match to one rendered source block | 9 | 3 |
| Required alternatives or conditions recovered completely and correctly | 115/206 | 164/206 |
| Required licenses or certifications recovered completely and correctly | 18/23 | 22/23 |

The unmatched outputs include source-backed label/value joins and grouped
choices. The three without a literal source-block match join choice lists
across multiple blocks. The unmatched count does not establish a confirmed
false-positive count. Forty-two required units with an alternative or
condition still lack a complete correct match. That includes misses,
bucket disagreements, and grouping differences. The replay does not isolate
how many actually lost an option or condition. The targeted Cencora, Centene,
and Perplexity fixtures assert the full source clause.

In the blinded 11-job replay, required precision and recall changed from
27/29 (93.1%) and 27/35 (77.1%) to 32/36 (88.9%) and 32/35 (91.4%).
Preferred precision and recall changed from 27/31 (87.1%) and 27/40 (67.5%)
to 39/41 (95.1%) and 39/40 (97.5%). Reviewers had disagreed on some numeric
floors and generic labels. The drop in required precision is an additional
reason to adjudicate those cases in the next evaluation. On the original
21-case set, one GE Vernova accepted-major criterion remains ambiguous, three
required statements lack a complete correct match, and no output went
unmatched by wording.

The default cap of 24 per bucket was held fixed for the comparison. It omitted
51 preferred candidates and zero required candidates on the corrected replay.
With the cap disabled for an audit only, preferred precision was 477/491
(97.1%) and recall was 477/605 (78.8%). Required results were identical.

### Employer and method limitations

| Employer | Complete required before → after | Complete preferred before → after | Remaining issue |
|---|---:|---:|---|
| Cencora | 8 → 14 of 14 | 6 → 7 of 8 | The separate pharmacist fixture covers the known state obligations. Other templates still need fresh review. |
| JPMorgan Chase | 0 → 38 of 38 | 0 → 21 of 29 | Regulatory, training, and travel material needs source-level adjudication. |
| Phillips 66 | 1 → 32 of 60 | 0 → 44 of 45 | Bare “What You’ll Bring” remains ambiguous for nonnumeric criteria. The primary reference often labels those criteria required. |
| Verizon | 6 → 8 of 8 | 0 → 7 of 17 | The ten remaining preferred reference labels are application or worksite logistics. The extractor excludes them. |
| Home Depot | 20 → 26 of 31 | 38 → 40 of 40 | Some label/value pairs and physical criteria differ from the reference. |
| Comcast | No required labels | 7 → 7 of 7 | Generic skills and degree-equivalence prose need adjudication. The blinded reference includes criteria omitted by the primary reference. |
| Intuit | 0 → 2 of 3 | 6 → 4 of 6 | Splitting an independently labeled degree pair can differ from the reference unit. Generic traits remain ambiguous. |
| ServiceNow | 0 → 3 of 7 | 3 → 3 of 3 | Plain experience counts and mixed baseline/preference language still need review. Tracking codes and bare labels are excluded. |
| Perplexity | 0 → 4 of 5 | 11 → 17 of 17 | Nested choices can differ from the rubric’s grouping. |
| Meta | 0 → 0 of 2 | No preferred labels | Flattened fields lack reliable statement boundaries and explicit strength labels. Keep the source-supported material ambiguous. |

For example, corrected required recall was 82/84 for Oracle requisition
details, 118/151 for general JobPosting JSON-LD, 43/99 for Disney metadata,
and 35/59 for Greenhouse. Preferred recall was 81/146 for Oracle and 29/55
for Greenhouse. These are replay denominators, with shared employer
templates within methods. The original sample lacked usable Apple, NVIDIA,
Salesforce and Fannie Mae captures. Some Cencora and Humana requests failed,
and one Walmart posting supplied empty sections. Those gaps require source
coverage review before any supported-method claim.

### Automated checks and fresh validation

All 226 Python tests and all 103 JavaScript tests passed locally. The
dataset validator passed all 4,307 existing official job records. The Python
suite ran on Windows with its temporary bare Git fixture repositories in
the writable worktree. Seventeen new extraction regressions cover the
confirmed parsing failure classes.

Freeze the extractor before drawing at least 100 new verified postings.
Exclude every tuning posting, archived duplicate, and repeated template
body. Stratify by employer, source method, and qualification severity.
For each method considered for deployment, aim for at least 30 postings
or 100 reviewed hard statements where available. Have two human reviewers
annotate complete source wording and strength without extractor output.
Adjudicate disagreements, including numeric floors under generic headings,
eligibility clauses, and nested alternatives. Score each bucket and source
method with denominators and confidence intervals. Audit false positives,
preferred-to-required promotions, and complete conditions and alternatives
separately. Require required precision of at least 99% and recall of at
least 95%, preferred precision of at least 95% and recall of at least 90%,
and zero audited preferred promotions or lost mandatory alternatives before
considering integration. Keep source-limited methods out of hard eligibility
decisions until their evidence supports those gates.
