# Release QA report - Northwind Outdoor demo - FR/EN release QA

Campaign `NEG-auth` · 2026-10-08T16:46:28.792Z → 2026-10-08T16:46:29.110Z

## 1. Scope

- Start URL: http://127.0.0.1:8766/en/
- Environment: local demo (tests/demo-site/server.py on 127.0.0.1:8765)
- Languages: en, fr
- Device profiles: desktop, mobile
- Journeys: J11 Open the account page (critical)
- Run filters: {'journeys': None, 'languages': None}
- Report language: en

## 2. Environment and capabilities

- Runner: run_journeys.cjs 1.0.0 · Node v22.22.0 · linux
- Browser: chromium 141.0.7390.37

| Capability | Available |
|---|---|
| page_extraction | yes |
| click | yes |
| typing | yes |
| screenshots | yes |
| network_observation | yes |
| console_capture | yes |
| traces | no |
| geo_verification | no |
| real_device | no |

- mobile profiles are Chromium device emulation, not real phones

## 3. Summary

**Verdict: `NO_VERDICT`** - no check was executed; nothing can be validated

| PLANNED | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 0 | 0 |

- Execution coverage: 0/1 (0%)
- Pass rate among executed: 0/0
- Release-critical cases passed: 0/1 (0%)
- BLOCKER: 0, MAJOR: 0, MINOR: 0, COSMETIC: 0

## 4. Priority issues

None.

## 5. Test matrix

| Journey | en / desktop |
|---|---|
| J11 Open the account page | BLOCKED |

Case details (status, reason, final URL):

- `J11-en-desktop` **BLOCKED** - HTTP 401 on /en/account: authentication or authorization required · http://127.0.0.1:8766/en/account

## 6. Tickets

None.

## 7. Observations, product questions and assumptions

- Assumptions: Expected localized strings and URL correspondences come from this config; they stand in for the product specification.; Brand and product names listed in keep_untranslated are intentionally identical in both languages.

### Geographic checks

None.

## 8. Limitations

- traces: no
- geo_verification: no
- real_device: no

## 9. Recommended next steps

- Cover the cases that were not executed: J11-en-desktop
