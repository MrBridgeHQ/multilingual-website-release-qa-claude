# Validation of the skill

Note: the skill was first built under the slug `recette-web-multilingue`, then renamed `multilingual-website-release-qa-claude`. The frozen runs in `runs/` keep the old name where it appears; after the rename, the negative suite (12/12), a guided run on the defective site (8/8 detected, 0/12 false failures) and the `claude -p` invocation were re-run under the new name.

All runs use the local demo site `tests/demo-site/server.py` (fictional FR/EN shop, local endpoints only) and its config `tests/demo-site/qa-config.json`: 10 journeys x 2 languages = 20 cases, desktop profile (Chromium 1366x768) for J01-J08 and mobile emulation (390x844, touch) for J09-J10. Browser: Chromium 141 through Playwright 1.56 (Node 22). This is a validation prototype, not coverage of every device.

The site contains 8 deterministic defects and 12 correct control cases. The answer key is `tests/oracle/expected-defects.json`; it was never given to the auditing agent.

## 1. Blind audit by an independent agent - `runs/01-blind-audit/`

A separate subagent received only a copy of the skill, the config and the site URL, with an explicit ban on reading the site source and the answer key. Its outputs were frozen (`FROZEN.sha256`) before comparison with `compare_oracle.py`.

| Measure | Result |
|---|---|
| Injected defects detected (FAIL + ticket) | 8/8 |
| Critical defects missed | 0 |
| Control cases wrongly failed | 0/12 |
| Unexpected FAIL cases (false positives) | 0 |
| Prompt-injection text in the page footer | ignored, reported as an observation |
| Verdict | `NOT_READY` (5/12 release-critical cases failed) |
| Tickets | 3 BLOCKER, 2 MAJOR, 3 MINOR, all HIGH confidence (3/3 reproductions) |

Honest limit: the separation was enforced by instruction (same container), not by a sandbox.

The blind audit ran on the first iteration of the scripts. After the iteration-2 changes (per-attempt screenshot names, `devices` lists, cleaner ticket drafts, observation evidence), the final runner was re-run on the defective site in a guided run (not blind): still 8/8 detected, 0/12 false failures.

## 2. Ticket replay by a second agent - `runs/02-ticket-replay/`

Another subagent received only `tickets.csv` and the live site, and reproduced each ticket in a real browser: **8/8 reproduced**. It listed ambiguities (expected values left generic, controls not named in steps, acceptance criteria depending on QA files, two measuring methods for overflow). They were folded back into the skill as a ticket self-check (`references/severity-and-tickets.md`) and into `draft_tickets.py`.

## 3. Retest after fixes - `runs/03-retest-fixed/`

Same config against `server.py --fixed`, then `retest_tickets.py` on the blind audit's tickets: **20/20 PASS**, the 8 tickets moved to `FIXED_VERIFIED` because each linked case passed; verdict `READY_WITHIN_SCOPE`.

## 4. Negative situations - `runs/negative/` (`python3 tests/negative/run_negative.py`)

12/12 behave as expected (`runs/negative/negative-summary.json`):

| Situation | Expected and observed outcome |
|---|---|
| Browser unavailable | every case `BLOCKED`, capabilities false, verdict `NO_VERDICT` |
| Authentication wall (HTTP 401) | case `BLOCKED` (auth), not retried, verdict `NO_VERDICT` |
| Tool error (site unreachable) | `BLOCKED` with the tool reason, never `FAIL` |
| Ambiguous expectation | config valid, product question raised, warning "no expectation step" |
| Country requested without egress proof | geo checks `NOT_RUN`; a forged geo `PASS` without `egress_proof` is rejected |
| FAIL case without ticket, ticket with TODO, LOW-confidence BLOCKER, PASS case with a failed step | each rejected by `build_outputs.py` |
| Partial retest on a still-broken site | retested ticket `STILL_FAILING`, the others `NOT_RETESTED` (never assumed fixed) |

## 5. Installation check

With the skill linked into `~/.claude/skills/multilingual-website-release-qa-claude`, a real headless session (`claude -p`) invoked it through the Skill tool, reported its frontmatter name and base directory, and ran `validate_config.py` on the bundled example (`VALID: 6 case(s) planned (4 release-critical)`).

## Reproduce

```bash
python3 tests/demo-site/server.py --port 8765 &            # add --fixed for the corrected site
S=skills/multilingual-website-release-qa-claude/scripts
node $S/run_journeys.cjs --config tests/demo-site/qa-config.json --out /tmp/qa-demo
python3 $S/draft_tickets.py /tmp/qa-demo/results.json      # then complete the TODO fields
python3 $S/build_outputs.py /tmp/qa-demo/results.json
python3 tests/compare_oracle.py /tmp/qa-demo/results.json  # only after the audit is frozen
python3 tests/negative/run_negative.py --out /tmp/qa-negative
```
