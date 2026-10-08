# Release QA report - Northwind Outdoor demo - FR/EN release QA

Campaign `NEG-retest` · 2026-10-08T14:49:15.359Z → 2026-10-08T14:49:18.567Z

## 1. Scope

- Start URL: http://127.0.0.1:8766/en/
- Environment: local demo (tests/demo-site/server.py on 127.0.0.1:8765)
- Languages: en, fr
- Device profiles: desktop, mobile
- Journeys: J01 Open the home page in the requested language (critical); J02 Follow the main navigation to an internal page (critical); J03 Switch language from an internal page (critical); J04 Follow a legacy redirect and keep the language (critical); J05 Search with results; J06 Search without results shows an empty state; J07 Submit an invalid form and check the error messages; J08 Fill the form with the keyboard and get a local confirmation (critical); J09 Open, use and close the menu on mobile (critical); J10 View a localized offer on mobile
- Run filters: {'journeys': ['J02'], 'languages': ['fr']}
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

**Verdict: `NOT_READY`** - release-critical failures: J02-fr-desktop

| PLANNED | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE |
|---|---|---|---|---|---|
| 1 | 0 | 1 | 0 | 0 | 0 |

- Execution coverage: 1/1 (100%)
- Pass rate among executed: 0/1 (0%)
- Release-critical cases passed: 0/1 (0%)
- BLOCKER: 1, MAJOR: 0, MINOR: 0, COSMETIC: 0

## 4. Priority issues

1. **[BLOCKER]** TCK-J02-fr-desktop - [FR][desktop] Main navigation: 'À propos' link points to /fr/apropos and returns a 404 page (J02-fr-desktop)

## 5. Test matrix

| Journey | fr / desktop |
|---|---|
| J02 Follow the main navigation to an internal page | FAIL 1/1 |

Case details (status, reason, final URL):

- `J02-fr-desktop` **FAIL** - expected path /fr/a-propos, observed /fr/apropos · http://127.0.0.1:8766/fr/apropos

## 6. Tickets

### TCK-J02-fr-desktop - [FR][desktop] Main navigation: 'À propos' link points to /fr/apropos and returns a 404 page

- Status: `STILL_FAILING` · Severity: `BLOCKER` · Diagnosis confidence: `HIGH`
- Rationale: Release-critical navigation journey (J02, P1) cannot be completed in French: every click on the nav entry ends on a 404. The only workaround is typing /fr/a-propos by hand, which is not a reasonable user workaround.
- Impact: French visitors who click 'À propos' in the main navigation land on a 'Page introuvable' 404 page instead of the About page. There is no in-site path to /fr/a-propos for a French visitor (see also TCK-J03-en-desktop).
- Observed scope: fr · desktop · pages: http://127.0.0.1:8765/fr/, http://127.0.0.1:8765/fr/apropos
- Preconditions: Start on the home page of the language under test

**Steps to reproduce**

1. Open http://127.0.0.1:8765/fr/ on desktop Chromium, 1366x768.
2. In the top navigation bar, click the link 'À propos'.
3. Look at the address bar and the page heading.

- Expected: The 'About' entry of the main navigation opens the localized About page.
- Observed: The link has href="/fr/apropos" (missing hyphen). The browser lands on /fr/apropos, which responds HTTP 404 with the heading "Page introuvable" and the text "404". Console: "Failed to load resource: the server responded with a status of 404 (Not Found)". The correct page /fr/a-propos exists and returns HTTP 200 (verified by direct GET).
- Reproduction: reproduced 3/3; retest reproduced 1/1
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J02-fr-desktop/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J02-fr-desktop/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J02-fr-desktop/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J02-fr-desktop/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J02-fr-desktop/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J02-fr-desktop/log-attempt3.json), [final-attempt1.png](evidence/J02-fr-desktop/final-attempt1.png), [log-attempt1.json](evidence/J02-fr-desktop/log-attempt1.json)
- Linked cases: J02-fr-desktop
- Fix hypothesis: Hypothesis: typo in the French navigation template or route table: the 'À propos' nav entry uses /fr/apropos instead of /fr/a-propos (the hreflang alternates on the About page already use /fr/a-propos).

**Acceptance criteria**

- [ ] From /fr/, clicking the nav link 'À propos' opens /fr/a-propos with HTTP 200.
- [ ] The opened page has <html lang="fr"> and the h1 "Qui sommes-nous".
- [ ] No 404 request appears in the console or network log during the journey.
- [ ] Case J02-fr-desktop passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J02 --languages fr, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J02-fr-desktop': 'FAIL'}}

### TCK-J03-en-desktop - [EN][desktop] About page: language switcher opens the French home page instead of /fr/a-propos

- Status: `NOT_RETESTED` · Severity: `MAJOR` · Diagnosis confidence: `HIGH`
- Rationale: Users of the language switch land on the wrong page (home instead of the equivalent page). The language does change and navigation remains possible, so it is a workaround-level degradation of a release-critical journey rather than a dead end.
- Impact: An English visitor reading the About page who switches to French loses their place and lands on the French home page; they must find the About page again (and the French nav link to it is broken, see TCK-J02-fr-desktop).
- Observed scope: en · desktop · pages: http://127.0.0.1:8765/en/about, http://127.0.0.1:8765/fr/
- Preconditions: Open the About page directly in the language under test

**Steps to reproduce**

1. Open http://127.0.0.1:8765/en/about on desktop Chromium, 1366x768.
2. In the header, click the language switcher 'Français' (#lang-switch).
3. Look at the address bar and page heading.

- Expected: The language switcher opens the same page (About) in the other language.
- Observed: The switcher link has href="/fr/". After clicking, the browser is on /fr/ showing "Bienvenue chez Northwind Outdoor" (French home page) instead of /fr/a-propos. The page's own hreflang alternate for fr is /fr/a-propos. The reverse direction (FR About -> EN) correctly opens /en/about (J03-fr-desktop PASS).
- Reproduction: reproduced 3/3
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J03-en-desktop/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J03-en-desktop/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J03-en-desktop/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J03-en-desktop/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J03-en-desktop/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J03-en-desktop/log-attempt3.json)
- Linked cases: J03-en-desktop
- Fix hypothesis: Hypothesis: the English About page's language switcher uses a default/fallback target (language root) instead of the page's counterpart URL from the URL correspondence table.

**Acceptance criteria**

- [ ] From /en/about, clicking 'Français' (#lang-switch) opens /fr/a-propos.
- [ ] The resulting page has <html lang="fr"> and the h1 "Qui sommes-nous".
- [ ] The switcher href on /en/about equals the hreflang=fr alternate (/fr/a-propos).
- [ ] Case J03-en-desktop passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J03 --languages en, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J03-en-desktop': 'NOT_RUN'}}

### TCK-J04-en-desktop - [EN][desktop] Legacy URL /en/old-offers redirects to the French offer page /fr/offres/premium

- Status: `NOT_RETESTED` · Severity: `MAJOR` · Diagnosis confidence: `HIGH`
- Rationale: Redirect loses the user's language (rubric example for MAJOR). The user can still switch back to English with the language switcher, so a workaround exists.
- Impact: English visitors following old links or bookmarks to /en/old-offers are moved to the French version of the offer, in a language they may not read.
- Observed scope: en · desktop · pages: http://127.0.0.1:8765/en/old-offers, http://127.0.0.1:8765/fr/offres/premium
- Preconditions: Legacy offers URL of the language under test

**Steps to reproduce**

1. Open http://127.0.0.1:8765/en/old-offers on desktop Chromium, 1366x768.
2. Wait for the redirect to complete and look at the address bar and page content.

- Expected: The legacy URL redirects to the current offer page in the same language.
- Observed: GET /en/old-offers responds "HTTP/1.0 301 Moved Permanently" with "Location: /fr/offres/premium". The final page is French: h1 "Pack randonnée premium", badge "Offre limitée", price "1 290,00 €". The French legacy URL /fr/anciennes-offres correctly redirects to /fr/offres/premium (J04-fr-desktop PASS).
- Reproduction: reproduced 3/3
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J04-en-desktop/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J04-en-desktop/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J04-en-desktop/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J04-en-desktop/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J04-en-desktop/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J04-en-desktop/log-attempt3.json)
- Linked cases: J04-en-desktop
- Fix hypothesis: Hypothesis: the redirect rule for /en/old-offers was copied from the French rule and targets /fr/offres/premium instead of /en/offers/premium.

**Acceptance criteria**

- [ ] GET /en/old-offers returns a 301 (or 308) with Location /en/offers/premium.
- [ ] Following the redirect ends on /en/offers/premium with <html lang="en">.
- [ ] /fr/anciennes-offres still redirects to /fr/offres/premium.
- [ ] Case J04-en-desktop passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J04 --languages en, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J04-en-desktop': 'NOT_RUN'}}

### TCK-J07-en-desktop - [EN][desktop] Contact form: required-field error messages are shown in French

- Status: `NOT_RETESTED` · Severity: `MINOR` · Diagnosis confidence: `HIGH`
- Rationale: Error message in the wrong language on a secondary state of the form (rubric example for MINOR); the form still blocks submission and highlights the field, so it remains usable.
- Impact: English visitors who submit the contact form with missing fields see the error "Ce champ est obligatoire." in French, which they may not understand.
- Observed scope: en · desktop · pages: http://127.0.0.1:8765/en/contact
- Preconditions: Contact page of the language under test
- Test data: email = not-an-email

**Steps to reproduce**

1. Open http://127.0.0.1:8765/en/contact on desktop Chromium, 1366x768.
2. Leave 'Name' and 'Message' empty, type not-an-email into 'Email'.
3. Click 'Send message'.
4. Read the error messages under each field.

- Expected: Submission is refused and localized errors are shown for the empty name and the invalid email.
- Observed: Under 'Name' the error reads "Ce champ est obligatoire." (expected "This field is required."). The screenshot shows the same French text under 'Message'. The email error is correctly in English: "Enter a valid email address.". Submission is refused and the URL stays /en/contact. The Message-field error was not part of the configured expectations; it is reported from the screenshot.
- Reproduction: reproduced 3/3
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J07-en-desktop/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J07-en-desktop/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J07-en-desktop/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J07-en-desktop/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J07-en-desktop/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J07-en-desktop/log-attempt3.json)
- Linked cases: J07-en-desktop
- Fix hypothesis: Hypothesis: the 'required' validation message is not looked up in the current locale (hard-coded French string or fallback to the fr catalogue), while the email message is localized correctly.

**Acceptance criteria**

- [ ] On /en/contact, submitting with empty Name shows exactly "This field is required." under Name.
- [ ] The empty Message field shows "This field is required." as well.
- [ ] On /fr/contact the same errors still read "Ce champ est obligatoire.".
- [ ] Case J07-en-desktop passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J07 --languages en, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J07-en-desktop': 'NOT_RUN'}}

### TCK-J08-fr-desktop - [FR][desktop] Contact form: 'Envoyer le message' cannot be reached or activated with the keyboard

- Status: `NOT_RETESTED` · Severity: `BLOCKER` · Diagnosis confidence: `HIGH`
- Rationale: Release-critical journey (J08) cannot be completed by keyboard users in French, with no keyboard workaround (rubric example for BLOCKER). Mouse users are not affected (mouse click submits).
- Impact: Keyboard-only and assistive-technology users cannot send the French contact form: Tab skips the submit control, so there is no way to submit without a mouse.
- Observed scope: fr · desktop · pages: http://127.0.0.1:8765/fr/contact
- Preconditions: Contact page of the language under test; Submission allowed: local demo endpoint only
- Test data: name = Alex Tester; email = alex.tester@example.test; message = Demo message, please ignore.

**Steps to reproduce**

1. Open http://127.0.0.1:8765/fr/contact on desktop Chromium, 1366x768.
2. Using only the Tab key, move focus to 'Nom' and type Alex Tester.
3. Press Tab, type alex.tester@example.test in 'E-mail'.
4. Press Tab, type Demo message, please ignore. in 'Message'.
5. Press Tab up to 5 times and watch where focus goes.

- Expected: Every field and the submit control are reachable with Tab; Enter submits; the localized confirmation page is shown.
- Observed: After 'Message', focus never reaches 'Envoyer le message' within 5 Tab presses; it moves to the header/navigation links (screenshot shows focus ring on 'Offres'). In the HTML the control is <div class="btn" id="send" onclick="submitForm()">Envoyer le message</div> (not a button, no tabindex). Supplementary check: clicking it with the mouse submits and opens /fr/contact/merci with h1 "Merci". The English form uses <button type="submit"> and passes J08-en-desktop.
- Reproduction: reproduced 3/3
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J08-fr-desktop/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J08-fr-desktop/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J08-fr-desktop/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J08-fr-desktop/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J08-fr-desktop/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J08-fr-desktop/log-attempt3.json), [manual-checks.json](../../../01-blind-audit/evidence/J08-fr-desktop/manual-checks.json), [manual-mouse-submit.png](../../../01-blind-audit/evidence/J08-fr-desktop/manual-mouse-submit.png)
- Linked cases: J08-fr-desktop
- Fix hypothesis: Hypothesis: the French template renders the submit control as a clickable <div> instead of <button type="submit">, so it is not focusable and does not respond to Enter.

**Acceptance criteria**

- [ ] On /fr/contact, pressing Tab from 'Message' moves focus to 'Envoyer le message' with a visible focus outline.
- [ ] Pressing Enter on it submits and opens /fr/contact/merci with h1 "Merci".
- [ ] The control is exposed as a button (role=button) to assistive technology.
- [ ] Case J08-fr-desktop passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J08 --languages fr, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J08-fr-desktop': 'NOT_RUN'}}

### TCK-J09-fr-mobile - [FR][mobile] Mobile menu: no visible close control, menu covers the page and cannot be dismissed

- Status: `NOT_RETESTED` · Severity: `BLOCKER` · Diagnosis confidence: `HIGH`
- Rationale: Release-critical mobile journey (J09) cannot be completed in French; a menu that cannot be dismissed and hides the page is the rubric example for BLOCKER. Leaving via a menu link is not a reasonable workaround for returning to the current page.
- Impact: On a phone-sized screen, French visitors who open the menu cannot close it: the 'Fermer le menu' button is hidden and Escape does nothing, so the full-screen menu hides the page they were on. The only way out is to tap a menu link and leave the page.
- Observed scope: fr · mobile · pages: http://127.0.0.1:8765/fr/
- Preconditions: Home page on the mobile profile

**Steps to reproduce**

1. Open http://127.0.0.1:8765/fr/ in mobile emulation (Chromium, 390x844, touch).
2. Tap 'Menu' (#menu-toggle).
3. Look for a control to close the menu; press Escape.

- Expected: The menu button opens the navigation, a visible close control dismisses it, and a menu link navigates.
- Observed: The menu opens and fills the screen with the links "Accueil", "À propos", "Offres", "Recherche", "Contact"; no close control is visible (#menu-close "Fermer le menu" exists in the DOM but is not visible). The French page CSS contains "@media (max-width:700px){#menu-close{display:none}}". Supplementary check: Escape leaves the menu open; tapping 'Offres' navigates to /fr/offres/premium. The English menu passes the same journey (J09-en-mobile PASS).
- Reproduction: reproduced 3/3
- Evidence: [final-attempt1.png](../../../01-blind-audit/evidence/J09-fr-mobile/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J09-fr-mobile/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J09-fr-mobile/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J09-fr-mobile/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J09-fr-mobile/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J09-fr-mobile/log-attempt3.json), [manual-checks.json](../../../01-blind-audit/evidence/J09-fr-mobile/manual-checks.json), [manual-after-escape.png](../../../01-blind-audit/evidence/J09-fr-mobile/manual-after-escape.png)
- Linked cases: J09-fr-mobile
- Fix hypothesis: Hypothesis: a French-only CSS rule (@media (max-width:700px){#menu-close{display:none}}) hides the close button at mobile widths.

**Acceptance criteria**

- [ ] On /fr/ at 390x844, after tapping 'Menu', a 'Fermer le menu' control is visible.
- [ ] Tapping it hides #main-nav and returns focus to 'Menu'.
- [ ] Re-opening the menu and tapping 'Offres' opens /fr/offres/premium.
- [ ] Case J09-fr-mobile passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J09 --languages fr, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J09-fr-mobile': 'NOT_RUN'}}

### TCK-J10-en-mobile - [EN][mobile] Offer page: badge shows French text 'Offre limitée' instead of 'Limited offer'

- Status: `NOT_RETESTED` · Severity: `MINOR` · Diagnosis confidence: `HIGH`
- Rationale: Untranslated badge in a secondary place (rubric example for MINOR); price, date and call to action are correct and usable.
- Impact: English visitors see the promotional badge in French on the premium offer page.
- Observed scope: en · mobile · pages: http://127.0.0.1:8765/en/offers/premium
- Preconditions: Offer page on the mobile profile

**Steps to reproduce**

1. Open http://127.0.0.1:8765/en/offers/premium in mobile emulation (Chromium, 390x844, touch).
2. Read the yellow badge under the product title.

- Expected: Badge, price and date are localized, the page has no horizontal overflow and the call to action is visible.
- Observed: #offer-badge reads "Offre limitée" (expected "Limited offer"). Other fields are correctly localized: price "€1,290.00", date "Valid until 12/31/2026", CTA "Add to cart". The badge markup is the same in the desktop HTML (static GET), but only the mobile profile was executed.
- Reproduction: reproduced 3/3
- Evidence: [08-offer.png](../../../01-blind-audit/evidence/J10-en-mobile/08-offer.png), [final-attempt1.png](../../../01-blind-audit/evidence/J10-en-mobile/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J10-en-mobile/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J10-en-mobile/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J10-en-mobile/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J10-en-mobile/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J10-en-mobile/log-attempt3.json)
- Linked cases: J10-en-mobile
- Fix hypothesis: Hypothesis: the badge label is hard-coded or missing from the English translation catalogue and falls back to French.

**Acceptance criteria**

- [ ] On /en/offers/premium, #offer-badge reads exactly "Limited offer".
- [ ] On /fr/offres/premium, #offer-badge still reads "Offre limitée".
- [ ] Case J10-en-mobile passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J10 --languages en, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J10-en-mobile': 'NOT_RUN'}}

### TCK-J10-fr-mobile - [FR][mobile] Offer page: specs table overflows horizontally at 390 px (page 660 px wide)

- Status: `NOT_RETESTED` · Severity: `MINOR` · Diagnosis confidence: `HIGH`
- Rationale: Degraded layout but the content and the 'Ajouter au panier' button stay visible and usable without horizontal scrolling.
- Impact: On phones, the French offer page scrolls sideways: the specs table sticks out of the viewport and the header no longer spans the page width.
- Observed scope: fr · mobile · pages: http://127.0.0.1:8765/fr/offres/premium
- Preconditions: Offer page on the mobile profile

**Steps to reproduce**

1. Open http://127.0.0.1:8765/fr/offres/premium in mobile emulation (Chromium, 390x844, touch).
2. Scroll the page horizontally / compare the page width with the screen width.

- Expected: Badge, price and date are localized, the page has no horizontal overflow and the call to action is visible.
- Observed: document scrollWidth is 660 px for a 390 px viewport. The full-page screenshot shows the specs table ("30 L | 1.2 kg | Gore-Tex | 2 years") extending beyond the screen and the dark header ending at 390 px. The French table has an inline style "min-width:640px"; the English page has no such style and does not overflow (scrollWidth 390 px).
- Reproduction: reproduced 3/3
- Evidence: [08-offer.png](../../../01-blind-audit/evidence/J10-fr-mobile/08-offer.png), [final-attempt1.png](../../../01-blind-audit/evidence/J10-fr-mobile/final-attempt1.png), [log-attempt1.json](../../../01-blind-audit/evidence/J10-fr-mobile/log-attempt1.json), [final-attempt2.png](../../../01-blind-audit/evidence/J10-fr-mobile/final-attempt2.png), [log-attempt2.json](../../../01-blind-audit/evidence/J10-fr-mobile/log-attempt2.json), [final-attempt3.png](../../../01-blind-audit/evidence/J10-fr-mobile/final-attempt3.png), [log-attempt3.json](../../../01-blind-audit/evidence/J10-fr-mobile/log-attempt3.json)
- Linked cases: J10-fr-mobile
- Fix hypothesis: Hypothesis: the inline style min-width:640px on table.specs in the French template forces the overflow.

**Acceptance criteria**

- [ ] On /fr/offres/premium at 390x844, document scrollWidth is <= 390 px.
- [ ] The specs table fits within the viewport (or scrolls inside its own container) and the header spans the full width.
- [ ] Case J10-fr-mobile passes on re-run with no other case regressing.

- Retest procedure: node <skill-dir>/scripts/run_journeys.cjs --config qa-config.json --out <retest-dir> --journeys J10 --languages fr, then python3 <skill-dir>/scripts/retest_tickets.py --previous qa-output/results.json --current <retest-dir>/results.json; finally replay the numbered steps by hand.
- Retest: {'date': '2026-10-08T14:49:18+00:00', 'campaign': 'NEG-retest', 'previous_status': 'OPEN', 'case_statuses': {'J10-fr-mobile': 'NOT_RUN'}}

## 7. Observations, product questions and assumptions

- Assumptions: Expected localized strings and URL correspondences come from this config; they stand in for the product specification.; Brand and product names listed in keep_untranslated are intentionally identical in both languages.

### Geographic checks

None.

## 8. Limitations

- traces: no
- geo_verification: no
- real_device: no

## 9. Recommended next steps

- Fix and retest the open tickets, highest severity first.
