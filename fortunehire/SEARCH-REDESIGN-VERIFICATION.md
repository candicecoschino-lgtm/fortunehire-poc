# Search redesign - November 17, 2026

The first design refinement makes job and company searches immediately accessible while retaining the existing green visual identity, source data and filter behavior.

Changes:
- Compact introductions replace the large decorative opening sections on both pages.
- Job title/company, state and work arrangement are the primary job controls. Company, pay, job type, industry, sector and travel stay available under More filters, with a selected-filter count.
- Active job filters can be removed individually. URL restoration, clear/reset, empty results and pagination retain their behavior.
- Job cards use a consistent single-column layout with company logos, employer posting dates, location/eligibility summaries, work arrangements, published pay and official employer application links.
- Long employer pay wording has a compact preview and a keyboard-accessible full disclosure. No numeric range, period, location applicability or remote eligibility is inferred by presentation code. Complete locations, pay qualifications, travel and successful check dates remain in Job details.
- The company directory offers collected-job links for enabled employers and official career links for every reviewed company. Paused and unconnected employers do not receive collected-job links.

Validation:
- 37 frontend tests passed, including four new presentation checks for posting dates across daylight saving changes, selected-state location summaries, unstructured pay preservation and state-specific pay applicability.
- All 2,885 current official posting records validated against the reviewed companies.
- Browser checks exercised combined state/arrangement/company/pay/travel filters, individual-chip removal and focus behavior, empty results, reset, pagination, URL restoration, state-restricted remote eligibility, full pay disclosure and company-to-job navigation.
- At the default 1,280 by 720 desktop viewport, search began around 302 pixels down and results around 519 pixels down, compared with approximately 870 and 1,214 in the prior layout.
- The job and company pages were checked at a 390 by 844 mobile viewport with no horizontal overflow. The 320 by 740 layout also passed overflow checks, with full-width state and arrangement controls.

Only frontend presentation and its tests are changed. Existing source collection, schedules, publication data and closure safeguards are preserved. RTX remains paused. Account-free saved jobs and a smaller search data index are later enhancements, not part of this first design pass.
