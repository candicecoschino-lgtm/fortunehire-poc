# Full-time fallback

User-selected policy: if no employment type can be verified, classify the posting as Full-time. Explicit Part-time, Contract, Temporary, Internship, and verified Full-time labels retain priority.

Defaulted records use employmentType=Full-time plus employmentTypeBasis=assumed-full-time and a disclosure note. Employer evidence is preserved; the assumption is not represented as an employer statement. Cards display Full-time (assumed), with the explanation in job details. The Full-time filter includes these records.

The publication policy handles current, newly collected, and retained jobs. Subsequent verified evidence replaces the default; explicit title evidence also removes stale assumption fields. Posting/check dates, source hashes, pay, geography, arrangement, saved searches, and collection limits are unchanged. RTX stays paused.

At the pinned data snapshot, 621 retained records lack an employment type, including 578 current visible listings. The migration defaults these records without altering any other source fields. Counts change as the feed refreshes. Earlier verification reports document the pre-default counts.

Validation: 168 Python tests and 61 frontend/data tests pass (229 total), including disclosure, preservation of verified types, idempotency, replacement by later evidence, and Full-time filter behavior.
