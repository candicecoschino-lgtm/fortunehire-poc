# Primary job function classification

Each job stores one `primaryJobFunction` key, its evidence basis, confidence, review flag, and up to four short evidence excerpts. Search reads the stored key; it does not run the classifier for each filter operation.

## Taxonomy

Administrative & Office Support; Business Strategy & Planning; Communications & Public Relations; Customer Service & Support; Customer Success & Account Management; Cybersecurity & Information Security; Data & Analytics; Design & Creative; Engineering; Finance & Accounting; Food Service & Hospitality; Healthcare Administration & Operations; Healthcare & Clinical Care; Human Resources & Talent; IT Infrastructure & Support; Legal & Compliance; Manufacturing & Production; Marketing & Advertising; Operations & Facilities; Other / Unclassified; Product Management; Program & Project Management; Purchasing & Procurement; Quality & Safety; Research & Science; Retail & Store Operations; Sales & Business Development; Software Engineering & Development; Supply Chain & Logistics; Trades & Field Service.

The directory filter sorts the labels alphabetically. The taxonomy splits data roles from IT and software, and separates clinical care from healthcare administration, manufacturing from trades, and software from IT infrastructure and security.

## Decision order

1. Match role duties using bounded action-and-object phrases. Equal cross-function responsibility scores resolve to Other / Unclassified and require review.
2. If duties do not resolve a function, score required and preferred skills. Strong, unique matches may classify; weak or tied matches defer to the next step or resolve to Other.
3. Use a clear job title only when responsibility and skill evidence do not resolve the role. Ambiguous multi-function titles resolve to Other.
4. Use a single clear employer category only as a low-confidence fallback; conflicting or unclear evidence resolves to Other.

The rule set is deterministic and local. It does not use paid services or AI. Confidence indicates evidence strength; it is not a verified accuracy score.

## Collection and migration

The existing official-page collector stores at most 16 responsibility sentences and 16 required/preferred skill excerpts from the matched posting. It excludes benefits and employer-profile text. After collection, `scripts/classify-jobs.mjs` updates the stored primary function. The one-time migration reuses the 473 already-collected audit contexts only when job ID and official URL match. It does not re-fetch pages or modify IDs, links, status, source hashes, or posting/check dates.

## Review outputs

The migration writes `outputs/job-function-audit/transition/before-after.csv`, `review-required.csv`, `manual-review-sample.csv`, and `summary.json`. The sample is intended for human review. Accuracy has not been measured; the project does not claim the 90% quality goal until a representative sample is manually checked.
