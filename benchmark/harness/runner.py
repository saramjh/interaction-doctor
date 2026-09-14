"""Invokes one isolated Claude Code run and captures structured results.

This module performs the ONLY step in the pipeline that costs real API
money. Callers must run contamination_check.check() first and refuse to
call run() if it reports any violation.

v6 ARCHITECTURE: the Claude Code PARENT process is launched normally,
UNSANDBOXED by us -- it needs its own host authentication and normal
model-service networking, neither of which the v4/v5 custom outer Seatbelt
sandbox could reliably provide (see config.py's module docstring). Isolation
is instead delegated to Claude Code's OWN native architecture: a trusted,
per-run --settings policy (settings_policy.py) governs built-in-tool
authorization (permissions.allow/deny under --permission-mode dontAsk) and
configures Claude Code's native Bash sandbox (sandbox.* keys) fail-closed.
sandbox.py (the old custom outer sandbox) is NOT imported here.
"""

import hashlib
import json
import os
import subprocess
import time

import settings_policy
from config import (
    ARMS,
    BENCHMARK_ROOT,
    CLAUDE_LAUNCHER_PATH,
    DISALLOWED_TOOLS,
    EVENT_LOG_MODE,
    EXPERIMENT_FREEZE_FILENAME,
    MAX_BUDGET_USD_PER_RUN,
    MODEL,
    EFFORT,
    PERMISSION_MODE,
    REPO_ROOT,
    RUN_TIMEOUT_SECONDS,
    TOOLS,
)


def _git_commit_sha():
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or None
    except Exception as e:
        return f"<error: {e}>"


def _claude_cli_version():
    """CORRECTION (post-report): invokes the exact frozen launcher path,
    never bare "claude" resolved through PATH -- a PATH entry shadowing
    the frozen launcher must never be able to affect this."""
    try:
        out = subprocess.run(
            [CLAUDE_LAUNCHER_PATH, "--version"], capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return out.split()[0] if out else None
    except Exception as e:
        return f"<error: {e}>"


def _claude_executable_realpath():
    try:
        return os.path.realpath(CLAUDE_LAUNCHER_PATH)
    except Exception as e:
        return f"<error: {e}>"


def _claude_executable_sha256():
    try:
        real = os.path.realpath(CLAUDE_LAUNCHER_PATH)
        if not os.path.exists(real):
            return None
        h = hashlib.sha256()
        with open(real, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"<error: {e}>"


def _experiment_freeze_file_sha256(freeze_filename=EXPERIMENT_FREEZE_FILENAME):
    p = os.path.join(BENCHMARK_ROOT, "design", freeze_filename)
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def build_args(arm: str, workspace: str, prompt: str, event_log_mode: bool = EVENT_LOG_MODE):
    # The skill/slash-command subsystem is left ENABLED for every arm,
    # including baseline and generic -- all three arms have identical
    # access to Claude Code's built-in default skills; the ONLY thing
    # that differs is whether .claude/skills/interaction-doctor/ exists
    # in that arm's workspace (workspace.py), discovered through the
    # normal project-local skill mechanism.
    #
    # v6: --allowedTools (a broad, unrestricted grant under the old
    # bypassPermissions mode) is REMOVED. --tools remains the
    # availability boundary; --disallowedTools remains as narrow,
    # redundant belt-and-suspenders. Real authorization now comes from
    # the trusted --settings policy evaluated under
    # --permission-mode dontAsk.
    settings_json = settings_policy.build_settings_json(workspace)

    args = [
        "--model", MODEL,
        "--effort", EFFORT,
        "--output-format", "json",
        "--permission-mode", PERMISSION_MODE,
        "--settings", settings_json,
        "--strict-mcp-config",
        "--setting-sources", "project",
        "--tools", TOOLS,
        "--disallowedTools", DISALLOWED_TOOLS,
        "--no-session-persistence",
        "--max-budget-usd", MAX_BUDGET_USD_PER_RUN,
    ]
    if event_log_mode:
        idx = args.index("--output-format")
        args = args[:idx] + ["--output-format", "stream-json", "--verbose"] + args[idx + 2:]
    # CORRECTION (post-report): invoke the exact frozen launcher by its
    # absolute path, never bare "claude" resolved through PATH -- a
    # different binary at the same reported version, or a PATH entry
    # shadowing the frozen launcher, must never be able to run instead.
    return [CLAUDE_LAUNCHER_PATH, "-p", prompt, "--add-dir", workspace] + args


def run(case_id: str, arm: str, run_no: int, ws_dir: str, dry_run: bool = True,
        extra_parent_env: dict = None) -> dict:
    """extra_parent_env: ONLY used by the v6 preflight mechanism
    (orchestrate.run_preflight_sequential) to place a synthetic,
    non-secret canary variable in the Claude PARENT's own subprocess
    environment, to test whether the native Bash sandbox keeps it out
    despite the parent having it. Always None for the 90 empirical runs.
    Merged on top of this harness process's own environment (os.environ),
    never replacing it -- the parent still needs its own normal
    authentication/environment."""
    assert arm in ARMS
    workspace = os.path.join(ws_dir, "workspace")
    with open(os.path.join(ws_dir, "run_manifest.json")) as f:
        manifest = json.load(f)
    prompt = manifest["prompt"]
    args = build_args(arm, workspace, prompt)

    record = {
        "case_id": case_id,
        "arm": arm,
        "run_no": run_no,
        "workspace": workspace,
        "cli_args": args,
        "dry_run": dry_run,
        "experiment_freeze_file_sha256": _experiment_freeze_file_sha256(),
        "git_commit_sha": _git_commit_sha(),
        "claude_cli_version": _claude_cli_version(),
        "claude_launcher_path": CLAUDE_LAUNCHER_PATH,
        "claude_executable_realpath": _claude_executable_realpath(),
        "claude_executable_sha256": _claude_executable_sha256(),
        "active_sandbox_architecture": "CLAUDE_NATIVE_BASH_SANDBOX",
        "custom_outer_sandbox_active": False,
        "extra_parent_env_names": sorted(extra_parent_env) if extra_parent_env else [],
        # Explicit identity fields (previously only embedded inside
        # cli_args as strings) -- kept top-level so per-run provenance
        # comparison (orchestrate.aggregate_preflight) doesn't need to
        # re-parse the argv to find them.
        "model": MODEL,
        "effort": EFFORT,
    }

    if dry_run:
        record["status"] = "not_executed_dry_run"
        _persist(ws_dir, record)
        return record

    start = time.time()
    record["start_ts"] = start
    try:
        # The Claude Code parent process is launched NORMALLY -- no
        # custom OS sandbox wraps it. Isolation is delegated to Claude
        # Code's own native architecture: the trusted --settings policy
        # (baked into `args` above) governs built-in-tool authorization
        # and configures its native Bash sandbox fail-closed. See
        # config.py's module docstring and settings_policy.py.
        run_env = None
        if extra_parent_env:
            run_env = {**os.environ, **extra_parent_env}
        proc = subprocess.run(
            args,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            env=run_env,
        )
        record["end_ts"] = time.time()
        record["wall_clock_seconds"] = record["end_ts"] - start
        record["returncode"] = proc.returncode
        record["stderr"] = proc.stderr[-20000:] if proc.stderr else proc.stderr
        if EVENT_LOG_MODE:
            events = []
            for line in proc.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            with open(os.path.join(ws_dir, "event_log.json"), "w") as f:
                json.dump(events, f, indent=2)
            record["event_count"] = len(events)
            # stream-json's terminal line is the same `type: "result"`
            # object plain --output-format json returns.
            record["result_json"] = next(
                (e for e in reversed(events) if e.get("type") == "result"), None
            )
            if record["result_json"] is None:
                record["stdout_raw"] = proc.stdout[-40000:]
        else:
            try:
                record["result_json"] = json.loads(proc.stdout)
            except json.JSONDecodeError:
                record["result_json"] = None
                record["stdout_raw"] = proc.stdout[-40000:]
        record["status"] = "completed" if proc.returncode == 0 else "nonzero_exit"
    except subprocess.TimeoutExpired as e:
        record["end_ts"] = time.time()
        record["wall_clock_seconds"] = record["end_ts"] - start
        record["status"] = "timeout"
        record["stdout_raw"] = (e.stdout or "")[-40000:] if isinstance(e.stdout, str) else None

    # capture the post-run diff of the fixture (agent's edits)
    record["files_after"] = sorted(
        os.path.relpath(os.path.join(dp, f), workspace)
        for dp, _, fs in os.walk(workspace)
        for f in fs
    )

    _persist(ws_dir, record)
    return record


def _persist(ws_dir: str, record: dict):
    with open(os.path.join(ws_dir, "run_result.json"), "w") as f:
        json.dump(record, f, indent=2, default=str)
