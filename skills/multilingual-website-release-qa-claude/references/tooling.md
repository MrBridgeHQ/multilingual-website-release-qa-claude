# Tooling and capability inventory

## 1. Inventory first

At the start of each campaign, record in `results.json > capabilities` what you can really do, as booleans: `page_extraction`, `click`, `typing`, `screenshots`, `network_observation`, `console_capture`, `traces`, `geo_verification`, `real_device`, plus `notes`. The runner fills this automatically; update it when you add other tools. Check tool permissions and the user's preferences before using a tool.

## 2. What each tool proves

| Tool | Good for | Does not prove |
|---|---|---|
| `scripts/run_journeys.cjs` (Playwright, Chromium) | Deterministic journeys, clicks, typing, keyboard, viewport emulation, console and network capture, screenshots | Real-device behaviour, other browsers unless configured, geographic origin |
| Claude in Chrome (`mcp__claude-in-chrome__*`) or the built-in browser (`mcp__Claude_Browser__*`) | Exploratory checks, sites needing the user's own session, journeys hard to script | Reproducibility unless every step is recorded; it uses the user's real browser, so stay non-destructive |
| Firecrawl / ZenRows MCP (user preference), WebFetch | URL discovery, static extraction of `lang`, `hreflang`, canonical, visible text | That a menu opens, a form works or a button is clickable |
| Screenshot alone | The state of one screen at one moment | That the whole journey ran |
| Narrow viewport | Responsive layout in emulation | Behaviour on a real phone |

MCP tools are agent capabilities, not libraries: scripts cannot call them. If a script needs a client or API, document and test that dependency.

If a capability is missing, continue the independent checks and mark the others `BLOCKED` or `NOT_RUN` with the precise reason.

## 3. Runner usage

```bash
node scripts/run_journeys.cjs --config qa-config.json --out qa-output \
     [--journeys J02,J03] [--languages fr] [--executable-path /path/to/chromium] [--label "retest after fix"]
```

- Resolves `playwright` locally, then from the global npm root. Browser path can also come from `QA_BROWSER_PATH`.
- `--out` defaults to the config's `output.dir`, resolved from the current directory.
- Each case gets a fresh browser context with the device viewport, `isMobile`, `hasTouch`, the language `locale` and the configured timezone.
- Requests outside `target.allowed_origins` and non-GET requests outside `allowed_actions.submit_paths` are aborted and logged as `blocked_requests`.
- HTTP 401/403 on `goto` makes the case `BLOCKED` (authentication), not `FAIL`.
- A failing expectation makes the case `FAIL`; an action the tool could not perform makes it `BLOCKED`. FAIL and BLOCKED cases are retried up to `limits.retries` times; `reproduction` reports `failures/attempts`, and `flaky: true` marks intermittent failures.

## 4. Journey step reference

Placeholders: `{{url.<key>}}` and `{{s.<key>}}` resolve from the current language's `urls` and `strings`, `{{data.<key>}}` from the journey's `test_data`, `{{lang}}` is the language code.

| Action | Fields | Notes |
|---|---|---|
| `goto` | `url` | Relative to `target.start_url`; records the HTTP status |
| `click` | `selector` or `role`+`name` or `text`, `exact` | Waits for load afterwards |
| `fill` | target, `value`, `sensitive` | `sensitive: true` masks the value in results |
| `type` | `value`, `sensitive` | Types into the focused element (keyboard journeys) |
| `press` | `key`, `times` | e.g. `Enter`, `Escape`, `Tab` |
| `tab_until_focus` | `selector`, `max` | Expectation: FAIL if focus never reaches the element |
| `wait` | `ms` | Avoid; expectations already wait up to `limits.assert_timeout_ms` |
| `screenshot` | `name`, `full_page` | Saved under `evidence/<case_id>/<step>-<name>-attempt<n>.png` (one file per attempt) |
| `expect_status` | `in` (list) | Status of the last `goto` |
| `expect_url` | `path` or `path_regex` | Waits for navigation |
| `expect_lang` | `value` | Compares the primary subtag of `<html lang>` |
| `expect_text` / `expect_no_text` | `text`, `selector`, `exact` | Quotes the observed text on failure |
| `expect_visible` / `expect_hidden` | target | Waits for the state |
| `expect_attr` | `selector`, `attr`, `value` | e.g. `hreflang`, `canonical` |
| `expect_no_horizontal_overflow` | | `scrollWidth` vs viewport width |

Add `"soft": true` to an expectation to record its failure and continue with independent checks of the same journey (e.g. several localized fields on one page). Add `"description"` to any step to make reports more readable.
