#!/usr/bin/env python3
"""Deterministic consistency checks for the frozen v3.1 benchmark design
manifest (benchmark/design/manifest-v3.1.json).

This is the persisted form of the exact validation that produced
ALL_CHECKS_PASS=True during the v3.1 design-review pass. It reads the
manifest from disk -- it does not hard-code a PASS result, and it does
not re-derive or reinterpret case content; it only checks structural and
count invariants against whatever manifest-v3.1.json actually contains.

Usage:
    python3 benchmark/design/validate_manifest.py

Exits 0 and prints ALL_CHECKS_PASS = True only if every check below
passes against the on-disk manifest. Exits 1 and prints the actual
computed counts/failures otherwise.

This script validates the DESIGN manifest only. It is authoring
metadata, not agent-visible task content -- it must never be copied into
a case's public fixture/ directory or referenced from any task.md.
"""

import json
import os
import sys
from collections import Counter

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest-v3.1.json")


def load_manifest(path):
    with open(path) as f:
        return json.load(f)


def run_checks(data):
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # -- structural -----------------------------------------------------
    check("exactly_30_entries", len(data) == 30, f"len={len(data)}")

    ids = [d.get("case_id") for d in data]
    expected_ids = [f"{i:03d}" for i in range(1, 31)]
    check("unique_ids", len(set(ids)) == len(ids),
          f"dupes={[i for i, c in Counter(ids).items() if c > 1]}")
    check("ids_001_to_030_no_missing", sorted(str(i) for i in ids) == expected_ids,
          f"missing={sorted(set(expected_ids) - set(ids))} extra={sorted(set(ids) - set(expected_ids))}")

    # -- outcome counts ---------------------------------------------------
    outcome_counts = Counter(d.get("outcome") for d in data)
    expected_outcomes = {"YES": 19, "NO": 5, "NEEDS_INTENT": 6, "UNMODELED": 0}
    for k, v in expected_outcomes.items():
        check(f"outcome_{k}_count", outcome_counts.get(k, 0) == v,
              f"actual={outcome_counts.get(k, 0)} expected={v}")
    check("outcome_counts_sum_30", sum(outcome_counts.values()) == 30,
          f"sum={sum(outcome_counts.values())}")

    # -- difficulty counts -------------------------------------------------
    diff_counts = Counter(d.get("difficulty") for d in data)
    expected_diff = {"T1": 5, "T2": 18, "T3": 7}
    for k, v in expected_diff.items():
        check(f"difficulty_{k}_count", diff_counts.get(k, 0) == v,
              f"actual={diff_counts.get(k, 0)} expected={v}")
    check("difficulty_counts_sum_30", sum(diff_counts.values()) == 30,
          f"sum={sum(diff_counts.values())}")

    # -- runtime counts -----------------------------------------------------
    runtime_counts = Counter(d.get("runtime") for d in data)
    check("runtime_counts_sum_30", sum(runtime_counts.values()) == 30,
          f"sum={sum(runtime_counts.values())}; breakdown={dict(runtime_counts)}")

    # -- relation family coverage --------------------------------------------
    all_relations = set()
    for d in data:
        all_relations.update(d.get("relations", []) or [])
    required_relations = {"COMPETES", "COOPERATES", "PREEMPTS", "CONDITIONAL", "SEQUENCES", "DERIVES_FROM"}
    check("all_six_relations_represented", required_relations.issubset(all_relations),
          f"present={sorted(all_relations)} missing={sorted(required_relations - all_relations)}")

    # -- lifecycle coverage ---------------------------------------------------
    all_lifecycle = set()
    for d in data:
        all_lifecycle.update(d.get("lifecycle_categories", []) or [])
    required_lifecycle = {
        "completion", "cancellation", "focus_loss", "device_loss",
        "mode_change", "runtime_interruption", "scope_resource_invalidation",
    }
    check("lifecycle_coverage_complete", required_lifecycle.issubset(all_lifecycle),
          f"present={sorted(all_lifecycle)} missing={sorted(required_lifecycle - all_lifecycle)}")

    # -- effect-lifetime coverage ------------------------------------------
    all_el = set()
    for d in data:
        all_el.update(d.get("effect_lifetime_categories", []) or [])
    required_el = {"timer", "debounce", "async_request", "queued_work", "animation_completion", "stale_callback"}
    check("effect_lifetime_coverage_complete", required_el.issubset(all_el),
          f"present={sorted(all_el)} missing={sorted(required_el - all_el)}")

    # -- N-ary policy coverage ------------------------------------------------
    all_group_policies = set(d.get("group_policy") for d in data if d.get("group_policy"))
    required_policies = {"exclusive", "capacity(2)", "simultaneous", "ordered", "runtime-defined"}
    check("all_five_nary_policies_represented", required_policies.issubset(all_group_policies),
          f"present={sorted(all_group_policies)} missing={sorted(required_policies - all_group_policies)}")

    # every N-ary-tagged case has >=3 named participants and a stated property
    nary_cases = [d for d in data if d.get("group_policy")]
    bad_nary = [d["case_id"] for d in nary_cases
                if len(d.get("nary_participants", []) or []) < 3 or not d.get("nary_behavioral_property")]
    check("nary_cases_have_3plus_participants_and_property", len(bad_nary) == 0,
          f"violations={bad_nary}")

    # -- contamination risk -----------------------------------------------
    contam_counts = Counter(d.get("contamination_risk") for d in data)
    check("high_contamination_count_zero", contam_counts.get("HIGH", 0) == 0,
          f"HIGH={contam_counts.get('HIGH', 0)}")
    medium_cases = sorted(d["case_id"] for d in data if d.get("contamination_risk") == "MEDIUM")
    check("exactly_one_medium_is_005", medium_cases == ["005"], f"medium_cases={medium_cases}")

    # -- recursive revalidation ---------------------------------------------
    rr_cases = sorted(d["case_id"] for d in data if d.get("requires_recursive_revalidation"))
    check("recursive_revalidation_case_030_present", rr_cases == ["030"], f"rr_cases={rr_cases}")

    # -- oracle presence ----------------------------------------------------
    yes_missing_oracle = [d["case_id"] for d in data
                           if d.get("outcome") == "YES" and not d.get("primary_hidden_oracles")]
    check("every_YES_case_has_oracle", len(yes_missing_oracle) == 0, f"missing={yes_missing_oracle}")

    no_missing_oracle = [d["case_id"] for d in data
                          if d.get("outcome") == "NO" and not d.get("primary_hidden_oracles")]
    check("every_NO_case_has_oracle", len(no_missing_oracle) == 0, f"missing={no_missing_oracle}")

    ni_bad = []
    for d in data:
        if d.get("outcome") == "NEEDS_INTENT":
            oracles = d.get("primary_hidden_oracles", []) or []
            if not oracles or not any("transcript" in o.lower() or "manual" in o.lower() for o in oracles):
                ni_bad.append(d["case_id"])
    check("every_NEEDS_INTENT_has_transcript_manual_oracle", len(ni_bad) == 0, f"violations={ni_bad}")

    return results, outcome_counts, diff_counts, runtime_counts, contam_counts


def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    data = load_manifest(MANIFEST_PATH)
    results, outcome_counts, diff_counts, runtime_counts, contam_counts = run_checks(data)

    all_pass = True
    print(f"{'CHECK':<45}{'RESULT':<8}DETAIL")
    for name, passed, detail in results:
        if not passed:
            all_pass = False
        print(f"{name:<45}{'PASS' if passed else 'FAIL':<8}{detail}")

    print()
    print(f"outcome breakdown: {dict(outcome_counts)}")
    print(f"difficulty breakdown: {dict(diff_counts)}")
    print(f"runtime breakdown: {dict(runtime_counts)}")
    print(f"contamination breakdown: {dict(contam_counts)}")
    print()
    print("ALL_CHECKS_PASS =", all_pass)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
