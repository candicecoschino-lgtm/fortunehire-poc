# Location-based work arrangement policy - November 17, 2026

The user explicitly requested: postings listing a city and state, with no stated work arrangement, should be considered on-site at that location.

The collector first extracts employer-stated remote, hybrid and on-site evidence. A separate classification step then defaults remaining jobs with physical city/state locations to On-site. These records carry arrangementBasis: listed-location and an arrangementNote explaining the policy. Employer evidence, source hashes, employer dates and successful-check dates are retained; a location-based classification is not presented as an employer statement. Job details disclose the distinction. Future successful refreshes apply the same policy.

Remote, virtual, multiple-location and state-only placeholders are not physical city addresses. New York, New York is a valid physical city/state pair. Conflicting settings, unrecognized authoritative worksite fields and explicit remote-or-hybrid alternatives stay unresolved.

Exact employer location labels saying Remote are handled as remote evidence for ordinary JobPosting sources, limited to the states attached to those labels. Salesforce and the Microsoft/NVIDIA PCSX sources retain their source-specific worksite requirements because their location labels alone are not reliable work-model declarations.

On the current visible collection, the change reduces unspecified work arrangements from 1,866 to 19: 1,834 location-based On-site classifications and 13 employer-labeled, state-restricted Remote classifications. The remaining 19 postings have remote-labeled or mixed locations under the source-specific Salesforce/NVIDIA rules, so they are not assigned to On-site. Total visible jobs stay at 2,743. Across all retained reviewed records, 1,853 receive the location-based default and 13 receive the explicit Remote-location interpretation.

Six sampled current official postings from Bank of America, Comcast, Walmart, Cardinal Health, General Motors and Target returned usable pages but no job-specific stated work arrangement. These corroborate the distinction between employer-provided location and employer-stated work model.

Validation: 151 Python tests and 38 frontend tests passed. All 2,885 publication records validated. The migration checks that postedAt, reviewedAt, sourceHash, official URLs and geographic locations are unchanged. All previously classified Remote, Hybrid and On-site records are preserved. No account, paid provider or AI call is added to collection. RTX remains paused.
