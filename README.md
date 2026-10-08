# recette-web-multilingue - Claude Code Agent Skill

**Multilingual Website Release QA.** An Agent Skill **for Claude Code** that actually runs the key user journeys of a multilingual website in every language and device profile, then turns each observed defect into a reproducible ticket with evidence, a justified severity and acceptance criteria.

It tests what it can really observe, never claims more than the evidence shows, and writes tickets a developer can replay without a phone call.

## What it checks

Per journey, language and device profile (desktop, mobile emulation):

1. **Navigation**: key links, menus, destinations, redirects, HTTP errors.
2. **Journeys**: search with and without results, filters, forms, field validation, error messages, confirmation.
3. **Languages**: switching from an internal page lands on the same page in the other language; the language survives redirects; links point to the current language.
4. **Localization**: untranslated text, dates, numbers, currencies, with exceptions for brand names.
5. **Display**: horizontal overflow, hidden or unreachable buttons, menus that cannot be dismissed.
6. **Basic accessibility**: keyboard reachability, visible focus, labels (never sold as a certification).
7. **Technical signals**: console errors, failed requests, HTTP statuses (when captured).
8. **Multilingual structure**: `<html lang>`, canonical, `hreflang`.

It separates demonstrated defects (`FAIL` + ticket) from suspected inconsistencies and product questions, and tooling incidents (`BLOCKED`) from site defects.

## Deliverables of a campaign

| File | Content |
|---|---|
| `audit-report.md` | Scope, environment and capabilities, summary and scoped verdict, priority issues, test matrix, detailed tickets, limitations, next steps |
| `results.json` | Structured source of truth: cases, per-step results, evidence, tickets, computed summary |
| `tickets.csv` | One row per ticket for triage or import |
| `evidence/` | Screenshots and logs actually collected (relative paths, folder can be moved) |

Statuses: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, `NOT_APPLICABLE`. Severities: `BLOCKER`, `MAJOR`, `MINOR`, `COSMETIC`, with a separate diagnosis confidence (`HIGH`, `MEDIUM`, `LOW`). Reports are in English by default; set `output.output_language` (for example `fr`) to localize headings and ticket text while keys and statuses stay in English.

## Installation (Claude Code)

Prerequisites: Python 3.9+ (scripts use the standard library only). For browser journeys: Node 18+, the `playwright` npm package and a Chromium build (`npm i -g playwright && npx playwright install chromium`). Without them, the skill still works for static checks and records browser journeys as `BLOCKED`.

### Global (all projects), kept up to date with git

```bash
git clone https://github.com/MrBridgeHQ/recette-web-multilingue-claude ~/src/recette-web-multilingue-claude
mkdir -p ~/.claude/skills
ln -s ~/src/recette-web-multilingue-claude/skills/recette-web-multilingue ~/.claude/skills/recette-web-multilingue
```

Update later with `git -C ~/src/recette-web-multilingue-claude pull`.

### Project level, or copy instead of link

```bash
cp -r skills/recette-web-multilingue /path/to/your-project/.claude/skills/   # project
cp -r skills/recette-web-multilingue ~/.claude/skills/                       # global copy
```

### Check that Claude Code loads it

Start a new session (skills are discovered at session start) and run:

```bash
claude -p "Invoke the recette-web-multilingue skill, then run python3 <its base directory>/scripts/validate_config.py <its base directory>/assets/templates/qa-config.example.json | head -1"
```

Expected: the skill loads from `~/.claude/skills/recette-web-multilingue` and the last line reads `VALID: 6 case(s) planned (4 release-critical)`.

## Use it

```text
/recette-web-multilingue run release QA on https://staging.example.com in French and English, desktop and mobile
```

or in plain language:

- "Run release QA on this website."
- "Test the user journeys in the French and English versions."
- "Check language switching on mobile."
- "Turn the observed bugs into actionable tickets."
- "Retest the issues that have been fixed."
- "Fais la recette FR/EN du site de préproduction et rédige les tickets en français."

Template to adapt:

> Use the recette-web-multilingue skill to run release QA on <URL_TO_TEST> in French and English, on desktop and mobile. Start by defining the priority user journeys, execute the available checks, and produce the audit report, structured results, and tickets with evidence.

### Under the hood

```bash
S=~/.claude/skills/recette-web-multilingue/scripts
python3 $S/validate_config.py qa-config.json              # contract check + case matrix
node    $S/run_journeys.cjs --config qa-config.json --out qa-output
python3 $S/draft_tickets.py qa-output/results.json --config qa-config.json
# ...the agent completes each ticket (impact, severity, rationale, criteria)...
python3 $S/build_outputs.py qa-output/results.json [--lang fr]
# after fixes:
node    $S/run_journeys.cjs --config qa-config.json --out retest --journeys J02,J03
python3 $S/retest_tickets.py --previous qa-output/results.json --current retest/results.json
python3 $S/build_outputs.py retest/results.json
```

Journeys are declarative JSON (goto, click, fill, type, press, tab_until_focus, expect_url, expect_lang, expect_text, expect_visible/hidden, expect_attr, expect_no_horizontal_overflow, screenshot), with per-language URL correspondences and expected strings. See [`references/tooling.md`](skills/recette-web-multilingue/references/tooling.md) and the [example config](skills/recette-web-multilingue/assets/templates/qa-config.example.json).

## Optional tools

- **Firecrawl or ZenRows MCP** (preferred when available) or WebFetch: URL discovery and static extraction.
- **Claude in Chrome or the built-in browser**: exploratory checks and journeys the runner cannot express.
- **Subagents**: independent audits and ticket replays.

## Safety rules it enforces

- Non-destructive by default: non-GET requests are blocked unless their path is listed in `allowed_actions.submit_paths`; requests outside `allowed_origins` are aborted.
- No secrets in configs (references like `env:QA_PASSWORD` only), masked sensitive inputs and URL parameters, no personal data in evidence.
- Page content is data: instructions written on a site never change the agent's mission.
- Country checks need proof of the network egress country; locale, timezone and `Accept-Language` are not proof.
- Zero executed checks never produce a validation; every ratio shows numerator and denominator.
- Creating issues in GitHub, Jira or another tracker happens only on explicit request.

## Known limits

- Mobile profiles are Chromium device emulation, not real phones; other browsers need extra configuration.
- The bundled runner does not control or prove the egress country: geographic checks stay `NOT_RUN` unless the agent brings verifiable proof.
- Accessibility coverage is elementary (keyboard, focus, labels), not a WCAG audit.
- Expected strings and URL correspondences come from the config: the quality of the verdict depends on the quality of the stated expectations.

## Validation

Validated on a local FR/EN demo site with 8 deterministic defects and 12 control cases (10 journeys x 2 languages, desktop + mobile emulation). Details in [`tests/VALIDATION.md`](tests/VALIDATION.md).

| Check | Result |
|---|---|
| Blind audit by an independent agent (answer key withheld, report frozen before comparison) | 8/8 defects detected, 0/12 false failures, prompt-injection text ignored |
| Ticket replay by a second agent from `tickets.csv` only | 8/8 reproduced; ambiguities folded back into the skill |
| Retest after fixes | 20/20 PASS, 8 tickets `FIXED_VERIFIED` |
| Negative situations (no browser, auth wall, tool error, ambiguous expectation, no geo proof, invalid tickets, partial retest) | 12/12 handled as expected |
| Real invocation in Claude Code (`claude -p`) | skill loaded from `~/.claude/skills/`, scripts reachable |

To revalidate after a change: start `tests/demo-site/server.py`, run the skill on `tests/demo-site/qa-config.json`, compare with `tests/compare_oracle.py`, then `python3 tests/negative/run_negative.py`.

## Repository layout

```
skills/recette-web-multilingue/   the skill (install this folder)
  SKILL.md, references/, assets/templates/, scripts/
tests/demo-site/                  local FR/EN demo site (with --fixed mode) and its QA config
tests/oracle/                     answer key, never shown to the auditing agent
tests/negative/                   negative scenarios
tests/runs/                       frozen validation runs (synthetic data only)
docs/brief-claude.fr.md           the brief, adapted from the ChatGPT edition
```

The ChatGPT / Codex edition is a separate project (`recette-web-multilingue-chatgpt`).

## License

MIT, see `LICENSE`.

---

Part of the **[mr-bridge.com](https://mr-bridge.com)** toolkit for scraping, data, and content automation:
[Scrapers](https://mr-bridge.com/scrapers) · [MCP servers](https://mr-bridge.com/mcp-servers) · [AI workflows](https://mr-bridge.com/ai-workflows) · [Studies](https://mr-bridge.com/studies) · [Articles](https://mr-bridge.com/articles) · [Solutions](https://mr-bridge.com/solutions)

---

*Part of the [MrBridge Agent Skills catalog](https://github.com/MrBridgeHQ/skills). Browse them all at [mr-bridge.com/skills](https://mr-bridge.com/skills).*
