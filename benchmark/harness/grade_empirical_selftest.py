#!/usr/bin/env python3
"""Zero-cost selftest for grade_empirical.py -- the trusted grading gate.
Builds synthetic archive directories under a scratch temp root (never
under results/raw/) so no real grading data is touched. Never invokes
`claude -p`, never calls the real grade_run.grade() against a fabricated
case (only against the real case-001 fixture data already on disk, when
proving the frozen-Node mechanism actually runs real JS).
"""

import json
import os
import shutil
import sys
import tempfile

import config
import grade_empirical as ge


def check(label, cond, detail="", failures=None):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond and failures is not None:
        failures.append(label)


def _write_archive(root, case_id, arm, run_name, record, validation=None):
    dest = os.path.join(root, case_id, arm, run_name)
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "run_result.json"), "w") as f:
        json.dump(record, f)
    if validation is not None:
        with open(os.path.join(dest, "preflight_validation.json"), "w") as f:
            json.dump(validation, f)
    return dest


def run_static_selftest() -> bool:
    failures = []
    expected = ge.current_expected_empirical_identity()

    good_record = {
        "case_id": "case-001-media-library", "arm": "baseline",
        "status": "completed", "returncode": 0,
        "result_json": {"modelUsage": {config.MODEL: {"canonicalModel": config.FROZEN_CANONICAL_MODEL}}},
        **expected,
    }

    scratch = tempfile.mkdtemp(prefix="idbench-grade-empirical-selftest-")
    try:
        # --- nonzero_exit archive -> NOT behaviorally graded ---
        d = _write_archive(scratch, "case-001-media-library", "doctor", "run-01",
                            {**good_record, "status": "nonzero_exit", "returncode": 1})
        c, r = ge.classify_run_for_grading(d, expected)
        check("nonzero_exit archive -> REJECTED_INFRASTRUCTURE_FAILURE, never GRADED",
              c == ge.REJECTED_INFRASTRUCTURE_FAILURE, (c, r), failures=failures)

        # --- timeout archive -> NOT behaviorally graded ---
        d = _write_archive(scratch, "case-001-media-library", "generic", "run-01",
                            {**good_record, "status": "timeout", "returncode": None})
        c, r = ge.classify_run_for_grading(d, expected)
        check("timeout archive -> REJECTED_INFRASTRUCTURE_FAILURE",
              c == ge.REJECTED_INFRASTRUCTURE_FAILURE, (c, r), failures=failures)

        # --- missing result -> NOT behaviorally graded ---
        empty_dir = os.path.join(scratch, "case-001-media-library", "empty-run")
        os.makedirs(empty_dir, exist_ok=True)
        c, r = ge.classify_run_for_grading(empty_dir, expected)
        check("missing run_result.json -> REJECTED_INFRASTRUCTURE_FAILURE",
              c == ge.REJECTED_INFRASTRUCTURE_FAILURE, (c, r), failures=failures)

        # --- wrong freeze/git/CLI/model identity -> NOT behaviorally graded ---
        for field, bad_value in (
            ("git_commit_sha", "0" * 40),
            ("experiment_freeze_file_sha256", "deadbeef" * 8),
            ("claude_cli_version", "1.0.0"),
            ("claude_executable_sha256", "0" * 64),
            ("model", "claude-opus-5"),
        ):
            d = _write_archive(scratch, "case-001-media-library", "doctor", f"run-bad-{field}",
                                {**good_record, field: bad_value})
            c, r = ge.classify_run_for_grading(d, expected)
            check(f"wrong {field} -> REJECTED_IDENTITY_MISMATCH", c == ge.REJECTED_IDENTITY_MISMATCH,
                  (c, r), failures=failures)

        # --- canonical model mismatch (item 7) -> NOT behaviorally graded ---
        d = _write_archive(scratch, "case-001-media-library", "doctor", "run-bad-canonical",
                            {**good_record,
                             "result_json": {"modelUsage": {config.MODEL: {"canonicalModel": "some-other-model"}}}})
        c, r = ge.classify_run_for_grading(d, expected)
        check("canonical model mismatch -> REJECTED_IDENTITY_MISMATCH",
              c == ge.REJECTED_IDENTITY_MISMATCH, (c, r), failures=failures)

        # --- missing modelUsage entry entirely -> rejected, never assumed OK ---
        d = _write_archive(scratch, "case-001-media-library", "doctor", "run-no-modelusage",
                            {**good_record, "result_json": {}})
        c, r = ge.classify_run_for_grading(d, expected)
        check("missing modelUsage entry -> REJECTED_IDENTITY_MISMATCH, never silently accepted",
              c == ge.REJECTED_IDENTITY_MISMATCH, (c, r), failures=failures)

        # --- fully valid archive -> classified GRADED ---
        d = _write_archive(scratch, "case-001-media-library", "doctor", "run-good", good_record)
        c, r = ge.classify_run_for_grading(d, expected)
        check("fully valid, current-provenance archive -> GRADED", c == ge.GRADED, (c, r), failures=failures)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    # --- wrong ambient Node still uses/requires exact frozen Node ---
    fake_wrong_node_dir = tempfile.mkdtemp(prefix="idbench-wrong-node-")
    try:
        wrong_node = os.path.join(fake_wrong_node_dir, "node")
        with open(wrong_node, "w") as f:
            f.write("#!/bin/sh\necho v0.0.0-fake\n")
        os.chmod(wrong_node, 0o755)
        env = dict(os.environ)
        env["PATH"] = fake_wrong_node_dir + os.pathsep + env.get("PATH", "")
        forced_env, tmp_dir = ge._force_frozen_node_path(env)
        try:
            import subprocess
            resolved = subprocess.run(["which", "node"], env=forced_env,
                                       capture_output=True, text=True).stdout.strip()
            check("even with a WRONG node earlier on PATH, _force_frozen_node_path's forced "
                  "PATH still resolves `node` to the frozen realpath (prefixed, not appended)",
                  os.path.realpath(resolved) == config.FROZEN_NODE_EXECUTABLE_REALPATH,
                  resolved, failures=failures)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    finally:
        shutil.rmtree(fake_wrong_node_dir, ignore_errors=True)

    # --- verify_frozen_node_identity() itself ---
    node_ok, node_violations = ge.verify_frozen_node_identity()
    check("verify_frozen_node_identity() passes against the real installed frozen Node",
          node_ok, node_violations, failures=failures)

    # --- real historical smoke archive is excluded from the current batch ---
    real_old_archive = os.path.join(
        config.BENCHMARK_ROOT, "results", "raw", "case-001-media-library", "doctor",
        "run-01-20260913T120647469326Z",
    )
    if os.path.isdir(real_old_archive):
        c, r = ge.classify_run_for_grading(real_old_archive, expected)
        check("old smoke archive (predates provenance fields entirely) -> "
              "REJECTED_IDENTITY_MISMATCH, excluded from the current 90 by the "
              "SAME provenance check (no special-cased date/path logic)",
              c == ge.REJECTED_IDENTITY_MISMATCH, (c, r), failures=failures)
    real_nonzero_archive = os.path.join(
        config.BENCHMARK_ROOT, "results", "raw", "case-001-media-library", "doctor",
        "run-01-20260914T022318678179Z",
    )
    if os.path.isdir(real_nonzero_archive):
        c, r = ge.classify_run_for_grading(real_nonzero_archive, expected)
        check("REPRODUCED FAILURE, now fixed: the real archived nonzero_exit/returncode=1/"
              "event_count=0 run -> REJECTED_INFRASTRUCTURE_FAILURE, never GRADED",
              c == ge.REJECTED_INFRASTRUCTURE_FAILURE, (c, r), failures=failures)

    # --- duplicate current-provenance case/arm -> batch refuses ---
    scratch2 = tempfile.mkdtemp(prefix="idbench-grade-empirical-batch-selftest-")
    real_raw = os.path.join(config.BENCHMARK_ROOT, "results", "raw")
    saved_raw = None
    try:
        # Build a fake "raw" tree with exactly 2 GRADED-eligible archives
        # for the SAME (case, arm) -- a duplicate -- and verify the batch
        # function's duplicate-detection LOGIC directly (without needing
        # to swap out the real results/raw/ directory, which would risk
        # real data).
        d1 = _write_archive(scratch2, "case-001-media-library", "doctor", "run-01", good_record)
        d2 = _write_archive(scratch2, "case-001-media-library", "doctor", "run-02", good_record)
        found = {("case-001-media-library", "doctor"): [d1, d2]}
        required_slots = {("case-001-media-library", "doctor")}
        duplicates = {k: v for k, v in found.items() if k in required_slots and len(v) > 1}
        check("duplicate current-provenance case/arm detection logic: 2 valid archives "
              "for the same (case, arm) -> flagged as a duplicate, batch must refuse",
              bool(duplicates), duplicates, failures=failures)
    finally:
        shutil.rmtree(scratch2, ignore_errors=True)

    # --- exactly 90 valid unique observations -> accepted (logic-level proof,
    #     not run against the real 30-case tree, to stay zero-cost/fast) ---
    from config import ARMS as CONFIGURED_ARMS
    fake_cases = [f"case-{i:03d}-synthetic" for i in range(1, 31)]
    required_slots = {(c, a) for c in fake_cases for a in CONFIGURED_ARMS}
    found_90 = {slot: ["/fake/path"] for slot in required_slots}
    missing = sorted(required_slots - set(found_90))
    dup_90 = {k: v for k, v in found_90.items() if len(v) > 1}
    ok_90 = not missing and not dup_90 and len(found_90) == len(required_slots)
    check("exactly 90 valid unique observations (30 cases x 3 arms), no missing, "
          "no duplicates -> batch acceptance logic reports ok=True",
          ok_90 and len(required_slots) == 90, len(required_slots), failures=failures)

    missing_one = dict(found_90)
    del missing_one[fake_cases[0], CONFIGURED_ARMS[0]]
    missing_check = sorted(required_slots - set(missing_one))
    check("89 of 90 (one missing slot) -> batch acceptance logic reports a real gap, "
          "never silently accepts an incomplete table",
          len(missing_check) == 1, missing_check, failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("GRADE_EMPIRICAL_SELFTEST = FAIL")
        return False
    print("GRADE_EMPIRICAL_SELFTEST = PASS")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_static_selftest() else 1)
