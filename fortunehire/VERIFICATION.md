# Verification — November 13, 2026

## Passed
- Seven automated tests: sourced record structure, safe URLs, unique IDs, search normalization, intersecting filters, sorting/reset/empty results, URL round trips, unknown selections, and rejecting malformed records.
- Local HTTP: index, stylesheet, application module, filtering module, JSON dataset, and favicon return 200.
- Browser: initial 12 records load; uppercase `MICRO` returns Microsoft; General Merchandisers + Washington returns Costco Wholesale; those filters survive reload; adding Apple yields zero results and the empty state appears; clear restores 12; Atlanta returns Home Depot and UPS; reverse sorting puts UPS first; a source disclosure opens by keyboard.
- Mobile viewport: document width equals viewport width with all 12 cards loaded; no horizontal overflow observed. Desktop and mobile screenshots inspected.
- Browser console: no errors observed during the tested flow.
- Official career landing pages for all 12 companies were opened and reviewed through web browsing. Corporate career subdomains and company-owned destinations are used. Normal redirect destinations were retained where appropriate. Microsoft's JavaScript-heavy landing page provided limited text; its official careers destination resolved.
- Company industry and headquarters facts reviewed against each linked Fortune company profile. Membership source: Fortune's 2026 U.S. list. Only minimal factual metadata is stored; no company descriptions, revenue tables, logos, or ranking numbers are copied.

## Not yet completed
- GitHub repository upload and Netlify publication. No repository or deployment has been created by this task.
- Verification on the eventual deployed URL, including hosting headers and deployed asset paths.
- Full 500-company coverage: 12 verified starter entries are included. The interface and documentation state this explicitly. Remaining entries must be researched and reviewed before the directory can be called complete.
- An automated live link monitor, screen-reader audit, and testing on physical phones are outside this initial scaffold.

## Primary deployment references
- [Create a GitHub repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
- [Netlify build configuration](https://docs.netlify.com/build/configure-builds/overview/)
- [Netlify create deploys](https://docs.netlify.com/deploy/create-deploys/)

Use the deployment smoke checklist in README.md after Netlify assigns a URL. External career sites can change or show region-dependent content; the review date records a point-in-time check, not continuous availability.
