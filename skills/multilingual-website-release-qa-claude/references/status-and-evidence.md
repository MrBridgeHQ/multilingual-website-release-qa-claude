# Statuses, evidence and retries

## Case and step statuses

| Status | Meaning |
|---|---|
| `PASS` | Executed; the expected result was observed |
| `FAIL` | Executed; a deviation from the expected result was demonstrated |
| `BLOCKED` | Attempted, prevented by an identified obstacle (auth wall, tool failure, missing capability, config error) |
| `NOT_RUN` | Planned but not executed (budget, time, filter, prerequisite failed) |
| `NOT_APPLICABLE` | Out of context for this site or language, with a justification |

Rules:
- A case is `PASS` only if every step passed. Partial execution keeps its per-step results.
- `FAIL`, `BLOCKED`, `NOT_RUN` and `NOT_APPLICABLE` always carry a `reason`.
- Tooling incidents are `BLOCKED`, never `FAIL`. Record them as `TOOLING_INCIDENT` observations when they affect coverage.
- Zero executed checks never yields a validation.

## Minimum record per case

Campaign and case id, timestamps, start and final URL, language, device profile (viewport, emulation flag), browser and version when known, preconditions, steps with per-step status and detail, expected, observed (`reason`), status, requested and verified country if relevant, evidence references, attempts and reproduction, limitations and remaining uncertainty.

## Retries

Transient errors get bounded retries (`limits.retries`). Report the observed frequency, e.g. "reproduced 2/3", and mark `flaky: true` when some attempts passed. Lower confidence for intermittent failures rather than dropping them.

## Evidence

- Store only evidence actually collected, under `evidence/<case_id>/`, with paths relative to the results folder so the folder can be moved or zipped.
- The runner saves a final screenshot and a log (console errors, failed requests, blocked requests) per attempt, plus any `screenshot` step.
- For manual checks, save what you really observed (screenshot, extracted HTML snippet, quoted text) and reference it.
- `build_outputs.py` lists missing files in the report; never reference a file you did not create.

## Masking

Do not record passwords, cookies, tokens, authorization headers or unnecessary personal data. Use `"sensitive": true` on steps that type secrets; the runner masks sensitive query parameters and URL credentials. Before publishing evidence, check screenshots for personal data and crop or redact it.
