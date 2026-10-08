#!/usr/bin/env python3
"""Carry tickets from a previous campaign into a retest run and set their retest status.

    python3 retest_tickets.py --previous old/results.json --current retest/results.json

For each previous ticket, every linked case_id is looked up in the retest run:
  all linked cases PASS          -> FIXED_VERIFIED
  any linked case FAIL           -> STILL_FAILING (evidence of the retest appended)
  a case missing/BLOCKED/NOT_RUN -> NOT_RETESTED  (never assume a defect disappeared)
New FAIL cases in the retest that no ticket covers stay unlinked: draft them with draft_tickets.py.
"""
import argparse
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_common import dump_json, load_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previous", required=True)
    ap.add_argument("--current", required=True)
    a = ap.parse_args()
    prev, cur = load_json(a.previous), load_json(a.current)
    by_id = {c["case_id"]: c for c in cur.get("cases") or []}
    existing = {t["id"] for t in cur.get("tickets") or []}
    prev_dir = Path(a.previous).resolve().parent
    cur_dir = Path(a.current).resolve().parent
    out = []
    for t in prev.get("tickets") or []:
        if t["id"] in existing:
            continue
        t = copy.deepcopy(t)
        statuses = {cid: (by_id.get(cid) or {}).get("status", "NOT_RUN") for cid in t["case_ids"]}
        if all(s == "PASS" for s in statuses.values()):
            new = "FIXED_VERIFIED"
        elif any(s == "FAIL" for s in statuses.values()):
            new = "STILL_FAILING"
        else:
            new = "NOT_RETESTED"
        # Original evidence stays in the previous campaign folder; reference it relative to the new one.
        rel = os.path.relpath(prev_dir, cur_dir)
        t["evidence"] = [p if prev_dir == cur_dir else os.path.join(rel, p) for p in t["evidence"]]
        for cid, s in statuses.items():
            if s == "FAIL":
                t["evidence"] += [e["path"] for e in by_id[cid].get("evidence") or []]
                t["reproduction"] = f"{t['reproduction']}; retest reproduced {by_id[cid].get('reproduction')}"
        t["retest"] = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "campaign": cur.get("campaign", {}).get("id"), "previous_status": t["status"],
                       "case_statuses": statuses}
        t["status"] = new
        out.append(t)
        print(f"{t['id']:<28} {new:<15} {statuses}")
    cur.setdefault("tickets", []).extend(out)
    dump_json(a.current, cur)
    print(f"carried {len(out)} ticket(s) into {a.current}")


if __name__ == "__main__":
    main()
