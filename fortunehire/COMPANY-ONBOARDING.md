# Company directory onboarding

Use this guide for small, reviewed batches of Fortune 500 companies. A directory record points visitors to an official career site; **it does not connect a job feed** or guarantee current openings. Keep job collection work in a separate, verified change.

## Verify each company

1. Check membership on Fortune's list for the applicable `listYear`. Record the company profile and list source; do not infer membership from a prior year.
2. Verify headquarters city and state, industry, and the official career destination against authoritative sources, including the company's own site. Confirm ownership when the application site uses another host. Skip a company whose required facts cannot be verified; continue with the rest of the batch.
3. Add one unique, stable `id` and the verified fields to [`public/data/companies.json`](public/data/companies.json), following existing records. Include `name`, `industry`, `headquarters`, `listYear`, `careerUrl`, `profileSource`, `membershipSource`, `reviewedAt`, and an accurate `verificationNote`; use `supportingSources` when needed. Do not alter existing company records or jobs to increase coverage.

## Add branding when available

4. Find an authentic, recognizable logo or icon on an official corporate or employer career site. Check that the source is suitable for local use and recognizable at the existing 40-pixel card size. Do not use a third-party logo API, hotlink, or unofficial substitute.
5. Save the verified image in [`public/assets/company-logos/`](public/assets/company-logos/) using the company ID as its filename and an image format supported by the current cards (`png`, `ico`, `jpg`, or `svg`). Open the file and confirm it is a valid image.
6. Add an entry under the same ID in [`public/data/company-logos.json`](public/data/company-logos.json): local `src` (for example, `./assets/company-logos/<id>.png`), exact official `sourceUrl`, official `companyUrl`, and `reviewedAt`. If no suitable official asset can be obtained, leave the entry absent so the existing initials fallback remains visible. Do not modify older logos without a demonstrated defect.

## Record feed status and verify

7. Add the company to [`public/data/company-feed-status.json`](public/data/company-feed-status.json). For a directory-only addition, use the existing `verification-needed` convention with a truthful `reason`, `nextStep`, `officialCareerUrl`, and `reviewedAt`; update the status counts and coverage text. Do **not** mark it `connected` or add it to `job-sources.json` without a separately verified job-feed integration.
8. Update directory and feed-status count assertions in [`test/`](test/) and the relevant coverage statements in [`README.md`](README.md) and the [root README](../README.md). Keep the year and counts consistent with the JSON data.
9. From `fortunehire/`, run `npm test` and `node scripts/validate-jobs.mjs`. Confirm the existing job count and records have not changed. Start a local preview with `npm start`; inspect every new company card on desktop and mobile, its official career link, source disclosure, and logo or initials fallback. Check for broken images and layout overflow.
10. Create one focused pull request against the latest `main`. List added and skipped companies, sources, counts, and checks. Leave the PR for review; do not merge automatically.

## November 22, 2026 eligibility review

The directory review yielded zero additions. Fortune's [2026 U.S. Fortune 500 ranking](https://fortune.com/ranking/fortune500/) determines eligibility for this batch.

| Company | Review outcome |
| --- | --- |
| OpenAI | 2026 Fortune 500 membership could not be verified. [Fortune profile](https://fortune.com/company/openai/) |
| Perplexity | 2026 Fortune 500 membership could not be verified. [Fortune profile](https://fortune.com/company/perplexity/) |
| Anthropic | 2026 Fortune 500 membership could not be verified. [Fortune profile](https://fortune.com/company/anthropic/) |
| Brown & Brown | Fortune's 2026 ranking data places the company at No. 601, outside the first 500. [Fortune profile](https://fortune.com/company/brown-brown/) |

## Reuse in a future Codex task

> Add the next five verified Fortune 500 companies to FortuneHire's directory. Follow `fortunehire/COMPANY-ONBOARDING.md`, add every company whose required facts can be verified, and report any skips. Keep job feeds and existing jobs unchanged. Run the guide's checks and open one PR against `main`; do not merge.
