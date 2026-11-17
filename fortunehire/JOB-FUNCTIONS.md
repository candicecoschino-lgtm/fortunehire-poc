# Role functions and employment types

The jobs page replaces the employer Sector filter with Job function. Industry continues to describe the employer. The company directory and its company data remain independent.

Job function is inferred from explicit title wording using a local rule set in `public/job-functions.js`; no AI or paid service is called. Categories include Sales, Marketing & Communications, Human Resources, IT & Software, Operations, Customer Service, Administrative, Legal & Compliance, Finance & Accounting, Engineering & Design, Healthcare & Clinical, Supply Chain & Logistics, Manufacturing & Skilled Trades, Research & Science, Product/Project/Program Management, Business & Strategy, Retail & Store Roles, Food & Hospitality, and Quality & Safety. Unclear titles remain Other / Unclassified. Cross-functional roles match each applicable function, once per results list.

The interface identifies this classification as title-based. It does not claim an employer supplied these categories. Titles can omit duties, so this first version deliberately leaves ambiguous roles unclassified. Rule refinements can improve coverage without altering employer data.

The previous Job type control is labeled Employment type: Full-time, Part-time, Contract, Temporary, Internship, or Not specified by employer. A Sales or Administrative role can still have an unknown employment type. Adding job functions must not guess schedules or contracts.

The same module classifies every current and newly received title at display/filter time. It has no requisition-ID overrides and is not replaced by scheduled job-data updates. Its tests run on GitHub pushes and before collection. A new listing does not need a manual category migration.

November 17 review: 956 unclassified titles were examined. Expanded technical vocabulary includes application development, programming, AI/ML, data analysis, networking, and architecture. Other gaps included frontline, banking, customer-success, clinical, creative, product, and business roles. Rules classify 900 of that reviewed set; 56 ambiguous titles remain unclassified. The retained count can change as new jobs arrive or old jobs expire.

Verification: 48 frontend/data tests pass, including newly received synthetic listings, reviewed title gaps, ambiguous titles, physical versus IT roles, overlapping functions, employment-type independence, state intersection, and shareable URLs. Existing 159 Python collector tests passed during the preceding multi-location change; this update changes no collector code or job data. RTX stays paused.
