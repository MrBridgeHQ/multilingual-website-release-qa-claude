# Geographic checks (only when requested)

Keep five things apart: site language, browser locale, timezone, simulated geolocation, and **network egress country**. Only the last one makes a request come "from" a country.

A `country` URL parameter, a localized URL, an `Accept-Language` header, a locale or a timezone is **not** proof that the test ran from that country.

For each requested country, record in `geo_checks`:
- `country_requested`;
- `country_verified` and `egress_proof`: how the egress country was established (e.g. a geo-IP echo fetched **through the same proxy and browser context** as the site requests, with its response saved as evidence);
- whether that proof covers the same network context as the site requests;
- `status` and `reason`.

If the correspondence cannot be established, the geo check is `NOT_RUN` (no capability) or `BLOCKED` (capability failed), with the reason. Language checks can continue normally. `build_outputs.py` rejects a geo `PASS`/`FAIL` without `egress_proof`.

The bundled runner does not control the egress country; it records requested countries as `NOT_RUN`.
