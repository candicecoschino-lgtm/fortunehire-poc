# All 52 company feed statuses — November 13, 2026

26 connected; 25 need further work or authorized access; RTX is paused. All 52 are accounted for, but all 52 job feeds are not operational. No access denial or crawler restriction was bypassed. Unverified jobs are not published. See public/data/company-feed-status.json for evidence and next steps.

| Company | Status | Reason / next step |
| --- | --- | --- |
| AT&T | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Abbott Laboratories | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Alphabet (Google) | access-restricted | Published crawler rules exclude the tested Google career paths. Obtain an authorized job feed or employer permission. |
| Amazon | adapter-needed | Official search page loads, but individual jobs are not in its sitemap; the linked search-data script host returned 403. Review a permitted public search interface or an authorized feed. |
| Apple | rules-unresolved | The official jobs-host robots file redirects to a corporate page-not-found destination. Resolve the published crawler-policy and search-interface requirements. |
| Bank of America | no-eligible-sample | Of twenty tested candidates, thirteen were outside the 14-day window and seven lacked usable matching posting metadata. Review newer individual pages and their publication dates. |
| Boeing | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| CVS Health | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Cardinal Health | no-eligible-sample | Tested structured pages parsed, but the sampled U.S. postings were outside the 14-day window. Improve discovery ordering and verify a recent U.S. sample. |
| Caterpillar | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Cencora | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Centene | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Chevron | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Cigna Group | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Cisco Systems | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Citigroup | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Coca-Cola | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Comcast | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Costco Wholesale | adapter-needed | Official career pages did not expose a compatible individual-job discovery feed. Review the linked application-system integration. |
| Dell Technologies | adapter-needed | The official site redirects to the Dell Oracle Candidate Experience portal; it does not expose jobs in the tested page or sitemap. Implement and verify the permitted public Oracle interface. |
| Delta Air Lines | verification-needed | The officially linked Avature portal returned HTTP 202 without usable job data in this check. Review a permitted discovery method and dated job details. |
| Elevance Health | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Fannie Mae | location-review-needed | Linked Workday pages provide incomplete state/location metadata, and generic telecommute metadata conflicts with office-cadence language. Verify actual work arrangement and job-state evidence before publishing. |
| FedEx | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Ford Motor | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| General Motors | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Home Depot | access-restricted | The directly linked role parses locally, but the GitHub request returned HTTP 403. Use an authorized source that works from the scheduled collector. |
| Humana | adapter-needed | The GitHub sample had nineteen recent candidate pages without matching JobPosting blocks; no eligible role was published. Review the active-page format and verify a current role. |
| IBM | verification-needed | The corporate sitemap timed out; the linked careers portal returned HTTP 202 without usable job discovery. Review a permitted source with verified publication dates. |
| JPMorgan Chase | access-restricted | The Oracle portal linked by JPMorgan returned HTTP 403. Obtain an authorized endpoint or employer permission. |
| Kroger | adapter-needed | The corporate site redirects to the Kroger Oracle portal, which renders search dynamically. Implement and verify the permitted public Oracle interface. |
| Lowe's | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| McKesson | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Meta Platforms | access-restricted | The GitHub discovery request returned HTTP 403. Use an authorized source; do not bypass the denial. |
| Microsoft | access-restricted | The official Microsoft job portal excludes the tested career route in its crawler rules. Obtain an authorized job feed or employer permission. |
| Nike | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Nvidia | access-restricted | The officially linked NVIDIA jobs portal excludes the tested career route in its crawler rules. Obtain an authorized job feed or employer permission. |
| Oracle | access-restricted | Official-host access returned HTTP 403. Use an authorized source; do not bypass the denial. |
| PepsiCo | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Phillips 66 | adapter-needed | Legacy sitemap discovery now works, but twenty sampled pages lacked compatible JobPosting blocks. Add a verified individual-page reader with publication-date evidence. |
| Progressive | access-restricted | Official-host access returned HTTP 403. Use an authorized source; do not bypass the denial. |
| RTX | paused | Skipped at the explicit user request after GitHub access denial. Leave paused unless the user asks to revisit it. |
| Salesforce | rules-unresolved | The career-host robots file redirects to a corporate 404 page. Resolve the current public job portal and crawler policy. |
| Target | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Tesla | access-restricted | Official-host access returned HTTP 403. Use an authorized source; do not bypass the denial. |
| UPS | retired-discovery | The published sample contained retired individual-job URLs, including HTTP 410; no current verified posting was collected. Verify the replacement discovery source and active individual pages. |
| United Airlines Holdings | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| UnitedHealth Group | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Valero Energy | adapter-needed | The corporate page links to Taleo roles whose query-based job identifiers need a dedicated reader. Implement the permitted Taleo job-detail format with date and location evidence. |
| Verizon Communications | adapter-needed | Individual pages are accessible but the reviewed page format lacks the structured posting/date block required by this collector. Verify employer publication dates and implement a dedicated reader. |
| Walmart | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
| Walt Disney | connected | Enabled after verified first-party collection and publication validation. Limited sample, not all openings. Monitor field coverage, freshness, and scheduled refresh results. |
