# Independent holdout classification validation

**Result: Needs further work.** This validation is not approval to merge or deploy.

## Sample and method

This is a new 150-job sample selected after the classifier corrections. It excludes prior reviewed/tuning job IDs and posting URLs from the final independent validation, transition manual-review, and prior comparison cohorts. Similar descriptions from employers represented in earlier samples were screened out to reduce reuse of employer templates. Selection was stratified to cover the classifier's 30 existing functions, but the function labels were hidden during independent classification. The sample contains 43 employers and 24 industries, with no repeated job IDs or posting URLs. Independent decisions were based on captured duties and required skills, and employer posting evidence where available; classifier output was compared only after decisions were recorded.

Evidence available in the sample: 92 jobs had responsibility text, 6 had skills only, and 52 had no usable captured duty/skill text. Some responsibility text was generic, so 62 jobs were ultimately judged insufficient for a reliable function decision.

## Results

| Outcome | Count |
| --- | ---: |
| Correct | 48 |
| Incorrect | 35 |
| Ambiguous | 5 |
| Insufficient evidence | 62 |
| **Total** | **150** |

Among 83 adjudicable jobs, accuracy is **48/83 = 57.8%** (approximate 95% interval 47.2–68.5%). Ambiguous and insufficient-evidence cases are excluded from that denominator and shown separately. This is not the development-set score: the same previously reviewed development sample now yields 92/96 (95.8%), but it was used to tune the rules and is not independent.

### Error causes

| Evidence source/root cause | Incorrect jobs | Examples |
| --- | ---: | --- |
| Responsibility matching or weighting | 20 | Boeing facilities mechanical engineer and supplier quality specialist classified as procurement; medical assistant/nurse/hearing roles mapped to admin; mechanical/avionics technician roles crossed with logistics/manufacturing; sanitation supervisor mapped to finance. |
| Title fallback | 12 | Cigna data science manager and Lowe’s selling specialist fell to Other; Costco optician fell to Other; manufacturing and service occupations crossed between adjacent functions. |
| Employer category fallback | 2 | IV technician and proposal project specialist were pulled toward broad employer/department categories. |
| Required-skill evidence | 1 | Chevron cloud engineer crossed between IT and cyber. |

These are repeated rule families, not a reason to add one-off employer exceptions. Responsibility precedence alone is not sufficient: responsibility keywords can still overcount a secondary task or a generic phrase and can collide across adjacent occupations. Title fallback also has both overclassification and coverage gaps.

## Other / Unclassified review

Fourteen holdout jobs were classified as Other. Independent review found 4 clear, adjudicable roles that were unnecessarily unclassified (Chevron E&I Specialist A, Cigna Senior Manager – Data Science, Costco Non-Licensed Optician, and Lowe’s Central Selling Specialist); 1 was ambiguous and 9 lacked adequate evidence in the captured record. This subset is small and not a population-wide estimate, but confirms that “Other” still includes both evidence gaps and avoidable fallback misses.

## Existing data and validation checks

In the 3,224-record branch dataset, Other / Unclassified decreased from 1,185 to 1,105 after reclassifying 407 records. The earlier assessment’s 1,161 value came from a different dataset snapshot. Stable IDs, application URLs, and protected date/status/source fields were checked by the reclassification process.

- JavaScript: **86/86 passed**.
- Python: **178/178 passed** (including collector and function-context tests).
- Dataset validation: **3,224 official job records validated**.
- `git diff --check`: passed.

## Recommendation

**Needs further work before production.** The untouched 57.8% result is not acceptable and is far below the tuned development sample’s 95.8%, so current improvements have not generalized. The rule-based approach may remain useful, but it needs another focused iteration on responsibility collision weighting and occupation-family fallback coverage, followed by a fresh untouched sample. Do not tune against this sample and continue to call it independent validation.
