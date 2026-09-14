#!/usr/bin/env python3
"""Trusted, frozen, harness-side grading GATE for the 90-row empirical
result table -- WITHOUT modifying graders/grade_run.py (protected
scientific content, byte-identical to commit a4fdfe3, never touched here).

Two concrete failures this module closes (see module docstrings elsewhere
for the broader v6 correction history):

  A. grade_run.py's hidden-test subprocess calls plain `["node", ...]`,
     resolved via whatever PATH the calling process happens to have. A
     zero-cost selftest proving "PATH happens to resolve to the frozen
     Node right now" does not force GRADING LATER to use the same
     interpreter. This module forces PATH, for the duration of the grade
     call only, to resolve `node` to EXACTLY config.FROZEN_NODE_EXECUTABLE_REALPATH
     -- verified immediately before every hidden-test execution, not
     merely at selftest time.

  B. An archived run whose harness execution itself failed (timeout,
     nonzero exit, missing event data) is NOT a model behavioral
     observation. Reproduced directly: a real archived run with
     status="nonzero_exit", returncode=1, event_count=0, passed straight
     to grade_run.grade(), received an ordinary verdict
     ("defect_not_fixed") -- indistinguishable from a genuine behavioral
     miss. classify_run_for_grading() below refuses to hand such an
     archive to grade_run.grade() at all; it is reported as a distinct
     infrastructure/identity rejection instead.

This module also distinguishes the future 90 fresh empirical observations
(exactly one valid, current-provenance run per case x arm) from historical
smoke/diagnostic archives already present under results/raw/ -- those
predate this instrument's provenance fields entirely and are excluded by
the same provenance check, not by any special-cased path/date logic.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graders"))

import config
import runner
from verify_experiment_freeze import verify_freeze

REJECTED_INFRASTRUCTURE_FAILURE = "REJECTED_INFRASTRUCTURE_FAILURE"
REJECTED_IDENTITY_MISMATCH = "REJECTED_IDENTITY_MISMATCH"
GRADED = "GRADED"

# The provenance fields an archived run_result.json must match EXACTLY
# against the current expected empirical execution identity before its
# hidden-test evidence is trusted as a genuine behavioral observation.
REQUIRED_PROVENANCE_FIELDS = (
    "git_commit_sha", "experiment_freeze_file_sha256", "claude_cli_version",
    "claude_launcher_path", "claude_executable_realpath", "claude_executable_sha256",
    "active_sandbox_architecture", "custom_outer_sandbox_active", "model", "effort",
)


def current_expected_empirical_identity():
    """The CURRENT expected execution identity for a genuine empirical
    observation -- computed fresh at grading time from config.py/git
    (grading happens strictly after execution, so unlike the preflight's
    pre-captured identity, there is no earlier snapshot to thread
    through; this IS the authoritative reference, exactly what
    verify_freeze() and runner.py themselves would compute right now)."""
    freeze_path = os.path.join(config.BENCHMARK_ROOT, "design", config.EXPERIMENT_FREEZE_FILENAME)
    freeze_hash = None
    if os.path.exists(freeze_path):
        with open(freeze_path, "rb") as f:
            freeze_hash = hashlib.sha256(f.read()).hexdigest()
    return {
        "git_commit_sha": runner._git_commit_sha(),
        "experiment_freeze_file_sha256": freeze_hash,
        "claude_cli_version": config.FROZEN_CLAUDE_CLI_VERSION,
        "claude_launcher_path": config.CLAUDE_LAUNCHER_PATH,
        "claude_executable_realpath": config.FROZEN_CLAUDE_EXECUTABLE_REALPATH,
        "claude_executable_sha256": config.FROZEN_CLAUDE_EXECUTABLE_SHA256,
        "active_sandbox_architecture": config.ACTIVE_SANDBOX_ARCHITECTURE,
        "custom_outer_sandbox_active": config.CUSTOM_OUTER_SANDBOX_ACTIVE,
        "model": config.MODEL,
        "effort": config.EFFORT,
    }


def verify_frozen_node_identity():
    """Verified immediately before hidden-test execution (not merely at
    selftest time): the frozen Node realpath/version/SHA-256, re-read live
    from disk, matches config's frozen values. Returns (ok, violations)."""
    violations = []
    if not os.path.exists(config.FROZEN_NODE_EXECUTABLE_REALPATH):
        violations.append(f"frozen Node executable missing: {config.FROZEN_NODE_EXECUTABLE_REALPATH}")
        return False, violations
    import subprocess
    actual_version = subprocess.run(
        [config.FROZEN_NODE_EXECUTABLE_REALPATH, "--version"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    if actual_version != config.FROZEN_NODE_VERSION:
        violations.append(f"Node version drift: expected {config.FROZEN_NODE_VERSION!r}, "
                           f"actual {actual_version!r}")
    return (len(violations) == 0), violations


def _force_frozen_node_path(base_env):
    """Returns a NEW env dict (never mutates base_env) whose PATH is
    prefixed with a fresh directory containing ONLY a `node` symlink
    pointing at the exact frozen Node executable. grade_run.py's own
    `["node", ...]` subprocess calls -- unmodified, protected code --
    resolve "node" via this forced PATH when this env is applied to the
    calling process before grade_run.grade() runs, since grade_run.py's
    subprocess.run(["node", ...]) inherits its caller's environment."""
    node_bin_dir = tempfile.mkdtemp(prefix="idbench-frozen-node-")
    link_path = os.path.join(node_bin_dir, "node")
    os.symlink(config.FROZEN_NODE_EXECUTABLE_REALPATH, link_path)
    env = dict(base_env)
    env["PATH"] = node_bin_dir + os.pathsep + env.get("PATH", "")
    return env, node_bin_dir


def _provenance_mismatches(record, expected):
    mismatches = []
    for field in REQUIRED_PROVENANCE_FIELDS:
        if record.get(field) != expected.get(field):
            mismatches.append(f"{field}: expected={expected.get(field)!r} actual={record.get(field)!r}")
    return mismatches


def _runtime_model_identity_ok(record):
    """Best-effort check of the runtime model identity actually observed
    in this run's own archived evidence (system/init model field and/or
    result.modelUsage[...].canonicalModel), against
    config.FROZEN_CANONICAL_MODEL. Returns (ok, detail). Missing evidence
    is NOT ok -- a genuine empirical observation must have EVENT_LOG_MODE
    evidence available (config.EVENT_LOG_MODE is True for every real run)."""
    result_json = record.get("result_json") or {}
    model_usage = result_json.get("modelUsage") or {}
    entry = model_usage.get(config.MODEL)
    if not entry:
        return False, f"no modelUsage entry for {config.MODEL!r} in this run's result_json"
    canonical = entry.get("canonicalModel")
    if canonical != config.FROZEN_CANONICAL_MODEL:
        return False, (f"canonicalModel mismatch: expected {config.FROZEN_CANONICAL_MODEL!r}, "
                        f"actual {canonical!r}")
    return True, None


def classify_run_for_grading(run_archive_dir: str, expected_identity: dict = None):
    """Reads run_result.json from an archived run directory and decides
    whether it may be handed to grade_run.grade() as a genuine behavioral
    observation. Returns (classification, reasons) where classification
    is one of GRADED / REJECTED_INFRASTRUCTURE_FAILURE /
    REJECTED_IDENTITY_MISMATCH. Never calls grade_run.grade() itself."""
    if expected_identity is None:
        expected_identity = current_expected_empirical_identity()

    result_path = os.path.join(run_archive_dir, "run_result.json")
    if not os.path.exists(result_path):
        return REJECTED_INFRASTRUCTURE_FAILURE, ["run_result.json missing from archive"]
    try:
        with open(result_path) as f:
            record = json.load(f)
    except json.JSONDecodeError as e:
        return REJECTED_INFRASTRUCTURE_FAILURE, [f"run_result.json unparseable: {e}"]

    reasons = []
    if record.get("status") != "completed":
        reasons.append(f"status != 'completed' (actual: {record.get('status')!r})")
    if record.get("returncode") != 0:
        reasons.append(f"returncode != 0 (actual: {record.get('returncode')!r})")
    if reasons:
        return REJECTED_INFRASTRUCTURE_FAILURE, reasons

    mismatches = _provenance_mismatches(record, expected_identity)
    if mismatches:
        return REJECTED_IDENTITY_MISMATCH, mismatches

    model_ok, model_detail = _runtime_model_identity_ok(record)
    if not model_ok:
        return REJECTED_IDENTITY_MISMATCH, [model_detail]

    return GRADED, []


def grade_one(run_archive_dir: str, expected_identity: dict = None) -> dict:
    """The full trusted gate for one archived run: freeze verification,
    frozen-Node verification, classification, and (only if accepted)
    grading via the UNMODIFIED grade_run.grade(), executed with PATH
    forced to the exact frozen Node. Always returns a dict with
    'grading_status' set to GRADED or a rejection classification --
    rejected rows never carry a 'verdict' field at all, so they can never
    be silently mistaken for defect_not_fixed/correct_no_op/etc."""
    freeze_ok, freeze_violations = verify_freeze()
    if not freeze_ok:
        return {"grading_status": REJECTED_INFRASTRUCTURE_FAILURE,
                "reasons": [f"experiment freeze verification failed: {v}" for v in freeze_violations]}

    node_ok, node_violations = verify_frozen_node_identity()
    if not node_ok:
        return {"grading_status": REJECTED_INFRASTRUCTURE_FAILURE, "reasons": node_violations}

    classification, reasons = classify_run_for_grading(run_archive_dir, expected_identity)
    if classification != GRADED:
        return {"grading_status": classification, "reasons": reasons, "run_archive_dir": run_archive_dir}

    import grade_run  # protected, unmodified -- imported here, not at module load,
                       # so every other function in this module stays usable even
                       # if graders/** is ever absent from a given checkout.

    forced_env, tmp_node_dir = _force_frozen_node_path(os.environ)
    old_environ = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update(forced_env)
        actual_node = shutil.which("node")
        if actual_node is None or os.path.realpath(actual_node) != config.FROZEN_NODE_EXECUTABLE_REALPATH:
            return {"grading_status": REJECTED_INFRASTRUCTURE_FAILURE,
                    "reasons": [f"failed to force PATH to the frozen Node "
                                f"(resolved: {actual_node!r})"]}
        result = grade_run.grade(run_archive_dir)
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
        shutil.rmtree(tmp_node_dir, ignore_errors=True)

    result["grading_status"] = GRADED
    return result


def discover_valid_current_observations():
    """For every (case, arm), finds every archived run under
    results/raw/<case>/<arm>/run-*/ whose provenance matches the CURRENT
    expected empirical identity, status=='completed', returncode==0, and
    runtime model identity checks out. Historical smoke/diagnostic
    archives (which predate these provenance fields entirely, or were run
    under a different git commit/freeze/launcher) are excluded by this
    same check -- no special-cased path or date logic needed. Returns
    {(case_id, arm): [archive_dir, ...]} -- callers must treat more than
    one entry per (case, arm) as a batch-blocking duplicate, and zero
    entries as a missing observation, never silently picking one."""
    expected_identity = current_expected_empirical_identity()
    raw_root = os.path.join(config.BENCHMARK_ROOT, "results", "raw")
    found = {}
    if not os.path.isdir(raw_root):
        return found
    for case_id in sorted(os.listdir(raw_root)):
        case_dir = os.path.join(raw_root, case_id)
        if not os.path.isdir(case_dir):
            continue
        for arm in sorted(os.listdir(case_dir)):
            arm_dir = os.path.join(case_dir, arm)
            if not os.path.isdir(arm_dir):
                continue
            valid = []
            for run_dir_name in sorted(os.listdir(arm_dir)):
                run_dir = os.path.join(arm_dir, run_dir_name)
                if not os.path.isdir(run_dir):
                    continue
                classification, _ = classify_run_for_grading(run_dir, expected_identity)
                if classification == GRADED:
                    valid.append(run_dir)
            if valid:
                found[(case_id, arm)] = valid
    return found


def grade_empirical_batch():
    """Refuses to produce the final empirical score table unless it finds
    EXACTLY ONE valid current-provenance observation for every
    (30 cases x 3 arms) = 90 required (case, arm) slots. Duplicates for
    the current empirical identity are a hard failure requiring explicit
    resolution, never silently resolved by timestamp. Returns
    (ok: bool, detail: dict) -- detail always reports missing/duplicate
    slots even on failure, never just a bare False."""
    from config import CASES_DIR, ARMS as CONFIGURED_ARMS

    expected_cases = sorted(
        d for d in os.listdir(CASES_DIR)
        if os.path.isdir(os.path.join(CASES_DIR, d)) and not d.startswith(".")
    )
    required_slots = {(c, a) for c in expected_cases for a in CONFIGURED_ARMS}

    found = discover_valid_current_observations()
    missing = sorted(required_slots - set(found))
    duplicates = {k: v for k, v in found.items() if k in required_slots and len(v) > 1}
    unexpected = sorted(set(found) - required_slots)

    ok = not missing and not duplicates and not unexpected and len(found) == len(required_slots)
    detail = {
        "required_slots": len(required_slots),
        "found_slots": len(found),
        "missing": missing,
        "duplicates": duplicates,
        "unexpected": unexpected,
    }
    if not ok:
        return False, detail

    graded_rows = []
    expected_identity = current_expected_empirical_identity()
    for (case_id, arm), dirs in sorted(found.items()):
        graded_rows.append(grade_one(dirs[0], expected_identity))
    detail["graded_rows"] = len(graded_rows)
    return True, detail


if __name__ == "__main__":
    ok, detail = grade_empirical_batch()
    print(json.dumps(detail, indent=2, default=str))
    print("EMPIRICAL_BATCH_GRADEABLE =", ok)
    sys.exit(0 if ok else 1)
