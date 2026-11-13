# Directory expansion — November 13, 2026

Coverage expanded from 12 to 50 reviewed employers from the 2026 Fortune 500. There are 450 companies still to research; this is not a complete 500-company directory. Coverage is displayed from the actual dataset length.

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
