"""Invokes one isolated Claude Code run and captures structured results.

This module performs the ONLY step in the pipeline that costs real API
money. Callers must run contamination_check.check() first and refuse to
call run() if it reports any violation.
"""

import hashlib
import json
import os
import subprocess
import time

import sandbox
from config import (
    ARMS,
    BENCHMARK_ROOT,
    COMMON_CLAUDE_ARGS,
    EVENT_LOG_MODE,
    EXPERIMENT_FREEZE_FILENAME,
    MODEL_SERVICE_EGRESS_HOSTS,
    REPO_ROOT,
    RUN_TIMEOUT_SECONDS,
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
    try:
        out = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return out.split()[0] if out else None
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
    # including baseline and generic. This is a deliberate correction from
    # an earlier draft that disabled it for all three arms and had arm C
    # read the frozen skill as plain files -- that measured "the effect of
    # extra reference documents in context," not "the effect of Claude
    # Code's installed Interaction Doctor skill," which is the actual
    # product condition under test.
    #
    # With slash-commands enabled uniformly:
    #   - all three arms have identical access to Claude Code's built-in
    #     default skills (design, dataviz, code-review, ...) -- this is
    #     now a constant across arms, not a variable, so it isn't a
    #     confound even though it wasn't true in arm C alone before.
    #   - arm C additionally has .claude/skills/interaction-doctor/ in its
    #     own workspace (workspace.py), which is the ONLY thing that
    #     differs from arm A/B's skill surface, and is discovered through
    #     the normal project-local skill mechanism, not injected as
    #     instructions to manually Read files.
    #   - arms A/B have no .claude/ directory at all in their workspace
    #     (enforced by workspace.py and contamination_check.py), so there
    #     is nothing for the skill subsystem to discover there regardless
    #     of the subsystem being enabled.
    args = COMMON_CLAUDE_ARGS
    if event_log_mode:
        # Swap the single end-of-run summary for the full per-turn event
        # stream (each line a JSON object, including tool_use/tool_result
        # content blocks -- the only way to prove which tools, including
        # Skill, an arm actually invoked). --verbose is required alongside
        # stream-json in --print mode per `claude --help`. The final line
        # of the stream is still the same `type: "result"` object plain
        # --output-format json returns, so downstream parsing is unchanged.
        idx = args.index("--output-format")
        args = args[:idx] + ["--output-format", "stream-json", "--verbose"] + args[idx + 2:]
    return ["claude", "-p", prompt, "--add-dir", workspace] + args


def run(case_id: str, arm: str, run_no: int, ws_dir: str, dry_run: bool = True) -> dict:
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
    }

    if dry_run:
        record["status"] = "not_executed_dry_run"
        _persist(ws_dir, record)
        return record

    start = time.time()
    record["start_ts"] = start
    record["sandboxed"] = True
    record["sandbox_egress_hosts"] = list(MODEL_SERVICE_EGRESS_HOSTS)
    try:
        # Every arm runs under the identical OS-level sandbox (sandbox.py):
        # filesystem access restricted to exactly `workspace`, network
        # egress restricted to MODEL_SERVICE_EGRESS_HOSTS. This is a real
        # process-isolation boundary, not a workspace-copying convention --
        # see benchmark/harness/isolation_selftest.py and
        # network_selftest.py for the zero-cost proofs, and
        # config.EXPERIMENT_PREFLIGHT_REQUIRED for the one limitation that
        # cannot be proven without a real network call to the model service.
        proc = sandbox.run_sandboxed(
            args,
            workspace_path=workspace,
            allowed_egress_hosts=MODEL_SERVICE_EGRESS_HOSTS,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
        )
        record["end_ts"] = time.time()
        record["wall_clock_seconds"] = record["end_ts"] - start
        record["returncode"] = proc.returncode
        record["stderr"] = proc.stdout and proc.stderr[-20000:]
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
