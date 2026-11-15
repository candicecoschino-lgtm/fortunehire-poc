# Free-source verification — November 15, 2026

42 of the 52 directory companies now have enabled feeds. Nine remain unconnected; RTX stays paused. These are bounded samples, not complete opening inventories. No paid provider or model API is used by scheduled collection.

## NVIDIA

GitHub run 43724355714 independently collected and refreshed twenty recent U.S. jobs with zero errors or warnings. The corporate careers page links to jobs.nvidia.com/careers. The portal explicitly permits /careers and /api/pcsx in its crawler rules. Public search supplies discovery; each individual role page is matched to the permitted per-ID public details response by role ID, URL, title, ATS requisition and posting date. postedTs matches the page datePosted; creationTs is not a publication date. One original employer Workday posting was independently checked and its date matches the public portal.

Four sampled jobs have explicit Hybrid descriptions; sixteen have no sufficiently explicit work arrangement. An Office search category is not proof of a full-time onsite requirement. All twenty preserve published base-pay text; multiple levels or unstated pay periods are not fabricated into numeric salary filters. State names in office locations do not become remote eligibility. Generic six-month schema validity is not an application deadline.

## Home Depot

GitHub run 43732245766 collected and independently refreshed twenty recent U.S. jobs without errors or warnings. The employer search page publishes its credential-free jobsapi-google.m-cloud.io job-search interface and organization ID. Date-sorted discovery is scoped to that organization and published portal IDs. Individual employer JobPosting pages provide the actual publication date and U.S. city/state. JSONP is parsed as data, never executed. Store openings that share ATS requisitions retain distinct employer public posting IDs. Navigation and related roles cannot set work arrangements.

Two sampled jobs explicitly identify Remote work; eighteen have no verified arrangement. Missing salary, employment type or eligibility stays unknown. Search-index timestamps and far-future generic close dates do not replace verified posting dates or application deadlines.

## Microsoft and existing feeds

The Microsoft portal explicitly allows the tested career and public-data paths. Three roles were verified, then GitHub received HTTP 429. Microsoft remains disabled and its staged jobs are excluded. Honor cooldown and Retry-After guidance before a smaller permitted request-budget test. No denial, robot challenge or rate limit is bypassed.

The revised crawler-rule matcher follows RFC 9309 longest-match precedence, merged matching agent groups, Allow ties, wildcard/end anchors and percent normalization. Regression checks preserve blocking on excluded routes. A compatibility check of the existing forty feeds found thirty-eight clean feeds and two individual missing postings at Walmart and Kroger. Inspection verified Walmart's explicit soft-404 template and Kroger's exact empty per-ID response. These now use the existing repeated-missing guard: two checks at least six hours apart, plus the bulk-closure safeguard. An empty generic page, malformed response or service error cannot close jobs.

Local verification: 123 Python tests, 32 directory/filter/data tests, and validation of all 1,905 assembled records passed. Existing records were synchronized from main commit 0f9e68a77cffc6a5eaed02b8a75d91e93fc6959a before adding the forty verified jobs. Per-source check times remain actual request times. Current production refresh results are in public/data/collection-status.json.

References: https://www.rfc-editor.org/rfc/rfc9309.html#section-2.2.2 ; https://www.nvidia.com/en-us/about-nvidia/careers/ ; https://careers.homedepot.com/job-search-results/ ; https://careers.microsoft.com/ .
