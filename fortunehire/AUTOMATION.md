# Official job collection pilot

The collector reads Boeing, Citi, and UnitedHealth Group's published XML sitemaps and individual official JobPosting structured data. It does not call the excluded paginated search endpoints, sign in, collect applicant information, or use a paid provider. It checks crawler rules on every run and stops on access denial or rate limiting.

## Scope and schedule

This is a bounded US pilot, not complete coverage of all three employers. Each run considers up to 20 new sitemap candidates per employer and rechecks existing active pilot jobs. Non-US candidates are skipped. There is a cap of 100 tracked active jobs per employer. Sitemap ordering and numeric posting identifiers prioritize discovery; they do not prove posting dates. The published job's date controls the site's date ordering. The status JSON records discovery counts, checks, additions, changes, closures, skipped geography, errors, and last successful checks.

GitHub Actions runs at 10:17 and 22:17 UTC daily and can be run manually through **Actions → Refresh official jobs → Run workflow**. Scheduled runs can be delayed by GitHub. It requires no employer credentials or extra dependency packages. The existing Netlify connection publishes data commits. The workflow validates before committing and does not force-push across concurrent user edits.

## Job lifecycle

- New: validate employer host, requisition identity, structured posting, and explicit US location before publication.
- Changed: replace fields from current employer evidence, keeping the stable employer/requisition ID. A source hash detects edits without retaining full descriptions.
- Closed: honor structured expiry, or require two HTTP 404/410 checks at least six hours apart. Sitemap absence alone never closes a job. A bulk closure guard retains previous jobs when missing responses could indicate an outage.
- Failure: preserve the previous record and its last successful check date. Invalid pages and access failures never refresh freshness. Existing seven-day expiry continues to hide stale records.
- Unknown: do not infer remote eligibility from a job's title or office address, pay scope from another state, or job type from generic benefits language. Conservative extraction means some filters remain unspecified even when a human could interpret the description.

## Validation

Run `python -m unittest discover -s test -p 'test_*.py' -v`, `npm test`, and `node scripts/validate-jobs.mjs`. Lifecycle fixtures are explicitly synthetic and are never published. The original 22 reviewed roles remain filter regression fixtures; the current production dataset is validated separately. Live runs prove connectivity and current field extraction. Simulated lifecycle tests prove handling of changes and closures; observing a real employer change over time requires later runs.

Check `public/data/collection-status.json` and the workflow summary after each run. If coverage is reliable, increase scope deliberately and add adapters rather than removing the pilot limits silently.

