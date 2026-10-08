#!/usr/bin/env python3
"""Validate a QA config before any test runs, and print the case matrix.

    python3 validate_config.py qa-config.json [--json]

Exit code 0 = runnable (warnings allowed), 1 = errors. Warnings flag missing
business expectations: turn each into an explicit assumption or a product
question in the report, never into an invented requirement.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_common import PLACEHOLDER, STEP_ACTIONS, load_json  # noqa: E402

SECRET_KEY = re.compile(r"(password|passwd|secret|token|cookie|api_?key|authorization)", re.I)
SECRET_REF = re.compile(r"^(env|vault|op|keychain|file):", re.I)
REPORT_LABEL_LANGS = {"en", "fr"}


def scan_secrets(obj, where, errors):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SECRET_KEY.search(k) and isinstance(v, str) and v and not SECRET_REF.match(v) and not k.endswith("_ref"):
                errors.append(f"{where}.{k}: looks like a plaintext secret; store a reference such as 'env:QA_PASSWORD' instead")
            scan_secrets(v, f"{where}.{k}", errors)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_secrets(v, f"{where}[{i}]", errors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()
    cfg = load_json(a.config)
    errors, warnings, questions = [], [], []

    target = cfg.get("target") or {}
    if not target.get("start_url"):
        errors.append("target.start_url is required")
    elif not re.match(r"^https?://", target["start_url"]):
        errors.append("target.start_url must be an absolute http(s) URL")
    if not target.get("allowed_origins"):
        warnings.append("target.allowed_origins not set: only the start_url origin will be allowed")

    langs = {l.get("code"): l for l in cfg.get("languages") or []}
    if not langs:
        errors.append("languages: at least one language is required")
    for code, l in langs.items():
        if not code:
            errors.append("languages[]: 'code' is required")
        if not l.get("urls"):
            warnings.append(f"language {code}: no 'urls' map; URL correspondences between languages cannot be checked")
    devices = {d.get("id"): d for d in cfg.get("devices") or []}
    if not devices:
        errors.append("devices: at least one device profile is required")
    for did, d in devices.items():
        vp = d.get("viewport") or {}
        if not (isinstance(vp.get("width"), int) and isinstance(vp.get("height"), int)):
            errors.append(f"device {did}: viewport.width and viewport.height must be integers")
    if not any((d.get("is_mobile")) for d in devices.values()):
        warnings.append("no mobile profile: mobile menus and layouts will not be covered")

    if cfg.get("countries"):
        warnings.append("countries requested: a geo check only passes with proof of the network egress country "
                        "for the same context as the site requests; otherwise it stays NOT_RUN")

    out = cfg.get("output") or {}
    ol = out.get("output_language", "en")
    if ol not in REPORT_LABEL_LANGS:
        warnings.append(f"output_language '{ol}': report headings fall back to English; write ticket text in '{ol}'")

    auth = cfg.get("auth") or {"method": "none"}
    if auth.get("method") not in (None, "none") and not any(k.endswith("_ref") for k in auth):
        warnings.append("auth.method set without a *_ref field: authentication is likely to be BLOCKED")
    scan_secrets(cfg, "config", errors)

    allowed = cfg.get("allowed_actions") or {}
    if not allowed.get("submit_paths"):
        warnings.append("allowed_actions.submit_paths empty: every POST/PUT/DELETE will be blocked (non-destructive default)")

    matrix = []
    for j in cfg.get("journeys") or []:
        jid = j.get("id") or "?"
        if not j.get("steps"):
            errors.append(f"journey {jid}: no steps")
            continue
        jdevs = j.get("devices") or [j.get("device")]
        for dv in jdevs:
            if dv not in devices:
                errors.append(f"journey {jid}: device '{dv}' is not defined")
        if not j.get("expected"):
            questions.append(f"journey {jid}: no 'expected' result. Record an explicit assumption or ask the product owner; do not invent a requirement.")
        if not any(str(s.get("action", "")).startswith("expect_") or s.get("action") == "tab_until_focus" for s in j["steps"]):
            warnings.append(f"journey {jid}: no expectation step; it can only ever PASS by default, which proves nothing")
        for i, s in enumerate(j["steps"]):
            if s.get("action") not in STEP_ACTIONS:
                errors.append(f"journey {jid} step {i + 1}: unknown action '{s.get('action')}'")
        for code in j.get("languages") or list(langs):
            if code not in langs:
                errors.append(f"journey {jid}: language '{code}' is not defined")
                continue
            l = langs[code]
            tables = {"url": l.get("urls") or {}, "s": l.get("strings") or {}, "data": j.get("test_data") or {}}
            for s in j["steps"]:
                for v in s.values():
                    for m in PLACEHOLDER.finditer(v if isinstance(v, str) else ""):
                        ns, _, name = m.group(1).partition(".")
                        if ns == "lang":
                            continue
                        if ns not in tables or name not in tables[ns]:
                            errors.append(f"journey {jid} [{code}]: placeholder {m.group(0)} has no value")
            for dv in jdevs:
                matrix.append({"case_id": f"{jid}-{code}-{dv}", "journey": jid, "language": code,
                               "device": dv, "release_critical": bool(j.get("release_critical")),
                               "priority": j.get("priority", "P2")})

    limits = cfg.get("limits") or {}
    if matrix and limits.get("max_cases") and len(matrix) > limits["max_cases"]:
        warnings.append(f"{len(matrix)} cases planned but limits.max_cases={limits['max_cases']}: the rest will be NOT_RUN")
    if not matrix:
        errors.append("no case can be planned")

    report = {"valid": not errors, "errors": errors, "warnings": warnings, "product_questions": questions,
              "cases_planned": len(matrix), "matrix": matrix}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{'VALID' if not errors else 'INVALID'}: {len(matrix)} case(s) planned "
              f"({sum(m['release_critical'] for m in matrix)} release-critical)")
        for title, items in (("ERROR", errors), ("WARNING", warnings), ("QUESTION", questions)):
            for it in items:
                print(f"  {title}: {it}")
        for m in matrix:
            print(f"  - {m['case_id']:<24} {m['priority']} {'critical' if m['release_critical'] else ''}")
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
