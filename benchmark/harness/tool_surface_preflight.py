#!/usr/bin/env python3
"""Tool-surface preflight: (1) a zero-cost STATIC check that build_args()
actually requests the intended tool boundary via --tools (never relying on
--allowedTools as the availability mechanism), and (2) a validator for the
REQUIRED live-preflight invariant -- inspecting an arm's actual archived
system/init event (from a real EVENT_LOG_MODE run) to confirm forbidden
tools are genuinely absent and required tools genuinely present, since
--allowedTools alone does NOT define tool availability (confirmed against
the benchmark's own prior archived Doctor event log, which listed
WebFetch/WebSearch/Task/ToolSearch as available despite none of them being
in --allowedTools).

Part (2) cannot be exercised against a REAL event without a paid Claude
call; this module's selftest instead proves the VALIDATOR LOGIC itself is
correct against synthetic event objects shaped like a documented
stream-json system/init event. The exact field names must be reconfirmed
against real archived events during the live preflight -- FIELD_CANDIDATES
below is deliberately tolerant of a couple of plausible shapes for exactly
that reason, and this limitation is documented, not hidden.

The live preflight this module supports is EXACTLY config.PREFLIGHT_CASE_ID
run under all three of config.PREFLIGHT_ARMS -- 3 paid `claude -p`
invocations, never 1 (a single run cannot produce "every arm" evidence)
and never more (the case is fixed in config.py, not chosen after seeing
results), executed via `orchestrate.py --preflight`. The full required
sequence is: commit the immutable snapshot -> verify_experiment_freeze.py
passes -> the 3 preflight runs execute under the ACTIVE v6 architecture --
the Claude Code parent unsandboxed by the harness, built-in tools governed
by the trusted inline --settings permission policy under
--permission-mode dontAsk, and Bash governed by Claude Code's own native
Seatbelt sandbox (sandbox.* keys, fail-closed) -- NOT the retired v4/v5
custom outer sandbox/proxy, which is inactive historical code only (see
config.py's module docstring) -> validate_system_init_event() is run
against ALL THREE archived system/init events (integrated into
orchestrate.run_preflight_sequential via
validate_arm_tool_surface_and_skill()) -> the doctor run's event log is
checked for an actual Skill tool_use naming interaction-doctor via
validate_skill_invocation_occurred() -> preflight_validator.py's 9
infrastructure-probe assertions are also scored from real, bound
tool_use/tool_result evidence (never from assistant text alone) ->
orchestrate.aggregate_preflight() combines all of the above into one
explicit PASS/HOLD gate -> only then may the 90 FRESH empirical runs
proceed, and only as a separate, explicit, human-authorized invocation --
no code path in this harness auto-starts them. See
config.EXPERIMENT_PREFLIGHT_REQUIRED for the authoritative statement of
this sequence.
"""

import os
import sys

from config import (
    DOCTOR_REQUIRED_SKILL_SUBSTRING,
    FORBIDDEN_TOOLS,
    REQUIRED_TOOLS_ALL_ARMS,
    TOOLS,
)

TOOLS_FIELD_CANDIDATES = ("tools", "available_tools", "tool_names")
SKILLS_FIELD_CANDIDATES = ("skills", "slash_commands", "available_skills")


def _first_present(event: dict, candidates):
    for key in candidates:
        if key in event:
            return event[key]
    return None


def get_tools_list(system_init_event: dict) -> list:
    tools = _first_present(system_init_event, TOOLS_FIELD_CANDIDATES)
    if tools is None:
        raise KeyError(
            "no recognized tools field in system/init event "
            f"(tried {TOOLS_FIELD_CANDIDATES}); update TOOLS_FIELD_CANDIDATES "
            "against a real archived event before the live preflight"
        )
    return list(tools)


def get_skill_names(system_init_event: dict) -> list:
    skills = _first_present(system_init_event, SKILLS_FIELD_CANDIDATES) or []
    names = []
    for s in skills:
        if isinstance(s, str):
            names.append(s)
        elif isinstance(s, dict):
            names.append(s.get("name", "") or s.get("id", ""))
    return names


EXPECTED_TOOL_SET = frozenset(TOOLS.split(","))


def validate_system_init_event(system_init_event: dict, arm: str) -> list:
    """Returns a list of violation strings; empty list means PASS.

    CORRECTION (post-report): checking only "no KNOWN forbidden tool
    present" is weaker than the frozen experiment condition -- it says
    nothing about a tool this harness never anticipated (reproduced: a
    synthetic system/init containing the expected set PLUS "CronCreate"
    previously produced zero violations, since CronCreate was never added
    to FORBIDDEN_TOOLS). The real archived system/init event already in
    this repo (a Phase-1 smoke-test run, pre-v6, under bypassPermissions)
    independently confirms this is not a theoretical concern: its real
    "tools" list includes many tools well beyond config.TOOLS (Task,
    CronCreate, CronDelete, DesignSync, ListAgents, Monitor, NotebookEdit,
    PushNotification, RemoteTrigger, ReportFindings, ScheduleWakeup,
    SendMessage, TaskOutput, TaskStop, ToolSearch, WebFetch, WebSearch, ...).

    The expected available built-in tool set is now required to be EXACTLY
    EXPECTED_TOOL_SET (== set(config.TOOLS.split(","))) -- missing and
    unexpected tools are reported separately, and ANY unexpected tool is a
    violation even if it was never explicitly added to FORBIDDEN_TOOLS.
    FORBIDDEN_TOOLS is still checked too, as a named, human-readable
    belt-and-suspenders list, but it is no longer the boundary."""
    violations = []
    tools = get_tools_list(system_init_event)
    actual_set = set(tools)

    missing = sorted(EXPECTED_TOOL_SET - actual_set)
    unexpected = sorted(actual_set - EXPECTED_TOOL_SET)
    for t in missing:
        violations.append(f"expected tool missing: {t}")
    for t in unexpected:
        violations.append(f"unexpected tool present (not in config.TOOLS): {t}")

    # FORBIDDEN_TOOLS is a subset of "everything outside EXPECTED_TOOL_SET",
    # so any forbidden tool present is already caught by the unexpected-tool
    # check above; this defensive assertion just confirms that overlap
    # actually holds so FORBIDDEN_TOOLS never silently stops mattering.
    assert not (set(FORBIDDEN_TOOLS) & EXPECTED_TOOL_SET), (
        "FORBIDDEN_TOOLS and EXPECTED_TOOL_SET must never overlap"
    )

    for required in REQUIRED_TOOLS_ALL_ARMS:
        if required not in tools:
            violations.append(f"required tool missing: {required}")

    skill_names = get_skill_names(system_init_event)
    has_doctor_skill = any(DOCTOR_REQUIRED_SKILL_SUBSTRING in name for name in skill_names)

    if arm == "doctor" and not has_doctor_skill:
        violations.append(
            f"doctor arm: {DOCTOR_REQUIRED_SKILL_SUBSTRING!r} not present in skills/slash_commands"
        )
    if arm in ("baseline", "generic") and has_doctor_skill:
        violations.append(
            f"{arm} arm: {DOCTOR_REQUIRED_SKILL_SUBSTRING!r} unexpectedly present"
        )

    return violations


def _content_blocks(event_log):
    for event in event_log:
        if not isinstance(event, dict):
            continue
        message = event.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict):
                yield block


def _find_doctor_skill_tool_use_ids(event_log):
    ids = []
    for block in _content_blocks(event_log):
        if block.get("type") == "tool_use" and block.get("name") == "Skill":
            skill_input = block.get("input") or {}
            target = str(skill_input.get("skill") or skill_input.get("name") or "")
            if DOCTOR_REQUIRED_SKILL_SUBSTRING in target:
                tid = block.get("id") or block.get("tool_use_id")
                if tid:
                    ids.append(tid)
    return ids


def validate_skill_invocation_occurred(event_log: list) -> bool:
    """For the doctor arm: confirms an actual Skill tool_use event naming
    interaction-doctor occurred somewhere in the archived event log (not
    merely that the skill was DISCOVERABLE per system/init). Does NOT by
    itself confirm the invocation succeeded -- see
    validate_skill_invocation_succeeded() for that stricter check."""
    return len(_find_doctor_skill_tool_use_ids(event_log)) > 0


def _tool_result_content_text(block) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
        )
    return ""


def validate_skill_invocation_succeeded(event_log: list):
    """Stricter than validate_skill_invocation_occurred(): finds the
    matching tool_result (by tool_use_id) for a real Skill tool_use naming
    interaction-doctor and confirms it indicates success. An invocation
    that OCCURRED but whose result indicates failure (or is unrecognizable)
    must not be reported as a successful doctor-skill invocation.

    CORRECTION (post-report): the real, already-archived 2.1.270 event
    (results/raw/case-001-media-library/doctor/run-01-20260913T120647469326Z)
    for a genuine successful interaction-doctor invocation carries NO
    `is_error` field at all -- only a tool_result content string
    "Launching skill: interaction-doctor" (config.DOCTOR_SKILL_SUCCESS_CONTENT_PREFIX).
    The original is_error-only logic classified this real success as HOLD.
    Semantics, in order:
      - is_error == True                                    -> FAIL (False)
      - is_error == False                                   -> PASS (True)
      - is_error absent AND content starts with the frozen
        success-content prefix (case-sensitive, exact match to
        the real observed evidence)                          -> PASS (True)
      - matching result exists but is ambiguous/unrecognized  -> HOLD (None)
    Ordinary assistant prose is never consulted -- only tool_result blocks
    bound to a genuine Skill tool_use by tool_use_id.

    Returns True (succeeded), False (occurred but failed, or never
    occurred at all), or None (a bound tool_result exists but its shape is
    not recognized as either -- insufficient evidence, caller must treat
    this as HOLD, never as True)."""
    from config import DOCTOR_SKILL_SUCCESS_CONTENT_PREFIX

    tool_use_ids = _find_doctor_skill_tool_use_ids(event_log)
    if not tool_use_ids:
        return False
    for tid in tool_use_ids:
        for block in _content_blocks(event_log):
            if block.get("type") == "tool_result" and block.get("tool_use_id") == tid:
                if block.get("is_error") is True:
                    return False
                if block.get("is_error") is False:
                    return True
                text = _tool_result_content_text(block)
                if text.startswith(DOCTOR_SKILL_SUCCESS_CONTENT_PREFIX):
                    return True
                # is_error absent AND content doesn't match the recognized
                # success shape: ambiguous, not a trustworthy signal either
                # way -- keep looking at any other matching tool_use id,
                # otherwise fall through to HOLD.
    return None


def run_static_selftest():
    """Zero-cost: confirms build_args() itself requests the intended
    boundary via --tools, not --allowedTools, and never names a forbidden
    tool anywhere in the constructed argv.

    v6: --allowedTools (the old broad, bypassPermissions-era grant) must be
    ABSENT entirely -- real authorization now comes from the trusted
    --settings policy, evaluated under --permission-mode dontAsk."""
    import json as _json

    sys.path.insert(0, ".")
    import runner  # noqa: E402
    from config import TOOLS, DISALLOWED_TOOLS, PERMISSION_MODE  # noqa: E402

    failures = []

    def check(label, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
        if not cond:
            failures.append(label)

    for arm in ("baseline", "generic", "doctor"):
        args = runner.build_args(arm, "/tmp/fake-ws", "fake prompt")
        check(f"{arm}: --tools is present and set to the intended boundary",
              "--tools" in args and args[args.index("--tools") + 1] == TOOLS, args)
        check(f"{arm}: --disallowedTools present (belt-and-suspenders)",
              "--disallowedTools" in args and args[args.index("--disallowedTools") + 1] == DISALLOWED_TOOLS)
        tools_value = args[args.index("--tools") + 1]
        for forbidden in FORBIDDEN_TOOLS:
            check(f"{arm}: {forbidden} absent from --tools value",
                  forbidden not in tools_value.split(","))
        check(f"{arm}: Skill present in --tools value",
              "Skill" in tools_value.split(","))
        check(f"{arm}: --strict-mcp-config present",
              "--strict-mcp-config" in args)
        check(f"{arm}: --allowedTools ABSENT (v6: authorization moved to trusted --settings)",
              "--allowedTools" not in args)
        check(f"{arm}: --permission-mode present and equal to {PERMISSION_MODE!r} (not bypassPermissions)",
              "--permission-mode" in args
              and args[args.index("--permission-mode") + 1] == PERMISSION_MODE
              and args[args.index("--permission-mode") + 1] != "bypassPermissions")
        check(f"{arm}: --settings present with a well-formed JSON payload",
              "--settings" in args and _settings_json_parses(args))
        if "--settings" in args and _settings_json_parses(args):
            payload = _json.loads(args[args.index("--settings") + 1])
            check(f"{arm}: --settings payload declares permissions.defaultMode == {PERMISSION_MODE!r}",
                  payload.get("permissions", {}).get("defaultMode") == PERMISSION_MODE)
            check(f"{arm}: --settings payload declares sandbox.enabled == True",
                  payload.get("sandbox", {}).get("enabled") is True)
            check(f"{arm}: --settings payload declares sandbox.failIfUnavailable == True",
                  payload.get("sandbox", {}).get("failIfUnavailable") is True)
            check(f"{arm}: --settings payload declares sandbox.allowUnsandboxedCommands == False",
                  payload.get("sandbox", {}).get("allowUnsandboxedCommands") is False)
            check(f"{arm}: --settings payload declares sandbox.excludedCommands == []",
                  payload.get("sandbox", {}).get("excludedCommands") == [])
            check(f"{arm}: --settings payload declares sandbox.filesystem.disabled == False",
                  payload.get("sandbox", {}).get("filesystem", {}).get("disabled") is False)
            check(f"{arm}: --settings payload declares sandbox.network.strictAllowlist == True",
                  payload.get("sandbox", {}).get("network", {}).get("strictAllowlist") is True)
            check(f"{arm}: --settings payload declares sandbox.network.allowedDomains == []",
                  payload.get("sandbox", {}).get("network", {}).get("allowedDomains") == [])

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("TOOL_SURFACE_STATIC_LOCKDOWN = FAIL")
        return False
    print("TOOL_SURFACE_STATIC_LOCKDOWN = PASS")
    return True


def _settings_json_parses(args) -> bool:
    import json as _json
    try:
        idx = args.index("--settings")
        _json.loads(args[idx + 1])
        return True
    except (ValueError, IndexError, TypeError, _json.JSONDecodeError):
        return False


def run_validator_selftest():
    """Zero-cost: proves validate_system_init_event()'s LOGIC is correct
    against synthetic event objects. Does not, and cannot, prove the field
    names match a real Claude Code system/init event without a real call
    -- see module docstring."""
    failures = []

    def check(label, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
        if not cond:
            failures.append(label)

    clean_event = {
        "tools": ["Read", "Edit", "Write", "Glob", "Grep", "Bash", "Skill"],
        "skills": ["design", "dataviz", "code-review"],
    }
    doctor_event = {
        "tools": ["Read", "Edit", "Write", "Glob", "Grep", "Bash", "Skill"],
        "skills": ["design", "dataviz", "interaction-doctor"],
    }
    dirty_event = {
        "tools": ["Read", "Edit", "Write", "Glob", "Grep", "Bash", "Skill",
                  "WebFetch", "WebSearch", "Task", "ToolSearch"],
        "skills": ["design"],
    }
    missing_skill_event = {
        "tools": ["Read", "Edit", "Write", "Glob", "Grep", "Bash"],  # no Skill
        "skills": [],
    }

    check("baseline: clean event (no interaction-doctor) -> no violations",
          validate_system_init_event(clean_event, "baseline") == [])
    check("generic: clean event -> no violations",
          validate_system_init_event(clean_event, "generic") == [])
    check("doctor: doctor_event (has interaction-doctor) -> no violations",
          validate_system_init_event(doctor_event, "doctor") == [])
    check("baseline: interaction-doctor unexpectedly present -> violation",
          len(validate_system_init_event(doctor_event, "baseline")) > 0)
    check("doctor: interaction-doctor missing -> violation",
          len(validate_system_init_event(clean_event, "doctor")) > 0)
    check("any arm: dirty_event with forbidden tools -> violations for each",
          len(validate_system_init_event(dirty_event, "baseline")) >= 4)
    check("any arm: missing Skill tool -> violation",
          len(validate_system_init_event(missing_skill_event, "baseline")) >= 1)

    # ADVERSARIAL (item 4): exact tool-set equality, not just "no known
    # forbidden tool." Reproduced failure: expected set + an unlisted tool
    # (CronCreate, never added to FORBIDDEN_TOOLS) previously produced ZERO
    # violations.
    exact_expected_event = {"tools": sorted(EXPECTED_TOOL_SET), "skills": []}
    check("ADVERSARIAL: exact expected tool set -> no violations",
          validate_system_init_event(exact_expected_event, "baseline") == [])

    cron_event = {"tools": sorted(EXPECTED_TOOL_SET | {"CronCreate"}), "skills": []}
    cron_violations = validate_system_init_event(cron_event, "baseline")
    check("ADVERSARIAL: expected set + CronCreate (never listed in "
          "FORBIDDEN_TOOLS) -> FAIL (exact-set equality catches it anyway)",
          any("CronCreate" in v for v in cron_violations), cron_violations)

    arbitrary_unknown_event = {"tools": sorted(EXPECTED_TOOL_SET | {"SomeFutureToolXYZ"}),
                                "skills": []}
    arbitrary_violations = validate_system_init_event(arbitrary_unknown_event, "baseline")
    check("ADVERSARIAL: expected set + an arbitrary unknown tool name -> FAIL",
          any("SomeFutureToolXYZ" in v for v in arbitrary_violations), arbitrary_violations)

    missing_edit_event = {"tools": sorted(EXPECTED_TOOL_SET - {"Edit"}), "skills": []}
    missing_edit_violations = validate_system_init_event(missing_edit_event, "baseline")
    check("ADVERSARIAL: expected set with Edit removed -> FAIL (missing expected tool)",
          any("Edit" in v for v in missing_edit_violations), missing_edit_violations)

    # ADVERSARIAL (item 5/7): validate against the ACTUAL, already-archived
    # real 2.1.270 system/init event in this repo -- not an invented shape.
    # This is historical evidence (a Phase-1 smoke-test run, pre-v6,
    # bypassPermissions) and is read-only here, never modified.
    import json as _json
    real_event_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "raw", "case-001-media-library", "doctor",
        "run-01-20260913T120647469326Z", "event_log.json",
    )
    if os.path.exists(real_event_path):
        with open(real_event_path) as f:
            real_events = _json.load(f)
        real_system_init = next(
            (e for e in real_events if isinstance(e, dict)
             and e.get("type") == "system" and e.get("subtype") == "init"),
            None,
        )
        check("real archived system/init event found in this repo (schema evidence)",
              real_system_init is not None)
        if real_system_init is not None:
            real_violations = validate_system_init_event(real_system_init, "doctor")
            # This is a pre-v6, bypassPermissions smoke-test run -- its
            # real tool list is expected to be broader than config.TOOLS
            # (that is exactly the confirmed defect this fix closes), so
            # violations are EXPECTED here, not a bug in the validator.
            check("real archived (pre-v6) system/init event's actual tool list is "
                  "broader than config.TOOLS -- the exact-set check correctly flags "
                  "this as violations rather than silently passing",
                  len(real_violations) > 0, real_violations)

        check("validate_skill_invocation_occurred() on the REAL archived doctor "
              "event log finds the real Skill/interaction-doctor tool_use",
              validate_skill_invocation_occurred(real_events) is True)
        real_success = validate_skill_invocation_succeeded(real_events)
        check("validate_skill_invocation_succeeded() on the REAL archived doctor "
              "event log (whose tool_result has NO is_error field, only "
              "'Launching skill: interaction-doctor') now correctly resolves "
              "to True, not HOLD",
              real_success is True, real_success)
    else:
        check("real archived system/init event found in this repo (schema evidence) "
              "-- SKIPPED, file not present in this checkout", True)

    skill_use_log = [
        {"message": {"content": [{"type": "tool_use", "id": "toolu_skill1", "name": "Skill",
                                   "input": {"skill": "interaction-doctor"}}]}}
    ]
    skill_use_and_success_log = skill_use_log + [
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_skill1",
                                   "is_error": False, "content": "ok"}]}}
    ]
    skill_use_and_failure_log = skill_use_log + [
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_skill1",
                                   "is_error": True, "content": "error"}]}}
    ]
    no_skill_use_log = [
        {"message": {"content": [{"type": "text", "text": "hello"}]}}
    ]
    check("skill invocation detector: finds a real Skill/interaction-doctor tool_use",
          validate_skill_invocation_occurred(skill_use_log) is True)
    check("skill invocation detector: absence correctly detected",
          validate_skill_invocation_occurred(no_skill_use_log) is False)
    check("skill invocation succeeded detector: bound tool_result is_error=False -> True",
          validate_skill_invocation_succeeded(skill_use_and_success_log) is True)
    check("skill invocation succeeded detector: bound tool_result is_error=True -> False",
          validate_skill_invocation_succeeded(skill_use_and_failure_log) is False)
    check("skill invocation succeeded detector: tool_use occurred but no bound "
          "tool_result exists -> None (insufficient evidence, never True)",
          validate_skill_invocation_succeeded(skill_use_log) is None)
    check("skill invocation succeeded detector: no tool_use at all -> False",
          validate_skill_invocation_succeeded(no_skill_use_log) is False)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("TOOL_SURFACE_VALIDATOR_SELFTEST = FAIL")
        return False
    print("TOOL_SURFACE_VALIDATOR_SELFTEST = PASS")
    return True


if __name__ == "__main__":
    ok1 = run_static_selftest()
    print()
    ok2 = run_validator_selftest()
    sys.exit(0 if (ok1 and ok2) else 1)
