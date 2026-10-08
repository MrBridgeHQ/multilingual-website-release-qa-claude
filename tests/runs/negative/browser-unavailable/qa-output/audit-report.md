# Release QA report - Northwind Outdoor demo - FR/EN release QA

Campaign `NEG-browser` · 2026-10-08T14:49:08.650Z → 2026-10-08T14:49:08.651Z

## 1. Scope

- Start URL: http://127.0.0.1:8766/en/
- Environment: local demo (tests/demo-site/server.py on 127.0.0.1:8765)
- Languages: en, fr
- Device profiles: desktop, mobile
- Journeys: J01 Open the home page in the requested language (critical); J02 Follow the main navigation to an internal page (critical); J03 Switch language from an internal page (critical); J04 Follow a legacy redirect and keep the language (critical); J05 Search with results; J06 Search without results shows an empty state; J07 Submit an invalid form and check the error messages; J08 Fill the form with the keyboard and get a local confirmation (critical); J09 Open, use and close the menu on mobile (critical); J10 View a localized offer on mobile
- Run filters: {'journeys': ['J01', 'J02'], 'languages': None}
- Report language: en

## 2. Environment and capabilities

- Runner: run_journeys.cjs 1.0.0 · Node v22.22.0 · linux
- Browser: chromium  - browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium

| Capability | Available |
|---|---|
| page_extraction | no |
| click | no |
| typing | no |
| screenshots | no |
| network_observation | no |
| console_capture | no |
| traces | no |
| geo_verification | no |
| real_device | no |

- browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium

## 3. Summary

**Verdict: `NO_VERDICT`** - no check was executed; nothing can be validated

| PLANNED | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE |
|---|---|---|---|---|---|
| 4 | 0 | 0 | 4 | 0 | 0 |

- Execution coverage: 0/4 (0%)
- Pass rate among executed: 0/0
- Release-critical cases passed: 0/4 (0%)
- BLOCKER: 0, MAJOR: 0, MINOR: 0, COSMETIC: 0

## 4. Priority issues

None.

## 5. Test matrix

| Journey | en / desktop | fr / desktop |
|---|---|---|
| J01 Open the home page in the requested language | BLOCKED | BLOCKED |
| J02 Follow the main navigation to an internal page | BLOCKED | BLOCKED |

Case details (status, reason, final URL):

- `J01-en-desktop` **BLOCKED** - browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium
- `J01-fr-desktop` **BLOCKED** - browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium
- `J02-en-desktop` **BLOCKED** - browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium
- `J02-fr-desktop` **BLOCKED** - browser unavailable: browserType.launch: Failed to launch chromium because executable doesn't exist at /nonexistent/chromium

## 6. Tickets

None.

## 7. Observations, product questions and assumptions

- Assumptions: Expected localized strings and URL correspondences come from this config; they stand in for the product specification.; Brand and product names listed in keep_untranslated are intentionally identical in both languages.

### Geographic checks

None.

## 8. Limitations

- page_extraction: no
- click: no
- typing: no
- screenshots: no
- network_observation: no
- console_capture: no
- traces: no
- geo_verification: no
- real_device: no

## 9. Recommended next steps

- Cover the cases that were not executed: J01-en-desktop, J01-fr-desktop, J02-en-desktop, J02-fr-desktop
