# FortuneHire continuation

38 feeds enabled; 13 employers remain unconnected and RTX stays paused. Latest additions: Amazon, Costco, UPS, and Fannie Mae. Each passed initial collection and repeat refresh on GitHub. Coverage remains a bounded sample.

Remaining: Alphabet/Google, Apple, Delta, Home Depot, IBM, JPMorgan Chase, Meta, Microsoft, Nvidia, Oracle, Progressive, Salesforce, Tesla. Nine have access restrictions; do not bypass them or assume a paid provider is mandatory. The other four need further adapter or access-policy work. COMPANY-FEED-STATUS.md records current evidence for every employer.

Apple public search exposes actual role links. Its exact two-hop robots redirect ends at a corporate HTTP 404; this behavior is only implemented in the isolated research workflow, not production. Individual pages return 200 but no JobPosting JSON-LD; inspect their employer-rendered public data and verify posting dates, state, identity, and independent refresh. Exclude locationPicker routes. IBM’s published API policy redirects to an HTML homepage; resolve policy before using it. Salesforce’s new linked search script returned 403; do not retry through alternate channels. Delta still returns an unusable 202 response.

Keep the fourteen-day posting window, seven-day verification freshness limit, per-host pacing, closure safeguards, and visible source health. State-restricted remote stays Remote. Office locations do not establish remote eligibility. Fannie Mae generic telecommute metadata must not override explicit role evidence.
