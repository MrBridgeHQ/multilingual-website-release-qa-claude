# Input contract and results schema

## Config (JSON)

Start from `assets/templates/qa-config.example.json`. Validate with `scripts/validate_config.py` before running.

| Key | Content |
|---|---|
| `campaign` | `id`, `name`, `environment` (e.g. staging, local) |
| `target` | `start_url`, `allowed_origins`, `allowed_paths`, `excluded_paths`, optional `timezone` |
| `languages[]` | `code`, `label`, `locale`, `urls` (logical page -> localized path: the URL correspondence table), `strings` (expected localized texts), `keep_untranslated` |
| `countries` | Only when a geographic check is requested; see `geo.md` |
| `devices[]` | `id`, `label`, `browser`, `viewport` {`width`,`height`}, `is_mobile`, `has_touch`, optional `user_agent`, `timezone` |
| `journeys[]` | `id`, `title`, `priority` (P1-P3), `release_critical`, `device` or `devices` (list), `languages`, `checks`, `preconditions`, `test_data`, `expected`, `steps` (see `tooling.md`) |
| `auth` | `method` (`none`, `basic`, `form`, `sso`...) and secret **references** only (`password_ref: "env:QA_PASSWORD"`) |
| `allowed_actions` | `submit_paths` allowed for non-GET requests; default empty = non-destructive |
| `limits` | `timeout_ms`, `assert_timeout_ms`, `retries`, `max_cases`, `max_minutes` |
| `output` | `dir` (relative to the directory you run the scripts from), `formats`, `output_language` (default `en`) |
| `assumptions` | Explicit assumptions made where the specification is silent |

Natural-language requests are fine: draft the config, list your assumptions, and ask only for what you cannot infer (typically: which journeys are release-critical, test accounts, whether submissions are allowed).

## results.json (schema_version 1.0)

```
schema_version, campaign {id, name, label, environment, started_at, finished_at, output_language},
scope {start_url, allowed_origins, languages, devices, journeys[{id,title,release_critical,priority}], filters},
environment {runner, browser, browser_version, node, platform, browser_error},
capabilities {page_extraction, click, typing, screenshots, network_observation, console_capture, traces, geo_verification, real_device, notes[]},
assumptions[],
cases[] {case_id, journey_id, title, language, device, viewport, emulated_mobile, country, priority, release_critical,
         preconditions, expected, url_start, url_final, status, reason, attempts, reproduction, flaky, manual,
         started_at, finished_at, steps[{index, action, description, status, detail}],
         evidence[{type, path, step}], console_errors, failed_requests, blocked_requests, limitations[]},
geo_checks[] {country_requested, country_verified, egress_proof, status, reason},
observations[] {id, kind: SUSPECTED_INCONSISTENCY|PRODUCT_QUESTION|TOOLING_INCIDENT|NOTE, summary, case_ids[], evidence[]},
tickets[] (see severity-and-tickets.md, plus optional retest {date, campaign, previous_status, case_statuses}),
summary (computed by build_outputs.py; never written by hand)
```

`qa_common.validate_results` enforces the schema and the consistency rules (statuses, reasons, PASS needs every step PASS, open tickets linked to FAIL cases, no LOW-confidence BLOCKER, geo proof).
