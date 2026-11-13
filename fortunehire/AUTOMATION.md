# Official job collection pilot

The collector reads published XML sitemaps and individual official JobPosting structured data for the 14 reviewed employers enabled in public/data/job-sources.json. See FEED-EXPANSION.md for the audit and remaining work. It does not call the excluded paginated search endpoints, sign in, collect applicant information, or use a paid provider. It checks crawler rules on every run and stops on access denial or rate limiting.

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
