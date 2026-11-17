# Employment-type cleanup, November 17, 2026

Reviewed the 747 currently visible jobs with unspecified employment type across 17 employers. The bounded check inspected 652 individual pages with existing crawler rules and pacing. Corrections use actual employer fields or explicit role-title/description labels: 100 Verizon, 47 Home Depot, and 23 across seven other employers.

170 records corrected: 153 Full-time, 13 Internship, 2 Temporary (explicit seasonal titles), 1 Part-time, and 1 Contract. 577 remain unspecified. Missing/inconclusive fields, Apple and Abbott connection failures, and unmatched Phillips 66 page formats prevent a complete determination. Extra Workday schedule checks for Boeing, Elevance and McKesson returned HTTP 429; they were stopped and no recurring endpoint or exception was added.

Verizon TimeType is matched by role ID and exact title, alongside the existing primary record, URL, and description identity checks. Home Depot's current_job employment_type must match the posting ID, requisition, and employer organization; JSON arguments are read as data without executing JavaScript. No further requests are added to the recurring collectors.

The shared employment_type module handles explicit Full Time/Fulltime, Part-time, Intern/Internship, Seasonal/Temporary, and unambiguous bracketed/suffix Contract titles. It also reads explicit structured employment types and role-scoped schedule declarations. It does not derive a schedule from Regular, Casual, weekly-hour counts, benefits eligibility, pay expressed as a full-time equivalent, navigation, or remote-work frequency. Ambiguous full-time/part-time options remain unresolved. The existing explicit part-time title priority is preserved.

The rules apply during normalization and as a publication fallback over retained records, so newly collected jobs and previously retained jobs keep the fixes. Workflow triggers include the new module and its tests. Current-data corrections change employmentType and its evidence only; posting/check dates, source hashes, locations, work arrangements, eligibility, and pay are preserved.

Validation: 166 Python tests plus 60 frontend/data tests pass (226 total), and all 2,862 retained records validate. No accounts, paid provider, or AI calls are introduced to ongoing refreshes. RTX remains paused.
