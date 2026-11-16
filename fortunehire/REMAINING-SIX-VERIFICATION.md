# Remaining six source review - November 16, 2026

No additional employer passed verification in this review. Production remains at 45 connected employers, six disabled and RTX paused. No production collector code or registry entry changed, and no paid provider was used.

Microsoft was tested first because its existing adapter already verifies matching individual posting identity and dates, employer state geography, work arrangements, pay and travel. GitHub run 43879839952 used six-second request spacing, one search page, a maximum of two new candidates and ten tracked jobs, with a repeat refresh planned only after a successful collection. The first search returned HTTP 429 at 8:51 a.m. Eastern with no Retry-After. The test stopped before any candidates or individual postings; the repeat and publication steps did not run. The draft remains isolated on the verification branch. The failed diagnostic is an upstream access failure, not a failure of the existing 45 production feeds. Its 143 Python and 33 directory/filter/publication tests passed before the network check.

Fresh normal checks of the other five sources:

| Employer | Actual result | Outcome |
| --- | --- | --- |
| Google | Public search and one linked role returned HTTP 200, with no named original publication-date field or JobPosting block. The linked format file is crawler-excluded and was not fetched. | Disabled; positional timestamps and index dates are not substituted for employer posting dates. |
| IBM | Inspected individual role returned HTTP 202 with an explicit AWS verification challenge. | Stopped; corporate search does not independently establish state-level job geography and individual posting status. |
| Delta | Official Avature portal returned HTTP 202 with an explicit verification challenge; corporate page still announces maintenance. | Stopped. |
| Progressive | robots.txt returned HTTP 403. | Stopped before fetching job-search content. The earlier approved diagnostic had separately confirmed a job-search HTTP 403. |
| Tesla | robots.txt returned HTTP 403. | Stopped before fetching job-search content. The earlier approved diagnostic had separately confirmed a job-search HTTP 403. |

No proxy, alternate identity, login, verification solver or excluded endpoint was used to bypass these results. RTX was not contacted. Further connection work needs a change in source access, an employer-permitted feed, or authoritative publication-date evidence. Repeating the same denied requests does not establish a working integration or a need for a paid provider.

The last full production refresh, run 43875004193, passed for all 45 connected employers with zero errors or warnings. Its published data and successful-check dates are retained.
