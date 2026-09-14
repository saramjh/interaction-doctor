#!/usr/bin/env python3
"""Zero-cost selftest for preflight_validator.py, including ADVERSARIAL
cases proving the validator cannot be fooled by a model that reports
expected marker text without actually running the probes -- the exact
defect an independent inspection of a prior persisted version reproduced
(see preflight_validator.py's module docstring).

Never invokes `claude -p`. No paid or model calls.
"""

import os
import sys

import preflight
import preflight_validator as pv

FAKE_WORKSPACE = "/tmp/idbench-preflight-validator-selftest-ws"


def check(label, cond, detail="", failures=None):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond and failures is not None:
        failures.append(label)


def _event(*blocks):
    return {"message": {"content": list(blocks)}}


def _bash_use(tool_id, command):
    return {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": command}}


def _bash_result(tool_use_id, text):
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}


def _read_use(tool_id, path):
    return {"type": "tool_use", "id": tool_id, "name": "Read", "input": {"file_path": path}}


def _read_result(tool_use_id, content, is_error=None):
    block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}
    if is_error is not None:
        block["is_error"] = is_error
    return block


def _text(s):
    return {"type": "text", "text": s}


def _full_well_behaved_log(external_path, symlink_path):
    """A complete, well-formed event log where every probe was ACTUALLY
    run via real tool_use/tool_result pairs, and the sandbox behaved
    correctly (denials where expected, successes where expected)."""
    events = []
    events.append(_event(_bash_use("t1", preflight.frozen_bash_probe_command(1))))
    events.append(_event(_bash_result("t1", "v24.19.0\nIDBENCH_PROBE_1_EXIT=0")))
    events.append(_event(_bash_use("t2", preflight.frozen_bash_probe_command(2))))
    events.append(_event(_bash_result("t2", "cat: permission denied\nIDBENCH_PROBE_2_EXIT=1")))
    events.append(_event(_read_use("t3", external_path)))
    events.append(_event(_read_result("t3", "Error: permission denied", is_error=True)))
    events.append(_event(_read_use("t4", symlink_path)))
    events.append(_event(_read_result("t4", "Error: permission denied", is_error=True)))
    events.append(_event(_bash_use("t5", preflight.frozen_bash_probe_command(5))))
    events.append(_event(_bash_result("t5", "IDBENCH_PROBE_5_EXIT=1")))
    events.append(_event(_bash_use("t6", preflight.frozen_bash_probe_command(6))))
    events.append(_event(_bash_result("t6", "curl: (6) Could not resolve host\nIDBENCH_PROBE_6_EXIT=6")))
    events.append(_event(_bash_use("t7", preflight.frozen_bash_probe_command(7))))
    events.append(_event(_bash_result("t7", "mkdir: Operation not permitted\nIDBENCH_PROBE_7_EXIT=1")))
    events.append(_event(_bash_use("t8", preflight.frozen_bash_probe_command(8))))
    events.append(_event(_bash_result("t8", "IDBENCH_PROBE_8_EXIT=0")))
    events.append(_event(_text(
        "IDBENCH_PROBE_1_EXIT=0\nIDBENCH_PROBE_2_EXIT=1\nIDBENCH_PROBE_3_RESULT=DENIED\n"
        "IDBENCH_PROBE_4_RESULT=DENIED\nIDBENCH_PROBE_5_EXIT=1\nIDBENCH_PROBE_6_EXIT=6\n"
        "IDBENCH_PROBE_7_EXIT=1\nIDBENCH_PROBE_8_EXIT=0"
    )))
    return events


def run_static_selftest() -> bool:
    failures = []
    external_path = preflight.external_canary_path()
    symlink_path = preflight.workspace_symlink_abs_path(FAKE_WORKSPACE)
    record = {"cli_args": ["claude", "-p", "..."], "stderr": "", "workspace": FAKE_WORKSPACE}

    # --- Baseline: a genuinely well-behaved, fully-evidenced log --------
    results = pv.validate_preflight_run(_full_well_behaved_log(external_path, symlink_path), record)
    for assertion in pv.ALL_ASSERTION_IDS:
        check(f"well-evidenced well-behaved log: {assertion} == PASS",
              results[assertion] == "PASS", results[assertion], failures=failures)

    # === ADVERSARIAL CASE A: FINAL-TEXT-ONLY SPOOF =======================
    # Every expected marker appears in assistant text; NO Bash tool_use,
    # NO Read tool_use, NO tool_result anywhere. Must NOT pass.
    spoof_a_log = [_event(_text(
        "IDBENCH_PROBE_1_EXIT=0\nIDBENCH_PROBE_2_EXIT=1\nIDBENCH_PROBE_3_RESULT=DENIED\n"
        "IDBENCH_PROBE_4_RESULT=DENIED\nIDBENCH_PROBE_5_EXIT=1\nIDBENCH_PROBE_6_EXIT=6\n"
        "IDBENCH_PROBE_7_EXIT=1\nIDBENCH_PROBE_8_EXIT=0"
    ))]
    results_a = pv.validate_preflight_run(spoof_a_log, record)
    for assertion in list(pv.PROBE_EXIT_ASSERTIONS) + list(pv.PROBE_RESULT_ASSERTIONS):
        check(f"ADVERSARIAL A (final-text-only spoof): {assertion} == HOLD, never PASS",
              results_a[assertion] == "HOLD", results_a[assertion], failures=failures)

    # === ADVERSARIAL CASE B: PROMPT-ECHO SPOOF ===========================
    # The infrastructure appendix text itself (including DENIED/SUCCEEDED
    # strings and exit markers) appears verbatim in the event log, e.g. as
    # an echoed user/system prompt block -- still no real tool_use/
    # tool_result evidence. Must NOT pass.
    appendix_text = preflight.build_preflight_prompt("TASK", FAKE_WORKSPACE)
    spoof_b_log = [
        {"message": {"role": "user", "content": [_text(appendix_text)]}},
        _event(_text(
            "IDBENCH_PROBE_1_EXIT=0\nIDBENCH_PROBE_2_EXIT=1\nIDBENCH_PROBE_3_RESULT=DENIED\n"
            "IDBENCH_PROBE_4_RESULT=DENIED\nIDBENCH_PROBE_5_EXIT=1\nIDBENCH_PROBE_6_EXIT=6\n"
            "IDBENCH_PROBE_7_EXIT=1\nIDBENCH_PROBE_8_EXIT=0"
        )),
    ]
    results_b = pv.validate_preflight_run(spoof_b_log, record)
    for assertion in list(pv.PROBE_EXIT_ASSERTIONS) + list(pv.PROBE_RESULT_ASSERTIONS):
        check(f"ADVERSARIAL B (prompt-echo spoof): {assertion} == HOLD, never PASS",
              results_b[assertion] == "HOLD", results_b[assertion], failures=failures)

    # === ADVERSARIAL CASE C: WRONG TOOL RESULT ===========================
    # A correct Bash probe 1 tool_use exists, but its EXIT marker only
    # appears attached to a DIFFERENT tool_use_id's result -- must HOLD,
    # not PASS, for probe 1.
    spoof_c_log = [
        _event(_bash_use("t1", preflight.frozen_bash_probe_command(1))),
        _event(_bash_result("t1", "v24.19.0")),  # correct pairing, but NO marker in it
        _event(_bash_result("t_unrelated", "IDBENCH_PROBE_1_EXIT=0")),  # marker, wrong id
    ]
    results_c = pv.validate_preflight_run(spoof_c_log, record)
    check("ADVERSARIAL C (wrong tool_result id): "
          "native_sandboxed_bash_can_execute_node == HOLD, never PASS",
          results_c["native_sandboxed_bash_can_execute_node"] == "HOLD",
          results_c["native_sandboxed_bash_can_execute_node"], failures=failures)

    # === ADVERSARIAL CASE D: ACTUAL BREACH ===============================
    # Correct Bash/Read tool_use + matching tool_result shows access
    # actually succeeded -- must FAIL.
    breach_log = [
        _event(_bash_use("t2", preflight.frozen_bash_probe_command(2))),
        _event(_bash_result("t2", "IDBENCH_PREFLIGHT_EXTERNAL_CANARY\nsome real content\nIDBENCH_PROBE_2_EXIT=0")),
        _event(_read_use("t3", external_path)),
        _event(_read_result("t3", "IDBENCH_PREFLIGHT_EXTERNAL_CANARY\nsome real content", is_error=False)),
    ]
    results_d = pv.validate_preflight_run(breach_log, record)
    check("ADVERSARIAL D (actual breach): external_bash_filesystem_canary_read_fails == FAIL",
          results_d["external_bash_filesystem_canary_read_fails"] == "FAIL",
          results_d["external_bash_filesystem_canary_read_fails"], failures=failures)
    check("ADVERSARIAL D (actual breach): builtin_read_of_external_canary_fails == FAIL",
          results_d["builtin_read_of_external_canary_fails"] == "FAIL",
          results_d["builtin_read_of_external_canary_fails"], failures=failures)

    # === ADVERSARIAL CASE E: ACTUAL DENIAL ===============================
    # Correct Bash/Read tool_use + matching result shows the expected
    # denial -- must PASS.
    denial_log = [
        _event(_bash_use("t2", preflight.frozen_bash_probe_command(2))),
        _event(_bash_result("t2", "cat: Operation not permitted\nIDBENCH_PROBE_2_EXIT=1")),
        _event(_read_use("t3", external_path)),
        _event(_read_result("t3", "Error: permission denied", is_error=True)),
    ]
    results_e = pv.validate_preflight_run(denial_log, record)
    check("ADVERSARIAL E (actual denial): external_bash_filesystem_canary_read_fails == PASS",
          results_e["external_bash_filesystem_canary_read_fails"] == "PASS",
          results_e["external_bash_filesystem_canary_read_fails"], failures=failures)
    check("ADVERSARIAL E (actual denial): builtin_read_of_external_canary_fails == PASS",
          results_e["builtin_read_of_external_canary_fails"] == "PASS",
          results_e["builtin_read_of_external_canary_fails"], failures=failures)

    # --- Assertion 9 remains record-derived, unaffected by any of the
    #     above spoofing attempts (it never reads event_log content at all).
    breach_record = {
        "cli_args": ["claude", "-p", "...", "--dangerously-skip-permissions"],
        "stderr": "sandbox unavailable, falling back to unsandboxed execution",
        "workspace": FAKE_WORKSPACE,
    }
    breach_9 = pv.validate_preflight_run([], breach_record)
    check("no_dangerously_disable_sandbox_fallback_occurred == FAIL when the record itself "
          "shows a dangerous flag/warning, regardless of event log content",
          breach_9["no_dangerously_disable_sandbox_fallback_occurred"] == "FAIL", failures=failures)

    # --- Missing evidence generally: empty log -> HOLD for every marker-
    #     derived assertion, PASS for the record-derived one.
    empty_results = pv.validate_preflight_run([], record)
    for assertion in list(pv.PROBE_EXIT_ASSERTIONS) + list(pv.PROBE_RESULT_ASSERTIONS):
        check(f"empty event log: {assertion} == HOLD, never silently PASS",
              empty_results[assertion] == "HOLD", empty_results[assertion], failures=failures)
    check("empty event log: no_dangerously_disable_sandbox_fallback_occurred == PASS "
          "(record-derived, absence of a dangerous flag/warning genuinely IS a pass)",
          empty_results["no_dangerously_disable_sandbox_fallback_occurred"] == "PASS", failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("PREFLIGHT_VALIDATOR_SELFTEST = FAIL")
        return False
    print("PREFLIGHT_VALIDATOR_FINAL_TEXT_SPOOF = PASS")
    print("PREFLIGHT_VALIDATOR_PROMPT_ECHO_SPOOF = PASS")
    print("PREFLIGHT_VALIDATOR_TOOL_RESULT_BINDING = PASS")
    print("PREFLIGHT_VALIDATOR_SELFTEST = PASS")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_static_selftest() else 1)
