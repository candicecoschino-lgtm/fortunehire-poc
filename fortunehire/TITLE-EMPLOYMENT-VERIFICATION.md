# Part-time job-title classification - November 17, 2026

An employer job title explicitly containing Part-Time or Part Time is classified as Part-time. Matching is case-insensitive and accepts ordinary whitespace and common Unicode hyphens/dashes, including parenthetical labels. The explicit title takes priority over generic employment-type metadata. No inference is made from PT, hour counts, benefits text or unrelated words such as Department Timekeeper.

The latest published snapshot had 776 visible jobs with job type Not specified. Twenty-four of those titles explicitly state part-time; all 24 were corrected. The resulting visible counts are 752 unspecified and 376 Part-time jobs. Existing title-matched jobs already classified Part-time were retained. No current matching title had a conflicting known job type.

The correction is in the normal collector so subsequent refreshes retain it. Evidence records the employer title label. The immediate migration preserves employer posting dates, successful-check dates, source hashes, work arrangements, state geography and remote eligibility.

Validation: 156 Python tests and 38 frontend tests passed; all 2,862 current publication records validated. New tests cover title spelling/case/hyphen variants, title priority over generic Full-time metadata, benefits and PT false positives, preservation of other declared types, and repeated refresh stability. RTX remains paused.
