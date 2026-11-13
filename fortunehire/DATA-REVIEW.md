# Directory expansion — November 13, 2026

Coverage now includes 52 reviewed employers from the 2026 Fortune 500. There are 448 companies still to research; this is a curated sample, not a ranked top-50 or complete 500-company directory. Coverage is displayed from the actual dataset length.

Alphabet (Google) and Humana were added on November 13 at the user's request. JPMorgan Chase was already present and was not duplicated. Alphabet is listed once as the Fortune-listed parent; its destination is Google's career portal, not a claim of complete hiring coverage for every Alphabet subsidiary. Humana's official career site redirects to /us/en; its headquarters state is supported by its own corporate filing. Current membership was checked against Fortune's 2026 list. Automated job connections now cover 14 reviewed employers; see FEED-EXPANSION.md for collection scope and the remaining-employer audit.

Each added record links to its Fortune company profile for metadata and list history, the employer's career destination, and a dated review note. The underlying profile pages include the Fortune 500 list and 2026 history. No ranks, revenue tables, company descriptions, individual jobs, or remote-work claims were imported. New filter choices derive from reviewed metadata.

## Exceptions handled

- Older profile slugs were resolved for Cencora, Meta, Bank of America, Verizon, Phillips 66, Disney, Cisco, United Airlines and RTX. Current display names are retained.
- McKesson and Caterpillar profiles spell their Texas headquarters city as “Irvine.” Corporate sources confirm Irving; supporting source links appear on those cards.
- Meta's text-fetch request was rate-limited; its actual career page was reviewed successfully in the browser.
- PepsiCo's corporate careers page was reviewed and used as the destination because its separate recruiting site restricted automated access.
- Kroger and Dell's original corporate career URLs redirect to their JavaScript-based recruiting portals. Retain the original company-owned links and record the text-preview limitation.
- Tesla's career page exposes limited text without JavaScript. No jobs or work-arrangement facts are inferred from it.
- Intel, Lockheed Martin and American Express were researched but deferred after retrieval failures or unresolved career-page review. They are not included in this expansion batch; no guessed substitute addresses are published.

## Validation

Eight Node tests cover metadata and source validation, unique IDs, safe URLs including supporting sources, search normalization, filter intersections, new industry/location combinations, sorting, empty/reset behavior, and URL state. Browser checks and deployment result are recorded in VERIFICATION.md.

## Next data milestone

Expand in further reviewed batches, prioritizing the remaining industries and states. Resolve deferred companies before adding them. A full-roster reconciliation must confirm exactly 500 unique employers belonging to the same year's U.S. Fortune 500 list before changing the UI to claim full coverage.


