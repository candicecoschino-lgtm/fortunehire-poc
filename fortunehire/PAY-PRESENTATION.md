# Compact salary display

Job cards show only the published salary range in the top-right pay area. Starting-range/projected-range boilerplate and employer prose remain in job details. Published ranges get the same readable type size as verified structured pay.

Structured pay retains its verified hourly/annual period. A range extracted from published text displays a period only when the text explicitly supplies one. Duplicate ranges collapse; distinct ranges remain separate rather than being combined into an invented range. No clear range means See pay details. State-specific applicability checks remain active. All original pay wording and qualifiers remain accessible, and numeric minimum-pay filters still rely only on verified structured salary data.

60 frontend/data tests pass, including employer boilerplate, missing pay periods, distinct bands, duplicate ranges, hourly cents, unparseable text, and geographic applicability. No collector code, posting dates, job data, saved searches, or refresh rules change. RTX stays paused.
