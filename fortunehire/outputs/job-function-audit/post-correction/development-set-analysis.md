# Classification correction review

## Disposition

**Needs further work; not ready for production.** Targeted rule changes improved the known development set, but a new untouched 150-job holdout reached only **48/83 (57.8%) accuracy among adjudicable cases**. The held-out result is the relevant estimate; the development-set result must not be treated as independent accuracy.

## Analysis of the prior 150-job review set

The initial independent review found 45 incorrect classifications among 96 adjudicable jobs (51/96 correct, 53.1%). Root causes recorded for the 45 errors were:

| Root cause | Errors | Share of errors |
| --- | ---: | ---: |
| Title fallback overrode or misrepresented the work | 25 | 55.6% |
| Responsibility rules matched secondary/incidental work or weighted duties poorly | 14 | 31.1% |
| Required-skill rules were too broad or misleading | 4 | 8.9% |
| Employer category/dept fallback was misleading | 2 | 4.4% |

Of 25 unnecessary Other / Unclassified outcomes, **22 had usable duties but were missed by title-fallback coverage; 3 had usable skills**. Missing descriptions were not the main cause for those 25. Among the full initial sample, 90 had usable duty text, 21 had skills only, and 39 lacked usable evidence; the independently adjudicable subset contained 96 jobs.

The identified repeated gaps were weak action-verb extraction, broad keyword collisions, title fallback that either chose a competing function or failed to recognize a clear occupation, and weak separation between related technical, healthcare, production/trades, and corporate functions. Corrections narrowed incidental tool and department terms, expanded responsibility language in existing extraction, and made title evidence a constrained tie-break/fallback. No taxonomy, external service, or new infrastructure was introduced.

On the same 96 adjudicable development cases, the updated classifier reached **92/96 (95.8%)**, with 4 misses. This is an in-sample regression result, not independent validation. Remaining development-set misses included technical software versus infrastructure, a facilities/service role family, a cross-functional resort role, and a job with inadequate context.

## New untouched holdout

The new 150-job sample excludes prior review/tuning IDs and URLs from the final independent, transition/manual-review, and comparison cohorts. Similar employer descriptions were screened out to reduce template reuse. The sample spans **43 employers and 24 industries**, with all 30 classifier functions represented. Classifications were judged from captured responsibilities/skills and employer evidence without using the stored classifier label as the correctness standard.

| Independent result | Jobs |
| --- | ---: |
| Correct | 48 |
| Incorrect | 35 |
| Ambiguous | 5 |
| Insufficient evidence | 62 |

Accuracy on the 83 adjudicable cases (correct + incorrect) is **57.8% (48/83)**; approximate 95% interval 47.2–68.5%. The 62 insufficient-evidence cases are not included in the accuracy denominator. The five ambiguous cases are reported separately and also excluded.

### Holdout error patterns

The 35 errors group by the evidence source that led to the mismatch:

| Root cause | Errors | Share |
| --- | ---: | ---: |
| Responsibility matching/weighting | 20 | 57.1% |
| Title fallback | 12 | 34.3% |
| Employer category fallback | 2 | 5.7% |
| Required skills | 1 | 2.9% |

Recurring patterns in the mismatches include: procurement signals pulling in facilities, supplier quality, and planning engineers; healthcare clinical jobs drifting into administration or operations; hands-on technician roles crossing between trades, manufacturing, and logistics; technical roles crossing among data, software, IT, and cyber; and broad words such as “operations” or “finance” outweighing the actual domain. These are families of rule collisions rather than isolated company-specific exceptions. The held-out errors are distributed across 24 employers, so the result is not explained by one employer adapter.

The classifier returned Other for 14 of the 150 held-out jobs: **4 were independently adjudicable clear roles and therefore unnecessary Other outcomes**, 1 was ambiguous, and 9 lacked sufficient captured evidence. The four avoidable cases included an E&I Specialist, a Data Science manager, an optician, and a sales specialist. This indicates title fallback still misses several well-established occupations, while extraction gaps account for many—but not all—unclassified cases.

## Data changes and safeguards

The existing rule-based classifier and existing description adapters were refined; the 30-function taxonomy remains unchanged. Reclassification updated the stored primary function on **407 of 3,224** job records. Other / Unclassified fell from **1,185 to 1,105** in this branch dataset (80 fewer). A prior assessment referenced 1,161; that figure differs from the dataset snapshot used for this run, so the before/after here is computed from the exact pre-write and post-write files in this branch.

The reclassification script verified stable job IDs and URLs and preserved posting dates, review/check dates, close dates, status, and source hashes. Saved/hidden/applied state and saved searches remain keyed independently and were covered by regression tests; employer application links were not changed. Collection and refresh rules were not modified.

## Recommendation

**Do not approve production deployment.** A 57.8% untouched holdout accuracy is materially below the quality goal and contradicts the 95.8% development-set result. The rule-based approach has not yet demonstrated generalization. The next work should focus on reducing cross-function responsibility collisions and building occupation-family title fallbacks from adjudicated evidence, followed by another untouched holdout. Do not tune against this holdout and then reuse its score as independent evidence.
