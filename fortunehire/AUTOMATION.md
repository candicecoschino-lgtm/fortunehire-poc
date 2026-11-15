# Official job collection pilot

The collector reads published XML sitemaps, official individual JobPosting/page data, and explicitly reviewed public job-search interfaces for the 42 employers enabled in public/data/job-sources.json. See FEED-EXPANSION.md for the audit and remaining work. It does not call excluded endpoints, sign in, collect applicant information, or use a paid provider. It checks crawler rules on every run and stops on access denial or rate limiting.

## Scope and schedule

Show only employer postings dated within the last 14 days, including a posting exactly 14 days old. Unknown dates and future dates are excluded. This uses the employer's posting date, not a LinkedIn date or the collector's last check. Both collection and browser filtering enforce the window. Aging out is separate from an employer closing a role; window exclusions are counted in the status record. A new review never resets a job's original posting date.

This is a bounded US pilot, not complete coverage of the connected employers. Each run considers up to 20 new sitemap candidates per employer and rechecks existing active pilot jobs. Non-US candidates are skipped. There is a cap of 100 tracked active jobs per employer. Sitemap ordering and numeric posting identifiers prioritize discovery; they do not prove posting dates. The published job's date controls the site's date ordering. The status JSON records discovery counts, checks, additions, changes, closures, skipped geography, errors, and last successful checks.

GitHub Actions runs at 10:17 and 22:17 UTC daily and can be run manually through **Actions → Refresh official jobs → Run workflow**. Scheduled runs can be delayed by GitHub. It requires no employer credentials or extra dependency packages. The existing Netlify connection publishes data commits. The workflow validates before committing and does not force-push across concurrent user edits.

## Job lifecycle

- New: validate employer host, requisition identity, structured posting, and explicit US location before publication.
- Changed: replace fields from current employer evidence, keeping the stable employer/requisition ID. A source hash detects edits without retaining full descriptions.
- Closed: honor structured expiry, or require two HTTP 404/410 checks at least six hours apart. Sitemap absence alone never closes a job. A bulk closure guard retains previous jobs when missing responses could indicate an outage.
- Conflicting dates: a deadline before the employer's own posting date is flagged in the listing's source note, left unverified, and never used to declare the job closed.
- Failure: preserve the previous record and its last successful check date. Invalid pages and access failures never refresh freshness. Existing seven-day expiry continues to hide stale records.
- Interrupted downloads: retry up to three times with short delays. Access denials and rate limits stop collection immediately. A persistent failure still marks the workflow failed and retains previous records; failure notifications remain enabled.
- Unknown: do not infer remote eligibility from a job's title or office address, pay scope from another state, or job type from generic benefits language. Conservative extraction means some filters remain unspecified even when a human could interpret the description.
- Pay: read structured pay and employer-specific published pay paragraphs. Explicit hourly/annual ranges can support numeric filters when their geography is clear. Display other published bands verbatim with their labels and scope, without guessing a period or combining different level/location bands into one numeric range. Citi primary-location ranges never apply to a secondary state. Displayed pay can therefore be available even when a numeric pay filter cannot safely use it.
- UHG wording: handle salary-for-this-role statements, visible Travel: Yes percentage labels, and explicit nationwide telecommuting. Generic home-internet requirements do not restrict states. Actual state/radius residency restrictions prevent a nationwide assumption. An unqualified role-wide pay range on a confirmed nationwide U.S. role is not restricted to its listed office address.
- Unsupported new candidates: quarantine without publication and retry after 24 hours. Warnings remain in the public status record. An unparseable existing listing is a check failure and retains its prior successful check date.

## Validation

Run `python -m unittest discover -s test -p 'test_*.py' -v`, `npm test`, and `node scripts/validate-jobs.mjs`. Lifecycle fixtures are explicitly synthetic and are never published. The original 22 reviewed roles remain filter regression fixtures; the current production dataset is validated separately. Live runs prove connectivity and current field extraction. Simulated lifecycle tests prove handling of changes and closures; observing a real employer change over time requires later runs.

Check `public/data/collection-status.json` and the workflow summary after each run. If coverage is reliable, increase scope deliberately and add adapters rather than removing the pilot limits silently.

## Shared format handling

The source registry records the exact reviewed career host and broad sector group for each employer. Sitemap indexes and translated routes are deduplicated by posting identity, with English preferred. Encoded HTML descriptions are decoded before interpreting labeled work arrangements and pay text. Generic company-wide boilerplate does not establish a role’s arrangement. Location-dependent and period-ambiguous published pay stays visible without inventing a numeric filter value. Independent hosts may collect in parallel, with each host still paced separately. Code pushes refresh existing records; scheduled and manual runs consider new candidates.
See ARRANGEMENT-REVIEW.md for role declarations, structured location labels, false-positive protections, and bounded remote discovery hints. URL hints prioritize inspection only; they never set a job category or eligibility.

All 52 company feed outcomes and outstanding obstacles are documented in COMPANY-FEED-STATUS.md and public/data/company-feed-status.json. The State-restricted remote filter remains a subset of Remote; it does not relabel those jobs as hybrid.

## November 14 public portal readers

Humana uses its current canonical JobPosting pages. Verizon reads the public server-rendered role metadata and scoped description, using DisplayDate rather than UpdateDate. Explicit role work-model statements drive arrangement; mobile/field work is not automatically hybrid. Dell and Kroger use the credential-free public Oracle search and individual requisition details linked by their career portals. Discovery reads at most 60 recent candidates and retains only U.S. rows; every selected job page is checked separately. Kroger’s separately reviewed Oracle data host has its own crawler-rule check and pacing. Never use internal qualifications or responsibilities in published descriptions. External posting timestamps with an explicit offset are converted to the site’s New York calendar date.

Humana’s explicitly labeled annual base range can drive the pay filter; mixed per-visit compensation remains text. Verizon’s explicit annual location range can drive it. Missing periods and ambiguous scopes remain unverified.

Valero uses the query-based public Taleo job ID. Display fields are read from the employer’s explicit field map without executing scripts; repeated UI-control fields are ignored, while conflicting job fields are rejected. Posting dates and primary U.S. locations are verified independently. Discovery covers only roles featured on Valero’s official career page. Costco’s numeric public posting IDs are distinguished from requisitions, but the feed stays disabled: all twenty inspected roles were too old for the posting window. No sitemap modification date is substituted for an employer posting date.

Workflow health: an explicit upstream HTTP 5xx response or a tenant-matched official Workday outage redirect produces a warning and remains in the published source-error report and site banner. It retains previous job verification dates. Authentication/access problems, identity errors, missing diagnostics, failed tests, and invalid publication data still fail their checks. This separates employer availability from code/data validation without claiming every source refreshed successfully.

Workday outage redirects are recognized only for the exact HTTPS vendor outage host/path and matching employer tenant. They are never followed. All other cross-host/protocol redirects remain rejected; a generic empty discovery result remains a failure requiring investigation.

## Additional public searches — November 14

Amazon uses the credential-free public /en/search.json recent-results interface and an independent base_query job-ID lookup for older tracked roles. Every record is checked against the individual role page’s ID and title; metadata title whitespace is normalized. Posting dates come from the employer’s posted_date value, never updated_time. Pay is taken from the scoped role page, because search descriptions omit some pay information. Explicit single-location USD hourly/annual base bands support numeric filtering; mixed locations and pay components remain text. An office-location type is not used to invent a work arrangement.

Costco uses the public /api/jobs interface sorted by posted_date, then checks individual JobPosting dates. The earlier sitemap sample consisted of older evergreen roles; sorting by genuine posting date found four eligible roles. Explicit hourly Salary Range labels support pay filtering; experience/year-dependent intern wages remain text.

UPS uses employer-published eagerLoadRefineSearch data from the current U.S. search page. UUIDs and canonical UPBUPSGLOBAL identifiers resolve to the same posting; missing requisitions are labeled public posting IDs. Role JobPosting dates control eligibility; the separate dateCreated field is not substituted. A matching jobDetail.openingPayRate with an explicit hourly period and a single U.S. state supports a starting-rate pay filter.

The exact Salesforce robots redirect to its own corporate HTTP 404 page is followed only for robots retrieval, following RFC 9309 sections 2.3.1.2–3: https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.2 . Job redirects retain the strict host restriction. The Salesforce feed is now enabled after individual-role and public-details verification; access denials are not bypassed.

## Fannie Mae — November 14

For one explicitly U.S. office, retain the state from the employer sitemap URL when the canonical role URL drops it. Keep the employer office name; multiple ambiguous offices remain unpublished. Generic TELECOMMUTE metadata conflicts with the portal’s office policy, so only explicit role labels establish Hybrid or Remote. Annual Pay Range labels may appear inside a paragraph; numeric filtering requires an explicit annual period, one unique range and one state. Initial collection and independent repeat refresh must both pass.

## Apple — November 14

Read direct public /en-us/details/<job-location-id>/<slug> links from the search page. Decode the literal JSON string assigned to __staticRouterHydrationData with JSON parsers; never execute employer JavaScript. Match the full jobNumber and selectedLocation.postingIdentifier. Require an active U.S. city/state and the matching location-specific postingPostLocationData.en_US entry. Ignore changing general postingDateMeta/longPostingDate fields. Country-wide retail pipelines are excluded. Include only selected-office pay and deadline footers. Do not infer Remote from homeOffice or annual pay from the size of a dollar range. Exact robots-only corporate redirect hops end at verified HTTP 404; job redirects remain host-restricted.

## Salesforce — November 14

The public corporate careers page loads https://a.sfdcstatic.com/digital/xsf/careers/prod/jobs_1.json. This complete credential-free employer snapshot supplies requisition IDs, original posting dates, countries and exact Workday application URLs. Require matching Count/Total_Jobs/entry count and a snapshot fetched within 24 hours. Validate the Salesforce tenant and requisition in every URL. Use snapshot dates only to prioritize discovery; individual Workday JobPosting dates control publication. Initial collection and independent repeat refresh each verified nineteen jobs without errors or warnings.

Parse explicit U.S. state/city labels such as New York - New York. Generic TELECOMMUTE tags are not enough to label these roles remote. Location labels alone do not establish the work setting. Office - Flexible means Hybrid; Remote Home-Based establishes Remote, subject to conflicting explicit role declarations. State-restricted eligibility is inferred from explicit Remote location labels only after the role work setting is verified as Remote. Office addresses alone do not establish remote eligibility. Keep multiple location-dependent pay bands as published text when they cannot support one numeric range.

IBM research resolved the published two-hop robots redirect using RFC 9309 sections 2.3.1.2 and 2.3.1.5: https://www.rfc-editor.org/rfc/rfc9309.html . The API search works but individual role requests receive an explicit robot-verification challenge; IBM remains disabled. Delta remains disabled during its announced career-site maintenance.

### Salesforce role-details verification

The individual role page loads the public GET /wday/cxs/salesforce/External_Career_Site/job/<posting-id> interface, allowed by the employer robots policy. Require matching requisition, title, original posting date, posting-site ID, application host and explicit posted/canApply flags. Preserve additional U.S. location labels. Use the employer remoteType field rather than a primary location name to set Hybrid/Remote/On-site; conflicts remain unknown. Employer explanation: https://www.salesforce.com/news/stories/hybrid-workplace/ .

Code pushes cancel an outdated in-progress refresh in the same group so old code cannot publish stale classifications or fail when trying to overwrite a newer commit. Scheduled/manual runs remain serialized.

## NVIDIA and Home Depot — November 15

See FREE-SOURCE-VERIFICATION.md for verified free public interfaces, field provenance and request limits. Crawler rules use RFC 9309 longest-match precedence; explicit Allow rules can permit career paths under a general exclusion. Excluded paths, security challenges and HTTP 403/429 still stop collection. Home Depot uses distinct public posting IDs for shared store requisitions. Employer soft-404 and exact empty per-ID Oracle lookups enter the same two-check/six-hour missing guard; generic errors and malformed results do not close jobs.
