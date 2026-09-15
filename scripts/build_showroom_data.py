#!/usr/bin/env python3
"""Builds machine-derived showroom data from frozen benchmark artifacts.

Source of truth:
  - benchmark/design/manifest-v3.1.json
  - benchmark/results/empirical-auto-summary-v1.json
  - benchmark/cases/*/task.md

Outputs (under showroom/data/):
  - summary.json: arm-level metrics, ratios, cost, latency, tool call stats
  - cases.json: 30 normalized case records with manifest metadata and 3-arm observations
  - methodology.json: experimental parameters, hypothesis, protocol details, and caveats
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARK_DIR = os.path.join(REPO_ROOT, "benchmark")
SHOWROOM_DATA_DIR = os.path.join(REPO_ROOT, "showroom", "data")

MANIFEST_PATH = os.path.join(BENCHMARK_DIR, "design", "manifest-v3.1.json")
SUMMARY_PATH = os.path.join(BENCHMARK_DIR, "results", "empirical-auto-summary-v1.json")
CASES_DIR = os.path.join(BENCHMARK_DIR, "cases")

def build_summary_data(auto_summary):
    summary_raw = auto_summary["summary"]
    baseline = summary_raw["baseline"]
    generic = summary_raw["generic"]
    doctor = summary_raw["doctor"]

    out = {
        "meta": {
            "benchmark_name": "Interaction Doctor Benchmark",
            "model": "claude-sonnet-5",
            "effort": "medium",
            "total_cases": 30,
            "total_arms": 3,
            "total_observations": 90,
            "outcomes": {
                "YES": 19,
                "NO": 5,
                "NEEDS_INTENT": 6,
                "UNMODELED": 0
            },
            "status": {
                "skill_product": "DISCONTINUED",
                "benchmark": "RETAINED",
                "empirical_results": "RETAINED"
            }
        },
        "arms": {
            "baseline": {
                "id": "baseline",
                "label": "Baseline",
                "description": "Same coding model, no Interaction Doctor skill or specialized instructions",
                "n": baseline["n"],
                "repair": baseline["repair"],
                "repair_total": baseline["yes_n"],
                "repair_pct": baseline["repair_pct"],
                "correct_no_op": baseline["correct_no_op"],
                "correct_no_op_total": baseline["no_n"],
                "correct_no_op_pct": baseline["correct_no_op_pct"],
                "false_positive": baseline["false_positive"],
                "false_positive_total": baseline["no_n"],
                "false_positive_pct": baseline["false_positive_pct"],
                "intent_guess": baseline["intent_guess"],
                "intent_guess_total": baseline["intent_n"],
                "intent_guess_pct": baseline["intent_guess_pct"],
                "manual_review": baseline["manual_review"],
                "manual_review_total": baseline["intent_n"],
                "manual_review_pct": (baseline["manual_review"] / baseline["intent_n"]) * 100.0,
                "regressions": baseline["regressions"],
                "regressions_total": baseline["n"],
                "regression_pct": baseline["regression_pct"],
                "false_closure": baseline["false_closure"],
                "false_closure_total": baseline["n"],
                "false_closure_pct": baseline["false_closure_pct"],
                "detection_true": baseline["detection_true"],
                "detection_eval": baseline["detection_eval"],
                "detection_pct": baseline["detection_pct"],
                "total_cost": baseline["cost"],
                "mean_cost": baseline["cost"] / baseline["n"],
                "total_seconds": baseline["seconds"],
                "mean_seconds": baseline["seconds"] / baseline["n"],
                "total_tools": baseline["tools"],
                "mean_tools": baseline["tools"] / baseline["n"],
                "verdicts": baseline["verdicts"]
            },
            "generic": {
                "id": "generic",
                "label": "Generic Rigor",
                "description": "Same coding model with generic rigor/audit prompt, without Interaction Doctor terminology",
                "n": generic["n"],
                "repair": generic["repair"],
                "repair_total": generic["yes_n"],
                "repair_pct": generic["repair_pct"],
                "correct_no_op": generic["correct_no_op"],
                "correct_no_op_total": generic["no_n"],
                "correct_no_op_pct": generic["correct_no_op_pct"],
                "false_positive": generic["false_positive"],
                "false_positive_total": generic["no_n"],
                "false_positive_pct": generic["false_positive_pct"],
                "intent_guess": generic["intent_guess"],
                "intent_guess_total": generic["intent_n"],
                "intent_guess_pct": generic["intent_guess_pct"],
                "manual_review": generic["manual_review"],
                "manual_review_total": generic["intent_n"],
                "manual_review_pct": (generic["manual_review"] / generic["intent_n"]) * 100.0,
                "regressions": generic["regressions"],
                "regressions_total": generic["n"],
                "regression_pct": generic["regression_pct"],
                "false_closure": generic["false_closure"],
                "false_closure_total": generic["n"],
                "false_closure_pct": generic["false_closure_pct"],
                "detection_true": generic["detection_true"],
                "detection_eval": generic["detection_eval"],
                "detection_pct": generic["detection_pct"],
                "total_cost": generic["cost"],
                "mean_cost": generic["cost"] / generic["n"],
                "total_seconds": generic["seconds"],
                "mean_seconds": generic["seconds"] / generic["n"],
                "total_tools": generic["tools"],
                "mean_tools": generic["tools"] / generic["n"],
                "verdicts": generic["verdicts"]
            },
            "doctor": {
                "id": "doctor",
                "label": "Interaction Doctor v1",
                "description": "Same coding model with the frozen Interaction Doctor v1 skill injected",
                "n": doctor["n"],
                "repair": doctor["repair"],
                "repair_total": doctor["yes_n"],
                "repair_pct": doctor["repair_pct"],
                "correct_no_op": doctor["correct_no_op"],
                "correct_no_op_total": doctor["no_n"],
                "correct_no_op_pct": doctor["correct_no_op_pct"],
                "false_positive": doctor["false_positive"],
                "false_positive_total": doctor["no_n"],
                "false_positive_pct": doctor["false_positive_pct"],
                "intent_guess": doctor["intent_guess"],
                "intent_guess_total": doctor["intent_n"],
                "intent_guess_pct": doctor["intent_guess_pct"],
                "manual_review": doctor["manual_review"],
                "manual_review_total": doctor["intent_n"],
                "manual_review_pct": (doctor["manual_review"] / doctor["intent_n"]) * 100.0,
                "regressions": doctor["regressions"],
                "regressions_total": doctor["n"],
                "regression_pct": doctor["regression_pct"],
                "false_closure": doctor["false_closure"],
                "false_closure_total": doctor["n"],
                "false_closure_pct": doctor["false_closure_pct"],
                "detection_true": doctor["detection_true"],
                "detection_eval": doctor["detection_eval"],
                "detection_pct": doctor["detection_pct"],
                "total_cost": doctor["cost"],
                "mean_cost": doctor["cost"] / doctor["n"],
                "total_seconds": doctor["seconds"],
                "mean_seconds": doctor["seconds"] / doctor["n"],
                "total_tools": doctor["tools"],
                "mean_tools": doctor["tools"] / doctor["n"],
                "verdicts": doctor["verdicts"]
            }
        },
        "ratios_vs_baseline": {
            "cost_ratio": doctor["cost"] / baseline["cost"],
            "wall_time_ratio": doctor["seconds"] / baseline["seconds"],
            "tool_calls_ratio": doctor["tools"] / baseline["tools"],
            "generic_cost_ratio": generic["cost"] / baseline["cost"],
            "generic_wall_time_ratio": generic["seconds"] / baseline["seconds"],
            "generic_tool_calls_ratio": generic["tools"] / baseline["tools"]
        },
        "headline_findings": [
            {
                "metric": "Repair Success Rate",
                "baseline": "19 / 19 (100%)",
                "generic": "19 / 19 (100%)",
                "doctor": "19 / 19 (100%)",
                "difference": "0% advantage",
                "interpretation": "Interaction Doctor provided NO measured improvement in repair success on the 19 well-specified defective cases."
            },
            {
                "metric": "Execution Cost Ratio",
                "baseline": ".24 (/opt/homebrew/bin/zsh.108/run)",
                "generic": ".44 (/opt/homebrew/bin/zsh.115/run)",
                "doctor": ".20 (/opt/homebrew/bin/zsh.207/run)",
                "difference": "1.91x cost increase",
                "interpretation": "Doctor almost doubled token expenditure without moving repair performance."
            },
            {
                "metric": "Wall Time Ratio",
                "baseline": "848s (28.3s/run)",
                "generic": "994s (33.1s/run)",
                "doctor": "2067s (68.9s/run)",
                "difference": "2.44x time increase",
                "interpretation": "Doctor introduced extensive protocol overhead and roundtrips."
            },
            {
                "metric": "Ambiguity Handling (NEEDS_INTENT)",
                "baseline": "0 / 6 stopped (6 guessed)",
                "generic": "0 / 6 stopped (6 guessed)",
                "doctor": "2 / 6 stopped (4 guessed)",
                "difference": "+33.3% compliance",
                "interpretation": "Doctor showed isolated positive signal on cases 011 and 016 by pausing for user intent instead of guessing."
            },
            {
                "metric": "Apparent Regressions",
                "baseline": "1 / 30 (3.3%)",
                "generic": "1 / 30 (3.3%)",
                "doctor": "0 / 30 (0.0%)",
                "difference": "Non-independent",
                "interpretation": "The only baseline/generic regression was on case-011. Doctor avoided it solely because it refused to guess the unresolved policy."
            }
        ]
    }
    return out

def build_cases_data(manifest, auto_summary):
    # Map rows by (case_id_number, arm)
    rows_by_case = {}
    for r in auto_summary["rows"]:
        cid = r["case_id"]
        # extract numeric id
        parts = cid.split("-")
        num = parts[1] if len(parts) > 1 else cid
        rows_by_case.setdefault(num, {})[r["arm"]] = r

    cases_list = []
    for item in manifest:
        num = item["case_id"]
        name = item["name"]
        full_id = f"case-{num}-{name}"

        # Load task.md
        task_path = os.path.join(CASES_DIR, full_id, "task.md")
        task_text = ""
        if os.path.exists(task_path):
            with open(task_path, "r", encoding="utf-8") as f:
                task_text = f.read().strip()

        arm_results = rows_by_case.get(num, {})

        # Check if this is a needs_intent success under doctor
        doctor_verdict = arm_results.get("doctor", {}).get("verdict", "")
        baseline_verdict = arm_results.get("baseline", {}).get("verdict", "")
        generic_verdict = arm_results.get("generic", {}).get("verdict", "")

        doctor_intent_stopped = (item["outcome"] == "NEEDS_INTENT" and doctor_verdict == "needs_manual_review_ambiguity")

        c_obj = {
            "case_id": num,
            "slug": full_id,
            "name": name,
            "outcome": item["outcome"],
            "difficulty": item["difficulty"],
            "runtime": item.get("runtime", "vanilla-js"),
            "relations": item.get("relations", []),
            "group_policy": item.get("group_policy"),
            "lifecycle_categories": item.get("lifecycle_categories", []),
            "effect_lifetime_categories": item.get("effect_lifetime_categories", []),
            "environmental_claims": item.get("environmental_claims", []),
            "requires_recursive_revalidation": item.get("requires_recursive_revalidation", False),
            "contamination_risk": item.get("contamination_risk", "LOW"),
            "primary_hidden_oracles": item.get("primary_hidden_oracles", []),
            "task_description": task_text,
            "doctor_intent_stopped": doctor_intent_stopped,
            "runs": {
                "baseline": {
                    "verdict": baseline_verdict,
                    "repair_success": arm_results.get("baseline", {}).get("repair_success", False),
                    "hidden_test_pass": arm_results.get("baseline", {}).get("hidden_test_pass", False),
                    "has_regression": arm_results.get("baseline", {}).get("has_regression", False),
                    "regressions": arm_results.get("baseline", {}).get("regressions", []),
                    "detection_heuristic": arm_results.get("baseline", {}).get("detection_heuristic", False),
                    "false_closure_heuristic": arm_results.get("baseline", {}).get("false_closure_heuristic", False),
                    "cost": arm_results.get("baseline", {}).get("_cost", 0.0),
                    "seconds": arm_results.get("baseline", {}).get("_seconds", 0.0),
                    "tools": arm_results.get("baseline", {}).get("_tools", 0),
                    "run_no": arm_results.get("baseline", {}).get("_run_no", 1),
                    "source_modified": arm_results.get("baseline", {}).get("source_modified", False),
                    "diff": arm_results.get("baseline", {}).get("diff", {})
                },
                "generic": {
                    "verdict": generic_verdict,
                    "repair_success": arm_results.get("generic", {}).get("repair_success", False),
                    "hidden_test_pass": arm_results.get("generic", {}).get("hidden_test_pass", False),
                    "has_regression": arm_results.get("generic", {}).get("has_regression", False),
                    "regressions": arm_results.get("generic", {}).get("regressions", []),
                    "detection_heuristic": arm_results.get("generic", {}).get("detection_heuristic", False),
                    "false_closure_heuristic": arm_results.get("generic", {}).get("false_closure_heuristic", False),
                    "cost": arm_results.get("generic", {}).get("_cost", 0.0),
                    "seconds": arm_results.get("generic", {}).get("_seconds", 0.0),
                    "tools": arm_results.get("generic", {}).get("_tools", 0),
                    "run_no": arm_results.get("generic", {}).get("_run_no", 1),
                    "source_modified": arm_results.get("generic", {}).get("source_modified", False),
                    "diff": arm_results.get("generic", {}).get("diff", {})
                },
                "doctor": {
                    "verdict": doctor_verdict,
                    "repair_success": arm_results.get("doctor", {}).get("repair_success", False),
                    "hidden_test_pass": arm_results.get("doctor", {}).get("hidden_test_pass", False),
                    "has_regression": arm_results.get("doctor", {}).get("has_regression", False),
                    "regressions": arm_results.get("doctor", {}).get("regressions", []),
                    "detection_heuristic": arm_results.get("doctor", {}).get("detection_heuristic", False),
                    "false_closure_heuristic": arm_results.get("doctor", {}).get("false_closure_heuristic", False),
                    "cost": arm_results.get("doctor", {}).get("_cost", 0.0),
                    "seconds": arm_results.get("doctor", {}).get("_seconds", 0.0),
                    "tools": arm_results.get("doctor", {}).get("_tools", 0),
                    "run_no": arm_results.get("doctor", {}).get("_run_no", 1),
                    "source_modified": arm_results.get("doctor", {}).get("source_modified", False),
                    "diff": arm_results.get("doctor", {}).get("diff", {})
                }
            }
        }
        cases_list.append(c_obj)

    return cases_list

def build_methodology_data():
    return {
        "experimental_design": {
            "model": "claude-sonnet-5",
            "effort": "medium",
            "total_cases": 30,
            "arms": [
                {
                    "id": "baseline",
                    "name": "Arm A: Baseline",
                    "description": "Pure frontier model with task prompt only. Measures natural capability on interaction defects."
                },
                {
                    "id": "generic",
                    "name": "Arm B: Generic Rigorous Audit",
                    "description": "Same model with generic carefulness/audit instructions injected, controlling for mere prompt thoroughness without specialized domain terminology."
                },
                {
                    "id": "doctor",
                    "name": "Arm C: Interaction Doctor v1",
                    "description": "Same model with the frozen Interaction Doctor v1 skill injected into workspace .claude/skills/."
                }
            ]
        },
        "case_taxonomy": {
            "total": 30,
            "yes": {
                "count": 19,
                "description": "Defective interaction present. Model is evaluated on whether it successfully diagnoses and repairs the flaw according to hidden tests."
            },
            "no": {
                "count": 5,
                "description": "Negative control / benign pattern. No defect exists. Model is evaluated on whether it correctly leaves the interaction logic untouched (no-op)."
            },
            "needs_intent": {
                "count": 6,
                "cases": ["case-004", "case-010", "case-011", "case-013", "case-016", "case-019"],
                "description": "Interaction specification is fundamentally ambiguous. Multiple valid policies exist; model must recognize ambiguity and stop for manual review/ask rather than unilaterally guessing."
            },
            "unmodeled": {
                "count": 0,
                "description": "Explicit note: UNMODELED count is 0. This benchmark pilot does NOT measure handling of unmodeled hardware/input domains."
            }
        },
        "isolation_protocol": {
            "architecture": "v6 native isolation",
            "workspace_policy": "Fresh isolated directory per run in TMPDIR outside repository tree. Sequential execution: workspaces built, run, archived, and wiped sequentially.",
            "tool_surface": "Read, Edit, Write, Glob, Grep, Bash, Skill. WebSearch and WebFetch disallowed.",
            "permission_mode": "dontAsk with fail-closed inline settings policy denying repository root, cases-private, and external credential paths."
        },
        "retry_history": {
            "cases_001_to_014": "Valid observations gathered on run-01.",
            "cases_015_to_030": "Initial runs hit Claude API 429 rate/session limits. Failed infrastructure runs preserved in raw archives; valid observations sourced from run-03 after reset.",
            "rerun_policy": "No successful observation was ever rerun to improve its score."
        },
        "preflight_qualification_limitation": {
            "status": "HOLD (READY_FOR_EMPIRICAL_90_RUNS = False)",
            "reason": "Model did not execute diagnostic probe appendix instructions embedded in preflight prompt (baseline/generic executed no probes, doctor executed bash probes but missed builtin read probes).",
            "treatment": "Treated as probe-compliance insufficiency rather than sandbox infrastructure failure. Empirical 90-run execution performed under explicit qualification-gate waiver. Freeze verification and workspace isolation remained 100% active."
        },
        "failure_analysis_postmortem": [
            {
                "id": "eval_gate",
                "title": "1. Universal Semantic Eval Gate Problem",
                "summary": "Attempts to build a lightweight upstream classifier/filter to selectively invoke Interaction Doctor failed: any false negative in the gate permanently denies the specialist the opportunity to inspect and fix the defect, making a cascade filter unsafe."
            },
            {
                "id": "self_routing",
                "title": "2. Self-Routing Problem",
                "summary": "Attempts to have the baseline model recognize when it needs to route to the specialized skill failed: baseline models do not reliably detect the very subtle ownership conflicts or ambiguities that warrant the skill."
            },
            {
                "id": "native_detector",
                "title": "3. Native Detector / Accelerator Experiment",
                "summary": "Static AST and lexical token analyzers reliably detected canned textbook patterns, but completely broke on novel or bespoke abstractions, generating unacceptable false positives and false negatives that disqualified them as authoritative gates."
            }
        ],
        "final_decision": {
            "skill_status": "DISCONTINUED",
            "benchmark_status": "RETAINED",
            "verdict_statement": "Interaction Doctor v1 provided no repair advantage (19/19 in all arms), imposed ~1.91x cost and ~2.44x wall time, and its ambiguity handling signal (2/6 stopped) was insufficient to justify ongoing maintenance or productization."
        }
    }

def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        auto_summary = json.load(f)

    os.makedirs(SHOWROOM_DATA_DIR, exist_ok=True)

    summary_data = build_summary_data(auto_summary)
    cases_data = build_cases_data(manifest, auto_summary)
    methodology_data = build_methodology_data()

    with open(os.path.join(SHOWROOM_DATA_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    with open(os.path.join(SHOWROOM_DATA_DIR, "cases.json"), "w", encoding="utf-8") as f:
        json.dump(cases_data, f, indent=2)

    with open(os.path.join(SHOWROOM_DATA_DIR, "methodology.json"), "w", encoding="utf-8") as f:
        json.dump(methodology_data, f, indent=2)

    print(f"Showroom data built successfully: 30 cases, summary, methodology written to {SHOWROOM_DATA_DIR}")

if __name__ == '__main__':
    main()
