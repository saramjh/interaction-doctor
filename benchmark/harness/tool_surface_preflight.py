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
results). The full required sequence is: commit the immutable snapshot ->
verify_experiment_freeze.py passes -> the 3 preflight runs execute under
the identical hardened sandbox/proxy -> validate_system_init_event() is
run against ALL THREE archived system/init events -> the doctor run's
event log is checked for an actual Skill tool_use naming
interaction-doctor via validate_skill_invocation_occurred() -> only then
may the remaining 87 empirical runs proceed. See
config.EXPERIMENT_PREFLIGHT_REQUIRED for the authoritative statement of
this sequence.
"""

import sys

from config import (
    DOCTOR_REQUIRED_SKILL_SUBSTRING,
    FORBIDDEN_TOOLS,
    REQUIRED_TOOLS_ALL_ARMS,
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


def validate_system_init_event(system_init_event: dict, arm: str) -> list:
    """Returns a list of violation strings; empty list means PASS."""
    violations = []
    tools = get_tools_list(system_init_event)

    for forbidden in FORBIDDEN_TOOLS:
        if forbidden in tools:
            violations.append(f"forbidden tool present: {forbidden}")

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


def validate_skill_invocation_occurred(event_log: list) -> bool:
    """For the doctor arm: confirms an actual Skill tool_use event naming
    interaction-doctor occurred somewhere in the archived event log (not
    merely that the skill was DISCOVERABLE per system/init)."""
    for event in event_log:
        if not isinstance(event, dict):
            continue
        message = event.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                skill_input = block.get("input") or {}
                target = str(skill_input.get("skill") or skill_input.get("name") or "")
                if DOCTOR_REQUIRED_SKILL_SUBSTRING in target:
                    return True
    return False


def run_static_selftest():
    """Zero-cost: confirms build_args() itself requests the intended
    boundary via --tools, not --allowedTools, and never names a forbidden
    tool anywhere in the constructed argv."""
    sys.path.insert(0, ".")
    import runner  # noqa: E402
    from config import TOOLS, DISALLOWED_TOOLS  # noqa: E402

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

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("TOOL_SURFACE_STATIC_LOCKDOWN = FAIL")
        return False
    print("TOOL_SURFACE_STATIC_LOCKDOWN = PASS")
    return True


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

    skill_use_log = [
        {"message": {"content": [{"type": "tool_use", "name": "Skill",
                                   "input": {"skill": "interaction-doctor"}}]}}
    ]
    no_skill_use_log = [
        {"message": {"content": [{"type": "text", "text": "hello"}]}}
    ]
    check("skill invocation detector: finds a real Skill/interaction-doctor tool_use",
          validate_skill_invocation_occurred(skill_use_log) is True)
    check("skill invocation detector: absence correctly detected",
          validate_skill_invocation_occurred(no_skill_use_log) is False)

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
