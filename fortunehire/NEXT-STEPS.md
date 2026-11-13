# FortuneHire continuation

29 employer feeds are enabled. 22 companies need format, eligibility, discovery, or authorized-access work. Keep RTX paused. All 52 reviewed statuses and next steps are in COMPANY-FEED-STATUS.md and public/data/company-feed-status.json.

Latest additions: Cardinal Health, Bank of America, and Phillips 66. The first two use reviewed U.S. month/day/year dates. Bank of America emits literal newlines in some JSON strings; only its reader accepts those strings without editing values. Cardinal repeats a tenant identifier across jobs, so canonical public posting IDs are used and labeled as posting IDs. Phillips 66 has public HTML microdata, including explicit UTC posting/deadline dates. Its earlier stated application closing date takes precedence when supplied.

A shared collision guard quarantines new candidates with conflicting identifiers instead of replacing an existing job. Fixed published hourly rates are represented as equal minimum and maximum values and displayed once. Do not invent annual periods for salary bands without an explicit period.

Prioritize the remaining easiest readers next, including the Fannie Mae location/work-arrangement review and permitted alternative discovery methods. Do not bypass HTTP denials or crawler exclusions, and do not relabel state-restricted remote jobs as hybrid.

Keep the 14-day posting window, seven-day freshness limit, per-host pacing, twenty new candidates and one hundred active jobs per employer, and closure safeguards. Verify every new source from GitHub before enabling it; update the status report and source archive after release.
