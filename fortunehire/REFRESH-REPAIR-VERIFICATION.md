# Refresh repairs - November 16, 2026

## Completed full-refresh result

GitHub run 43875004193 completed successfully and published commit 279e43365d9fef9f107ce836447b7b52a744ccd1. All 45 enabled employers completed with zero errors or warnings; 2,498 postings were checked and all 2,544 publication records validated. Netlify's live collection-status.json independently reports the same successful result.

Coca-Cola checked 57 postings without errors. The original failing role, R-148492, is now correctly pending an unavailable-posting confirmation. Its first missing observation was November 16 at 8:22 a.m. Eastern; it cannot pass the six-hour closure guard before 2:22 p.m. Eastern, and only a later confirming check can close it. The routine twice-daily schedule will handle that check. Other Coca-Cola postings refreshed normally. A fresh local diagnostic at 8:24 a.m. still returned HTTP 429 with a challenge on robots.txt, and local requests stopped. This local restriction is separate from the production collector's successful result; no proxy, challenge bypass or additional runner was used to evade it.

Elevance checked 95 active records and Salesforce checked 79, both without errors. Salesforce also retains one pending unavailable posting. RTX was absent from the source registry and was not contacted. No further collector code change was needed after the prior repair; this follow-up verified its production behavior.

RTX remains paused and is not contacted by these checks.

## Changes

- HTTP 502, 503 and 504 failures have at most three total attempts, with paced backoff. A valid Retry-After is honored if the wait is at most sixty seconds; a longer or invalid wait stops the request. HTTP 403, HTTP 429 and explicit challenge headers are never retried.
- Reviewed Salesforce and Coca-Cola Workday pages can identify an unavailable individual posting without a canonical link or JobPosting block. Recognition requires the exact requested employer URL in og:url, the reviewed tenant and career-site ID, external cxs configuration, and one explicit postingAvailable:false value. Ambiguous, mismatched and generic empty pages do not establish closure.
- An unavailable posting goes through the existing repeated-missing guard: two observations at least six hours apart, with the bulk-closure guard retained. Failed and unavailable checks do not refresh the job's successful verification date.

## Evidence

The previously failing Elevance page returned HTTP 200 and a valid individual JobPosting dated November 10. Its earlier HTTP 502 was an upstream gateway failure, not evidence of closure.

Salesforce's previously failing page returned HTTP 200 with the exact matching og:url and explicit postingAvailable:false in its public configuration. The missing canonical link was a consequence of the unavailable posting. The recognition code matched this saved employer response without requesting the denied details API.

Coca-Cola initially returned HTTP 429 with an explicit Cloudflare challenge on robots.txt during the local diagnostic. Requests stopped immediately, and no live Coca-Cola refresh was claimed from that diagnostic. The subsequently completed production run above verified the repaired unavailable-posting handling and refreshed the source successfully. No access workaround or paid provider was used.

Validation: 143 Python tests and 33 directory, filter and publication tests passed locally. GitHub run 43874118747 passed: all 98 Elevance and 79 Salesforce records were checked, with zero errors or warnings. Three Elevance records passed the preexisting repeated-missing guard and were marked closed; five others remain pending. Salesforce has one pending unavailable posting, preserved until a confirming observation at least six hours after the first. All 2,544 staged publication records validated. Coca-Cola was not contacted from the test runner after its local challenge.
