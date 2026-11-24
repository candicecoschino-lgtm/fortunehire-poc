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


## November 24 targeted follow-up (not independently validated)

The extractor was updated on the same draft PR branch to recognize additional preferred and required section headings, including explicit licensing and credential headings, dash-delimited inline headings, and standalone must-hold/must-maintain credential language after a responsibility boundary. Three focused synthetic regression cases were added for section transitions, conditional licensing, and inline heading separators.

These are **development changes, not a new accuracy benchmark**. The original development numbers above remain historical results for the earlier revision. The November 23 independent holdout reported approximately 82.2% statement precision, 53.5% overall recall, and 49.9% required recall, and found preferred-to-required promotions, missing hard requirements, and unsupported statements. Its adjudication/reference files were not available in this editing session, so those metrics have **not** been recalculated. The fresh human-adjudicated holdout and source-specific review remain mandatory before merge or integration.

The GitHub Actions JavaScript workflow passed for commit `41a6a78bb153f4287d2297451cd4758020493524`. That workflow result does **not** establish that the expanded Python extraction tests or dataset validator passed on this revision. Those commands must be rerun in the repository's normal development environment before reviewing this change for merge.

Remaining priority risks: preferred-to-required promotions in untested employer templates, incomplete conditional/state-specific licensure, generic heading ambiguity, table and flattened-text boundaries, and boilerplate false positives. No production feeds, job classifications, public job data, search, or resume-matching code were changed in this update.
