# Check families

Pick the families that match the site's features and the expectations you were given. For each, the table says what really demonstrates the result. Anything weaker is an observation, not a PASS or FAIL.

| # | Family | What to check | Demonstrated by |
|---|---|---|---|
| 1 | Navigation | Key links and menus reach the right destination; redirects land where expected; no 4xx/5xx on navigation | Clicking in a real browser and asserting the final path and HTTP status |
| 2 | Journeys | Search with and without results, filters, forms: field validation, error messages, confirmation | Executing the journey end to end; asserting each intermediate state |
| 3 | Languages | Switching language from an internal page lands on the **same** page in the other language; the language survives redirects and the next steps of the journey; links point to the current language | Asserting the URL path and `<html lang>` after the switch or redirect |
| 4 | Localization | Untranslated text, date and number formats, currency, localized content consistency | Exact text assertions against the expected strings; quote the observed text verbatim |
| 5 | Display | Horizontal overflow, hidden or unreachable buttons, menus or dialogs that cannot be dismissed | Assertions in the target viewport (`expect_no_horizontal_overflow`, visibility) plus a screenshot |
| 6 | Basic accessibility | Keyboard reachability (`tab_until_focus`), visible focus, field labels, dialog labels | Keyboard-only execution; never presented as a full accessibility audit or certification |
| 7 | Technical signals | Console errors, failed requests, HTTP statuses, missing resources | Only when the tool captured them (runner logs); absence of capture is not absence of errors |
| 8 | Multilingual structure | `<html lang>`, canonical, `hreflang` alternates, where relevant and verifiable | Attribute assertions or static extraction of the rendered HTML |

## Localization exceptions

List brand names, product names and intentionally shared words in `languages[].keep_untranslated`. A word that is identical in both languages ("Contact", "Menu") is not an untranslated string. Flag a string only when you know the expected localized value or the text is clearly from another language.

## Defect, suspicion or question

- **Defect (FAIL + ticket)**: an executed check produced something different from a stated expectation.
- **Suspected inconsistency (observation)**: something looks wrong but there is no stated expectation or the evidence is incomplete.
- **Product question (observation)**: the expected behaviour is undefined (e.g. should `/en/old-offers` redirect or 404?). Ask; do not decide.
- A wording or style preference is not a defect.

## Optional extensions

Performance measurements and regulatory checks are opt-in. A measurement states its tool and conditions (device, network, cache, runs). A regulatory check needs an explicit scope and current official sources; it never becomes a compliance certificate.
