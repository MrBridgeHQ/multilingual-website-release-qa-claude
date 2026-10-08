"""Shared constants and validators for multilingual-website-release-qa-claude scripts (stdlib only)."""
import json
import re

CASE_STATUSES = ["PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"]
STEP_STATUSES = CASE_STATUSES
SEVERITIES = ["BLOCKER", "MAJOR", "MINOR", "COSMETIC"]
CONFIDENCES = ["HIGH", "MEDIUM", "LOW"]
TICKET_STATUSES = ["OPEN", "FIXED_VERIFIED", "STILL_FAILING", "NOT_RETESTED"]
OBSERVATION_KINDS = ["SUSPECTED_INCONSISTENCY", "PRODUCT_QUESTION", "TOOLING_INCIDENT", "NOTE"]
STEP_ACTIONS = [
    "goto", "click", "fill", "press", "type", "wait", "tab_until_focus", "screenshot",
    "expect_status", "expect_url", "expect_lang", "expect_text", "expect_no_text",
    "expect_visible", "expect_hidden", "expect_attr", "expect_no_horizontal_overflow",
]
TODO = "TODO"

TICKET_REQUIRED = [
    "id", "title", "impact", "severity", "severity_rationale", "confidence", "scope",
    "preconditions", "steps", "expected", "observed", "evidence", "case_ids",
    "reproduction", "fix_hypothesis", "acceptance_criteria", "retest_procedure", "status",
]

PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def contains_todo(value):
    if isinstance(value, str):
        return TODO in value
    if isinstance(value, list):
        return any(contains_todo(v) for v in value)
    if isinstance(value, dict):
        return any(contains_todo(v) for v in value.values())
    return False


def validate_results(res):
    """Return a list of human-readable schema errors for a results.json document."""
    errors = []

    def need(obj, key, where, kind=None):
        if not isinstance(obj, dict) or key not in obj:
            errors.append(f"{where}: missing '{key}'")
            return None
        if kind and obj[key] is not None and not isinstance(obj[key], kind):
            errors.append(f"{where}.{key}: expected {kind.__name__ if isinstance(kind, type) else kind}")
        return obj[key]

    if res.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    camp = need(res, "campaign", "root", dict) or {}
    for k in ("id", "started_at", "output_language"):
        need(camp, k, "campaign")
    need(res, "scope", "root", dict)
    need(res, "environment", "root", dict)
    need(res, "capabilities", "root", dict)
    cases = need(res, "cases", "root", list) or []
    ids = set()
    for i, c in enumerate(cases):
        w = f"cases[{i}]"
        for k in ("case_id", "journey_id", "language", "device", "status", "steps", "evidence", "attempts"):
            need(c, k, w)
        if c.get("case_id") in ids:
            errors.append(f"{w}: duplicate case_id {c.get('case_id')}")
        ids.add(c.get("case_id"))
        if c.get("status") not in CASE_STATUSES:
            errors.append(f"{w}: invalid status {c.get('status')!r}")
        if c.get("status") in ("BLOCKED", "NOT_RUN", "NOT_APPLICABLE", "FAIL") and not c.get("reason"):
            errors.append(f"{w}: status {c.get('status')} needs a 'reason'")
        for j, s in enumerate(c.get("steps") or []):
            if s.get("status") not in STEP_STATUSES:
                errors.append(f"{w}.steps[{j}]: invalid status {s.get('status')!r}")
        step_statuses = [s.get("status") for s in c.get("steps") or []]
        if c.get("status") == "PASS" and any(s != "PASS" for s in step_statuses):
            errors.append(f"{w}: case is PASS but not every step passed (a partial run is never a full pass)")
        if c.get("status") == "FAIL" and "FAIL" not in step_statuses and not c.get("manual"):
            errors.append(f"{w}: case is FAIL but no step is FAIL")
    for i, g in enumerate(res.get("geo_checks") or []):
        if g.get("status") not in CASE_STATUSES:
            errors.append(f"geo_checks[{i}]: invalid status")
        if g.get("status") in ("PASS", "FAIL") and not g.get("egress_proof"):
            errors.append(f"geo_checks[{i}]: PASS/FAIL requires 'egress_proof' tied to the same network context")
    for i, o in enumerate(res.get("observations") or []):
        if o.get("kind") not in OBSERVATION_KINDS:
            errors.append(f"observations[{i}]: kind must be one of {OBSERVATION_KINDS}")
        if not isinstance(o.get("evidence", []), list):
            errors.append(f"observations[{i}]: 'evidence' must be a list of relative paths")
    tids = set()
    for i, t in enumerate(res.get("tickets") or []):
        w = f"tickets[{i}]"
        for k in TICKET_REQUIRED:
            if k not in t or t[k] in (None, "", []):
                errors.append(f"{w}: missing or empty '{k}'")
        if t.get("id") in tids:
            errors.append(f"{w}: duplicate ticket id {t.get('id')}")
        tids.add(t.get("id"))
        if t.get("severity") not in SEVERITIES:
            errors.append(f"{w}: severity must be one of {SEVERITIES}")
        if t.get("confidence") not in CONFIDENCES:
            errors.append(f"{w}: confidence must be one of {CONFIDENCES}")
        if t.get("status") not in TICKET_STATUSES:
            errors.append(f"{w}: status must be one of {TICKET_STATUSES}")
        linked = [c for c in cases if c.get("case_id") in (t.get("case_ids") or [])]
        for cid in t.get("case_ids") or []:
            if cid not in ids and t.get("status") != "NOT_RETESTED":  # carried-over ticket whose case was not re-run
                errors.append(f"{w}: case_id {cid} does not exist")
        if t.get("status") in ("OPEN", "STILL_FAILING") and not any(c.get("status") == "FAIL" for c in linked):
            errors.append(f"{w}: open ticket must be linked to at least one FAIL case")
        if t.get("status") == "FIXED_VERIFIED" and not all(c.get("status") == "PASS" for c in linked):
            errors.append(f"{w}: FIXED_VERIFIED requires every linked case to PASS in this run")
        if t.get("severity") == "BLOCKER" and t.get("confidence") == "LOW":
            errors.append(f"{w}: a LOW-confidence suspicion cannot be a BLOCKER; gather evidence or lower the severity")
        if contains_todo(t):
            errors.append(f"{w}: still contains {TODO} placeholders")
        if not isinstance(t.get("steps"), list) or not isinstance(t.get("acceptance_criteria"), list):
            errors.append(f"{w}: 'steps' and 'acceptance_criteria' must be lists")
    return errors


def counts(cases):
    c = {s: 0 for s in CASE_STATUSES}
    for case in cases:
        c[case["status"]] = c.get(case["status"], 0) + 1
    c["PLANNED"] = len(cases)
    c["EXECUTED"] = c["PASS"] + c["FAIL"]
    return c


def verdict(res):
    """Verdict limited to what was actually verified."""
    cases = res.get("cases") or []
    c = counts(cases)
    if c["EXECUTED"] == 0:
        return "NO_VERDICT", "no check was executed; nothing can be validated"
    open_t = [t for t in res.get("tickets") or [] if t.get("status") in ("OPEN", "STILL_FAILING")]
    crit = [x for x in cases if x.get("release_critical")]
    crit_fail = [x["case_id"] for x in crit if x["status"] == "FAIL"]
    crit_uncovered = [x["case_id"] for x in crit if x["status"] in ("BLOCKED", "NOT_RUN")]
    if any(t.get("severity") == "BLOCKER" for t in open_t) or crit_fail:
        return "NOT_READY", f"release-critical failures: {', '.join(crit_fail) or 'blocker ticket open'}"
    if crit_uncovered:
        return "INCOMPLETE", f"release-critical cases not covered: {', '.join(crit_uncovered)}"
    if open_t or c["FAIL"]:
        return "READY_WITH_RESERVATIONS", "no release-critical failure in scope, but open defects remain"
    if c["BLOCKED"] or c["NOT_RUN"]:
        return "INCOMPLETE", "some planned cases were not executed"
    return "READY_WITHIN_SCOPE", "every planned case passed; valid only for the scope listed"
