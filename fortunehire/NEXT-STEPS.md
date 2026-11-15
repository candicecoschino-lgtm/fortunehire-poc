# FortuneHire continuation

43 employers connected; 8 remain unconnected and RTX stays paused. Meta is newly connected using its employer-advertised /jobsearch/sitemap.xml. Two recent U.S. roles were collected from sixty candidates in three bounded runs and independently refreshed. Forty-four older roles and fourteen non-U.S. roles were excluded. This is a small pilot, not all Meta openings.

Remaining: Alphabet/Google, Delta, IBM, JPMorgan Chase, Microsoft, Oracle, Progressive, Tesla. Keep RTX paused. Google has usable job content but its three positional timestamps still lack a verified publication-date mapping. Its linked format script is excluded by the script host's published crawler rules; no request was made to the excluded script. Do not guess which field is publication or substitute a modification/crawl date.

Meta: only the advertised working job-search sitemap is used. The general sitemap returned HTTP 403 and is unused. Canonical individual URL and exact numeric public role ID must match the employer's public xcp_requisition_job_description record and JobPosting title. Preserve the employer ATS requisition. Read only role responsibilities, qualifications and published U.S. compensation; do not retain internal departments, viewer data or unrelated records. Compensation remains published text until base-pay components and geographic applicability are verified. Missing work arrangement stays unknown. First-observed URL timestamps only prioritize newly appearing URLs over the backlog; actual JobPosting.datePosted always controls the fourteen-day window. Keep the normal twenty-candidate budget, one-second-or-published pacing, seven-day verification and guarded closure checks.

Microsoft remains disabled after HTTP 429, IBM needs a permitted individual-role interface without its robot challenge, and Delta had announced maintenance. Oracle, Progressive, Tesla and JPMorgan had access denials; no bypasses or paid-provider requirement are assumed. See GOOGLE-META-VERIFICATION.md and the complete company audit.

## Full production refresh

GitHub run 43750731217 completed successfully on November 15. All forty-three connected employers completed with zero source errors. Meta independently refreshed both tracked roles with zero changes, closures, errors or warnings. All 129 Python tests and 33 directory/filter/data tests passed, and all 2,272 published records validated. The eight unconnected companies remain disabled and RTX remains paused. Actual current request times and source outcomes are preserved in collection-status.json.
