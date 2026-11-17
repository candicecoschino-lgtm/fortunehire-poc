# City and ZIP search

The main search row includes City or ZIP with suggestions from the employer-listed office cities in the current feed. Users can enter a city, City/State, City/ST, or five-digit U.S. ZIP (ZIP+4 is also accepted). Leading zeroes are preserved. Input values round-trip through links and saved searches and have a removable filter chip and clear control.

City/ZIP narrows on-site and hybrid roles. Remote eligibility continues to use State; a city query never converts an office address into remote eligibility. Conflicting state selections and unrecognized ZIPs show explanations and do not broaden the search. ZIP loading/failure states are explicit, with Retry on failure and city entry as an alternative.

For multi-location roles, city and state must match the same location. A matching later-listed city appears first on the card. Pay presence and minimum-pay filtering honor the matched location's state even if State is not separately selected. City matching normalizes case, accents, St./Saint, Ft./Fort, Mt./Mount, and New York/NYC naming, without inferring nearby suburbs or a metro radius.

ZIP resolves a postal city, not the role's exact office ZIP, commute time, or distance radius: the current job records provide cities/states, not reliable office ZIPs. This limitation is stated beside the input and in ZIP results. City names can be entered freely even if they do not yet appear in suggestions.

The site bundles 40,977 ZIPs across 99 two-digit-prefix JSON shards from GeoNames' U.S. postal data, licensed CC BY 4.0. A ZIP search loads only its small same-origin shard; typing a city needs no lookup request. ZIPs are not sent to a third-party geocoder, and there is no mapping account/API key. The footer credits GeoNames and the license, and zip-source.json records the source and build metadata. scripts/build_zip_lookup.py regenerates the artifacts manually; it is not added to recurring job collection.

Verification: 77 frontend/data tests pass, covering real ZIPs/leading zeroes, all shard/schema counts and state codes, unknown/failed lookup behavior, city aliases, same-location state intersection, remote separation, later-listed cities, pay geography, saved searches, and older personal-list records. Browser checks verified Burlington ZIP 01803, Austin hybrid roles, invalid ZIP 00000, a conflicting state, saved-search restoration, clear-city behavior, and a 390px viewport. Temporary test searches were removed. Collector data, refresh cadence, employment defaults, and RTX's paused status are unchanged.
