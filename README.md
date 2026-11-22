# FortuneHire

FortuneHire is an independent job-search proof of concept covering reviewed Fortune 500 employers and other companies added by request. Explore [the live site](https://fortunehire.netlify.app/), compare individual job postings, and apply on the employer's official website.

The site offers job-function, company, location, work-arrangement, pay, and other search filters; saved jobs and searches; and local application tracking. No account or résumé upload is required. Listings come from verified employer career sources, with employer posting dates and direct application links. Directory membership does **not** imply that a job feed is connected.

**Directory coverage:** 75 reviewed companies, including 71 from the 2026 Fortune 500 and four added by request. At the November 20, 2026 job-data snapshot, 46 employer sources were enabled and 3,235 jobs were searchable. That snapshot contained 3,743 records, including closed postings. These figures change with scheduled refreshes and the 14-day posting window; current data is in [`companies.json`](fortunehire/public/data/companies.json), [`job-sources.json`](fortunehire/public/data/job-sources.json), and [`jobs.json`](fortunehire/public/data/jobs.json).

## How it runs

GitHub holds the static site and reviewed data. GitHub Actions checks approved employer sources twice daily, validates changes, and commits eligible job updates. Netlify publishes `fortunehire/public` from `main`; there is no production application server or paid job-data API. Job activity is stored in the visitor's browser.

For local checks, use Node.js 22 or later:

```sh
cd fortunehire
npm test
npm start
```

## Documentation

- [Project setup and technical overview](fortunehire/README.md)
- [Company onboarding guide](fortunehire/COMPANY-ONBOARDING.md)
- [Job collection and refresh safeguards](fortunehire/AUTOMATION.md)
- [Job board behavior](fortunehire/JOB-BOARD-SPEC.md)
- [Company feed status](fortunehire/public/data/company-feed-status.json)

FortuneHire is not affiliated with Fortune or the listed employers. Company names and logos belong to their respective owners.
