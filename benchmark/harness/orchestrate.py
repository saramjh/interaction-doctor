#!/usr/bin/env python3
"""Top-level CLI to build workspaces, gate on contamination checks, and
(optionally) execute real Claude Code runs.

Usage:
  python3 orchestrate.py --cases case-001,case-002 --arms baseline,generic,doctor
  python3 orchestrate.py --cases case-001 --arms baseline --execute
  python3 orchestrate.py --preflight

(check-only is the DEFAULT mode -- there is no --check-only flag; it runs
whenever neither --execute nor --preflight is given.)

--check-only (default) builds every requested arm's workspace for a case
TOGETHER (briefly, no money spent) so contamination_check's cross-arm
leakage comparison can run -- this is a static validation tool, not the
execution path, so momentary coexistence here is fine and is how the
zero-cost cross-arm selftest works.

--execute is the real (paid) path, and runs arms SEQUENTIALLY per case:
build ONE arm's workspace, contamination-check it, run it, archive it, then
DESTROY that workspace before the next arm's workspace is even built. No
two evaluated arm workspaces for the same case ever coexist during
--execute -- this eliminates sibling-workspace access as a live attack
surface during real runs, rather than merely denying it via permissions.
"""

import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design"))

import config
import contamination_check
import preflight
import runner
import tool_surface_preflight
import workspace
from config import CASES_DIR, RESULTS_RAW_DIR, BENCHMARK_ROOT, ARMS, PREFLIGHT_CASE_ID, PREFLIGHT_ARMS
from verify_experiment_freeze import verify_freeze


def discover_cases():
    return sorted(
        d for d in os.listdir(CASES_DIR)
        if os.path.isdir(os.path.join(CASES_DIR, d)) and not d.startswith(".")
    )


def archive(case_id, arm, run_no, ws_dir, record):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
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


def run_check_only(cases, arms, run_no):
    """Static validation path: builds every requested arm's workspace
    together (briefly, no execution) so cross-arm leakage can be checked.
    Never calls runner.run().

    CORRECTION (post-report): this used to leave every workspace it built
    behind on disk. Left behind, a stale baseline/generic/doctor
    workspace from an earlier --check-only run could coexist on disk with
    a LATER --execute run for the same case -- a live attack surface, not
    merely a permission question (closed at the OS level too, see
    config.REAL_WORKSPACE_ROOT / settings_policy.build_sandbox's
    denyRead, but that is defense-in-depth, not a reason to also leave
    stale directories lying around). Every workspace this function builds
    is now destroyed (try/finally, so cleanup happens even if a check
    raises) before it returns."""
    summary = []
    for case_id in cases:
        ws_dirs = {arm: workspace.build(case_id, arm, run_no) for arm in arms}
        try:
            per_arm_violations = {arm: contamination_check.check(ws, arm) for arm, ws in ws_dirs.items()}
            cross_arm_violations = (
                contamination_check.check_no_cross_arm_leakage(ws_dirs) if len(ws_dirs) > 1 else []
            )
            for arm, ws_dir in ws_dirs.items():
                row = {"case_id": case_id, "arm": arm, "run_no": run_no, "ws_dir": ws_dir}
                violations = list(per_arm_violations[arm]) + [f"case-level: {v}" for v in cross_arm_violations]
                if violations:
                    row["status"] = "BLOCKED_CONTAMINATION"
                    row["violations"] = violations
                    print(f"[BLOCKED] {case_id}/{arm}: {violations}", file=sys.stderr)
                else:
                    row["contamination_check"] = "clean"
                    row["status"] = "DRY_RUN_ONLY"
                summary.append(row)
        finally:
            for ws_dir in ws_dirs.values():
                shutil.rmtree(ws_dir, ignore_errors=True)
    return summary


def cleanup_stale_workspaces(cases, arms, run_no):
    """Defensive cleanup for --execute: removes any pre-existing temporary
    evaluation workspace for every requested (case, arm, run_no) BEFORE the
    first arm is built, so leftovers from an interrupted prior diagnostic
    (or a --check-only run that predates the cleanup fix above) cannot
    silently coexist with a fresh run. Only ever touches paths under
    workspace.run_dir(...) (== under config.WORKSPACE_ROOT) -- NEVER
    touches benchmark/results/raw/ (archived data), which lives in a
    completely different directory tree."""
    for case_id in cases:
        for arm in arms:
            stale = workspace.run_dir(case_id, arm, run_no)
            if os.path.exists(stale):
                print(f"[CLEANUP] removing stale temporary workspace: {stale}", file=sys.stderr)
                shutil.rmtree(stale, ignore_errors=True)


def run_execute_sequential(cases, arms, run_no):
    """Real (paid) execution path: one arm's workspace exists at a time.
    Build -> contamination-check (single arm) -> run -> archive -> destroy,
    strictly before the next arm's workspace is built.

    CORRECTION (post-audit, item 17): a single verify_freeze() call before
    the whole batch (main()) is insufficient across a long-running 90-run
    loop if instrument files could change mid-batch (e.g. another process
    editing harness/config.py while a batch is in flight). Every
    observation must be tied to the same immutable execution identity, or
    execution must abort -- never silently continue on drift, and never
    silently drop already-completed rows. verify_freeze() is therefore
    re-checked before EACH arm; on failure the function returns
    immediately with everything collected so far plus one final
    ABORTED_FREEZE_DRIFT row, never proceeding to build another
    workspace."""
    summary = []
    for case_id in cases:
        for arm in arms:
            ok, violations = verify_freeze()
            if not ok:
                summary.append({
                    "case_id": case_id, "arm": arm, "run_no": run_no,
                    "status": "ABORTED_FREEZE_DRIFT", "violations": violations,
                })
                print(f"[ABORT] freeze drift detected before {case_id}/{arm}: {violations}",
                      file=sys.stderr)
                return summary

            ws_dir = workspace.build(case_id, arm, run_no)
            row = {"case_id": case_id, "arm": arm, "run_no": run_no, "ws_dir": ws_dir}
            try:
                violations = contamination_check.check(ws_dir, arm)
                if violations:
                    row["status"] = "BLOCKED_CONTAMINATION"
                    row["violations"] = violations
                    print(f"[BLOCKED] {case_id}/{arm}: {violations}", file=sys.stderr)
                    summary.append(row)
                    continue
                row["contamination_check"] = "clean"
                record = runner.run(case_id, arm, run_no, ws_dir, dry_run=False)
                dest = archive(case_id, arm, run_no, ws_dir, record)
                row["status"] = record["status"]
                row["archived_at"] = dest
                summary.append(row)
            finally:
                # Destroy this arm's workspace before the next arm's is
                # built -- no two evaluated arm workspaces for this case
                # ever coexist during --execute.
                shutil.rmtree(ws_dir, ignore_errors=True)
    return summary


def _find_system_init_event(event_log):
    for e in event_log or []:
        if isinstance(e, dict) and e.get("type") == "system" and e.get("subtype") == "init":
            return e
    return None


def _extract_skill_names(event_log):
    """Full skill-name list from this arm's system/init event, for the
    cross-arm comparison in aggregate_preflight() (item 12: an unexpected
    global/user skill present in one arm but not another would be an
    undetected confound). None if no system/init event was found --
    treated as missing evidence, never as an empty (and therefore
    trivially "matching") list."""
    system_init = _find_system_init_event(event_log)
    if system_init is None:
        return None
    return sorted(tool_surface_preflight.get_skill_names(system_init))


def validate_arm_tool_surface_and_skill(event_log, arm):
    """Integrates the REQUIRED tool-surface/Skill-discoverability/actual-
    Skill-invocation checks (config.EXPERIMENT_PREFLIGHT_REQUIRED,
    README.md/DESIGN.md) into the preflight mechanism -- previously the
    live preflight documentation promised these checks but
    run_preflight_sequential never ran them.

    Unknown/missing evidence (no recognizable system/init event, or an
    entirely empty event log) is HOLD, never silently PASS -- in
    particular, an empty event log trivially "shows no Skill invocation,"
    which would otherwise let baseline/generic's "must not invoke the
    doctor skill" assertion pass on pure absence of evidence; guarded
    against explicitly below."""
    result = {
        "tool_surface_status": "HOLD",
        "tool_surface_violations": [],
        "skill_discoverability_status": "HOLD",
        "skill_discoverability_violations": [],
        "doctor_skill_invocation_status": "HOLD",
        # Model identity is a REQUIRES_LIVE_PREFLIGHT question by nature --
        # this records what evidence (if any) the real archived event
        # actually contains, never assuming a match when the field is
        # simply absent from the event shape.
        "model_identity_status": "HOLD",
    }
    if not event_log:
        return result

    system_init = _find_system_init_event(event_log)

    if system_init is not None:
        try:
            violations = tool_surface_preflight.validate_system_init_event(system_init, arm)
            from config import DOCTOR_REQUIRED_SKILL_SUBSTRING, MODEL
            skill_v = [v for v in violations if DOCTOR_REQUIRED_SKILL_SUBSTRING in v]
            tool_v = [v for v in violations if DOCTOR_REQUIRED_SKILL_SUBSTRING not in v]

            reported_model = system_init.get("model") or system_init.get("model_id")
            if reported_model is not None:
                if reported_model == MODEL:
                    result["model_identity_status"] = "PASS"
                else:
                    result["model_identity_status"] = "FAIL"
                    tool_v = tool_v + [
                        f"system/init reported model {reported_model!r}, expected {MODEL!r}"
                    ]

            result["tool_surface_status"] = "FAIL" if tool_v else "PASS"
            result["tool_surface_violations"] = tool_v
            result["skill_discoverability_status"] = "FAIL" if skill_v else "PASS"
            result["skill_discoverability_violations"] = skill_v
        except KeyError:
            # get_tools_list() raises KeyError if no recognized tools field
            # exists in the event -- genuinely insufficient evidence, HOLD.
            pass

    occurred = tool_surface_preflight.validate_skill_invocation_occurred(event_log)
    if arm == "doctor":
        if not occurred:
            result["doctor_skill_invocation_status"] = "FAIL"
        else:
            succeeded = tool_surface_preflight.validate_skill_invocation_succeeded(event_log)
            if succeeded is None:
                result["doctor_skill_invocation_status"] = "HOLD"
            else:
                result["doctor_skill_invocation_status"] = "PASS" if succeeded else "FAIL"
    else:
        result["doctor_skill_invocation_status"] = "PASS" if not occurred else "FAIL"

    return result


def run_preflight_sequential(run_no, expected_identity):
    """The v6 preflight-only infrastructure-qualification mechanism (see
    preflight.py / preflight_validator.py). Legal ONLY for
    PREFLIGHT_CASE_ID x PREFLIGHT_ARMS (exactly 3 arms); --preflight
    rejects anything else before building a single workspace. Runs are
    sequential exactly like run_execute_sequential (one arm's workspace at
    a time), plus: an external filesystem canary and a parent-only env
    canary are set up before the first arm, a workspace symlink to the
    external canary and the frozen infrastructure-check prompt appendix
    are added to each arm's workspace/manifest before it runs, and each
    archived run is scored against the 9 frozen preflight assertions PLUS
    the real tool-surface/Skill-discoverability/actual-invocation checks
    immediately after archiving. These runs are infrastructure
    qualification ONLY -- never counted as part of the 90-row empirical
    result table (archived under a distinct results/preflight/ tree, not
    results/raw/).

    expected_identity: the ONE immutable expected execution identity
    captured by capture_expected_identity() BEFORE this function was ever
    called (item 2) -- required, never recomputed here or in
    aggregate_preflight(). Embedded into the archived
    preflight_validation.json for each arm so a later re-validation
    (find_latest_passing_qualification's forgery check) has it available
    without needing to trust the caller's aggregate summary."""
    import preflight_validator

    cases = [PREFLIGHT_CASE_ID]
    arms = list(PREFLIGHT_ARMS)
    summary = []
    canary_path = preflight.setup_external_canary()
    try:
        for case_id in cases:
            for arm in arms:
                # verify_freeze() immediately before EACH arm -- exactly
                # like the empirical --execute path already does per arm
                # (item 2), never relying on a single check before the
                # whole preflight batch.
                ok, violations = verify_freeze()
                if not ok:
                    summary.append({
                        "case_id": case_id, "arm": arm, "run_no": run_no,
                        "status": "ABORTED_FREEZE_DRIFT", "violations": violations,
                    })
                    print(f"[ABORT] freeze drift detected before preflight {case_id}/{arm}: "
                          f"{violations}", file=sys.stderr)
                    return summary

                ws_dir = workspace.build(case_id, arm, run_no)
                row = {"case_id": case_id, "arm": arm, "run_no": run_no,
                       "ws_dir": ws_dir, "preflight": True}
                try:
                    workspace_dir = os.path.join(ws_dir, "workspace")
                    preflight.link_workspace_symlink(workspace_dir, canary_path)

                    manifest_path = os.path.join(ws_dir, "run_manifest.json")
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    manifest["prompt"] = preflight.build_preflight_prompt(
                        manifest["prompt"], workspace_dir
                    )
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)

                    violations = contamination_check.check(ws_dir, arm)
                    if violations:
                        row["status"] = "BLOCKED_CONTAMINATION"
                        row["violations"] = violations
                        print(f"[BLOCKED] {case_id}/{arm}: {violations}", file=sys.stderr)
                        summary.append(row)
                        continue
                    row["contamination_check"] = "clean"

                    env_name, env_value = preflight.build_env_canary_value_pair()
                    record = runner.run(case_id, arm, run_no, ws_dir, dry_run=False,
                                         extra_parent_env={env_name: env_value})
                    dest = archive_preflight(case_id, arm, run_no, ws_dir, record)
                    row["status"] = record["status"]
                    row["returncode"] = record.get("returncode")
                    row["archived_at"] = dest
                    # Captured BEFORE any provenance comparison, straight
                    # from this run's own record -- the aggregate/per-run
                    # provenance check (item 14) compares this against
                    # this instrument's CURRENT expected identity, not
                    # merely a single post-hoc verify_freeze() call.
                    row["provenance"] = {
                        field: record.get(field) for field in EXPECTED_PROVENANCE_FIELDS
                    }

                    event_log_path = os.path.join(ws_dir, "event_log.json")
                    event_log = []
                    if os.path.exists(event_log_path):
                        with open(event_log_path) as f:
                            event_log = json.load(f)

                    validation = {
                        "infrastructure_probe_assertions":
                            preflight_validator.validate_preflight_run(event_log, record),
                    }
                    validation.update(validate_arm_tool_surface_and_skill(event_log, arm))
                    validation["skill_surface_names"] = _extract_skill_names(event_log)
                    row["preflight_validation"] = validation
                    row["expected_identity"] = expected_identity
                    with open(os.path.join(dest, "preflight_validation.json"), "w") as f:
                        json.dump({"validation": validation, "provenance": row["provenance"],
                                    "returncode": row["returncode"], "status": row["status"],
                                    "expected_identity": expected_identity}, f, indent=2)
                    summary.append(row)
                finally:
                    shutil.rmtree(ws_dir, ignore_errors=True)
    finally:
        preflight.teardown_external_canary()
    return summary


def _aggregate_status(statuses):
    """FAIL if any explicit FAIL, else HOLD if any HOLD, else PASS."""
    if "FAIL" in statuses:
        return "FAIL"
    if "HOLD" in statuses or not statuses:
        return "HOLD"
    return "PASS"


EXPECTED_PROVENANCE_FIELDS = (
    "git_commit_sha", "experiment_freeze_file_sha256", "claude_cli_version",
    "claude_launcher_path", "claude_executable_realpath", "claude_executable_sha256",
    "active_sandbox_architecture", "custom_outer_sandbox_active", "model", "effort",
)


def _is_real_git_sha(value) -> bool:
    """A real 40-hex-character commit SHA. None / '<error...>' / '' / any
    other malformed value must never satisfy this, so a broken git lookup
    can never silently compare equal to itself on both sides of a
    provenance check."""
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(c in "0123456789abcdef" for c in value.lower())
    )


def capture_expected_identity():
    """Captures ONE immutable expected execution identity, snapshotted
    ONCE, BEFORE any preflight arm is built or executed (item 2: the
    prior implementation computed this DURING aggregate_preflight(),
    AFTER all three paid runs -- not truly a pre-execution reference).
    Callers must capture this exactly once per --preflight invocation and
    thread it explicitly through run_preflight_sequential(...) and
    aggregate_preflight(...) -- never recompute it after the runs."""
    import hashlib as _hashlib
    from config import (
        FROZEN_CLAUDE_CLI_VERSION, FROZEN_CLAUDE_EXECUTABLE_REALPATH,
        FROZEN_CLAUDE_EXECUTABLE_SHA256, CLAUDE_LAUNCHER_PATH,
        ACTIVE_SANDBOX_ARCHITECTURE, CUSTOM_OUTER_SANDBOX_ACTIVE,
        MODEL, EFFORT, EXPERIMENT_FREEZE_FILENAME,
    )
    freeze_path = os.path.join(BENCHMARK_ROOT, "design", EXPERIMENT_FREEZE_FILENAME)
    freeze_hash = None
    if os.path.exists(freeze_path):
        with open(freeze_path, "rb") as f:
            freeze_hash = _hashlib.sha256(f.read()).hexdigest()
    git_sha = runner._git_commit_sha()
    identity = {
        "git_commit_sha": git_sha,
        "git_commit_sha_is_valid": _is_real_git_sha(git_sha),
        "experiment_freeze_file_sha256": freeze_hash,
        "claude_cli_version": FROZEN_CLAUDE_CLI_VERSION,
        "claude_launcher_path": CLAUDE_LAUNCHER_PATH,
        "claude_executable_realpath": FROZEN_CLAUDE_EXECUTABLE_REALPATH,
        "claude_executable_sha256": FROZEN_CLAUDE_EXECUTABLE_SHA256,
        "active_sandbox_architecture": ACTIVE_SANDBOX_ARCHITECTURE,
        "custom_outer_sandbox_active": CUSTOM_OUTER_SANDBOX_ACTIVE,
        "model": MODEL,
        "effort": EFFORT,
        "max_budget_usd": config.MAX_BUDGET_USD_PER_RUN,
        "tool_surface": config.TOOLS,
        "permission_mode": config.PERMISSION_MODE,
    }
    return identity


def _row_provenance_status(row, expected):
    prov = row.get("provenance")
    if not prov:
        return "HOLD", ["no provenance recorded for this row"]
    if not expected.get("git_commit_sha_is_valid"):
        return "FAIL", [
            f"expected git_commit_sha is not a real 40-hex commit SHA: "
            f"{expected.get('git_commit_sha')!r} -- a malformed/missing "
            f"expected value must never compare equal to anything"
        ]
    mismatches = [
        f"{field}: expected={expected[field]!r} actual={prov.get(field)!r}"
        for field in EXPECTED_PROVENANCE_FIELDS
        if prov.get(field) != expected.get(field)
    ]
    return ("FAIL" if mismatches else "PASS"), mismatches


def aggregate_preflight(summary, expected_identity=None):
    """Computes the explicit, machine-readable gate required after exactly
    baseline + generic + doctor complete. NEVER a trigger for the 90
    empirical runs by itself -- see module docstring / main(): this
    function only reports a state, it does not start anything.

    expected_identity: the SAME immutable identity captured by
    capture_expected_identity() BEFORE the runs (item 2) -- passed through
    explicitly by the caller (main(), or re-derived from an archived
    preflight_validation.json's own "expected_identity" field when
    re-validating a qualification record after the fact). If omitted, this
    function captures it itself as a fallback (e.g. for ad-hoc/legacy
    callers) -- but the real --preflight path in main() always passes the
    one captured before execution, never lets this function silently
    recompute a "current" identity that could differ from what the runs
    actually executed against.

    CORRECTIONS (post-audit):
      - runs_completed now requires record status == "completed"
        (returncode == 0) -- a timeout, nonzero exit, or missing record
        never counts toward 3/3, and there is no automatic retry (this
        function never re-runs anything).
      - PREFLIGHT_PROVENANCE is now computed PER RUN, comparing each
        row's own recorded identity (captured at the moment that specific
        run executed) against the PRE-CAPTURED expected identity -- not
        merely one verify_freeze() call after all three runs finish,
        which could not detect one run having drifted relative to the
        others, and not a "current" identity recomputed after the fact.
      - An unexpected/global skill visible in one arm's system/init but
        not the others (a confound beyond interaction-doctor's expected
        doctor-only presence) is folded into PREFLIGHT_ARM_ISOLATION.
    """
    if expected_identity is None:
        expected_identity = capture_expected_identity()
    arms_present = {row["arm"] for row in summary}
    # CORRECTION (item 6): require BOTH status == "completed" AND
    # returncode == 0 explicitly HERE, in the aggregate gate itself --
    # never rely on an implicit assumption that runner.py's "completed"
    # status already implies returncode == 0. Reproduced failure: a
    # synthetic row with status="completed", returncode=1 previously
    # counted toward 3/3.
    runs_completed = sum(
        1 for row in summary
        if row.get("status") == "completed"
        and row.get("returncode") == 0
        and "preflight_validation" in row
    )

    runtime_statuses, tool_surface_statuses, isolation_statuses, skill_inv_statuses = [], [], [], []
    for row in summary:
        v = row.get("preflight_validation")
        if not v:
            runtime_statuses.append("HOLD")
            tool_surface_statuses.append("HOLD")
            isolation_statuses.append("HOLD")
            skill_inv_statuses.append("HOLD")
            continue
        runtime_statuses.append(_aggregate_status(list(v["infrastructure_probe_assertions"].values())))
        tool_surface_statuses.append(_aggregate_status(
            [v["tool_surface_status"], v.get("model_identity_status", "HOLD")]
        ))
        isolation_statuses.append(v["skill_discoverability_status"])
        skill_inv_statuses.append(v["doctor_skill_invocation_status"])

    # Cross-arm skill-surface confound check (item 12): every arm's
    # skill list, with interaction-doctor removed, must be IDENTICAL --
    # an unexpected global/user skill present in only one arm is a
    # confound this experiment's design does not account for.
    skill_surfaces = {}
    for row in summary:
        v = row.get("preflight_validation") or {}
        names = v.get("skill_surface_names")
        skill_surfaces[row["arm"]] = (
            None if names is None
            else sorted(n for n in names if "interaction-doctor" not in n)
        )
    if any(v is None for v in skill_surfaces.values()) or len(skill_surfaces) < 3:
        isolation_statuses.append("HOLD")
    else:
        distinct = {tuple(v) for v in skill_surfaces.values()}
        isolation_statuses.append("PASS" if len(distinct) == 1 else "FAIL")

    provenance_statuses = []
    provenance_mismatches = []
    for row in summary:
        status, mismatches = _row_provenance_status(row, expected_identity)
        provenance_statuses.append(status)
        if mismatches:
            provenance_mismatches.append({"arm": row.get("arm"), "mismatches": mismatches})
    # A single freeze verification is ADDITIONAL evidence, never a
    # substitute for the per-run comparison above.
    global_freeze_ok, global_freeze_violations = verify_freeze()
    if not global_freeze_ok:
        provenance_statuses.append("FAIL")

    aggregate = {
        "PAID_PREFLIGHT_RUNS_COMPLETED": f"{runs_completed}/3",
        "PREFLIGHT_RUNTIME_ASSERTIONS": _aggregate_status(runtime_statuses),
        "PREFLIGHT_TOOL_SURFACE": _aggregate_status(tool_surface_statuses),
        "PREFLIGHT_ARM_ISOLATION": _aggregate_status(isolation_statuses),
        "PREFLIGHT_DOCTOR_SKILL_INVOCATION": _aggregate_status(skill_inv_statuses),
        "PREFLIGHT_PROVENANCE": _aggregate_status(provenance_statuses),
        "provenance_mismatches": provenance_mismatches,
        "global_freeze_violations": global_freeze_violations,
        "freeze_file_sha256": expected_identity["experiment_freeze_file_sha256"],
        "expected_identity": expected_identity,
    }
    all_categories_pass = (
        runs_completed == 3
        and arms_present == set(PREFLIGHT_ARMS)
        and aggregate["PREFLIGHT_RUNTIME_ASSERTIONS"] == "PASS"
        and aggregate["PREFLIGHT_TOOL_SURFACE"] == "PASS"
        and aggregate["PREFLIGHT_ARM_ISOLATION"] == "PASS"
        and aggregate["PREFLIGHT_DOCTOR_SKILL_INVOCATION"] == "PASS"
        and aggregate["PREFLIGHT_PROVENANCE"] == "PASS"
    )
    aggregate["PAID_PREFLIGHT"] = "PASS" if all_categories_pass else "HOLD"
    # Even on PASS this is a REPORTED state only -- see main(): nothing in
    # this codebase ever reads this field to auto-start the 90 empirical
    # runs.
    aggregate["READY_FOR_EMPIRICAL_90_RUNS"] = all_categories_pass
    return aggregate


def archive_preflight(case_id, arm, run_no, ws_dir, record):
    """Like archive(), but under a distinct results/preflight/ tree so
    infrastructure-qualification runs are never mistaken for, or counted
    among, the 90-row empirical result table archived under
    results/raw/."""
    from config import BENCHMARK_ROOT
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest = os.path.join(BENCHMARK_ROOT, "results", "preflight", case_id, arm,
                         f"run-{run_no:02d}-{stamp}")
    os.makedirs(dest, exist_ok=False)
    for name in ("run_manifest.json", "run_result.json", "event_log.json"):
        src = os.path.join(ws_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, dest)
    workspace_dir = os.path.join(ws_dir, "workspace")
    if os.path.isdir(workspace_dir):
        shutil.copytree(workspace_dir, os.path.join(dest, "final_workspace"))
    return dest


def _reload_row_from_archive(row):
    """Re-reads a preflight summary row's evidence DIRECTLY from its
    archived directory (run_result.json + preflight_validation.json) --
    never trusts whatever the row already contains in memory or in a
    cached aggregate-*.json. Returns a freshly reconstructed row, or None
    if the archive is missing/unreadable/incomplete."""
    dest = row.get("archived_at")
    if not dest or not os.path.isdir(dest):
        return None
    result_path = os.path.join(dest, "run_result.json")
    validation_path = os.path.join(dest, "preflight_validation.json")
    if not (os.path.exists(result_path) and os.path.exists(validation_path)):
        return None
    try:
        with open(result_path) as f:
            result = json.load(f)
        with open(validation_path) as f:
            validation_doc = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return {
        "case_id": result.get("case_id"), "arm": result.get("arm"),
        "status": result.get("status"), "returncode": result.get("returncode"),
        "archived_at": dest,
        "provenance": validation_doc.get("provenance"),
        "preflight_validation": validation_doc.get("validation"),
        "expected_identity": validation_doc.get("expected_identity"),
    }


def _recompute_qualification_from_archive(candidate_path):
    """Recomputes a qualification from FIRST PRINCIPLES: reads the
    candidate aggregate-run-*.json only to find each arm's archived_at
    path, then re-reads and re-validates every field directly from the
    archived run_result.json/preflight_validation.json on disk, and
    re-runs aggregate_preflight() on the reconstructed rows. NEVER trusts
    the candidate file's own cached "aggregate"/"PAID_PREFLIGHT" verdict.

    Reproduced attack this closes: a minimal forged file containing only
    {"summary": [], "aggregate": {"PAID_PREFLIGHT": "PASS",
    "freeze_file_sha256": <current hash>}} -- with zero real per-arm
    evidence -- was previously accepted outright.

    Returns a freshly computed aggregate dict (with "_qualification_file"
    and "_recomputed" set), or None if the archive doesn't support a
    genuine 3-arm recomputation at all."""
    try:
        with open(candidate_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    raw_summary = data.get("summary")
    if not isinstance(raw_summary, list):
        return None

    reloaded = [r for r in (_reload_row_from_archive(row) for row in raw_summary
                             if isinstance(row, dict)) if r is not None]
    arms_seen = [r["arm"] for r in reloaded]
    if sorted(arms_seen) != sorted(PREFLIGHT_ARMS):
        # not exactly {baseline, generic, doctor} once each -- reject
        # (covers: fewer than 3 arms, a missing arm, a duplicated arm, or
        # any row whose archive could not be reloaded at all)
        return None
    if len(set(arms_seen)) != len(arms_seen):
        return None
    if any(r["case_id"] != PREFLIGHT_CASE_ID for r in reloaded):
        return None

    expected_identities = {json.dumps(r.get("expected_identity"), sort_keys=True) for r in reloaded}
    if len(expected_identities) != 1 or list(expected_identities)[0] == "null":
        # the 3 arms must all have been run against the SAME pre-captured
        # expected identity -- if they disagree (or none was recorded),
        # this is not a coherent single qualification attempt.
        return None
    expected_identity = reloaded[0].get("expected_identity")

    recomputed = aggregate_preflight(reloaded, expected_identity=expected_identity)
    recomputed["_qualification_file"] = candidate_path
    recomputed["_recomputed"] = True
    return recomputed


def find_latest_passing_qualification():
    """The frozen, explicit, human-controlled qualification gate for
    --execute (item 16). CORRECTION (item 3, reproduced failure): the
    prior implementation trusted a candidate file's own
    aggregate.PAID_PREFLIGHT / aggregate.freeze_file_sha256 fields
    directly -- a minimal FORGED file containing only those two fields,
    with zero real per-arm evidence, was accepted outright.

    This now scans benchmark/results/preflight/aggregate-run-*.json only
    to locate candidates, then for each candidate RECOMPUTES the
    qualification from the archived per-arm evidence on disk
    (_recompute_qualification_from_archive) -- never trusting the
    candidate file's own cached verdict. Returns the first (most recent)
    recomputed aggregate whose PAID_PREFLIGHT == 'PASS' and whose
    freeze_file_sha256 matches the CURRENT experiment-freeze-v6.json hash,
    or None if no candidate survives recomputation. Never runs anything
    itself."""
    import glob
    from config import EXPERIMENT_FREEZE_FILENAME
    import hashlib as _hashlib

    freeze_path = os.path.join(BENCHMARK_ROOT, "design", EXPERIMENT_FREEZE_FILENAME)
    if not os.path.exists(freeze_path):
        return None
    with open(freeze_path, "rb") as f:
        current_freeze_hash = _hashlib.sha256(f.read()).hexdigest()

    pattern = os.path.join(BENCHMARK_ROOT, "results", "preflight", "aggregate-run-*.json")
    candidates = sorted(glob.glob(pattern), reverse=True)  # timestamp suffix sorts lexicographically
    for path in candidates:
        recomputed = _recompute_qualification_from_archive(path)
        if recomputed is None:
            continue
        if recomputed.get("PAID_PREFLIGHT") == "PASS" and recomputed.get("freeze_file_sha256") == current_freeze_hash:
            return recomputed
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="", help="comma-separated case ids, default: all")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--run-no", type=int, default=1)
    ap.add_argument("--execute", action="store_true", help="actually invoke claude (costs money)")
    ap.add_argument("--preflight", action="store_true",
                     help="run the v6 infrastructure-qualification preflight (costs money); "
                          "legal ONLY for PREFLIGHT_CASE_ID x PREFLIGHT_ARMS, ignores --cases/--arms")
    args = ap.parse_args()

    if args.preflight and args.execute:
        print("--preflight and --execute are mutually exclusive", file=sys.stderr)
        sys.exit(2)

    if args.preflight:
        requested_cases = args.cases.split(",") if args.cases else [PREFLIGHT_CASE_ID]
        requested_arms = args.arms.split(",") if args.arms else list(PREFLIGHT_ARMS)
        if not preflight.is_legal_preflight_request(
            requested_cases[0] if len(requested_cases) == 1 else None, requested_arms
        ) or len(requested_cases) != 1:
            print("--preflight is legal ONLY for exactly "
                  f"{PREFLIGHT_CASE_ID!r} x {list(PREFLIGHT_ARMS)!r} (all 3 arms, never fewer, "
                  "never a different or dynamically-chosen case). Refusing before building "
                  "any workspace or making any paid call.", file=sys.stderr)
            sys.exit(1)

    if args.execute or args.preflight:
        # Fail-closed: --execute/--preflight may not build a single
        # workspace or make any paid call unless the live instrument
        # matches exactly what was frozen. No flag bypasses this.
        ok, violations = verify_freeze()
        if not ok:
            print("EXPERIMENT_FREEZE_HASH_VERIFY = FAIL", file=sys.stderr)
            for v in violations:
                print(f"[MISMATCH] {v}", file=sys.stderr)
            print("Aborting before any workspace was built or any paid call was made.",
                  file=sys.stderr)
            sys.exit(1)
        print("EXPERIMENT_FREEZE_HASH_VERIFY = PASS", file=sys.stderr)

    if args.preflight:
        # Captured ONCE, immediately after the initial verify_freeze()
        # passes, BEFORE baseline is built or executed (item 2) -- this
        # is the one immutable expected identity every arm's provenance
        # is compared against; it is never recomputed after the runs.
        expected_identity = capture_expected_identity()
        if not expected_identity.get("git_commit_sha_is_valid"):
            print("EXPECTED_IDENTITY_GIT_SHA_INVALID = TRUE", file=sys.stderr)
            print(f"git_commit_sha = {expected_identity.get('git_commit_sha')!r} is not a real "
                  "40-hex commit SHA. Aborting before any preflight workspace is built.",
                  file=sys.stderr)
            sys.exit(1)
        summary = run_preflight_sequential(args.run_no, expected_identity)
        aggregate = aggregate_preflight(summary, expected_identity=expected_identity)

        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        agg_path = os.path.join(BENCHMARK_ROOT, "results", "preflight",
                                 f"aggregate-run-{args.run_no:02d}-{stamp}.json")
        os.makedirs(os.path.dirname(agg_path), exist_ok=True)
        with open(agg_path, "w") as f:
            json.dump({"summary": summary, "aggregate": aggregate}, f, indent=2, default=str)

        print(json.dumps(summary, indent=2, default=str))
        print()
        for key in ("PAID_PREFLIGHT_RUNS_COMPLETED", "PREFLIGHT_RUNTIME_ASSERTIONS",
                    "PREFLIGHT_TOOL_SURFACE", "PREFLIGHT_ARM_ISOLATION",
                    "PREFLIGHT_DOCTOR_SKILL_INVOCATION", "PREFLIGHT_PROVENANCE",
                    "PAID_PREFLIGHT", "READY_FOR_EMPIRICAL_90_RUNS"):
            print(f"{key} = {aggregate[key]}")
        # Even a PASS aggregate is a REPORTED state only. This function
        # never invokes run_execute_sequential or otherwise starts the 90
        # empirical runs -- that requires a separate, explicit,
        # human-authorized invocation of --execute, which itself checks
        # find_latest_passing_qualification() below before proceeding.
        print("\nDO NOT START THE 90 EMPIRICAL RUNS FROM THIS INVOCATION.")
        return

    cases = args.cases.split(",") if args.cases else discover_cases()
    arms = args.arms.split(",")

    if args.execute:
        # Frozen, explicit, human-controlled qualification gate (item 16):
        # --execute refuses to start the empirical batch without proof of
        # a successful, freeze-hash-matched paid preflight already on
        # disk. This check never runs the preflight itself -- it only
        # looks for evidence one already ran and passed.
        qualification = find_latest_passing_qualification()
        if qualification is None:
            print("EMPIRICAL_EXECUTION_BLOCKED_NO_PASSING_QUALIFICATION = TRUE", file=sys.stderr)
            print("No valid PAID_PREFLIGHT == PASS qualification record was found under "
                  "results/preflight/ matching the CURRENT experiment-freeze-v6.json hash. "
                  "Run `orchestrate.py --preflight` and confirm it passes before --execute "
                  "may proceed. Aborting before any workspace was built or any paid call "
                  "was made.", file=sys.stderr)
            sys.exit(1)
        print(f"EMPIRICAL_EXECUTION_QUALIFICATION_FOUND = {qualification['_qualification_file']}",
              file=sys.stderr)

        # Defensive cleanup: never let a leftover temporary workspace from
        # an interrupted prior run/diagnostic coexist unnoticed with this
        # run. Only ever removes paths under WORKSPACE_ROOT -- archived
        # results/raw/ data is never touched here.
        cleanup_stale_workspaces(cases, arms, args.run_no)
        summary = run_execute_sequential(cases, arms, args.run_no)
    else:
        summary = run_check_only(cases, arms, args.run_no)

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
