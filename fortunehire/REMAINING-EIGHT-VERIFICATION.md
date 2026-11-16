# Remaining eight — November 16, 2026

Oracle and JPMorgan Chase are connected. Total: 45 connected, six disabled, RTX paused. Coverage is sampled, not complete.

Oracle: sixteen recent U.S. postings collected and independently refreshed with zero errors or warnings. Four other candidates without verified U.S. state geography were excluded. GitHub verification run 43864532500.

JPMorgan: five recent U.S. postings collected and independently refreshed with zero errors or warnings. GitHub verification run 43871040311 passed, including publication validation. The user explicitly approved public CX_1001 search and per-job routes and recurring checks. Requests are restricted to those routes on jpmc.fa.oraclecloud.com, at most five new candidates and twenty tracked jobs, minimum two-second pacing. Only this source may continue after its robots.txt returns HTTP 403; successfully published exclusions remain honored. Actual job-route denials, rate limits and verification challenges stop collection. No applicant APIs, accounts or private endpoints are used. The five sampled roles have unspecified work arrangements; location alone does not establish Onsite.

Six sources remain disabled:
- Google: no authoritative original posting-date mapping; excluded format script was not fetched.
- Microsoft: HTTP 429 in GitHub, including the reduced-request pacing experiment (run 43863539716).
- Delta and IBM: explicit robot-verification challenges.
- Progressive and Tesla: actual public job-search pages returned HTTP 403 during the user-approved limited check.

The initial audit confused a robots.txt denial with a job-page denial for JPMorgan, Progressive and Tesla. Automatic approval review rejected the first diagnostic and the broader API follow-up; neither rejected action ran. The user subsequently approved each necessary scope, including the bounded JPMorgan integration. No approval remains pending. The exception is source-specific and does not change other employers' crawler handling.

Validation: 138 Python tests and 33 directory/filter/data tests, plus publication validation. A regression check prevents a failed request from reusing another job's response and incorrectly marking a job closed.

The full 44-source Oracle refresh (run 43865460659) published verified updates but failed its health check for unrelated existing sources: Elevance HTTP 502, Coca-Cola lacking matching JobPosting data, and Salesforce lacking a canonical role URL. Follow-up checks returned Coca-Cola HTTP 429 and Salesforce public per-job API HTTP 403. Neither establishes closure. Prior records and their real successful-check times were preserved; requests stopped. These issues remain unresolved and must not be hidden to force a green workflow.
