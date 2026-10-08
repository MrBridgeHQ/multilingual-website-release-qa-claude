#!/usr/bin/env python3
"""Validate results.json, reconcile counts, check evidence, and render the deliverables.

    python3 build_outputs.py qa-output/results.json [--lang fr] [--allow-draft]

results.json is the source of truth. This script writes, next to it:
  audit-report.md   human report (headings in --lang / campaign.output_language)
  tickets.csv       ticket export for triage or import (English keys, normalized values)
and stores the computed `summary` back into results.json.
Exit 1 on schema errors, unlinked FAIL cases or TODO placeholders (unless --allow-draft).
Keys, statuses and severities are never translated.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_common import SEVERITIES, counts, dump_json, load_json, validate_results, verdict  # noqa: E402

L = {
    "en": {
        "title": "Release QA report", "scope": "Scope", "env": "Environment and capabilities", "summary": "Summary",
        "verdict": "Verdict", "priority": "Priority issues", "matrix": "Test matrix", "tickets": "Tickets",
        "obs": "Observations, product questions and assumptions", "geo": "Geographic checks", "limits": "Limitations",
        "next": "Recommended next steps", "start": "Start URL", "environment": "Environment", "languages": "Languages",
        "devices": "Device profiles", "journeys": "Journeys", "filters": "Run filters", "outlang": "Report language",
        "browser": "Browser", "runner": "Runner", "cap": "Capability", "avail": "Available", "yes": "yes", "no": "no",
        "planned": "Planned", "executed": "Executed (PASS + FAIL)", "coverage": "Execution coverage", "passrate": "Pass rate among executed",
        "critical": "Release-critical cases passed", "journey": "Journey", "impact": "Impact", "severity": "Severity",
        "confidence": "Diagnosis confidence", "scope_obs": "Observed scope", "pre": "Preconditions", "data": "Test data",
        "steps": "Steps to reproduce", "expected": "Expected", "observed": "Observed", "evidence": "Evidence",
        "cases": "Linked cases", "repro": "Reproduction", "fix": "Fix hypothesis", "ac": "Acceptance criteria",
        "retest": "Retest procedure", "status": "Status", "none": "None.", "missing": "Missing evidence files",
        "flaky": "Intermittent failures", "assumptions": "Assumptions", "draft": "DRAFT - contains unresolved TODO fields",
        "requested": "requested", "verified": "verified", "rationale": "Rationale", "pages": "pages",
        "next_open": "Fix and retest the open tickets, highest severity first.",
        "next_cover": "Cover the cases that were not executed:",
        "next_q": "Answer the open product questions before the next campaign.",
        "next_ok": "No action required within the tested scope; extend the scope if needed.",
    },
    "fr": {
        "title": "Rapport de recette", "scope": "Périmètre", "env": "Environnement et capacités", "summary": "Synthèse",
        "verdict": "Verdict", "priority": "Anomalies prioritaires", "matrix": "Matrice des tests", "tickets": "Tickets",
        "obs": "Observations, questions produit et hypothèses", "geo": "Vérifications géographiques", "limits": "Limites",
        "next": "Suite recommandée", "start": "URL de départ", "environment": "Environnement", "languages": "Langues",
        "devices": "Profils d'appareils", "journeys": "Parcours", "filters": "Filtres d'exécution", "outlang": "Langue du rapport",
        "browser": "Navigateur", "runner": "Exécuteur", "cap": "Capacité", "avail": "Disponible", "yes": "oui", "no": "non",
        "planned": "Planifiés", "executed": "Exécutés (PASS + FAIL)", "coverage": "Couverture d'exécution", "passrate": "Taux de réussite parmi les exécutés",
        "critical": "Cas critiques pour la livraison réussis", "journey": "Parcours", "impact": "Impact", "severity": "Gravité",
        "confidence": "Confiance du diagnostic", "scope_obs": "Périmètre observé", "pre": "Préconditions", "data": "Données de test",
        "steps": "Étapes de reproduction", "expected": "Attendu", "observed": "Observé", "evidence": "Preuves",
        "cases": "Cas liés", "repro": "Reproduction", "fix": "Piste de correction", "ac": "Critères d'acceptation",
        "retest": "Procédure de nouveau test", "status": "Statut", "none": "Aucun.", "missing": "Fichiers de preuve manquants",
        "flaky": "Échecs intermittents", "assumptions": "Hypothèses", "draft": "BROUILLON - contient des champs TODO non résolus",
        "requested": "demandé", "verified": "vérifié", "rationale": "Justification", "pages": "pages",
        "next_open": "Corriger puis retester les tickets ouverts, par gravité décroissante.",
        "next_cover": "Couvrir les cas non exécutés :",
        "next_q": "Répondre aux questions produit avant la prochaine campagne.",
        "next_ok": "Aucune action requise dans le périmètre testé ; étendre le périmètre si nécessaire.",
    },
}


def frac(n, d):
    return f"{n}/{d}" + (f" ({100 * n / d:.0f}%)" if d else "")


def md_cell(v):
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--lang", help="report language (default: campaign.output_language)")
    ap.add_argument("--allow-draft", action="store_true", help="render even with TODO fields (report marked DRAFT)")
    a = ap.parse_args()
    rpath = Path(a.results).resolve()
    out = rpath.parent
    res = load_json(rpath)
    lang = a.lang or res.get("campaign", {}).get("output_language", "en")
    t = L.get(lang, L["en"])

    errors = validate_results(res)
    cases = res.get("cases") or []
    tickets = res.get("tickets") or []
    linked = {cid for tk in tickets for cid in tk.get("case_ids") or []}
    linked |= {cid for o in res.get("observations") or [] for cid in o.get("case_ids") or []}
    unlinked = [c["case_id"] for c in cases if c["status"] == "FAIL" and c["case_id"] not in linked]
    if unlinked:
        errors.append(f"FAIL cases without ticket or observation: {', '.join(unlinked)}")
    todo_errors = [e for e in errors if "TODO" in e]
    hard = [e for e in errors if e not in todo_errors]
    if hard or (todo_errors and not a.allow_draft):
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
    draft = bool(todo_errors)

    # Evidence paths are relative to the results directory so the folder can be moved.
    missing = []
    for c in cases:
        for e in c.get("evidence") or []:
            p = e["path"] if isinstance(e, dict) else e
            if Path(p).is_absolute() or not (out / p).exists():
                missing.append(f"{c['case_id']}: {p}")
    for tk in tickets:
        for p in tk.get("evidence") or []:
            if Path(p).is_absolute() or not (out / p).exists():
                missing.append(f"{tk['id']}: {p}")
    for o in res.get("observations") or []:
        for p in o.get("evidence") or []:
            if Path(p).is_absolute() or not (out / p).exists():
                missing.append(f"{o.get('id', o['kind'])}: {p}")

    cnt = counts(cases)
    assert cnt["PLANNED"] == sum(cnt[s] for s in ("PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE")), "count reconciliation failed"
    crit = [c for c in cases if c.get("release_critical")]
    v, why = verdict(res)
    res["summary"] = {
        "counts": cnt, "verdict": v, "verdict_reason": why,
        "release_critical": {"passed": sum(c["status"] == "PASS" for c in crit), "total": len(crit)},
        "tickets_by_severity": {s: sum(tk.get("severity") == s and tk.get("status") in ("OPEN", "STILL_FAILING") for tk in tickets) for s in SEVERITIES},
        "missing_evidence": missing, "draft": draft,
    }
    dump_json(rpath, res)

    camp, scope, env, cap = res["campaign"], res.get("scope", {}), res.get("environment", {}), res.get("capabilities", {})
    sev_rank = {s: i for i, s in enumerate(SEVERITIES)}
    open_t = sorted([tk for tk in tickets if tk.get("status") in ("OPEN", "STILL_FAILING")], key=lambda x: sev_rank.get(x.get("severity"), 9))
    md = [f"# {t['title']} - {camp.get('name', '')}", ""]
    if draft:
        md += [f"> **{t['draft']}**", ""]
    md += [f"Campaign `{camp['id']}`{' - ' + camp['label'] if camp.get('label') else ''} · {camp.get('started_at', '')} → {camp.get('finished_at', '')}", ""]
    md += [f"## 1. {t['scope']}", "",
           f"- {t['start']}: {scope.get('start_url')}",
           f"- {t['environment']}: {camp.get('environment')}",
           f"- {t['languages']}: {', '.join(scope.get('languages', []))}",
           f"- {t['devices']}: {', '.join(scope.get('devices', []))}",
           f"- {t['journeys']}: " + "; ".join(f"{j['id']} {j['title']}{' (critical)' if j.get('release_critical') else ''}" for j in scope.get("journeys", [])),
           f"- {t['filters']}: {scope.get('filters')}",
           f"- {t['outlang']}: {lang}", ""]
    md += [f"## 2. {t['env']}", "",
           f"- {t['runner']}: {env.get('runner')} · Node {env.get('node')} · {env.get('platform')}",
           f"- {t['browser']}: {env.get('browser')} {env.get('browser_version') or ''}" + (f" - {env['browser_error']}" if env.get("browser_error") else ""), "",
           f"| {t['cap']} | {t['avail']} |", "|---|---|"]
    md += [f"| {k} | {t['yes'] if val else t['no']} |" for k, val in cap.items() if isinstance(val, bool)]
    md += [""] + [f"- {n}" for n in cap.get("notes") or []] + [""]
    md += [f"## 3. {t['summary']}", "", f"**{t['verdict']}: `{v}`** - {why}", "",
           "| PLANNED | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE |", "|---|---|---|---|---|---|",
           f"| {cnt['PLANNED']} | {cnt['PASS']} | {cnt['FAIL']} | {cnt['BLOCKED']} | {cnt['NOT_RUN']} | {cnt['NOT_APPLICABLE']} |", "",
           f"- {t['coverage']}: {frac(cnt['EXECUTED'], cnt['PLANNED'])}",
           f"- {t['passrate']}: {frac(cnt['PASS'], cnt['EXECUTED'])}",
           f"- {t['critical']}: {frac(res['summary']['release_critical']['passed'], len(crit))}",
           "- " + ", ".join(f"{s}: {n}" for s, n in res["summary"]["tickets_by_severity"].items()), ""]
    md += [f"## 4. {t['priority']}", ""]
    md += [f"{i}. **[{tk['severity']}]** {tk['id']} - {tk['title']} ({', '.join(tk['case_ids'])})" for i, tk in enumerate(open_t, 1)] or [t["none"]]
    md += ["", f"## 5. {t['matrix']}", ""]
    combos = sorted({(c["language"], c["device"]) for c in cases})
    md += [f"| {t['journey']} | " + " | ".join(f"{l} / {d}" for l, d in combos) + " |", "|---" * (len(combos) + 1) + "|"]
    for j in scope.get("journeys", []):
        row = []
        for l, d in combos:
            c = next((x for x in cases if x["journey_id"] == j["id"] and x["language"] == l and x["device"] == d), None)
            row.append("-" if not c else c["status"] + (f" {c['reproduction']}" if c.get("reproduction") else ""))
        if any(r != "-" for r in row):
            md.append(f"| {j['id']} {md_cell(j['title'])} | " + " | ".join(row) + " |")
    md += ["", "Case details (status, reason, final URL):", ""]
    for c in cases:
        md.append(f"- `{c['case_id']}` **{c['status']}**" + (f" - {c['reason']}" if c.get("reason") else "") + (f" · {c.get('url_final')}" if c.get("url_final") else ""))
    md += ["", f"## 6. {t['tickets']}", ""]
    for tk in tickets:
        sc = tk.get("scope", {})
        md += [f"### {tk['id']} - {tk['title']}", "",
               f"- {t['status']}: `{tk['status']}` · {t['severity']}: `{tk['severity']}` · {t['confidence']}: `{tk['confidence']}`",
               f"- {t['rationale']}: {tk['severity_rationale']}",
               f"- {t['impact']}: {tk['impact']}",
               f"- {t['scope_obs']}: {', '.join(sc.get('languages', []))} · {', '.join(sc.get('devices', []))} · {t['pages']}: {', '.join(p for p in sc.get('pages', []) if p)}",
               f"- {t['pre']}: {'; '.join(tk['preconditions']) if isinstance(tk['preconditions'], list) else tk['preconditions']}"]
        if tk.get("test_data"):
            md.append(f"- {t['data']}: {tk['test_data']}")
        md += ["", f"**{t['steps']}**", ""] + [f"{i}. {s}" for i, s in enumerate(tk["steps"], 1)]
        md += ["", f"- {t['expected']}: {tk['expected']}", f"- {t['observed']}: {tk['observed']}",
               f"- {t['repro']}: {tk['reproduction']}",
               f"- {t['evidence']}: " + ", ".join(f"[{Path(p).name}]({p})" for p in tk["evidence"]),
               f"- {t['cases']}: {', '.join(tk['case_ids'])}",
               f"- {t['fix']}: {tk['fix_hypothesis']}", "", f"**{t['ac']}**", ""]
        md += [f"- [ ] {x}" for x in tk["acceptance_criteria"]]
        md += ["", f"- {t['retest']}: {tk['retest_procedure']}"]
        if tk.get("retest"):
            md.append(f"- Retest: {tk['retest']}")
        md.append("")
    if not tickets:
        md += [t["none"], ""]
    md += [f"## 7. {t['obs']}", ""]
    for o in res.get("observations") or []:
        md.append(f"- **{o['kind']}**{' ' + o['id'] if o.get('id') else ''} - {o['summary']}" + (f" ({', '.join(o['case_ids'])})" if o.get("case_ids") else "")
                  + (" · " + ", ".join(f"[{Path(p).name}]({p})" for p in o["evidence"]) if o.get("evidence") else ""))
    md += [f"- {t['assumptions']}: " + ("; ".join(res.get("assumptions") or []) or t["none"]), ""]
    md += [f"### {t['geo']}", ""]
    for g in res.get("geo_checks") or []:
        md.append(f"- {g['country_requested']} ({t['requested']}) / {g.get('country_verified') or '-'} ({t['verified']}): **{g['status']}** - {g.get('reason', '')}")
    if not res.get("geo_checks"):
        md.append(t["none"])
    md += ["", f"## 8. {t['limits']}", ""]
    lim = [f"{k}: {t['no']}" for k, val in cap.items() if val is False]
    lim += [f"{c['case_id']}: {x}" for c in cases for x in c.get("limitations") or []]
    lim += [f"{t['flaky']}: {c['case_id']} {c['reproduction']}" for c in cases if c.get("flaky")]
    lim += [f"{t['missing']}: {m}" for m in missing]
    md += [f"- {x}" for x in lim] or [t["none"]]
    md += ["", f"## 9. {t['next']}", ""]
    nxt = []
    if open_t:
        nxt.append(t["next_open"])
    uncovered = [c["case_id"] for c in cases if c["status"] in ("BLOCKED", "NOT_RUN")]
    if uncovered:
        nxt.append(f"{t['next_cover']} {', '.join(uncovered)}")
    if any(o.get("kind") == "PRODUCT_QUESTION" for o in res.get("observations") or []):
        nxt.append(t["next_q"])
    md += [f"- {x}" for x in nxt] or [f"- {t['next_ok']}"]
    (out / "audit-report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    cols = ["id", "title", "severity", "confidence", "status", "languages", "devices", "pages", "case_ids",
            "reproduction", "impact", "preconditions", "steps", "expected", "observed", "acceptance_criteria",
            "fix_hypothesis", "retest_procedure", "evidence"]
    with open(out / "tickets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for tk in tickets:
            sc = tk.get("scope", {})
            pre = tk["preconditions"]
            w.writerow([tk["id"], tk["title"], tk["severity"], tk["confidence"], tk["status"],
                        ";".join(sc.get("languages", [])), ";".join(sc.get("devices", [])), ";".join(p for p in sc.get("pages", []) if p),
                        ";".join(tk["case_ids"]), tk["reproduction"], tk["impact"],
                        " | ".join(pre) if isinstance(pre, list) else pre,
                        " | ".join(f"{i}. {s}" for i, s in enumerate(tk["steps"], 1)), tk["expected"], tk["observed"],
                        " | ".join(tk["acceptance_criteria"]), tk["fix_hypothesis"], tk["retest_procedure"], ";".join(tk["evidence"])])
    print(f"{'DRAFT ' if draft else ''}verdict {v}: {cnt['PASS']} PASS, {cnt['FAIL']} FAIL, {cnt['BLOCKED']} BLOCKED, "
          f"{cnt['NOT_RUN']} NOT_RUN, {cnt['NOT_APPLICABLE']} N/A of {cnt['PLANNED']} planned; {len(tickets)} ticket(s); "
          f"{len(missing)} missing evidence file(s)")
    print(f"wrote {out / 'audit-report.md'} and {out / 'tickets.csv'}")


if __name__ == "__main__":
    main()
