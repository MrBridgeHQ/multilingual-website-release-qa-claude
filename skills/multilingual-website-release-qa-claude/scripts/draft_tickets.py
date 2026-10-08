#!/usr/bin/env python3
"""Add a ticket skeleton to results.json for every FAIL case not yet linked to a ticket.

    python3 draft_tickets.py qa-output/results.json [--config qa-config.json]

Facts (scope, steps, expected, observed, evidence, reproduction) are prefilled
from the recorded case; confidence is suggested from the reproduction rate
(k/k -> HIGH, otherwise MEDIUM) and must be reviewed. Judgement fields (title, impact, severity, rationale,
fix hypothesis, acceptance criteria) are left as TODO for the agent:
build_outputs.py refuses to publish while any TODO remains.
Merge equivalent manifestations by hand afterwards (keep every case_id and its scope).
"""
import argparse
import re
import sys
from urllib.parse import urljoin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_common import TODO, dump_json, load_json  # noqa: E402

RUNNER = Path(__file__).resolve().parent / "run_journeys.cjs"


def human_step(step, base):
    """Readable step from the runner's record; the agent still polishes the wording."""
    d = step.get("description") or ""
    a = step.get("action")
    if not d.startswith(a + "("):
        return d  # custom description from the config
    arg = d[len(a) + 1:-1]
    if a == "goto":
        m = re.search(r'url="([^"]*)"', arg)
        return f"Open {urljoin(base, m.group(1))}" if m else f"Open {arg}"
    m = re.search(r'name="([^"]*)"', arg) or re.search(r'selector="([^"]*)"', arg) or re.search(r'text="([^"]*)"', arg)
    target = m.group(1) if m else arg
    if a == "click":
        return f"Click \"{target}\""
    if a == "fill":
        v = re.search(r'value=("[^"]*"|\*\*\*)', arg)
        return f"In {target}, enter {v.group(1) if v else ''}"
    verbs = {  # remaining actions keep their raw arguments
        "goto": "Open", "click": "Click", "fill": "Fill", "press": "Press", "type": "Type",
        "tab_until_focus": "Press Tab until focus reaches", "screenshot": "Take a screenshot",
        "expect_status": "Check HTTP status", "expect_url": "Check the URL path", "expect_lang": "Check <html lang>",
        "expect_text": "Check the text", "expect_no_text": "Check the text is absent", "expect_visible": "Check visible",
        "expect_hidden": "Check hidden", "expect_attr": "Check attribute", "expect_no_horizontal_overflow": "Check there is no horizontal scroll",
        "wait": "Wait",
    }
    return f"{verbs.get(a, a)}: {arg}" if arg else verbs.get(a, a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--config", default="<qa-config.json>", help="config path quoted in the retest procedure")
    a = ap.parse_args()
    res = load_json(a.results)
    tickets = res.setdefault("tickets", [])
    linked = {cid for t in tickets for cid in t.get("case_ids") or []}
    start = res.get("scope", {}).get("start_url", "")
    added = 0
    for c in res.get("cases") or []:
        if c["status"] != "FAIL" or c["case_id"] in linked:
            continue
        executed = [s for s in c["steps"] if s["status"] in ("PASS", "FAIL")]
        steps = [human_step(s, start) for s in executed]
        fails = [s for s in c["steps"] if s["status"] == "FAIL"]
        k, _, n = (c.get("reproduction") or "").partition("/")  # always reproduced -> HIGH confidence
        tickets.append({
            "id": f"TCK-{c['case_id']}",
            "title": f"{TODO}: [{c['language'].upper()}][{c['device']}] {c.get('title', c['journey_id'])}",
            "impact": TODO,
            "severity": TODO,
            "severity_rationale": TODO,
            "confidence": "HIGH" if k and k == n else "MEDIUM",
            "scope": {"pages": list(dict.fromkeys(p for p in (c.get("url_start") or start, c.get("url_final")) if p)),
                      "languages": [c["language"]], "devices": [c["device"]]},
            "preconditions": c.get("preconditions") or [],
            "test_data": "",
            "steps": steps,
            "expected": f"{TODO}: exact expected value for this defect (journey expectation: {c.get('expected') or 'none stated'})",
            "observed": "; ".join(s["detail"] for s in fails) or c.get("reason"),
            "evidence": list(dict.fromkeys(e["path"] for e in c.get("evidence") or [])),
            "case_ids": [c["case_id"]],
            "reproduction": f"reproduced {c.get('reproduction')}" if c.get("reproduction") else TODO,
            "fix_hypothesis": f"{TODO} (state it as a hypothesis unless the cause is proven)",
            "acceptance_criteria": [f"{TODO}: observable, self-contained criteria (no dependency on QA files)"],
            "retest_procedure": (f"node {RUNNER} --config {a.config} --out <retest-dir> "
                                 f"--journeys {c['journey_id']} --languages {c['language']} (QA team: case {c['case_id']} must PASS "
                                 f"and no other case regress); developers: replay the steps above by hand"),
            "status": "OPEN",
        })
        added += 1
    dump_json(a.results, res)
    print(f"added {added} ticket skeleton(s); {len(tickets)} ticket(s) total. Replace every {TODO} before build_outputs.py.")


if __name__ == "__main__":
    main()
