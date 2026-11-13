# FortuneHire proof of concept

**Automation pilot:** Boeing, Citi, and UnitedHealth Group now have a first-party sitemap/JobPosting collector, with twice-daily GitHub checks and a bounded U.S. collection. See [AUTOMATION.md](AUTOMATION.md) for limits, lifecycle tests, and the manual-run button. Automation supersedes older manual-maintenance notes for these three employers; the 50-company directory remains separate.

**Current product:** the main page is now an individual-job board with State and Work arrangement first, plus company, industry, sector, job type, posted minimum pay and travel filtering. See [JOB-BOARD-SPEC.md](JOB-BOARD-SPEC.md) for current behavior and [JOB-DATA-REVIEW.md](JOB-DATA-REVIEW.md) for coverage, sourcing and maintenance. The 50-company directory is preserved at `public/companies.html`. The directory-specific notes below describe that secondary page.

A static, independent employer directory. Search names and combine company, industry, headquarters state, and headquarters city filters. Open the employer's own career page to find jobs and work arrangements. No accounts, personal data, uploads, tracking, job scraping, or remote-work claims.

**Coverage:** 50 reviewed employers from the 2026 Fortune 500. This is an intentionally labeled growing collection, not a complete 500-company directory. Every record links to its company profile, list membership source, reviewed official career destination, and review date. No rankings, financial figures, logos, or descriptions are republished.

## Preview and checks

Install Node.js 22 or later if needed. No package installation is required.

```sh
npm test
npm start
```

Open http://127.0.0.1:4173. Keep that terminal open while previewing; stop with Ctrl+C. Opening index.html directly is unsupported because the site fetches its JSON data.

## GitHub → Netlify

1. Sign in to GitHub and create a repository named `fortunehire-poc`. Choose visibility yourself. Initialize it with a README if uploading through the website. [GitHub instructions](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository).
2. Unzip the supplied source archive. In your repository, choose **Add file → Upload files**. Upload the CONTENTS of the `fortunehire` folder, including `public`, `scripts`, `test`, `package.json`, and `netlify.toml`. The repository's top level must contain `netlify.toml` and `public/`; avoid an extra nesting folder. Commit the upload. Hidden `.gitignore` and `.github` files can instead be included using Git.
3. Sign in to Netlify. Choose **Add new project → Import an existing project → GitHub**, authorize the intended repository, and select `fortunehire-poc`.
4. Set production branch to the repository's default branch (normally `main`). Leave base directory and build command blank. Set publish directory to **public**. The included `netlify.toml` also declares this setting. No environment variables are required. [Netlify build settings](https://docs.netlify.com/build/configure-builds/overview/).
5. Deploy and open the assigned `https://…netlify.app` address. No purchased domain is needed. Review the account's plan/usage settings yourself; do not select paid upgrades for this prototype. [Netlify deployment instructions](https://docs.netlify.com/deploy/create-deploys/).
6. Run the smoke checks below on the deployed address. Share the repository URL and deployed URL in this chat so we can verify the actual deployment together.

Quick alternative: drag the **public** folder into Netlify's manual deployment flow. This publishes the site assets but does not establish continuous deployment from GitHub. Use the repository import for ongoing updates.

## Deployment smoke checks

- Header and cards load; there are 50 companies with no filters. Check desktop and a narrow phone window.
- Search `micro` → Microsoft; change case → same result.
- Clear. Select General Merchandisers + Washington → Costco Wholesale.
- Select Apple + Minnesota → no results. Clear all filters restores 50 cards.
- Select Atlanta → Coca-Cola, Delta Air Lines, Home Depot and UPS. This is headquarters filtering, not job location filtering.
- Sort Z–A. Copy the URL into a fresh tab and reload: selections, sorting and results persist.
- Tab through controls, open a source disclosure with the keyboard, and follow an official career link. It should open a new tab with the employer's site.
- Verify at least Apple, Walmart, and Microsoft career destinations after deployment. Review destinations for all added companies before accepting them.
- Open `/data/companies.json`, `/styles.css`, and `/app.js` at the deployed origin. Each must return content, not a hosting error.

## Expand the directory

Edit `public/data/companies.json`. Each entry requires a unique ID, name, sourced industry, headquarters city/state, list year, official career URL, company-profile source, membership source and review date. Confirm ownership of the destination through the corporate site, especially when using an external applicant-tracking domain. Store a specific verification note when there is an exception. Do not invent missing fields or use guessed `/careers` addresses. Recheck list membership for the chosen year. Run `npm test` after updates; update the coverage assertion and documentation when the verified record count changes. Filters derive from the data automatically.

Before calling the directory complete, verify all 500 records against appropriate sources and review permission to redistribute any third-party dataset used. The current UI deliberately avoids claiming that milestone. Metadata is a reviewed snapshot, not an automatic live feed. Headquarters can differ from operational locations and the employer's legal address.

## Layout

- `IMPLEMENTATION-SPEC.md`: concise scope and acceptance criteria.
- `public/`: everything Netlify serves; all assets are local and relative.
- `public/data/companies.json`: curated factual records and sources.
- `public/directory.js`: pure filtering, URL-state and validation logic.
- `test/`: Node's built-in tests. GitHub Actions runs these on pushes and pull requests.
- `scripts/serve.mjs`: local preview only, not a production backend.
- `netlify.toml`: publish directory and browser security headers.

GitHub Pages is also compatible when the contents of `public/` are published; Netlify is the primary V1 deployment target. No service-specific API is required.


