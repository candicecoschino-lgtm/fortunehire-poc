# FortuneHire independent job-function validation

> Historical baseline: this sample was later used to tune the classifier and is now a development/regression set. Post-tuning scores on it are in-sample and are not independent accuracy. See `../post-correction/holdout/report.md` for the untouched validation.

**Decision: Needs further work.** This review is not approval to merge or deploy.

## Method

A new 150-posting holdout was drawn from the current 3,224-job publication dataset. The sample spans 45 employers, 27 industries, and all 30 stored function labels. It excludes every URL in both prior manual-review cohorts (`manual-review-sample.csv` and `manual-review-sample-current.csv`) and the previous review comparison cohort. Duplicate URLs and duplicate employer/title pairs were checked; none remain. Function labels were used only to balance coverage. Independent judgments were based on captured employer-page responsibilities and role-specific required skills, not agreement with the stored label.

Evidence in the sample: 90 postings with responsibility text, 21 with skills only, and 39 with no usable text. Six additional records had only generic or irrelevant fragments, leaving 45 with insufficient evidence.

## Results

| Independent outcome | Jobs |
| --- | ---: |
| Correct | 51 |
| Incorrect | 45 |
| Ambiguous | 9 |
| Insufficient evidence | 45 |
| **Adjudicable accuracy** | **51 / 96 = 53.1%** |

Accuracy excludes ambiguous and insufficient-evidence cases. The sample's 53.1% is far below the 90% quality goal and is not a basis for deployment.

## Other / Unclassified review

The sample contains 49 jobs currently labeled Other / Unclassified:

- 25 (51.0%) have clear responsibility or skill evidence for another primary function.
- 5 (10.2%) remain genuinely cross-functional or too sparse to choose safely.
- 19 (38.8%) lack usable role-specific evidence.

Among the 30 records with some role-specific context, 25 (83.3%) had enough evidence to assign a specific function; the remaining 5 were ambiguous. Examples include a PepsiCo Transportation Coordinator (driver dispatch and delivery scheduling → Logistics), a Humana Behavioral Health Liaison (care access and continuity → Healthcare Administration), a Boeing GNC Engineer (control algorithms and aircraft simulations → Engineering), and a McKesson Business Process Improvement Analyst (Lean/process improvement and operational KPIs → Operations). Other clear misses include Walmart stocking leadership → Retail and Boeing IT infrastructure leadership → IT.

## Recurring error patterns

1. **Evidence present but no rule fires.** Specific duties are captured, yet multiple jobs fall to Other. This is the largest issue in the holdout and in the Other subset.
2. **Specialized duties get routed by generic vocabulary.** Examples include AT&T standards engineering routed to IT, environmental remediation engineering routed to Research, an infrastructure engineering role routed to Software Engineering, and a clinical laboratory scientist routed to Research.
3. **Function boundaries still overlap.** Quality assurance automation, technical platform/DevOps work, finance versus sales, and clinical care coordination need narrow responsibility-based precedence rules. Ambiguous cases should remain flagged.

## Recommended next steps

1. Do not deploy this branch based on the present accuracy result.
2. Improve only targeted responsibility patterns for the recurring misses above; do not add broad title or employer-department rules.
3. Keep ambiguous and evidence-poor jobs flagged. Expand description coverage through existing approved adapters where it can provide actual duties.
4. Validate the targeted fixes on a fresh holdout before reconsidering deployment.

## Verification

- JavaScript: **85 passed, 0 failed** (`node --test`).
- Python: **177 passed, 0 failed** (full `unittest` discovery, using the bundled Python runtime and a writable temp directory).
- Dataset validation: **passed; 3,224 official job records** (`node scripts/validate-jobs.mjs`).
- Code and live filters were not changed. No merge or deployment was performed. The repository remains at `4d676c2951e47860ca4c3571955de01751497958`; the sample and this report are local validation artifacts only.
