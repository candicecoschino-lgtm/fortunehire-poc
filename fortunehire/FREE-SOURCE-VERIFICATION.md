# Free-source verification — November 15, 2026

42 of the 52 directory companies now have enabled feeds. Nine remain unconnected; RTX stays paused. These are bounded samples, not complete opening inventories. No paid provider or model API is used by scheduled collection.

## NVIDIA

GitHub run 43724355714 independently collected and refreshed twenty recent U.S. jobs with zero errors or warnings. The corporate careers page links to jobs.nvidia.com/careers. The portal explicitly permits /careers and /api/pcsx in its crawler rules. Public search supplies discovery; each individual role page is matched to the permitted per-ID public details response by role ID, URL, title, ATS requisition and posting date. postedTs matches the page datePosted; creationTs is not a publication date. One original employer Workday posting was independently checked and its date matches the public portal.

Four sampled jobs have explicit Hybrid descriptions; sixteen have no sufficiently explicit work arrangement. An Office search category is not proof of a full-time onsite requirement. All twenty preserve published base-pay text; multiple levels or unstated pay periods are not fabricated into numeric salary filters. State names in office locations do not become remote eligibility. Generic six-month schema validity is not an application deadline.

## Home Depot

GitHub runs 43732245766 and 43733597351 collected and independently refreshed twenty recent U.S. jobs without errors or warnings. The employer search page publishes its credential-free jobsapi-google.m-cloud.io job-search interface and organization ID. Date-sorted discovery is scoped to that organization and published portal IDs. Individual employer JobPosting pages provide the actual publication date and U.S. city/state. JSONP is parsed as data, never executed. Store openings that share ATS requisitions retain distinct employer public posting IDs. Navigation and related roles cannot set work arrangements.

The matched role sections identify thirteen Onsite, two Remote and five unknown arrangements. Eleven jobs preserve published pay text. Missing pay periods, employment type and eligible-state declarations stay unknown. Remote/virtual roles can require commuting to an assigned office; retain that caveat and do not convert a generic country schema into nationwide eligibility. Search-index timestamps and far-future generic close dates do not replace verified posting dates or application deadlines.

## Microsoft and existing feeds

The Microsoft portal explicitly allows the tested career and public-data paths. Three roles were verified, then GitHub received HTTP 429. Microsoft remains disabled and its staged jobs are excluded. Honor cooldown and Retry-After guidance before a smaller permitted request-budget test. No denial, robot challenge or rate limit is bypassed.

The revised crawler-rule matcher follows RFC 9309 longest-match precedence, merged matching agent groups, Allow ties, wildcard/end anchors and percent normalization. Regression checks preserve blocking on excluded routes. A compatibility check of the existing forty feeds found thirty-eight clean feeds and two individual missing postings at Walmart and Kroger. Inspection verified Walmart's explicit soft-404 template and Kroger's exact empty per-ID response. These now use the existing repeated-missing guard: two checks at least six hours apart, plus the bulk-closure safeguard. An empty generic page, malformed response or service error cannot close jobs.

Local verification: 125 Python tests, 32 directory/filter/data tests, and validation of all 1,905 assembled records passed. Existing records were synchronized from main commit 0f9e68a77cffc6a5eaed02b8a75d91e93fc6959a before adding the forty verified jobs. Per-source check times remain actual request times. Current production refresh results are in public/data/collection-status.json.

References: https://www.rfc-editor.org/rfc/rfc9309.html#section-2.2.2 ; https://www.nvidia.com/en-us/about-nvidia/careers/ ; https://careers.homedepot.com/job-search-results/ ; https://careers.microsoft.com/ .

Follow-up run 43733632425 verified HTTP 200 individual-role access for Google and Meta under their published rules. Google still needs original date extraction; Meta still needs permitted recent-job discovery. The inspected Meta featured role is dated April 14, so it remains excluded. Oracle, Progressive and Tesla again returned HTTP 403; no further requests were attempted.

## Full production refresh

Run 43733871384 completed successfully on November 15, validating all 1,904 published records and passing 125 Python tests plus 32 directory/filter/data tests. NVIDIA and Home Depot each independently refreshed all twenty tracked jobs without errors or warnings. Forty-one employers had no source errors; one CVS individual posting returned a temporary HTTP 502. Its previous verified record and real check date were retained, and the source health report preserves the error. Walmart and Kroger missing-page formats entered the existing guarded missing checks without causing collection errors. The workflow succeeded with the recorded temporary employer outage.
