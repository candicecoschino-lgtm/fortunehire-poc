# FortuneHire V1 implementation spec

## Purpose
Help visitors discover Fortune 500 employers and continue to their official career sites. This is a company directory, not a live job board. FortuneHire is an independent prototype, unaffiliated with Fortune or the listed employers.

## Scope
- Buildless HTML, CSS, and JavaScript; no runtime services, dependencies, tracking, or secret keys.
- Search company names; combine exact company, industry, and headquarters city/state filters. Headquarters is never described as a job location.
- Responsive cards with name, industry, headquarters, official career link, source links, list year, and review date.
- Alphabetical sorting, clear filters, result count, empty/loading/error states, keyboard access, visible focus, and shareable URL filters.
- Seed only sourced records whose career destinations have been reviewed. Display the actual verified coverage; do not imply a complete 500-company dataset until all entries are verified. Initial proof-of-concept target: 12 sourced employers across several industries and states. Expansion to all 500 is a separate data-verification milestone, not simulated data.

## Data contract
Versioned JSON: ID, display name, list year, industry, headquarters city/state, official career URL, Fortune company-profile source, verification date, and career-verification note. Industry is the sourced category, not an invented business description. Verify each employer's current ranking and metadata against its profile, and review the official career landing page before inclusion. Store no individual jobs.

## Exclusions
No accounts, resumes, uploads, scraping of jobs, job-level remote/salary filters, AI matching, purchases, or custom domain. No claim that a working career link guarantees an open vacancy. No bulk copying of proprietary list descriptions or rankings.

## Deployment
Repository root contains package.json, netlify.toml, README, tests, and public/. Netlify publishes public/ with no build command. Relative assets also support GitHub Pages. GitHub is the source of record; Netlify imports the repository and provides its assigned netlify.app address. Initial handoff includes an upload-ready archive and deployment instructions. Account sign-in and repository selection remain with the user when necessary.

## Acceptance
Validate data fields, unique IDs, HTTPS destinations, and source provenance. Test combined filters, reset, case/diacritic normalization, URL state, empty states, sorting, safe rendering, and responsive keyboard operation. Confirm local HTTP delivery. After a deployment URL exists, check assets, filters, reload with query parameters, and several outgoing career links on that deployed URL.

Current data milestone: 50 reviewed employers; 450 remain to be researched. Supporting corporate evidence appears on cards when a profile requires correction.
