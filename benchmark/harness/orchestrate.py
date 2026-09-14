#!/usr/bin/env python3
"""Top-level CLI to build workspaces, gate on contamination checks, and
(optionally) execute real Claude Code runs.

Usage:
  python3 orchestrate.py --cases case-001,case-002 --arms baseline,generic,doctor --check-only
  python3 orchestrate.py --cases case-001 --arms baseline --execute

--check-only (default) builds workspaces and runs the contamination gate
for every requested (case, arm) pair but does NOT call the paid claude CLI.
--execute additionally invokes claude for each pair that passed the gate,
and archives results immutably under results/raw/.
"""

import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design"))

import contamination_check
import runner
import workspace
from config import CASES_DIR, RESULTS_RAW_DIR, ARMS
from verify_experiment_freeze import verify_freeze


def discover_cases():
    return sorted(
        d for d in os.listdir(CASES_DIR)
        if os.path.isdir(os.path.join(CASES_DIR, d)) and not d.startswith(".")
    )


def archive(case_id, arm, run_no, ws_dir, record):
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    dest = os.path.join(RESULTS_RAW_DIR, case_id, arm, f"run-{run_no:02d}-{stamp}")
    os.makedirs(dest, exist_ok=False)  # never overwrite a prior run
    for name in ("run_manifest.json", "run_result.json", "event_log.json"):
        src = os.path.join(ws_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, dest)
    # archive the final workspace diff (full tree, since these are small fixtures)
    workspace_dir = os.path.join(ws_dir, "workspace")
    if os.path.isdir(workspace_dir):
        shutil.copytree(workspace_dir, os.path.join(dest, "final_workspace"))
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="", help="comma-separated case ids, default: all")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--run-no", type=int, default=1)
    ap.add_argument("--execute", action="store_true", help="actually invoke claude (costs money)")
    args = ap.parse_args()

    if args.execute:
        # Fail-closed: --execute may not build a single workspace or make
        # any paid call unless the live instrument matches exactly what
        # was frozen. No flag bypasses this.
        ok, violations = verify_freeze()
        if not ok:
            print("EXPERIMENT_FREEZE_HASH_VERIFY = FAIL", file=sys.stderr)
            for v in violations:
                print(f"[MISMATCH] {v}", file=sys.stderr)
            print("Aborting before any workspace was built or any paid call was made.",
                  file=sys.stderr)
            sys.exit(1)
        print("EXPERIMENT_FREEZE_HASH_VERIFY = PASS", file=sys.stderr)

    cases = args.cases.split(",") if args.cases else discover_cases()
    arms = args.arms.split(",")

    summary = []
    for case_id in cases:
        # Build every requested arm's workspace for this case FIRST, so the
        # cross-arm leakage check can compare them all before any arm is
        # allowed to execute.
        ws_dirs = {arm: workspace.build(case_id, arm, args.run_no) for arm in arms}

        per_arm_violations = {arm: contamination_check.check(ws, arm) for arm, ws in ws_dirs.items()}
        cross_arm_violations = (
            contamination_check.check_no_cross_arm_leakage(ws_dirs) if len(ws_dirs) > 1 else []
        )

        case_blocked = bool(cross_arm_violations)
        if case_blocked:
            print(f"[BLOCKED] {case_id}: cross-arm leakage: {cross_arm_violations}", file=sys.stderr)

        for arm, ws_dir in ws_dirs.items():
            row = {"case_id": case_id, "arm": arm, "run_no": args.run_no, "ws_dir": ws_dir}
            violations = list(per_arm_violations[arm])
            if case_blocked:
                violations = violations + [f"case-level: {v}" for v in cross_arm_violations]
            if violations:
                row["status"] = "BLOCKED_CONTAMINATION"
                row["violations"] = violations
                print(f"[BLOCKED] {case_id}/{arm}: {violations}", file=sys.stderr)
                summary.append(row)
                continue
            row["contamination_check"] = "clean"
            if not args.execute:
                row["status"] = "DRY_RUN_ONLY"
                summary.append(row)
                continue
            record = runner.run(case_id, arm, args.run_no, ws_dir, dry_run=False)
            dest = archive(case_id, arm, args.run_no, ws_dir, record)
            row["status"] = record["status"]
            row["archived_at"] = dest
            summary.append(row)

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
