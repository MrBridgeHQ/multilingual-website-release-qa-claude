# Ticket replay report

Source: `replay/tickets.csv` (8 tickets). Site: http://127.0.0.1:8765. Date: 2026-10-08.
Method: Node Playwright and Chromium (headless). Desktop: 1366x768 context. Mobile: 390x844, `isMobile`, `hasTouch`, DPR 3. The tickets do not give a DPR or UA, so I chose those. Scripts are in `replay/work/` (`run.cjs`, `j09.cjs`, `j09b.cjs`).
Nothing was submitted to a backend. The only form actions were the J07 "Send message" click, which the steps require and which client validation refused, and one validation-only click on `/fr/contact` with empty fields to check a J07 acceptance criterion. That second click was also refused and the URL did not change. I did not run the J08 "supplementary" mouse submission because it is not one of the numbered steps.

---

## TCK-J02-fr-desktop: 'À propos' nav link points to /fr/apropos (404)
**Result: REPRODUCED**

Observed:
- On `/fr/`, `#main-nav` holds one link "À propos" with `href="/fr/apropos"`.
- Clicking it lands on `http://127.0.0.1:8765/fr/apropos` with HTTP 404, h1 "Page introuvable", body text "404" and `<html lang="fr">`.
- The console shows "Failed to load resource: the server responded with a status of 404 (Not Found)".
- A direct GET of `/fr/a-propos` returns 200, with h1 "Qui sommes-nous" and lang `fr`.

Acceptance criteria are verifiable as written: URL and status, `lang` and h1, and no 404 in the console or network log. The last criterion ("Case J02-fr-desktop passes on re-run with no other case regressing") depends on the reporter's automated suite and config (`run_journeys.cjs`, `qa-config.json`). A developer holding only this ticket cannot run them. The same applies to every ticket.

Ambiguity:
- Expected says "opens the localized About page" but does not give the URL. The URL appears only in the criteria (`/fr/a-propos`).
- Step 3 says "page heading". The site shows only an h1 "Page introuvable" and a paragraph "404". The ticket's wording ("heading ... and the text '404'") matches what I saw.

## TCK-J03-en-desktop: EN About language switcher opens /fr/ instead of /fr/a-propos
**Result: REPRODUCED**

Observed:
- On `/en/about`, `#lang-switch` has the text "Français" and `href="/fr/"`.
- The page declares `hreflang="fr"` as `http://127.0.0.1:8765/fr/a-propos`.
- After the click, the URL is `/fr/`, the h1 is "Bienvenue chez Northwind Outdoor" and lang is `fr`.
- The reverse direction works: on `/fr/a-propos` the switcher has `href="/en/about"` and opens `/en/about`.

Acceptance criteria are all verifiable, apart from the "re-run" criterion.

Ambiguity:
- The step says to click "the language switcher 'Français' (#lang-switch)". This is clear.
- The third criterion compares an href written as a relative path (`/fr/a-propos`) with an hreflang value that is absolute (`http://127.0.0.1:8765/fr/a-propos`). The ticket should say whether "equals" means after URL resolution.

## TCK-J04-en-desktop: /en/old-offers redirects to French offer page
**Result: REPRODUCED**

Observed:
- `GET /en/old-offers` returns 301 with `Location: /fr/offres/premium`.
- The final URL is `/fr/offres/premium`, with h1 "Pack randonnée premium", badge "Offre limitée", price "1 290,00 €" and lang `fr`.
- `/fr/anciennes-offres` returns 301 to `/fr/offres/premium`, which is correct.
- `/en/offers/premium` exists (200, lang `en`).

Acceptance criteria are verifiable with a browser and the network log. The ticket quotes "HTTP/1.0 301 Moved Permanently". The protocol version is not visible from Playwright, and it does not matter for the fix.

Ambiguity:
- Expected says "current offer page in the same language" without naming the URL. It is named only in the criteria (`/en/offers/premium`).
- "301 (or 308)" is fine, but the ticket does not say whether 302 or 307 would be acceptable.

## TCK-J07-en-desktop: EN contact form required-field errors in French
**Result: REPRODUCED**

Observed after typing `not-an-email` in Email and clicking "Send message", with Name and Message left empty:
- Under Name: "Ce champ est obligatoire." (`#name-error`)
- Under Email: "Enter a valid email address."
- Under Message: "Ce champ est obligatoire."
- The URL stays `/en/contact`.
- The fields have no `required` attribute, so all validation is the site's own.
- On `/fr/contact` with all fields empty, all three errors read "Ce champ est obligatoire." This satisfies the third criterion as it stands today.

Acceptance criteria are verifiable, apart from the "re-run" criterion.

Ambiguity:
- Expected mentions only "the empty name and the invalid email". The criteria add the Message field, and nothing gives the English text for the email error. "This field is required." for Message is in the criteria only.
- Step 2 says to leave Name and Message empty "and type not-an-email". It does not say whether the fields start empty. They did.
- The third criterion ("On /fr/contact the same errors") does not give the FR input data. Which fields are empty, and is the email invalid or empty?

## TCK-J08-fr-desktop: 'Envoyer le message' not reachable or activatable by keyboard
**Result: REPRODUCED** (for the steps as written. I did not repeat the mouse-submit supplementary check.)

Observed:
- From page load, it took 8 Tab presses to reach "Nom" (`input#name`). The order was the 7 header and nav links, then the field.
- After typing in Nom, E-mail and Message, the next 5 Tab presses gave this focus sequence: `BODY`, "Northwind Outdoor", "Accueil", "À propos", "Offres". Focus never reached the submit control, and the 5th press lands on "Offres" as the ticket says.
- The control is `<div class="btn" id="send" onclick="submitForm()">Envoyer le message</div>`, and `getByRole('button', {name:'Envoyer le message'})` finds 0 elements.
- On EN, the control is `<button class="btn" id="send" type="submit">Send message</button>`.

Acceptance criteria are verifiable. "Visible focus outline" is subjective and gives no contrast or size threshold. "Exposed as a button (role=button)" can be checked through the accessibility tree.

Ambiguity:
- Step 2 ("Using only the Tab key, move focus to 'Nom'") does not say how many presses are needed (8 here) or where focus starts.
- Expected says "Enter submits", but no step presses Enter. The ticket also does not say whether Space should activate the control.
- The precondition reads "Submission allowed: local demo endpoint only", yet the steps never submit. The submission appears only as a supplementary mouse check outside the steps.
- The first Tab after Message goes to the document or browser chrome (`BODY`), not straight to the header. The ticket summarizes this as "moves to the header/navigation links".

## TCK-J09-fr-mobile: Mobile menu has no visible close control
**Result: REPRODUCED**

Observed at 390x844 with touch:
- Tapping "Menu" (`#menu-toggle`) opens `#main-nav` as a full-screen layer (0,0,390x844) with the links "Accueil", "À propos", "Offres", "Recherche" and "Contact".
- `#menu-close` exists with the text "Fermer le menu", but its computed `display` is `none` and it is not visible.
- The stylesheet contains `@media (max-width: 700px) { #menu-close { display: none; } }` after the rule that shows it.
- Escape leaves the menu open.
- The open nav covers the "Menu" toggle (`elementFromPoint` at its centre returns `NAV#main-nav`). Tapping where the toggle was does not close the menu.
- Tapping "Offres" goes to `/fr/offres/premium` (h1 "Pack randonnée premium"). My first script showed `/fr/` here because it read the URL before navigation finished. A re-run with a URL wait confirmed the result.
- EN control check: `#menu-close` "Close menu" is visible on `/en/`.
- Extra finding outside the ticket: `#menu-toggle` keeps `aria-expanded="false"` after opening.

Acceptance criteria are verifiable. "Returns focus to 'Menu'" can be checked with `document.activeElement`.

Ambiguity:
- Step 3 says "Look for a control to close the menu". It does not say which name or position to look for. The name "Fermer le menu" appears only in the observed text and the criteria.
- Expected does not say whether Escape should close the menu. The ticket mixes Escape into step 3, but no criterion covers it.
- The criterion "Tapping it hides #main-nav and returns focus to 'Menu'" requires focus to return to a toggle that the open nav currently covers. This is fine, but the expected focus behaviour is not stated in Expected.

## TCK-J10-en-mobile: EN offer badge shows 'Offre limitée'
**Result: REPRODUCED**

Observed on `/en/offers/premium` at 390x844:
- h1 "Premium hiking bundle", then the badge `#offer-badge` "Offre limitée" (yellow, rgb(244,180,0)).
- Price "€1,290.00", date "Valid until 12/31/2026", CTA "Add to cart".
- scrollWidth is 390, so there is no overflow.

Acceptance criteria are verifiable.

Ambiguity:
- Expected is the generic J10 journey sentence ("Badge, price and date are localized, the page has no horizontal overflow and the call to action is visible"). It does not name the expected badge text. "Limited offer" appears only in the title and criteria.
- Device scope is unclear. The ticket says only mobile was executed, but the markup is the same on desktop, so it is not stated whether the fix must be checked on desktop too.

## TCK-J10-fr-mobile: FR offer specs table overflows at 390 px
**Result: REPRODUCED**

Observed on `/fr/offres/premium`:
- `document.documentElement.scrollWidth` is 660.
- `table.specs` has `style="min-width:640px"` and a rendered width of 640 ("30 L 1.2 kg Gore-Tex 2 years").
- The `header` is 390 px wide, so it does not span the 660 px page.
- EN: scrollWidth is 390, the table is 350 wide and has no inline style.
- Note on the emulation: with `isMobile: true`, Chromium widens the layout viewport to the content (`innerWidth` also reports 660), so `window.scrollTo` did not move. The overflow shows in scrollWidth and in the full-page screenshot, not as a scrollable offset.

Acceptance criteria are mostly verifiable. "scrollWidth <= 390" is measurable, although `innerWidth` cannot be used as the reference under `isMobile` emulation. "Scrolls inside its own container" is acceptable but loose.

Ambiguity:
- Step 2, "Scroll the page horizontally / compare the page width with the screen width", gives two different methods. The result of the first depends on the emulation mode (`isMobile` or not), and the ticket does not say which to use.
- Expected is the same generic J10 sentence and does not single out the overflow.
- Side observation, not a new ticket: the FR specs cells read "2 years", which is English text on the French page.

---

## Summary

| Ticket | Severity | Result | Criteria verifiable? | Main ambiguity |
|---|---|---|---|---|
| TCK-J02-fr-desktop | BLOCKER | REPRODUCED | Yes, except the "re-run" criterion | Target URL only in the criteria |
| TCK-J03-en-desktop | MAJOR | REPRODUCED | Yes, except the "re-run" criterion | Relative vs absolute href comparison |
| TCK-J04-en-desktop | MAJOR | REPRODUCED | Yes (HTTP/1.0 detail not observable in the browser) | Target URL only in the criteria; 302/307 not addressed |
| TCK-J07-en-desktop | MINOR | REPRODUCED | Yes, except the "re-run" criterion | Expected omits the Message field; FR test data unspecified |
| TCK-J08-fr-desktop | BLOCKER | REPRODUCED | Mostly ("visible focus outline" is subjective) | Tab count to "Nom" unstated; Enter required but not in steps; submission precondition unused |
| TCK-J09-fr-mobile | BLOCKER | REPRODUCED | Yes | Escape behaviour not in Expected or criteria; close-control name not in steps |
| TCK-J10-en-mobile | MINOR | REPRODUCED | Yes | Generic Expected; desktop scope unclear |
| TCK-J10-fr-mobile | MINOR | REPRODUCED | Mostly (depends on emulation mode) | Two measuring methods in step 2; generic Expected |

The criterion "Case ... passes on re-run with no other case regressing", and the retest procedure that relies on `<skill-dir>`, `qa-config.json` and `qa-output/results.json`, cannot be carried out from the ticket export alone. This applies to all 8 tickets.
