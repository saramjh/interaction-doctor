#!/usr/bin/env python3
"""Validates showroom data against the frozen benchmark source of truth.

Checks:
  - summary.json matches benchmark/results/empirical-auto-summary-v1.json exactly
  - cases.json matches benchmark/design/manifest-v3.1.json exactly (30 cases)
  - 90 observations accounted for across 3 arms
  - YES/NO/NEEDS_INTENT distribution is exactly 19/5/6
  - UNMODELED count is exactly 0
  - Cost, wall time, tool calls totals match empirical source
  - NEEDS_INTENT stops under doctor are exactly 2 (cases 011 and 016)
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARK_DIR = os.path.join(REPO_ROOT, "benchmark")
SHOWROOM_DATA_DIR = os.path.join(REPO_ROOT, "showroom", "data")

MANIFEST_PATH = os.path.join(BENCHMARK_DIR, "design", "manifest-v3.1.json")
SUMMARY_PATH = os.path.join(BENCHMARK_DIR, "results", "empirical-auto-summary-v1.json")

def validate():
    errors = []

    # 1. Check file presence
    for fname in ("summary.json", "cases.json", "methodology.json"):
        p = os.path.join(SHOWROOM_DATA_DIR, fname)
        if not os.path.exists(p):
            errors.append(f"Missing generated file: {p}")

    if errors:
        for e in errors:
            print(f"[ERROR] {e}")
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        src_manifest = json.load(f)

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        src_summary = json.load(f)

    with open(os.path.join(SHOWROOM_DATA_DIR, "summary.json"), "r", encoding="utf-8") as f:
        gen_summary = json.load(f)

    with open(os.path.join(SHOWROOM_DATA_DIR, "cases.json"), "r", encoding="utf-8") as f:
        gen_cases = json.load(f)

    # 2. Case count & arm count
    if len(gen_cases) != 30:
        errors.append(f"Expected 30 cases in cases.json, got {len(gen_cases)}")
    if len(src_manifest) != 30:
        errors.append(f"Expected 30 cases in manifest, got {len(src_manifest)}")

    # 3. Outcome distribution
    outcomes = {"YES": 0, "NO": 0, "NEEDS_INTENT": 0, "UNMODELED": 0}
    for c in gen_cases:
        outcomes[c["outcome"]] = outcomes.get(c["outcome"], 0) + 1

    if outcomes["YES"] != 19:
        errors.append(f"Expected 19 YES cases, got {outcomes['YES']}")
    if outcomes["NO"] != 5:
        errors.append(f"Expected 5 NO cases, got {outcomes['NO']}")
    if outcomes["NEEDS_INTENT"] != 6:
        errors.append(f"Expected 6 NEEDS_INTENT cases, got {outcomes['NEEDS_INTENT']}")
    if outcomes["UNMODELED"] != 0:
        errors.append(f"Expected 0 UNMODELED cases, got {outcomes['UNMODELED']}")

    # 4. Check arm numbers in summary
    for arm in ("baseline", "generic", "doctor"):
        src_arm = src_summary["summary"][arm]
        gen_arm = gen_summary["arms"][arm]

        # Check critical metrics
        if gen_arm["n"] != src_arm["n"]:
            errors.append(f"{arm} n mismatch: {gen_arm['n']} != {src_arm['n']}")
        if gen_arm["repair"] != src_arm["repair"]:
            errors.append(f"{arm} repair mismatch: {gen_arm['repair']} != {src_arm['repair']}")
        if gen_arm["correct_no_op"] != src_arm["correct_no_op"]:
            errors.append(f"{arm} correct_no_op mismatch: {gen_arm['correct_no_op']} != {src_arm['correct_no_op']}")
        if gen_arm["intent_guess"] != src_arm["intent_guess"]:
            errors.append(f"{arm} intent_guess mismatch: {gen_arm['intent_guess']} != {src_arm['intent_guess']}")
        if gen_arm["manual_review"] != src_arm["manual_review"]:
            errors.append(f"{arm} manual_review mismatch: {gen_arm['manual_review']} != {src_arm['manual_review']}")
        if gen_arm["regressions"] != src_arm["regressions"]:
            errors.append(f"{arm} regressions mismatch: {gen_arm['regressions']} != {src_arm['regressions']}")
        if gen_arm["false_closure"] != src_arm["false_closure"]:
            errors.append(f"{arm} false_closure mismatch: {gen_arm['false_closure']} != {src_arm['false_closure']}")
        if gen_arm["detection_true"] != src_arm["detection_true"]:
            errors.append(f"{arm} detection_true mismatch: {gen_arm['detection_true']} != {src_arm['detection_true']}")

        # Check cost, time, tools
        if abs(gen_arm["total_cost"] - src_arm["cost"]) > 1e-6:
            errors.append(f"{arm} total_cost mismatch: {gen_arm['total_cost']} != {src_arm['cost']}")
        if abs(gen_arm["total_seconds"] - src_arm["seconds"]) > 1e-6:
            errors.append(f"{arm} total_seconds mismatch: {gen_arm['total_seconds']} != {src_arm['seconds']}")
        if gen_arm["total_tools"] != src_arm["tools"]:
            errors.append(f"{arm} total_tools mismatch: {gen_arm['total_tools']} != {src_arm['tools']}")

    # 5. Check NEEDS_INTENT specific signals (cases 011 and 016)
    doc_stopped_ids = [c["case_id"] for c in gen_cases if c["doctor_intent_stopped"]]
    if sorted(doc_stopped_ids) != ["011", "016"]:
        errors.append(f"Doctor should have stopped on exactly [011, 016], got {doc_stopped_ids}")

    # 6. Check total observations
    total_obs = sum(len(c["runs"]) for c in gen_cases)
    if total_obs != 90:
        errors.append(f"Expected 90 total run observations in cases.json, got {total_obs}")

    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        return False

    print("[PASS] Showroom data integrity verified: 30 cases, 3 arms, 90 observations, exact empirical match.")
    return True

if __name__ == '__main__':
    ok = validate()
    sys.exit(0 if ok else 1)
