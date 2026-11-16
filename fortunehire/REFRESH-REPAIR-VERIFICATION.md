# Refresh repairs â€” November 16, 2026

RTX remains paused and is not contacted by these checks.

## Changes

- HTTP 502, 503 and 504 failures have at most three total attempts, with paced backoff. A valid Retry-After is honored if the wait is at most sixty seconds; a longer or invalid wait stops the request. HTTP 403, HTTP 429 and explicit challenge headers are never retried.
- Reviewed Salesforce and Coca-Cola Workday pages can identify an unavailable individual posting without a canonical link or JobPosting block. Recognition requires the exact requested employer URL in og:url, the reviewed tenant and career-site ID, external cxs configuration, and one explicit postingAvailable:false value. Ambiguous, mismatched and generic empty pages do not establish closure.
- An unavailable posting goes through the existing repeated-missing guard: two observations at least six hours apart, with the bulk-closure guard retained. Failed and unavailable checks do not refresh the job's successful verification date.

## Evidence

The previously failing Elevance page returned HTTP 200 and a valid individual JobPosting dated November 10. Its earlier HTTP 502 was an upstream gateway failure, not evidence of closure.

Salesforce's previously failing page returned HTTP 200 with the exact matching og:url and explicit postingAvailable:false in its public configuration. The missing canonical link was a consequence of the unavailable posting. The recognition code matched this saved employer response without requesting the denied details API.

Coca-Cola returned HTTP 429 with an explicit Cloudflare challenge on robots.txt. Requests stopped immediately. Its current postings could not be reverified, and its earlier zero-JobPosting response is not proven to represent a closed role. The Workday change is tested against synthetic Coca-Cola fixtures and the saved active employer page format; it is not a successful live Coca-Cola refresh. No access workaround or paid provider was used.

Validation: 143 Python tests and 33 directory, filter and publication tests passed locally. GitHub run 43874118747 passed: all 98 Elevance and 79 Salesforce records were checked, with zero errors or warnings. Three Elevance records passed the preexisting repeated-missing guard and were marked closed; five others remain pending. Salesforce has one pending unavailable posting, preserved until a confirming observation at least six hours after the first. All 2,544 staged publication records validated. Coca-Cola was not contacted from the test runner after its local challenge.
