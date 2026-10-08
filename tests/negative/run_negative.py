#!/usr/bin/env python3
"""Negative situations: the outputs must reflect each limitation, never a false PASS.

    python3 tests/negative/run_negative.py [--out tests/runs/negative]

Starts its own demo-site instance on port 8766. Requires Node + Playwright + Chromium.
"""
import argparse
import copy
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "recette-web-multilingue" / "scripts"
BASE = json.loads((ROOT / "tests" / "demo-site" / "qa-config.json").read_text(encoding="utf-8"))
PORT = 8766


def cfg_for(name, **patch):
    c = copy.deepcopy(BASE)
    c["campaign"]["id"] = f"NEG-{name}"
    c["target"]["start_url"] = f"http://127.0.0.1:{PORT}/en/"
    c["target"]["allowed_origins"] = [f"http://127.0.0.1:{PORT}"]
    c["limits"]["retries"] = 0
    for k, v in patch.items():
        c[k] = v
    return c


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "tests" / "runs" / "negative"))
    out = Path(ap.parse_args().out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    srv = subprocess.Popen([sys.executable, str(ROOT / "tests" / "demo-site" / "server.py"), "--port", str(PORT)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    results = []

    def check(name, cond, detail):
        results.append((name, bool(cond), detail))
        print(f"{'OK  ' if cond else 'FAIL'} {name}: {detail}")

    def campaign(name, cfg, extra=()):
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "qa-config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run(["node", str(SKILL / "run_journeys.cjs"), "--config", str(d / "qa-config.json"), "--out", str(d / "qa-output"), *extra])
        res = json.loads((d / "qa-output" / "results.json").read_text(encoding="utf-8")) if (d / "qa-output" / "results.json").exists() else None
        return d, r, res

    try:
        # 1. Browser unavailable -> every case BLOCKED, verdict NO_VERDICT.
        d, r, res = campaign("browser-unavailable", cfg_for("browser"), ["--journeys", "J01,J02", "--executable-path", "/nonexistent/chromium"])
        st = {c["status"] for c in res["cases"]}
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(d / "qa-output" / "results.json")])
        summ = json.loads((d / "qa-output" / "results.json").read_text())["summary"]
        check("browser unavailable", st == {"BLOCKED"} and summ["verdict"] == "NO_VERDICT" and not res["capabilities"]["click"],
              f"statuses={st}, verdict={summ['verdict']}, reason={res['cases'][0]['reason'][:70]}")

        # 2. Authentication wall -> BLOCKED (auth), not FAIL.
        cfg = cfg_for("auth")
        cfg["target"]["excluded_paths"] = []
        cfg["journeys"] = [{"id": "J11", "title": "Open the account page", "priority": "P1", "release_critical": True,
                            "device": "desktop", "languages": ["en"], "expected": "Account dashboard is shown.",
                            "steps": [{"action": "goto", "url": "/en/account"}, {"action": "expect_status", "in": [200]}]}]
        d, r, res = campaign("auth-blocking", cfg)
        c = res["cases"][0]
        check("authentication blocking", c["status"] == "BLOCKED" and "401" in c["reason"] and c["attempts"] == 1,
              f"status={c['status']}, reason={c['reason']}")
        run([sys.executable, str(SKILL / "build_outputs.py"), str(d / "qa-output" / "results.json")])
        v = json.loads((d / "qa-output" / "results.json").read_text())["summary"]["verdict"]
        check("auth blocking verdict", v == "NO_VERDICT", f"verdict={v}")

        # 3. Tool error (site unreachable) -> BLOCKED with a tool reason, never FAIL.
        cfg = cfg_for("tool")
        cfg["target"]["start_url"] = "http://127.0.0.1:8799/en/"
        cfg["target"]["allowed_origins"] = ["http://127.0.0.1:8799"]
        d, r, res = campaign("tool-error", cfg, ["--journeys", "J01"])
        st = [c["status"] for c in res["cases"]]
        check("tool error", set(st) == {"BLOCKED"} and all("tool could not perform" in c["reason"] for c in res["cases"]),
              f"statuses={st}, reason={res['cases'][0]['reason'][:80]}")

        # 4. Ambiguous expectation -> validate_config raises a product question, never an invented requirement.
        cfg = cfg_for("ambiguous")
        cfg["journeys"] = [{"id": "J12", "title": "Legacy URL behaviour", "priority": "P2", "device": "desktop", "languages": ["en"],
                            "steps": [{"action": "goto", "url": "/en/old-offers"}]}]
        p = out / "ambiguous-expectation"
        p.mkdir()
        (p / "qa-config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        v = run([sys.executable, str(SKILL / "validate_config.py"), str(p / "qa-config.json"), "--json"])
        (p / "validation.json").write_text(v.stdout, encoding="utf-8")
        rep = json.loads(v.stdout)
        check("ambiguous expectation", rep["valid"] and rep["product_questions"] and any("no expectation step" in w for w in rep["warnings"]),
              f"questions={len(rep['product_questions'])}, warnings={len(rep['warnings'])}")

        # 5. Geographic check without proof -> NOT_RUN; a geo PASS without egress proof is rejected.
        cfg = cfg_for("geo", countries=["DE", "CA"])
        d, r, res = campaign("geo-without-proof", cfg, ["--journeys", "J01", "--languages", "en"])
        g = res["geo_checks"]
        check("geo without proof", [x["status"] for x in g] == ["NOT_RUN", "NOT_RUN"], f"geo={[(x['country_requested'], x['status']) for x in g]}")
        forged = copy.deepcopy(res)
        forged["geo_checks"][0].update(status="PASS", country_verified="DE")
        fp = d / "qa-output" / "forged-results.json"
        fp.write_text(json.dumps(forged), encoding="utf-8")
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(fp)])
        check("geo PASS without egress proof rejected", b.returncode == 1 and "egress_proof" in b.stderr, b.stderr.strip().splitlines()[0] if b.stderr else "")

        # 6. Unfinished tickets and inconsistent tickets are rejected.
        d, r, res = campaign("ticket-rules", cfg_for("tickets"), ["--journeys", "J02", "--languages", "fr"])
        rp = d / "qa-output" / "results.json"
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(rp)])
        check("FAIL case without ticket rejected", b.returncode == 1 and "without ticket" in b.stderr, b.stderr.strip()[:90])
        run([sys.executable, str(SKILL / "draft_tickets.py"), str(rp)])
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(rp)])
        check("TODO ticket rejected", b.returncode == 1 and "TODO" in b.stderr, b.stderr.strip().splitlines()[0][:90])
        doc = json.loads(rp.read_text())
        doc["tickets"][0].update(severity="BLOCKER", confidence="LOW")
        rp.write_text(json.dumps(doc), encoding="utf-8")
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(rp), "--allow-draft"])
        check("LOW-confidence BLOCKER rejected", b.returncode == 1 and "LOW-confidence" in b.stderr, "")
        doc["cases"][0]["status"] = "PASS"
        rp.write_text(json.dumps(doc), encoding="utf-8")
        b = run([sys.executable, str(SKILL / "build_outputs.py"), str(rp), "--allow-draft"])
        check("PASS case with a failed step rejected", b.returncode == 1 and "not every step passed" in b.stderr, "")

        # 7. Partial retest on a site that is still broken: no defect is declared fixed without evidence.
        prev = ROOT / "tests" / "runs" / "01-blind-audit" / "results.json"
        if prev.exists():
            d, r, res = campaign("partial-retest", cfg_for("retest"), ["--journeys", "J02", "--languages", "fr"])
            rp = d / "qa-output" / "results.json"
            run([sys.executable, str(SKILL / "retest_tickets.py"), "--previous", str(prev), "--current", str(rp)])
            doc = json.loads(rp.read_text())
            st = {t["id"]: t["status"] for t in doc["tickets"]}
            b = run([sys.executable, str(SKILL / "build_outputs.py"), str(rp)])
            check("partial retest", st.get("TCK-J02-fr-desktop") == "STILL_FAILING"
                  and all(v == "NOT_RETESTED" for k, v in st.items() if k != "TCK-J02-fr-desktop") and b.returncode == 0,
                  f"J02-fr={st.get('TCK-J02-fr-desktop')}, others={sorted(set(v for k, v in st.items() if k != 'TCK-J02-fr-desktop'))}")
    finally:
        srv.terminate()

    passed = sum(ok for _, ok, _ in results)
    summary = {"passed": passed, "total": len(results), "checks": [{"name": n, "ok": ok, "detail": dt} for n, ok, dt in results]}
    (out / "negative-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{passed}/{len(results)} negative checks behave as expected")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
