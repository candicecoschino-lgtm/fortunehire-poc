# Google and Meta verification — November 15, 2026

Meta is the forty-third connected employer. Eight directory employers remain unconnected and RTX stays paused. This is a bounded pilot, not all Meta openings. No paid provider, login or model API is used by collection.

## Meta

The employer advertises https://www.metacareers.com/jobsearch/sitemap.xml in its crawler policy. This public job-specific sitemap works locally and from GitHub and currently lists 1,343 individual roles. The separate general sitemap returned HTTP 403 and is unused. Only the exact advertised working feed and strict individual /profile/job_details/<numeric-id>/ pages are read.

Three bounded collection passes inspected sixty candidates. Two actual recent U.S. roles were published; forty-four older candidates and fourteen non-U.S. candidates stayed excluded. Individual JobPosting.datePosted, not sitemap lastmod or observation time, controls the fourteen-day window. Both roles independently refreshed without errors or warnings. Initial and expanded checks: runs 43740460510 and 43740681758. Final observation-priority and independent-repeat verification: run 43741020284.

The canonical role URL and its numeric ID must match the employer-published xcp_requisition_job_description record; the title must match JobPosting. The original ATS requisition is preserved. Only role-specific responsibilities, qualifications and published U.S. compensation amounts are read from the matched records. Internal department fields, viewer metadata and unrelated content are excluded. Compensation is displayed as published text while base-pay components and geographic applicability remain unverified for numerical salary filtering. Work arrangement is unknown unless explicitly stated. First-observed URL timestamps prioritize new URLs over the backlog; they never become publication or verification dates.

Current sample: Machine Learning ASIC Power Architect, posted November 1, Sunnyvale, California, published U.S. compensation $178,000/year to $250,000/year; Network Planner, Network Infrastructure, posted November 5, Menlo Park, California, published U.S. compensation $122,000/year to $181,000/year. These are employer compensation labels; no base-pay assumption is made. Older roles will leave the board as the fourteen-day window advances.

## Google

Google's public career search and directly linked individual role load, but their embedded array has three positional timestamps without a verified publication-date mapping. The presence of a plausible timestamp does not establish that it is the original publication date. The linked format script is excluded by its host's crawler policy and was not fetched. No guessed field index, crawl time, sitemap modification time, or third-party posting age is published. Google remains disabled pending a permitted dated source or authoritative field mapping.

## Validation

129 Python tests and 33 directory/filter/data tests passed. Tests cover exact Meta URL ownership, advertised sitemap selection, stale-date exclusion, matching role identity, field isolation, U.S. compensation selection and prioritization of newly observed URLs without replacing employer posting dates. The source registry and all 52 audited company statuses agree. Existing scheduled data is synchronized before promotion; production check results remain in collection-status.json.

## Full production refresh

GitHub run 43750731217 completed successfully on November 15. All forty-three connected employers completed with zero source errors. Meta independently refreshed both tracked roles with zero changes, closures, errors or warnings. All 129 Python tests and 33 directory/filter/data tests passed, and all 2,272 published records validated. The eight unconnected companies remain disabled and RTX remains paused. Actual current request times and source outcomes are preserved in collection-status.json.
