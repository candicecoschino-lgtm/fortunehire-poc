# FortuneHire continuation

37 feeds enabled; 14 employers remain unconnected and RTX stays paused. November 14 additions in the latest batch: Amazon 20, Costco 4, UPS 6. They passed initial collection and refresh on GitHub, including a separate Amazon job-ID lookup. Run 43607132530. Coverage remains a small sample.

Remaining: Alphabet/Google, Apple, Delta, Fannie Mae, Home Depot, IBM, JPMorgan Chase, Meta, Microsoft, Nvidia, Oracle, Progressive, Salesforce, Tesla. Nine have access restrictions; do not bypass them or assume a paid provider is mandatory.

Salesforce’s old career portal moved to https://www.salesforce.com/company/careers/ and its jobs page is /company/careers/jobs/. Its known corporate robots redirect resolves to HTTP 404, but the new public career-script request returned 403. Review an authorized public feed. IBM’s corporate search at /careers/search works; the tested individual JobDetail page returned HTTP 202. Its published public client uses a search API template on www-api.ibm.com; verify actual employer posting dates and role status before implementing it. Fannie Mae returned HTTP 503 and still needs job-specific state and work-arrangement evidence. Apple’s published robots redirect goes to https://apple.com/pagenotfound and remains unresolved after network interruption. Delta’s portal previously returned HTTP 202 without usable data.

Keep the fourteen-day posting window, seven-day verification freshness limit, bounded discovery, per-host pacing, and closure safeguards. State-restricted remote roles remain Remote; an office address does not establish remote eligibility. Preserve visible source-health warnings and verification dates during outages.
