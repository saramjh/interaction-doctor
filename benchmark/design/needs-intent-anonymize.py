#!/usr/bin/env python3
"""Frozen preparation step for needs-intent-scoring-v2's blind review.

Given the archived NEEDS_INTENT run directories (results/raw/<case_id>/<arm>/<run-dir>/),
assigns each a stable opaque transcript_id, and writes:
  - a private identity map (transcript_id -> case_id, arm, run_id) to
    needs-intent-identity-map.json (withhold this from the reviewer)
  - blind record shells (transcript_id + case_id only, other fields empty)
    to needs-intent-blind-records.json (hand this to the reviewer)

Frozen now, before any real archived NEEDS_INTENT run exists -- this
script requires no editing to run later against actual archived runs. It
does not read or interpret any transcript content; it only assigns IDs
and splits case/arm/run_id apart.

Usage:
    python3 needs-intent-anonymize.py --results-dir ../results/raw
"""
import argparse
import hashlib
import json
import os
import secrets

NEEDS_INTENT_CASE_IDS = ("004", "010", "011", "013", "016", "019")
ARMS = ("baseline", "generic", "doctor")


def _case_dir_name(results_dir, case_id):
    for name in os.listdir(results_dir):
        if name.startswith(f"case-{case_id}-"):
            return name
    return None


def discover_runs(results_dir):
    """Returns a list of (case_id, arm, run_id, run_dir) for every
    archived NEEDS_INTENT run found under results_dir."""
    runs = []
    for case_id in NEEDS_INTENT_CASE_IDS:
        case_dir_name = _case_dir_name(results_dir, case_id)
        if case_dir_name is None:
            continue
        for arm in ARMS:
            arm_dir = os.path.join(results_dir, case_dir_name, arm)
            if not os.path.isdir(arm_dir):
                continue
            for run_id in sorted(os.listdir(arm_dir)):
                run_dir = os.path.join(arm_dir, run_id)
                if os.path.isdir(run_dir):
                    runs.append((case_id, arm, run_id, run_dir))
    return runs


def assign_transcript_id(salt, case_id, arm, run_id):
    digest = hashlib.sha256(f"{salt}:{case_id}:{arm}:{run_id}".encode()).hexdigest()
    return f"ni-{case_id}-{digest[:8]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "raw"))
    ap.add_argument("--out-dir", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    runs = discover_runs(args.results_dir)
    if not runs:
        print(f"No archived NEEDS_INTENT runs found under {args.results_dir}.")
        print("This is expected before any experiment has been executed -- "
              "re-run this script after real runs are archived.")
        return

    salt = secrets.token_hex(16)

    identity_map = []
    blind_records = []
    seen_ids = set()
    for case_id, arm, run_id, run_dir in runs:
        tid = assign_transcript_id(salt, case_id, arm, run_id)
        assert tid not in seen_ids, f"transcript_id collision: {tid}"
        seen_ids.add(tid)

        identity_map.append({
            "transcript_id": tid, "case_id": case_id, "arm": arm, "run_id": run_id,
        })
        blind_records.append({
            "transcript_id": tid, "case_id": case_id,
            "recognized_ambiguity": None,
            "invented_product_intent": None,
            "made_unsafe_behavior_change": None,
            "requested_clarification_when_required": None,
            "intent_guessing_violation": None,
            "manual_outcome": None,
            "evidence": [],
            "reviewer_note": "",
        })

    os.makedirs(args.out_dir, exist_ok=True)
    identity_path = os.path.join(args.out_dir, "needs-intent-identity-map.json")
    blind_path = os.path.join(args.out_dir, "needs-intent-blind-records.json")

    with open(identity_path, "w") as f:
        json.dump({"salt_used_do_not_reuse": salt, "entries": identity_map}, f, indent=2)
    with open(blind_path, "w") as f:
        json.dump(blind_records, f, indent=2)

    print(f"{len(runs)} runs anonymized.")
    print(f"Identity map (WITHHOLD from reviewer): {identity_path}")
    print(f"Blind record shells (hand to reviewer): {blind_path}")


if __name__ == "__main__":
    main()
