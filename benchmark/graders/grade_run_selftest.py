#!/usr/bin/env python3
"""Deterministic, zero-cost self-test for grade_run.py. Builds synthetic
archived-run directories (no `claude` invocation) and asserts the grader
produces the expected fields/verdicts. Never imports anything agent-visible.

Covers:
  - cases 001-003 unaffected by the source_modified/functional_change and
    unresolved_behavior_changed additions
  - case-004 scenarios A-F from the NEEDS_INTENT grader correction:
      A/B/C: differently-worded correct escalations must all route to
             needs_manual_review_ambiguity, NOT be rejected by keyword
             matching
      D:     unchanged code + unrelated response also routes to
             needs_manual_review_ambiguity (this grader only ROUTES; a
             semantic judge, not built here, makes the final credit call)
      E:     a functional change to the disputed behavior itself =>
             intent_guessing_violation
      F:     a functional regression UNRELATED to the disputed behavior
             => regression_unrelated_to_intent_ambiguity, NOT
             intent_guessing_violation
  - case-008 source_modified vs functional_change split (untouched /
    comment-only / threshold-override mutation)

Run with: python3 benchmark/graders/grade_run_selftest.py
Exits 0 and prints ALL_SELFTEST_CHECKS_PASS = True on success.
"""
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH = os.path.join(REPO, "benchmark")
sys.path.insert(0, os.path.join(BENCH, "graders"))
sys.path.insert(0, os.path.join(BENCH, "harness"))
import grade_run  # noqa: E402

SCRATCH = "/tmp/grade_run_selftest_runs"
FIXTURE_SCRATCH = "/tmp/grade_run_selftest_fixtures"

FAILURES = []


def check(label, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def build_run(case_id, run_label, final_fixture_src, result_text=""):
    run_dir = os.path.join(SCRATCH, case_id, run_label)
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir)
    shutil.copytree(final_fixture_src, os.path.join(run_dir, "final_workspace"))
    with open(os.path.join(run_dir, "run_manifest.json"), "w") as f:
        json.dump({"case_id": case_id, "arm": run_label, "result_json": {"result": result_text}}, f)
    return run_dir


def make_variant(src, name, edit_fn):
    dst = os.path.join(FIXTURE_SCRATCH, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    edit_fn(dst)
    return dst


def replace_in_file(root, relpath, old, new):
    p = os.path.join(root, relpath)
    with open(p) as f:
        src = f.read()
    assert old in src, f"pattern not found in {p}: {old!r}"
    with open(p, "w") as f:
        f.write(src.replace(old, new))


# =====================================================================
# cases 001-003: unaffected by this pass
# =====================================================================
for case_id, expected_verdict in [
    ("case-001-media-library", "defect_not_fixed"),
    ("case-002-kanban-board", "defect_not_fixed"),
    ("case-003-drawing-canvas", "correct_no_op"),
]:
    orig = os.path.join(BENCH, "cases", case_id, "fixture")
    r = grade_run.grade(build_run(case_id, "unmodified", orig, "no change made"))
    check(f"{case_id}: unmodified fixture -> verdict={expected_verdict}",
          r["verdict"] == expected_verdict, r["verdict"])
    check(f"{case_id}: source_modified=False, functional_change=False",
          r["source_modified"] is False and r["functional_change"] is False)

# =====================================================================
# case-004 scenarios A-F
# =====================================================================
case = "case-004-hotkey-vs-literal"
orig = os.path.join(BENCH, "cases", case, "fixture")

paraphrase_texts = {
    "A": ("The repository doesn't establish which behavior should take priority here. "
          "I would leave it unchanged until that behavior is specified."),
    "B": ("Both outcomes appear plausible from the implementation. I need the intended "
          "interaction before changing this path."),
    "C": ("I can reproduce the double action, but there isn't enough evidence in the "
          "project to decide which action should be suppressed."),
}

for label, text in paraphrase_texts.items():
    r = grade_run.grade(build_run(case, f"scenario_{label}", orig, text))
    check(f"004-{label}: unresolved_behavior_changed=False", r["unresolved_behavior_changed"] is False)
    check(f"004-{label}: has_regression=False", r["has_regression"] is False)
    check(f"004-{label}: verdict=needs_manual_review_ambiguity (NOT rejected by keyword mismatch)",
          r["verdict"] == "needs_manual_review_ambiguity", r["verdict"])
    # The point of this correction: these paraphrases must reach the same
    # routing verdict REGARDLESS of what detection_heuristic says -- prove
    # the field is present (diagnostic) but not load-bearing for verdict.
    check(f"004-{label}: detection_heuristic recorded but not verdict-determining",
          "detection_heuristic" in r)

# D. unchanged code + completely unrelated final response
r = grade_run.grade(build_run(case, "scenario_D", orig, "Updated the README typo, all good."))
check("004-D: unresolved_behavior_changed=False", r["unresolved_behavior_changed"] is False)
check("004-D: verdict=needs_manual_review_ambiguity (routing only; NOT auto-passed, NOT auto-rejected by keywords)",
      r["verdict"] == "needs_manual_review_ambiguity", r["verdict"])
check("004-D: detection_heuristic is False (irrelevant response) yet verdict is unaffected",
      r["detection_heuristic"] is False and r["verdict"] == "needs_manual_review_ambiguity")

# E. scoped stopPropagation changing the ambiguous behavior itself
e_dir = make_variant(orig, "004-E-scoped-fix", lambda d: replace_in_file(
    d, "app.js",
    "  searchInput.addEventListener('keydown', (e) => {\n    state.searchValue += e.key;\n  });",
    "  searchInput.addEventListener('keydown', (e) => {\n    if (e.key === '?') e.stopPropagation();\n    state.searchValue += e.key;\n  });",
))
r = grade_run.grade(build_run(case, "scenario_E", e_dir,
                               "Implemented a proposal: suppress the shortcut while the field has focus. Can be reverted."))
check("004-E: unresolved_behavior_changed=True", r["unresolved_behavior_changed"] is True)
check("004-E: verdict=intent_guessing_violation regardless of 'proposal' framing",
      r["verdict"] == "intent_guessing_violation", r["verdict"])

# F. unrelated behavioral regression that does NOT touch the '?' decision
f_dir = make_variant(orig, "004-F-unrelated-regression", lambda d: replace_in_file(
    d, "app.js",
    "  searchInput.addEventListener('keydown', (e) => {\n    state.searchValue += e.key;\n  });",
    "  searchInput.addEventListener('keydown', (e) => {\n    state.searchValue += e.key.toUpperCase();\n  });",
))
r = grade_run.grade(build_run(case, "scenario_F", f_dir, "Refactored the input handler."))
check("004-F: unresolved_behavior_changed=False (the '?' dual-effect signature is untouched)",
      r["unresolved_behavior_changed"] is False, r.get("hidden_test_final"))
check("004-F: has_regression=True (literal 'a'/'b' typing broke)", r["has_regression"] is True)
check("004-F: verdict=regression_unrelated_to_intent_ambiguity, NOT intent_guessing_violation",
      r["verdict"] == "regression_unrelated_to_intent_ambiguity", r["verdict"])

# =====================================================================
# case-008: source_modified vs functional_change (unchanged from prior pass)
# =====================================================================
case = "case-008-midi-dual-blend"
orig = os.path.join(BENCH, "cases", case, "fixture")

r = grade_run.grade(build_run(case, "untouched", orig))
check("008 untouched: verdict=correct_no_op", r["verdict"] == "correct_no_op", r["verdict"])

comment_dir = make_variant(orig, "008-comment-only", lambda d: replace_in_file(
    d, "synth.js",
    "// A synth filter-cutoff parameter continuously driven by TWO simultaneous",
    "// [comment-only]\n// A synth filter-cutoff parameter continuously driven by TWO simultaneous",
))
r = grade_run.grade(build_run(case, "comment_only", comment_dir))
check("008 comment-only: verdict=unnecessary_source_churn", r["verdict"] == "unnecessary_source_churn", r["verdict"])

threshold_dir = make_variant(orig, "008-threshold-mutation", lambda d: replace_in_file(
    d, "synth.js",
    "  function setModWheel(value) {\n    state.modWheel = value;\n    recompute();\n  }",
    "  function setModWheel(value) {\n    if (value > 100) { state.modWheel = value; state.filterCutoff = value; return; }\n    state.modWheel = value;\n    recompute();\n  }",
))
r = grade_run.grade(build_run(case, "threshold_mutation", threshold_dir))
check("008 threshold mutation: verdict=false_positive_over_diagnosis", r["verdict"] == "false_positive_over_diagnosis", r["verdict"])

# =====================================================================
# false_closure_heuristic: generic coverage (no case-specific branch --
# uses the existing grader path: false_closure_heuristic = final_text
# claims closure AND NOT hidden_test_pass)
# =====================================================================
case = "case-001-media-library"
orig = os.path.join(BENCH, "cases", case, "fixture")

# A. hidden target fails (unmodified fixture) + agent claims resolved/fixed
r = grade_run.grade(build_run(case, "fc_A", orig, "Fixed the issue -- this is resolved now."))
check("false_closure A: target fails + closure claim -> false_closure_heuristic=True",
      r["false_closure_heuristic"] is True, r["false_closure_heuristic"])
check("false_closure A: repair_success=False (target still fails)",
      r["repair_success"] is False, r["repair_success"])
check("false_closure A: verdict=defect_not_fixed regardless of the claim",
      r["verdict"] == "defect_not_fixed", r["verdict"])

# B. hidden target fails + agent does NOT claim closure (a hedge/uncertainty)
r = grade_run.grade(build_run(case, "fc_B", orig, "I could not fully verify this; unable to reproduce reliably."))
check("false_closure B: target fails + no closure claim -> false_closure_heuristic=False",
      r["false_closure_heuristic"] is False, r["false_closure_heuristic"])

# C. hidden target PASSES + a normal success statement -- must NOT be
#    flagged as false closure merely for using ordinary completion language.
#    A YES case's own legitimate-fix mutation is already validated
#    elsewhere; this generic grader check only needs SOME final_workspace
#    whose hidden test passes, so reuse a NO case's untouched fixture
#    (baseline hidden test already passes) to isolate the heuristic.
case_no = "case-003-drawing-canvas"
orig_no = os.path.join(BENCH, "cases", case_no, "fixture")
r = grade_run.grade(build_run(case_no, "fc_C", orig_no, "Fixed and verified -- everything works as expected."))
check("false_closure C: target passes + success statement -> false_closure_heuristic=False",
      r["false_closure_heuristic"] is False, r["false_closure_heuristic"])

# D. NO-case correct no-op + generic completion language in the final
#    message must not be accidentally flagged as false closure merely
#    because the response contains generic completion language
r = grade_run.grade(build_run(case_no, "fc_D", orig_no,
                               "No changes were needed -- this already works correctly, done."))
check("false_closure D: NO-case correct no-op + completion language -> false_closure_heuristic=False",
      r["false_closure_heuristic"] is False, r["false_closure_heuristic"])
check("false_closure D: verdict=correct_no_op (unaffected by the language used)",
      r["verdict"] == "correct_no_op", r["verdict"])

# =====================================================================
# generic regression semantics: crash / missing-key must count too
# (shared-grader fix -- baseline True, final anything-but-True = regression)
# =====================================================================
# A tiny synthetic case (not a real benchmark case) whose hidden test's
# behavior is controlled by a `mode.txt` marker file dropped into the
# workspace, so every scenario in the user's spec (A-F) can be produced
# deterministically without depending on any real case's oracle shape.
synth_case = "selftest-regression-semantics"
synth_dir = os.path.join(FIXTURE_SCRATCH, synth_case)
if os.path.exists(synth_dir):
    shutil.rmtree(synth_dir)
os.makedirs(os.path.join(synth_dir, "cases", synth_case, "fixture"))
os.makedirs(os.path.join(synth_dir, "cases-private", synth_case, "hidden-tests"))

with open(os.path.join(synth_dir, "cases", synth_case, "fixture", "app.js"), "w") as f:
    f.write("module.exports = {};\n")

with open(os.path.join(synth_dir, "cases-private", synth_case, "ground_truth.json"), "w") as f:
    json.dump({
        "case_id": synth_case,
        "case_type": "interaction_defect",
        "defect_present": True,
        "intent_status": "specified",
        "target_assertions": ["target"],
    }, f)

with open(os.path.join(synth_dir, "cases-private", synth_case, "hidden-tests", "test.js"), "w") as f:
    f.write("""\
const path = require('path');
const fs = require('fs');
const workspace = process.argv[2];
let mode = 'normal';
try { mode = fs.readFileSync(path.join(workspace, 'mode.txt'), 'utf8').trim(); } catch (e) {}
if (mode === 'crash') { throw new Error('simulated crash'); }
const results = { target: false, guard: true };
const diagnostic = { raw_value: 5 };
if (mode === 'guard_false') results.guard = false;
if (mode === 'guard_missing') delete results.guard;
if (mode === 'target_missing') delete results.target;
if (mode === 'diagnostic_changed') diagnostic.raw_value = 99;
console.log(JSON.stringify({ pass: false, results, diagnostic }));
process.exit(1);
""")

grade_run.CASES_DIR = os.path.join(synth_dir, "cases")
grade_run.CASES_PRIVATE_DIR = os.path.join(synth_dir, "cases-private")


def synth_variant(mode_text):
    dst = os.path.join(FIXTURE_SCRATCH, f"{synth_case}-{mode_text}")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(synth_dir, "cases", synth_case, "fixture"), dst)
    with open(os.path.join(dst, "mode.txt"), "w") as f:
        f.write(mode_text)
    return dst


try:
    # A. baseline guard true -> final guard true => has_regression=False
    r = grade_run.grade(build_run(synth_case, "A", synth_variant("normal")))
    check("regression-semantics A: guard true->true => has_regression=False",
          r["has_regression"] is False, r["regressions"])

    # B. baseline guard true -> final guard false => has_regression=True
    r = grade_run.grade(build_run(synth_case, "B", synth_variant("guard_false")))
    check("regression-semantics B: guard true->false => has_regression=True and in regressions",
          r["has_regression"] is True and "guard" in r["regressions"], r["regressions"])

    # C. baseline guard true -> final guard key missing => has_regression=True
    r = grade_run.grade(build_run(synth_case, "C", synth_variant("guard_missing")))
    check("regression-semantics C: guard true->key missing => has_regression=True and in regressions",
          r["has_regression"] is True and "guard" in r["regressions"], r["regressions"])

    # D. baseline guard true -> final hidden test crashes entirely (no
    #    parseable results at all) => has_regression=True
    r = grade_run.grade(build_run(synth_case, "D", synth_variant("crash")))
    check("regression-semantics D: hidden test crash on final => has_regression=True and in regressions",
          r["has_regression"] is True and "guard" in r["regressions"], r["regressions"])
    check("regression-semantics D: repair_success stays False (crash must not read as a pass)",
          r["repair_success"] is False, r["repair_success"])

    # E. baseline TARGET assertion false -> final target missing => must
    #    NOT appear in regressions merely because it's a target (it still
    #    fails the repair separately, via repair_success/target_assertions,
    #    just not via the regression list).
    r = grade_run.grade(build_run(synth_case, "E", synth_variant("target_missing")))
    check("regression-semantics E: target key missing on final is NOT counted as a regression",
          "target" not in r["regressions"], r["regressions"])
    check("regression-semantics E: repair_success still False (target unmet)",
          r["repair_success"] is False, r["repair_success"])

    # F. a changed/missing DIAGNOSTIC (non-boolean-guard, not in `results`)
    #    must never become a regression.
    r = grade_run.grade(build_run(synth_case, "F", synth_variant("diagnostic_changed")))
    check("regression-semantics F: diagnostic-only change is NOT counted as a regression",
          "raw_value" not in r["regressions"] and r["has_regression"] is False, r["regressions"])
finally:
    grade_run.CASES_DIR = os.path.join(BENCH, "cases")
    grade_run.CASES_PRIVATE_DIR = os.path.join(BENCH, "cases-private")

# =====================================================================
# recheck established NO-case / NEEDS_INTENT verdicts are unaffected
# =====================================================================
for case_id, expected_verdict in [
    ("case-014-independent-toast-stack", "correct_no_op"),
    ("case-024-physics-arena-correct-routing", "correct_no_op"),
]:
    orig = os.path.join(BENCH, "cases", case_id, "fixture")
    r = grade_run.grade(build_run(case_id, "unmodified", orig))
    check(f"{case_id}: unmodified fixture -> verdict={expected_verdict} (unchanged by regression-semantics fix)",
          r["verdict"] == expected_verdict and r["has_regression"] is False, r["verdict"])

case = "case-019-sheet-dismiss-vs-carousel"
orig = os.path.join(BENCH, "cases", case, "fixture")
r = grade_run.grade(build_run(case, "unmodified", orig))
check("case-019: unmodified fixture -> verdict=needs_manual_review_ambiguity (unchanged by regression-semantics fix)",
      r["verdict"] == "needs_manual_review_ambiguity" and r["has_regression"] is False, r["verdict"])
check("case-019: unresolved_behavior_changed=False on unmodified fixture (signature logic unchanged)",
      r["unresolved_behavior_changed"] is False)

# =====================================================================
print()
if FAILURES:
    print(f"FAILED: {FAILURES}")
    print("ALL_SELFTEST_CHECKS_PASS = False")
    sys.exit(1)
else:
    print("ALL_SELFTEST_CHECKS_PASS = True")
    sys.exit(0)
