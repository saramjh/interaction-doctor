#!/usr/bin/env python3
"""Persisted, execution-time freeze verifier. Re-hashes every
execution-relevant file named in the experiment freeze inventory and
compares against the persisted hashes; also compares live configuration
(model, effort, EVENT_LOG_MODE, expected arms, tool-surface, installed
Claude CLI version) against what was frozen. Zero mismatches required.

Wired into orchestrate.py: --execute refuses to build a single workspace
or make any paid call unless this verifier passes first. No flag bypasses
this in the normal empirical-run command.

Usage:
    python3 benchmark/design/verify_experiment_freeze.py
        [--freeze-file experiment-freeze-v4.json]

Importable as:
    from verify_experiment_freeze import verify_freeze
    ok, violations = verify_freeze()

Both this module and runner.py read the SAME authoritative filename --
config.EXPERIMENT_FREEZE_FILENAME -- rather than each independently
hardcoding a versioned freeze filename. That duplication is exactly what
previously let runner.py silently keep recording a stale v2 freeze hash
in run_result.json after this verifier had already moved on to v3.
"""

import hashlib
import json
import os
import subprocess
import sys

DESIGN_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(DESIGN_DIR)
HARNESS_DIR = os.path.join(BENCH, "harness")

sys.path.insert(0, HARNESS_DIR)
import config  # noqa: E402  (harness/config.py, path inserted above)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def sha256_tree(root, exclude_names=(".DS_Store", "__pycache__")):
    lines = []
    for dp, dns, fs in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in exclude_names)
        for fn in sorted(fs):
            if fn in exclude_names or fn.endswith(".pyc"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            with open(p, "rb") as fh:
                lines.append(f"{rel}:{hashlib.sha256(fh.read()).hexdigest()}")
    lines.sort()
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _installed_claude_version():
    try:
        out = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
        # e.g. "2.1.270 (Claude Code)" -> "2.1.270"
        return out.split()[0] if out else None
    except Exception as e:
        return f"<error: {e}>"


def verify_freeze(freeze_filename=None):
    """Returns (ok: bool, violations: list[str]). Defaults to
    config.EXPERIMENT_FREEZE_FILENAME -- the one authoritative freeze
    filename shared with runner.py."""
    if freeze_filename is None:
        freeze_filename = config.EXPERIMENT_FREEZE_FILENAME

    freeze_path = os.path.join(DESIGN_DIR, freeze_filename)
    violations = []

    if not os.path.exists(freeze_path):
        return False, [f"freeze file not found: {freeze_path}"]

    with open(freeze_path) as f:
        frozen = json.load(f)

    def check(label, expected, actual):
        if expected != actual:
            violations.append(f"{label}: frozen={expected!r} actual={actual!r}")

    check("manifest_sha256", frozen.get("manifest_sha256"),
          sha256_file(os.path.join(BENCH, "design", "manifest-v3.1.json")))
    check("validator_sha256", frozen.get("validator_sha256"),
          sha256_file(os.path.join(BENCH, "design", "validate_manifest.py")))
    check("shared_grader_sha256", frozen.get("shared_grader_sha256"),
          sha256_file(os.path.join(BENCH, "graders", "grade_run.py")))
    check("grader_selftest_sha256", frozen.get("grader_selftest_sha256"),
          sha256_file(os.path.join(BENCH, "graders", "grade_run_selftest.py")))

    for fn, h in (frozen.get("harness_files_sha256") or {}).items():
        p = os.path.join(HARNESS_DIR, fn)
        check(f"harness:{fn}", h, sha256_file(p) if os.path.exists(p) else None)

    for fn, h in (frozen.get("needs_intent_scoring_protocol_sha256") or {}).items():
        p = os.path.join(DESIGN_DIR, fn)
        check(f"needs_intent_protocol:{fn}", h, sha256_file(p) if os.path.exists(p) else None)

    for fn, h in (frozen.get("prompt_files_sha256") or {}).items():
        p = os.path.join(BENCH, "prompts", fn)
        check(f"prompt:{fn}", h, sha256_file(p) if os.path.exists(p) else None)

    for rel, h in (frozen.get("public_case_files_sha256") or {}).items():
        p = os.path.join(BENCH, "cases", rel)
        actual = sha256_file(p) if os.path.exists(p) else None
        if actual != h:
            violations.append(f"public_case_file:{rel}: frozen={h!r} actual={actual!r}")

    for rel, h in (frozen.get("private_oracle_files_sha256") or {}).items():
        p = os.path.join(BENCH, "cases-private", rel)
        actual = sha256_file(p) if os.path.exists(p) else None
        if actual != h:
            violations.append(f"private_oracle_file:{rel}: frozen={h!r} actual={actual!r}")

    if frozen.get("interaction_doctor_v1_skill_tree", {}).get("aggregate_sha256"):
        check("interaction_doctor_v1_skill_tree.aggregate_sha256",
              frozen["interaction_doctor_v1_skill_tree"]["aggregate_sha256"],
              sha256_tree(config.SKILL_SRC))

    if frozen.get("doc_files_sha256"):
        for fn, h in frozen["doc_files_sha256"].items():
            p = os.path.join(BENCH, fn)
            check(f"doc:{fn}", h, sha256_file(p) if os.path.exists(p) else None)

    mc = frozen.get("model_configuration") or {}
    check("model", mc.get("model"), config.MODEL)
    check("effort", mc.get("effort"), config.EFFORT)
    check("event_log_mode", frozen.get("event_log_mode"), config.EVENT_LOG_MODE)
    check("expected_arms", frozen.get("expected_arms"), list(config.ARMS))

    ts = frozen.get("tool_surface_configuration") or {}
    check("tools", ts.get("tools"), config.TOOLS)
    check("disallowed_tools", ts.get("disallowed_tools"), config.DISALLOWED_TOOLS)
    check("forbidden_tools", ts.get("forbidden_tools"), list(config.FORBIDDEN_TOOLS))
    check("required_tools_all_arms", ts.get("required_tools_all_arms"),
          list(config.REQUIRED_TOOLS_ALL_ARMS))

    ne = frozen.get("network_egress_configuration") or {}
    check("model_service_egress_host", ne.get("host"), config.MODEL_SERVICE_EGRESS_HOST)
    check("model_service_egress_port", ne.get("port"), config.MODEL_SERVICE_EGRESS_PORT)
    check("wildcard_fallback_allowed", ne.get("wildcard_fallback_allowed"),
          config.WILDCARD_EGRESS_FALLBACK_ALLOWED)

    pf = frozen.get("preflight_configuration") or {}
    check("preflight_case_id", pf.get("case_id"), config.PREFLIGHT_CASE_ID)
    check("preflight_arms", pf.get("arms"), list(config.PREFLIGHT_ARMS))
    check("preflight_expected_run_count", pf.get("expected_run_count"),
          config.PREFLIGHT_EXPECTED_RUN_COUNT)

    frozen_cli_version = frozen.get("claude_cli_version")
    installed_version = _installed_claude_version()
    check("claude_cli_version", frozen_cli_version, installed_version)
    check("config.FROZEN_CLAUDE_CLI_VERSION matches frozen file",
          frozen_cli_version, config.FROZEN_CLAUDE_CLI_VERSION)

    # The freeze file must name itself as the authoritative filename, and
    # that name must match what config.py (and therefore runner.py) is
    # actually using -- otherwise a run could verify against one freeze
    # file while recording provenance against another.
    check("experiment_freeze_filename", frozen.get("experiment_freeze_filename"),
          config.EXPERIMENT_FREEZE_FILENAME)
    check("experiment_freeze_filename matches the file actually being verified",
          frozen.get("experiment_freeze_filename"), freeze_filename)

    # verifier_sha256 is stored in the freeze file but was previously never
    # checked -- this is accidental-drift detection for this verifier
    # itself, not a tamper-proofing claim (a modified verifier could always
    # rewrite this check too; the point is to catch an UNINTENTIONAL edit
    # to verify_experiment_freeze.py that nobody refroze after).
    if frozen.get("verifier_sha256"):
        check("verifier_sha256", frozen.get("verifier_sha256"), sha256_file(os.path.abspath(__file__)))

    return (len(violations) == 0), violations


def provenance_consistency_selftest():
    """Zero-cost: proves the verifier's target freeze filename and
    runner.py's provenance freeze filename are the SAME file (both read
    from config.EXPERIMENT_FREEZE_FILENAME, never independently
    hardcoded), and that runner._experiment_freeze_file_sha256() actually
    returns the hash of that exact authoritative freeze file. No Claude
    execution."""
    import inspect
    import runner  # noqa: E402  (harness/runner.py, path inserted above)

    failures = []

    def check(label, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
        if not cond:
            failures.append(label)

    runner_default = inspect.signature(runner._experiment_freeze_file_sha256).parameters[
        "freeze_filename"
    ].default
    check("runner provenance freeze filename == config.EXPERIMENT_FREEZE_FILENAME",
          runner_default == config.EXPERIMENT_FREEZE_FILENAME, runner_default)

    verify_default = inspect.signature(verify_freeze).parameters["freeze_filename"].default
    check("verifier's own default parameter is None (resolves to the same authoritative "
          "constant at call time, never a second hardcoded filename)",
          verify_default is None, verify_default)

    freeze_path = os.path.join(DESIGN_DIR, config.EXPERIMENT_FREEZE_FILENAME)
    check("authoritative freeze file exists", os.path.exists(freeze_path), freeze_path)

    recorded_hash = runner._experiment_freeze_file_sha256()
    actual_hash = sha256_file(freeze_path) if os.path.exists(freeze_path) else None
    check("runner's recorded experiment_freeze_file_sha256 == actual authoritative freeze file hash",
          recorded_hash == actual_hash and recorded_hash is not None, (recorded_hash, actual_hash))

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("RUNNER_FREEZE_PROVENANCE = FAIL")
        return False
    print("RUNNER_FREEZE_PROVENANCE = PASS")
    return True


def main():
    freeze_filename = config.EXPERIMENT_FREEZE_FILENAME
    if "--freeze-file" in sys.argv:
        freeze_filename = sys.argv[sys.argv.index("--freeze-file") + 1]

    ok, violations = verify_freeze(freeze_filename)
    if violations:
        for v in violations:
            print(f"[MISMATCH] {v}")
    print()
    if ok:
        print("EXPERIMENT_FREEZE_HASH_VERIFY = PASS")
    else:
        print(f"EXPERIMENT_FREEZE_HASH_VERIFY = FAIL ({len(violations)} mismatches)")

    print()
    provenance_ok = provenance_consistency_selftest()

    sys.exit(0 if (ok and provenance_ok) else 1)


if __name__ == "__main__":
    main()
