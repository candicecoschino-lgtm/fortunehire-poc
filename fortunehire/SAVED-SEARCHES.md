# Saved filter searches

Visitors can select Save filters below the job filters, name the current search, and return to it under Saved searches. The same name updates an existing search; Remove deletes just that search. Clear all filters leaves saved searches intact. Up to 20 names of 60 characters are supported.

The saved query includes the keyword, state, work arrangement, company, industry, job function, employment type, minimum pay, travel preference, and sort. Loading starts at page one and filters the latest current job dataset, including new postings and excluding closed or expired records. It saves no result snapshots and changes none of the collection/classification rules.

Storage is browser-local under the versioned `fortunehire.saved-searches.v1` key. No account, server, AI call, email alert, or paid service is used. Searches remain in the same browser/device and can disappear if site data is cleared; private-browser storage may end with the session. Storage denial and quota errors produce honest messages and keep ordinary filtering available. Only known filter parameters are stored; malformed records are ignored and names render as text.

The editor has an associated label, length validation, Cancel, Escape, status announcements, and visible keyboard focus. Saved records update across same-origin tabs. Responsive controls were checked at a phone viewport and the default desktop size.

Verification: 56 frontend/data tests pass. Eight new tests cover all filter selections, persistence, updates, removal, malformed storage, bounds, storage failure, and newly received jobs. Browser checks confirmed save, page refresh, clear/load restoration (state, remote, IT, travel exclusion, sort), update, and removal. Temporary test records were removed. Collector code and job data are unchanged. RTX stays paused.
