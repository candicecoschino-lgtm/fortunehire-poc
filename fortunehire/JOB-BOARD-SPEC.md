# FortuneHire job-board implementation

Current automation behavior is defined in [AUTOMATION.md](AUTOMATION.md). The original manually reviewed collection below is retained as a regression fixture; the live pilot now checks official employer postings automatically.

The main page lists individual U.S. roles, not employers. The existing 52-company directory remains at companies.html. The connected job collection now covers 14 employers, with evidence-based work arrangements and explicit national/state-restricted remote eligibility. See FEED-EXPANSION.md for the current scope and remaining-employer audit.

## Filtering contract
- Primary: state, then work arrangement (All / On-site / Hybrid / Remote / Not specified).
- State matches an actual posting location for on-site/hybrid roles. For remote roles it matches stated eligible states or explicit nationwide eligibility. A headquarters address never establishes job eligibility. Unspecified eligibility does not match a selected state.
- Secondary: company, sourced employer industry and sector, employment type, and posted minimum base pay. Pay filters compare USD minimums within the selected period; hourly pay is never annualized. Missing/unverified pay is excluded only when a pay threshold is selected. Location-specific pay ranges require explicit scope; no blended range.
- Include travel-required roles defaults on. Turning it off excludes confirmed travel requirements; unknown travel remains included and is labeled. Remote does not mean travel-free.
- Search covers role title and employer. Filters intersect, URL state persists, and unavailable URL values never silently broaden results.

## Source and freshness
Manually review the official individual job page, retain employer requisition ID and destination URL, and publish only minimal factual metadata. Store source links, posted/reviewed dates, known closing date, location restrictions and explicit evidence notes. Avoid copied descriptions. Ambiguous/contradictory arrangements, expired deadlines and local-office exceptions are deferred rather than guessed. No scraping service or automatic job ingestion is included.

Hide closed records, postings past a stated deadline, and entries more than seven days past their review date. Use the current date in America/New_York. Re-review is manual; scheduled imports require an approved data source and are not implied. Explain curated coverage and point-in-time availability on the site. Unknown values say “not verified” or “not specified,” not “none.”

## UX and validation
Each role title and View role & apply button links to that exact employer posting. Cards show employer, work arrangement, actual location/eligibility, pay when verified, type, travel and source/review details. No login or resume upload on FortuneHire. Test state + arrangement combinations, nationwide and restricted remote eligibility, pay periods, unknown fields, travel behavior, expired/stale removal, URL state, safe URLs, keyboard operation, mobile overflow, pagination, and exact employer links. Publish through the existing GitHub → Netlify connection and verify the deployed version.


