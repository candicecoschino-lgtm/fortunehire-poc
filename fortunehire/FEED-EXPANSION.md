> Current status: 26 connected employers; all 52 companies are accounted for in COMPANY-FEED-STATUS.md. The earlier batch notes below are historical.

# Employer feed expansion — November 13, 2026

## Implementation spec

Keep the existing 52-company directory and expand job collection in verified batches. Each enabled employer must match its reviewed career host, permit the requested crawler access, expose individual postings with stable requisitions, and pass collection and publication validation. No paid service is needed for the connected batch.

Use a small source registry and shared adapters for compatible sitemap and JobPosting formats. Deduplicate translated URLs, prefer English postings, decode encoded descriptions, and check pay, work arrangement, location, travel, employment type, and employer posting dates independently. Preserve missing details as unknown. Never derive remote eligibility from a headquarters address or title.

Keep the 14-day posting window, seven-day freshness limit, twice-daily schedule, 20-new-candidate allowance, and 100-active-job cap per employer. Three employers may collect in parallel; each host retains its own request pacing and crawler rules. Existing lifecycle, access-failure, and bulk-closure protections remain in force.

Acceptance: source host checks, filter regression tests, lifecycle tests, zero collection errors for each newly enabled employer, valid production data, successful GitHub checks, and live state/arrangement/company/pay/travel checks. Incomplete sitemap discovery and quarantined candidates remain visible in collection-status.json.

## Current coverage

17 connected employers, 35 still requiring an adapter or access investigation. This is sampled coverage, not all openings at each employer. A successful discovery audit does not establish complete coverage or a need for a paid provider.

Some pay ranges have no explicit period or contain target incentives or different geographic bands. These remain visible as employer text and cannot drive numeric pay filters. Generic employer-wide remote policies and boilerplate are not role-level work arrangements. Sector values are broad employer groupings used by this prototype, not a licensed investment classification.

## Employer audit

The remaining-employer audit inspected published crawler rules, discovery documents, and available sample postings. Connection failures are observations from this environment, not proof that a company forbids all automation. External applicant-tracking hosts require separate ownership verification before adding an adapter.

| Employer | Status | Next step or limitation |
| --- | --- | --- |
| AT&T | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Abbott Laboratories | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Alphabet (Google) | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Amazon | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Apple | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Bank of America | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Boeing | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| CVS Health | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Cardinal Health | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Caterpillar | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Cencora | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Centene | Connected — bounded pilot | Verified official discovery and JobPosting; monitor scheduled refreshes. |
| Chevron | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Cigna Group | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Cisco Systems | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Citigroup | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Coca-Cola | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Comcast | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Costco Wholesale | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Dell Technologies | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Delta Air Lines | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Elevance Health | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Fannie Mae | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| FedEx | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Ford Motor | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| General Motors | Connected — bounded pilot | Verified official discovery and JobPosting; monitor scheduled refreshes. |
| Home Depot | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Humana | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| IBM | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| JPMorgan Chase | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Kroger | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Lowe's | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| McKesson | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Meta Platforms | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Microsoft | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Nike | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Nvidia | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Oracle | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| PepsiCo | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Phillips 66 | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Progressive | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| RTX | Paused — GitHub access blocked | Local collection passed, but GitHub returned HTTP 403. No bypass; investigate an authorized source before enabling scheduled collection. |
| Salesforce | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| Target | Connected — bounded pilot | Verified official discovery and JobPosting; monitor scheduled refreshes. |
| Tesla | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| UPS | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |
| United Airlines Holdings | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| UnitedHealth Group | Connected — bounded pilot | Monitor field extraction and scheduled refreshes; incomplete coverage. |
| Valero Energy | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Verizon Communications | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Walmart | Adapter investigation | Reviewed discovery did not provide a compatible individual-posting feed. |
| Walt Disney | Access/discovery investigation | Request, crawler-rule, redirect, or discovery issue; not enabled. |

