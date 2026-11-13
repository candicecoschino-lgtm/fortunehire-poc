# FortuneHire continuation — November 13, 2026

Keep the current 52-company directory. Fourteen employers have enabled bounded job feeds. RTX is paused at the user's request; do not retry or enable it as part of the next batch. Thirty-seven other employers still need connections.

## Current corrections

Job cards now reuse the directory's locally hosted official brand icons, with initials as the failure fallback. Explicit employer title qualifiers such as `(Remote)`, `(Hybrid)`, and `- Onsite` are arrangement evidence when the description and structured data do not already specify an arrangement. A remote qualifier alone never establishes eligible states or nationwide availability. Remote jobs with unknown eligibility say so on the card. Generic phrases such as `Remote Sensing Engineer` do not trigger remote classification.

Regression example: United Airlines requisition WHQ00027058, Analyst - Fraud Operations (Remote), was incorrectly unspecified. Check Remote + United Airlines with no state selection; it should appear. Adding a state requires explicit eligibility evidence, not its Chicago office address.

## Next small employer batch

Target is promising: tested official individual pages expose JobPosting data with USD annual base ranges and recent dates. A bounded GitHub probe is defined in `.github/workflows/probe-next-employer.yml`; inspect its output before activation. Target is not enabled yet. The collector and browser currently accept `/job/` routes, whereas Target uses `/jobs/w06/25/title`. Add plural-route support with a collision-safe full-path key for Target and tests. Review Target's non-ISO deadline format before relying on it. Stage a small sample, validate filters, then activate only after GitHub connectivity succeeds.

General Motors and Centene also expose structured data on `/jobs/` routes, but require additional format and eligibility work. GM has address arrays. Centene's Remote-MO/Remote-AZ labels must not be converted into nationwide eligibility based on a generic U.S. applicant-country field. Earlier samples were older than 14 days; find recent postings through approved discovery.

Walmart, Disney, and Verizon samples returned HTML without usable JobPosting blocks. Dedicated adapters remain pending; do not enable them on the shared collector or assume a paid provider is necessary. Humana and JPMorgan remain priorities for later investigation.

## Release checks

Run Python lifecycle tests, Node filter tests, and production-data validation. Require zero new employer collection errors in GitHub before treating a connection as scheduled-ready. Preserve 14-day posting age, seven-day freshness, twice-daily checks, per-host pacing, 20 new candidates per run, and 100 tracked active jobs per employer. Save a screenshot of the live result and update the source archive after a successful release.
