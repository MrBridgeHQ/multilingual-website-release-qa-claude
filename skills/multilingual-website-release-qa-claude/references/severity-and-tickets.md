# Severity, confidence and tickets

## Severity (impact on the user and the release)

| Severity | Use when | Example |
|---|---|---|
| `BLOCKER` | A release-critical journey cannot be completed for a language or device, with no reasonable workaround, or data/legal exposure | Keyboard users cannot submit the contact form; mobile menu cannot be closed, hiding the page |
| `MAJOR` | A key journey works only with a workaround, users land in the wrong language or page, or a core message is wrong | Language switch drops the user on the other language's home page; redirect loses the language |
| `MINOR` | Degraded but usable; localized text or format wrong in a secondary place | Error message in the wrong language; untranslated badge |
| `COSMETIC` | Visual or wording issue without functional effect | Misaligned icon, inconsistent capitalization |

Always write `severity_rationale` in one or two sentences: who is affected, what they cannot do, whether a workaround exists.

Weigh business value, not only the rubric: a broken link to a purely informational page in a release-critical navigation journey can be `MAJOR` rather than `BLOCKER` if users can still reach their goal another way; a defect that stops a conversion path (contact, checkout, sign-up) or traps the user on mobile leans `BLOCKER`. When you hesitate between two levels, choose one, say why in the rationale, and flag it as a point for the product owner to confirm. The `release_critical` flag of the journey says the journey matters for go-live; it does not by itself make every defect in it a BLOCKER.

## Confidence (strength of the diagnosis), kept separate

- `HIGH`: reproduced on every attempt with direct evidence.
- `MEDIUM`: reproduced intermittently, or evidence is indirect.
- `LOW`: a suspicion. A LOW-confidence item is not a `BLOCKER`: gather evidence first, or file it as an observation.

## Ticket fields (all required)

`id` (stable), `title` (precise: language, device, place, symptom), `impact`, `severity`, `severity_rationale`, `confidence`, `scope` {`pages`, `languages`, `devices`}, `preconditions`, `test_data` (non-sensitive), `steps` (numbered, executable by someone who never saw the site), `expected`, `observed` (quote the site text verbatim, in its original language), `evidence`, `case_ids`, `reproduction`, `fix_hypothesis` (start with "Hypothesis:" unless the cause is proven), `acceptance_criteria` (verifiable, one check per line), `retest_procedure`, `status` (`OPEN`, `FIXED_VERIFIED`, `STILL_FAILING`, `NOT_RETESTED`).

Good acceptance criteria are observable: "From /en/about, the language link opens /fr/a-propos with `<html lang="fr">`", not "the switcher works".

## Self-check before publishing a ticket

A developer will replay it with nothing but the ticket. Independent replays showed these gaps most often:

- **Expected is specific to the defect**, not the generic journey sentence: name the exact correct URL, text or value ("opens `/fr/a-propos`", "badge reads `Limited offer`").
- **Steps name every control as the user sees it** (`"Fermer le menu"` button, `#lang-switch` link labelled "Français") and include every action the expected result relies on (if Enter submits, a step presses Enter).
- **Keyboard steps state the starting point** ("after page load, press Tab until 'Nom' has focus, about 8 presses").
- **One measuring method**, the robust one: compare `document.documentElement.scrollWidth` with the viewport width rather than "try to scroll" (mobile emulation can hide the scroll).
- **Acceptable alternatives are explicit**: "a permanent redirect (301 or 308) to `/en/offers/premium`; 302/307 are not acceptable" or "any redirect status".
- **Acceptance criteria cover every behaviour mentioned in steps and observed** (e.g. Escape closes the menu, focus returns to "Menu"), with measurable wording (no "visible enough").
- **Acceptance criteria are self-contained**: they must not depend on the QA team's files (config, results.json, skill scripts). Put "re-run case X with the runner" in `retest_procedure`, which is for the QA team.
- Relative and absolute URLs are compared after resolving both against the page URL.
- Test data is given for every input the steps or criteria use, in each language checked.

## Grouping

Merge manifestations into one ticket only when they are clearly the same symptom (same component, same wrong behaviour), and keep all case ids, pages, languages and evidence. Two symptoms on the same page (untranslated badge and overflow) are two tickets. Never claim a shared root cause without evidence.

## Title pattern

`[LANG][device] <where>: <what is wrong>` - e.g. `[FR][mobile] Offer page: specs table overflows horizontally at 390 px`.

Write free text in `output_language`; keep keys, statuses and severities in English.
