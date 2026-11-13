# Job data review — November 13, 2026

Historical review of the original 22-posting starter collection. The current automated pilot supersedes this manual maintenance process; see [AUTOMATION.md](AUTOMATION.md), the dated records in `public/data/jobs.json`, and `public/data/collection-status.json` for current coverage and check results.

## Coverage and review method

22 manually reviewed individual postings from Boeing, Citigroup and UnitedHealth Group: 3 on-site, 15 hybrid and 4 remote. This is a small curated proof of concept, not a comprehensive or automatically refreshed feed. All titles and application buttons link to the official individual employer posting, not a generic career landing page.

Only minimal factual metadata is stored. No full job descriptions, qualifications, contact details, resume data, or candidate data are copied. Employer industry and sector are sourced from linked company profiles; employer headquarters do not participate in job-state filtering.

## Included evidence and limits

- On-site and hybrid arrangements come from explicit employer labels. Remote eligibility comes from explicit national-remote wording or named eligible geography. The Tampa coordinator role retains its 20-mile residency and commuting requirement. A remote role with Pacific Time working hours retains that condition.
- Travel is tri-state: required, employer states none, or not specified. Turning off travel-required roles excludes only confirmed requirements. Unknown travel remains visible and clearly labeled.
- Pay is used only when the reviewed range can be recorded. Hourly and yearly figures remain separate. Citi ranges are scoped to the primary posting state and are not used to qualify a different state's pay filter. A Boeing posting with varying state ranges has no single synthetic salary range. Missing pay is labeled “not verified,” not “not disclosed.”
- Job type is not inferred from salary, a job title, or work arrangement. Unverified employment type stays “Not specified.”
- Search pages and individual pages sometimes disagree or show past deadlines. Expired examples were excluded. Remote postings with local hybrid exceptions that could not be represented accurately in this first collection were deferred.
- A dated review does not guarantee the role remains open. The employer's page is the source of truth.

## Maintenance and expiry

Edit `public/data/jobs.json` to add or re-review jobs. Retain the official URL and requisition ID, posted date, reviewed date, closing date when specified, exact state eligibility, travel evidence and pay scope. Re-review a listing before changing its date; never merely extend dates to keep cards visible.

The client hides closed/needs-review records, published deadlines before today's New York date, future-dated records, and records more than seven days past review. Re-check freshness when the tab becomes visible and once per minute. No automatic refresh, job scraper, scheduler, account, paid provider or resume upload was added. Without continued manual review, this small collection will expire and show an honest empty state.

To add another employer, extend the employer-specific official-host allowlist in `public/jobs.js` only after confirming its domain, and add sourced classification metadata. Automated ingestion is a separate milestone requiring a permitted feed/API or licensed source.

## Validation

19 automated checks cover the existing company directory and new job board, including state/arrangement intersections, actual remote eligibility, unknown states, separate pay periods and pay geography, unknown travel, expired/stale records, date boundaries, query URLs, pagination and unsafe/wrong-employer links. Browser QA additionally checks representative official postings, Florida combinations, pay thresholds, URL reload, pagination, keyboard disclosures, mobile layout and the retained company page.

