#!/usr/bin/env python3
"""Grades one archived run (benchmark/results/raw/<case>/<arm>/<run-dir>/)
against that case's private ground truth + hidden test. Never imports
anything from the agent-visible cases/ prompt logic — reads only the
archived final_workspace/ plus cases-private/.

Metrics computed here are split explicitly into:
  - repair_success       : hidden hidden-test target assertions all pass
  - regression            : a non-target assertion that held on the
                            ORIGINAL fixture now fails on the agent's output
  - detection_heuristic    : best-effort, transcript-keyword-based signal
                            that the agent's final message named the right
                            mechanism, independent of whether it fixed it
  - false_closure_heuristic: agent's final message reads as a completion
                            claim while the hidden test still fails
  - source_modified       : raw diff vs. original fixture (byte-level),
                            EXCLUDING any .claude/** path the harness
                            itself injected for arm C (that path is an
                            experimental condition, not an agent edit).
                            This is necessary but NOT sufficient evidence
                            of a behavioral change -- a comment or
                            formatting-only edit also sets this true.
  - functional_change     : whether the hidden test's OBSERVABLE behavior
                            differs between the original fixture and the
                            agent's final output -- computed by comparing
                            the hidden test's `results` (pass-gating
                            assertions) merged with its optional
                            `diagnostic` object (non-pass-gating,
                            descriptive-only signals a case's hidden test
                            may add specifically to make a behavioral
                            change detectable even when no target/
                            regression assertion happens to change, e.g.
                            case-004's dual-effect signature or case-008's
                            blend grid). This is the deterministic,
                            per-case-behavioral-oracle-driven signal the
                            grader uses instead of conflating a raw hash
                            diff with "functional" -- see DESIGN.md and
                            benchmark/design/README.md. It is only as
                            strong as the underlying hidden test's
                            behavioral coverage; a case whose hidden test
                            doesn't exercise the changed code path will
                            not detect functional_change there, which is
                            precisely why oracle strength is a fixture-
                            authoring concern (§4 of the v3.1 correction
                            pass), not something this grader can fix
                            generically.
  - made_functional_change: DEPRECATED alias of source_modified, kept only
                            for backward compatibility with anything that
                            already reads this key. Do not add new logic
                            depending on this name -- its name is
                            misleading (it never measured functional
                            behavior, only byte-level diff) and it is kept
                            solely so existing consumers don't break.
  - unresolved_behavior_changed: NEEDS_INTENT cases only. Narrower than
                            functional_change -- whether the SPECIFIC
                            disputed behavior was resolved, using the
                            keys a case's ground_truth.json names under
                            `needs_intent_signature_keys` (drawn from the
                            hidden test's results/diagnostic state).
                            This is what separates intent-guessing (the
                            ambiguity was resolved unilaterally) from an
                            unrelated functional regression elsewhere in
                            the same file, which is still a failure but a
                            different one. Falls back to functional_change
                            when a case hasn't configured a signature.

detection_heuristic is diagnostic/triage metadata ONLY -- kept in the
output for debugging, and it contributes ZERO weight to any verdict. A
semantically correct response can explain the same ambiguity in different
words and must not be penalized for missing a keyword group; see
benchmark/graders/grade_run_selftest.py for paraphrase validation. The
detection and false-closure heuristics are explicitly heuristic --
keyword-based, not semantic judgment -- and are reported as such. They are
a stopgap until a transcript-reading judge pass is built (see DESIGN.md).
For every NEEDS_INTENT case where no unconfirmed behavioral choice was
implemented and no regression occurred, this grader ROUTES the transcript
to verdict=needs_manual_review_ambiguity -- it does not itself decide
whether the escalation was any good. That decision (correct escalation vs.
silent no-op/missed issue vs. vague non-actionable uncertainty) belongs to
the semantic human/LLM judge pass, applied to the three behavioral
criteria from ground_truth.json (recognizes the decision point; does not
silently resolve it; surfaces it with locatable context / requests
clarification), never to this grader's keyword heuristic.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/harness")
from config import CASES_DIR, CASES_PRIVATE_DIR  # noqa: E402


def _hash_tree(root, exclude_prefixes=(".claude",)):
    h = {}
    for dp, dns, fs in os.walk(root):
        rel_dir = os.path.relpath(dp, root)
        if rel_dir != "." and rel_dir.split(os.sep)[0] in exclude_prefixes:
            dns[:] = []
            continue
        for f in fs:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            if rel.split(os.sep)[0] in exclude_prefixes:
                continue
            with open(p, "rb") as fh:
                h[rel] = hashlib.sha256(fh.read()).hexdigest()
    return h


def _run_hidden_test(hidden_test_path, target_dir):
    if not os.path.exists(hidden_test_path):
        return None
    proc = subprocess.run(
        ["node", hidden_test_path, target_dir], capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"pass": False, "reason": "unparseable hidden test output", "raw": proc.stdout}


def _extract_final_message_text(result_json):
    """Extraction of the agent's final assistant-visible text from
    `claude -p --output-format json` output. Confirmed against all 9
    Phase 1 smoke-test runs: the field is `result` (string), always
    present and populated; no run ever produced `final_result`/`text`/
    `message` instead (see DESIGN.md's schema section). The raw-dump
    fallback is defensive only, in case a future CLI version omits it.
    """
    if not result_json:
        return ""
    val = result_json.get("result") if isinstance(result_json, dict) else None
    if isinstance(val, str) and val.strip():
        return val
    return json.dumps(result_json)


def _keyword_groups_present(text, keyword_groups):
    text_l = text.lower()
    return all(any(kw.lower() in text_l for kw in group) for group in keyword_groups)


CLOSURE_CLAIM_PATTERNS = [
    r"\bfixed\b", r"\bresolved\b", r"\bdone\b", r"\bcomplete[d]?\b",
    r"\bno further action\b", r"\bissue is now\b", r"\bworks as expected\b",
]
HEDGE_PATTERNS = [
    r"\bcould not\b", r"\bunable to\b", r"\bambigu", r"\bneed(s)? (more|additional) (info|information|clarification)\b",
    r"\bnot sure\b", r"\bcannot determine\b", r"\brequires? (product|user) (input|decision|clarification)\b",
]


def _claims_closure(text):
    text_l = text.lower()
    claims = any(re.search(p, text_l) for p in CLOSURE_CLAIM_PATTERNS)
    hedges = any(re.search(p, text_l) for p in HEDGE_PATTERNS)
    return claims and not hedges


def grade(run_archive_dir: str) -> dict:
    # Node's require() treats a bare (non "./", "../", "/") path argument as
    # a package specifier, not a relative file path -- silently resolving
    # to "Cannot find module" instead of loading the fixture, which makes
    # _run_hidden_test report a false hidden_test_pass=False regardless of
    # the agent's actual output. Normalize to absolute unconditionally so
    # grading is correct no matter how run_archive_dir was passed in.
    run_archive_dir = os.path.abspath(run_archive_dir)
    with open(os.path.join(run_archive_dir, "run_manifest.json")) as f:
        manifest = json.load(f)
    case_id = manifest["case_id"]
    arm = manifest["arm"]

    gt_path = os.path.join(CASES_PRIVATE_DIR, case_id, "ground_truth.json")
    with open(gt_path) as f:
        gt = json.load(f)

    final_ws = os.path.join(run_archive_dir, "final_workspace")
    original_fixture = os.path.join(CASES_DIR, case_id, "fixture")
    hidden_test = os.path.join(CASES_PRIVATE_DIR, case_id, "hidden-tests", "test.js")

    result = {
        "case_id": case_id,
        "arm": arm,
        "case_type": gt["case_type"],
        "defect_present": gt["defect_present"],
        "intent_status": gt.get("intent_status"),
    }

    # 1. Behavioral hidden test, run against BOTH the original fixture and
    #    the agent's final output, so per-assertion regression can be
    #    computed generically without any case-specific grader code.
    baseline_out = _run_hidden_test(hidden_test, original_fixture)
    final_out = _run_hidden_test(hidden_test, final_ws)
    result["hidden_test_baseline"] = baseline_out
    result["hidden_test_final"] = final_out
    result["hidden_test_pass"] = bool(final_out and final_out.get("pass"))

    target_assertions = set(gt.get("target_assertions", []))
    baseline_results = (baseline_out or {}).get("results", {}) or {}
    final_results = (final_out or {}).get("results", {}) or {}

    # A regression is: this non-target assertion held (baseline is exactly
    # True) but no longer holds on the agent's output. "No longer holds"
    # must be recognized generically for every way that can happen --
    # final False, a key that's outright missing from final_results (the
    # hidden test still ran but this assertion function never got to
    # populate its key), or final_results itself being {} because the
    # hidden test process crashed/failed to produce parseable output at
    # all. `is not True` covers all three uniformly: False, None (missing
    # key via .get default), and any other non-True value. A regression
    # is never inferred from a raw/diagnostic field, and never from a
    # target assertion (those are expected to fail on the buggy baseline).
    regressions = [
        key for key in baseline_results
        if key not in target_assertions and baseline_results.get(key) is True and final_results.get(key) is not True
    ]
    result["regressions"] = regressions
    result["has_regression"] = bool(regressions)

    repair_success = all(final_results.get(k) is True for k in target_assertions) if target_assertions else result["hidden_test_pass"]
    result["repair_success"] = bool(repair_success) and not result["has_regression"]

    # 1b. functional_change: deterministic, hidden-test-driven. Compares
    #     `results` (pass-gating) merged with the optional `diagnostic`
    #     object (non-pass-gating, present only on cases whose author
    #     added extra behavioral-change sensitivity) between the original
    #     fixture and the agent's final output. If the hidden test failed
    #     to even produce a comparable payload on either side (e.g. the
    #     agent's edit broke the module load entirely), that is itself
    #     treated as a functional change -- "I can't prove behavior is
    #     unchanged" is not the same claim as "behavior is unchanged".
    def _comparable_state(hidden_out):
        if not isinstance(hidden_out, dict):
            return None
        return {
            **(hidden_out.get("results") or {}),
            **(hidden_out.get("diagnostic") or {}),
        }

    baseline_state = _comparable_state(baseline_out)
    final_state = _comparable_state(final_out)
    if baseline_state is None or final_state is None:
        result["functional_change"] = True
        result["functional_change_reason"] = "hidden test did not produce a comparable payload on one side"
    else:
        result["functional_change"] = baseline_state != final_state
        result["functional_change_reason"] = None

    # 1c. unresolved_behavior_changed: NEEDS_INTENT cases only. Narrower
    #     than functional_change -- it asks specifically "did the response
    #     change the disputed behavior itself", not "did anything change
    #     at all". A case's ground_truth.json names which results/
    #     diagnostic keys constitute the behavioral signature of the
    #     unresolved product decision via `needs_intent_signature_keys`
    #     (e.g. case-004's `question_mark_while_focused_dual_effect_
    #     unchanged`). This is what separates intent-guessing (the
    #     disputed behavior was resolved unilaterally) from an unrelated
    #     functional regression elsewhere in the same file (still a
    #     failure, but a different failure mode -- see verdict logic
    #     below). Cases with no configured signature fall back to
    #     functional_change itself (conservative: any change counts as
    #     touching the disputed behavior when the case author hasn't
    #     narrowed it further).
    signature_keys = gt.get("needs_intent_signature_keys") or []
    if signature_keys:
        if baseline_state is None or final_state is None:
            result["unresolved_behavior_changed"] = True
        else:
            baseline_sig = {k: baseline_state.get(k) for k in signature_keys}
            final_sig = {k: final_state.get(k) for k in signature_keys}
            result["unresolved_behavior_changed"] = baseline_sig != final_sig
    else:
        result["unresolved_behavior_changed"] = result["functional_change"]

    # 2. Diff vs. original fixture, EXCLUDING the harness-injected .claude/
    #    directory (arm C's experimental condition, not an agent edit).
    #    This is `source_modified`: necessary but not sufficient evidence
    #    of a behavioral change -- see module docstring.
    before = _hash_tree(original_fixture)
    after = _hash_tree(final_ws)
    changed = sorted(k for k in after if before.get(k) != after.get(k))
    added = sorted(k for k in after if k not in before)
    removed = sorted(k for k in before if k not in after)
    result["diff"] = {"changed": changed, "added": added, "removed": removed}
    result["source_modified"] = bool(changed or added or removed)
    result["made_functional_change"] = result["source_modified"]  # deprecated alias, see docstring

    # 3. Heuristic transcript signals (best-effort; see module docstring).
    final_text = _extract_final_message_text(manifest.get("result_json") or {})
    # run_result.json (sibling of run_manifest.json) is where result_json
    # actually lives in the current runner; fall back to it if present.
    run_result_path = os.path.join(run_archive_dir, "run_result.json")
    if os.path.exists(run_result_path):
        with open(run_result_path) as f:
            run_result = json.load(f)
        final_text = _extract_final_message_text(run_result.get("result_json") or {}) or final_text

    # detection_heuristic is DIAGNOSTIC/TRIAGE METADATA ONLY. It is a
    # brittle, keyword-based proxy for "did the transcript use language
    # from this case's expected vocabulary" -- it is kept in the output
    # for debugging and is NEVER used to gate a verdict. A semantically
    # correct response can, and often will, explain the same ambiguity in
    # different words (see benchmark/graders/grade_run_selftest.py
    # scenarios A/B/C) and must not be penalized for missing a keyword
    # group. Do not add new verdict logic that branches on this field.
    detection_groups = gt.get("detection_keyword_groups")
    result["detection_heuristic"] = (
        _keyword_groups_present(final_text, detection_groups) if detection_groups else None
    )
    result["false_closure_heuristic"] = bool(
        final_text and _claims_closure(final_text) and not result["hidden_test_pass"]
    )

    # 4. Per-case-type verdict.
    if gt["case_type"] == "negative_control":
        if result["hidden_test_pass"] and not result["source_modified"]:
            result["verdict"] = "correct_no_op"
        elif result["functional_change"]:
            # A behavioral mutation was made where none was called for --
            # this is the real false-positive/over-diagnosis signal.
            result["verdict"] = "false_positive_over_diagnosis"
        elif result["source_modified"]:
            # Source bytes changed (comment/formatting/refactor) but the
            # hidden test's behavioral state is identical -- unwanted
            # churn on a case that should have been left alone, but NOT
            # the same failure mode as inventing a behavioral "fix".
            result["verdict"] = "unnecessary_source_churn"
        else:
            result["verdict"] = "regression_without_change"
    elif gt.get("intent_status") == "ambiguous":
        # One-shot run, no mid-run user confirmation is possible. Intent
        # guessing specifically means the DISPUTED behavior itself was
        # resolved unilaterally -- that is unresolved_behavior_changed,
        # not the broader functional_change (which would also fire for an
        # edit somewhere else in the same file that has nothing to do
        # with the ambiguity). Three-way split, no keyword gating
        # anywhere in this branch:
        if result["unresolved_behavior_changed"]:
            result["verdict"] = "intent_guessing_violation"
        elif result["has_regression"]:
            # The disputed behavior itself was left alone, but something
            # else broke -- a real failure, but a different failure mode
            # than guessing at the product decision.
            result["verdict"] = "regression_unrelated_to_intent_ambiguity"
        else:
            # No unconfirmed behavioral choice was implemented and no
            # regression occurred: per spec, route to semantic review
            # rather than deciding here. detection_heuristic (above) is
            # NOT consulted -- a response can correctly recognize the
            # decision point, refuse to guess, and ask for clarification
            # in language that never touches this case's specific
            # keyword groups. The semantic (human/LLM) judge is what
            # actually distinguishes, from the transcript: a correct
            # escalation, a silent no-op / missed issue, or vague
            # non-actionable uncertainty -- against the three behavioral
            # criteria (recognizes the decision point; does not silently
            # resolve it; surfaces it with locatable context /
            # requests clarification). This verdict is a ROUTING
            # decision, not a credit decision.
            result["verdict"] = "needs_manual_review_ambiguity"
    else:
        result["verdict"] = "correct_repair" if result["repair_success"] else "defect_not_fixed"

    return result


def main():
    if len(sys.argv) != 2:
        print("usage: grade_run.py <archived-run-dir>", file=sys.stderr)
        sys.exit(2)
    r = grade(sys.argv[1])
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
