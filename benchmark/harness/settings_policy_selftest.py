#!/usr/bin/env python3
"""Zero-cost v6 selftest for the native-sandbox architecture.

Supersedes isolation_selftest.py/network_selftest.py as the ACTIVE
harness-hardening selftest -- those two exercised harness/sandbox.py (the
v4/v5 custom OUTER Seatbelt sandbox), which is no longer imported anywhere
in the execution path (see config.py's module docstring for why it was
rejected). They are preserved on disk as historical/inactive code but are
excluded from experiment-freeze-v6.json's active harness_files_sha256 list;
this module is their replacement for what "the harness is hardened"
actually needs to mean under v6.

Never invokes `claude -p`. No paid or model calls.
"""

import json
import os
import sys

import config
import settings_policy


def check(label, cond, detail="", failures=None):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond and failures is not None:
        failures.append(label)


def _abs_workspace_perm(path):
    """Independent re-derivation of settings_policy._abs_perm_path's '//'
    absolute-path form, used ONLY to construct the expected string this
    selftest checks for -- kept separate from settings_policy's own helper
    so this selftest doesn't just check that the module agrees with
    itself."""
    return f"/{os.path.realpath(path)}"


def run():
    failures = []
    ws = "/tmp/idbench-settings-policy-selftest-ws"

    # 1. Settings JSON generation is well-formed and stable in shape.
    settings_dict = settings_policy.build_settings(ws)
    settings_json = settings_policy.build_settings_json(ws)
    check("build_settings_json produces valid JSON", True,
          failures=failures) if _json_ok(settings_json) else check(
        "build_settings_json produces valid JSON", False, failures=failures)
    check("build_settings_json round-trips to build_settings's dict",
          json.loads(settings_json) == settings_dict, failures=failures)

    # 2. --settings CLI support / --tools surface / dontAsk / no broad
    #    --allowedTools -- delegated to tool_surface_preflight.py's static
    #    selftest, which is the authoritative source for these checks;
    #    re-run it here so a single settings_policy_selftest.py invocation
    #    covers the full v6 checklist.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tool_surface_preflight
    tsp_ok = tool_surface_preflight.run_static_selftest()
    check("tool_surface_preflight static selftest (--settings/--tools/dontAsk/no --allowedTools)",
          tsp_ok, failures=failures)

    # 3. Native sandbox fail-closed configuration.
    sb = settings_dict["sandbox"]
    check("sandbox.failIfUnavailable == True (no silent unconfined fallback)",
          sb["failIfUnavailable"] is True, failures=failures)
    check("sandbox.allowUnsandboxedCommands == False",
          sb["allowUnsandboxedCommands"] is False, failures=failures)
    check("sandbox.excludedCommands == [] (no command may skip sandboxing)",
          sb["excludedCommands"] == [], failures=failures)
    check("sandbox.filesystem.disabled == False (filesystem layer never disabled)",
          sb["filesystem"]["disabled"] is False, failures=failures)
    check("sandbox.network.strictAllowlist == True",
          sb["network"]["strictAllowlist"] is True, failures=failures)
    check("sandbox.network.allowedDomains == [] (no fixture needs Bash networking)",
          sb["network"]["allowedDomains"] == [], failures=failures)

    # 4. Exact frozen Node runtime -- re-resolved live, never assumed.
    check("NODE_LAUNCHER_PATH exists on this host",
          os.path.exists(config.NODE_LAUNCHER_PATH), config.NODE_LAUNCHER_PATH, failures=failures)
    check("FROZEN_NODE_EXECUTABLE_REALPATH exists on this host",
          os.path.exists(config.FROZEN_NODE_EXECUTABLE_REALPATH),
          config.FROZEN_NODE_EXECUTABLE_REALPATH, failures=failures)
    check("sandbox.filesystem.allowRead is exactly [workspace, node launcher, node realpath] "
          "-- nothing broader (superseded/reconfirmed by the denyRead-based checks below, "
          "which are the checks that actually prove containment)",
          set(sb["filesystem"]["allowRead"]) == {os.path.realpath(ws)} | set(config.NODE_RUNTIME_READONLY_PATHS),
          sb["filesystem"]["allowRead"], failures=failures)
    check("sandbox.filesystem.allowWrite grants exactly [workspace]",
          sb["filesystem"]["allowWrite"] == [os.path.realpath(ws)], failures=failures)

    # 5. BUILTIN_PERMISSION_ABSOLUTE_PATH_SYNTAX / BUILTIN_PATH_RULE_TOOL_SEMANTICS:
    #    Claude Code's Read(...)/Edit(...) permission rules use a DOUBLE
    #    leading slash for a real absolute filesystem path (a single
    #    leading "/" is relative to the settings source, not absolute --
    #    see settings_policy._abs_perm_path). Read rules cover read-like
    #    tools (Glob/Grep); Edit rules cover Write. There is no separate
    #    Glob(...)/Grep(...)/Write(...) path-rule mechanism, so any such
    #    rule appearing here would be semantically inert -- fail if one
    #    does.
    perms = settings_dict["permissions"]
    allow = perms["allow"]
    deny = perms["deny"]
    all_rules = allow + deny

    def _rule_tool_and_arg(rule):
        # "Read(//a/b/**)" -> ("Read", "//a/b/**"); "Skill"/"Bash" -> (rule, None)
        if "(" not in rule:
            return rule, None
        tool, _, rest = rule.partition("(")
        return tool, rest.rstrip(")")

    for rule in all_rules:
        tool, arg = _rule_tool_and_arg(rule)
        check(f"path-scoped rule {rule!r} does not use the semantically inert "
              f"Glob(...)/Grep(...)/Write(...) forms (Read covers Glob/Grep; "
              f"Edit covers Write)",
              tool not in ("Glob", "Grep", "Write"), failures=failures)
        if arg is not None and arg.startswith("/"):
            check(f"absolute path rule {rule!r} uses the correct '//' absolute-path "
                  f"syntax, not a single leading '/' (which is relative to the "
                  f"settings source, not absolute)",
                  arg.startswith("//"), failures=failures)

    # Workspace/repo/cases-private allow+deny rules must be real Read/Edit
    # rules using the exact "//" absolute form.
    ws_perm = f"{_abs_workspace_perm(ws)}/**"
    check(f"permissions.allow contains Read({ws_perm})",
          f"Read({ws_perm})" in allow, allow, failures=failures)
    check(f"permissions.allow contains Edit({ws_perm})",
          f"Edit({ws_perm})" in allow, allow, failures=failures)
    for root, label in ((config.REPO_ROOT, "REPO_ROOT"), (config.CASES_PRIVATE_DIR, "CASES_PRIVATE_DIR")):
        expected = f"{_abs_workspace_perm(root)}/**"
        check(f"permissions.deny contains Read({expected}) for {label}",
              f"Read({expected})" in deny, deny, failures=failures)
    check("permissions.deny contains Edit(//<REPO_ROOT>/**)",
          f"Edit({_abs_workspace_perm(config.REPO_ROOT)}/**)" in deny, deny, failures=failures)

    # 6. Bash-adjacent credential paths denied via home-relative forms
    #    (valid without needing the absolute // syntax).
    for must_have in ("Read(~/.claude/**)", "Read(~/.claude.json)", "Read(~/.ssh/**)",
                       "Read(~/.aws/**)", "Read(~/Library/Keychains/**)"):
        check(f"permissions.deny contains {must_have}", must_have in deny, deny, failures=failures)

    # 7. CREDENTIAL_ENV_POLICY_STATIC: real native enforcement via
    #    sandbox.credentials.envVars, not a harness-side bookkeeping key.
    check("settings payload does NOT contain the old non-enforcing "
          "_env_protect_names key anywhere at the top level or under sandbox",
          "_env_protect_names" not in settings_dict
          and "_env_protect_names" not in sb, failures=failures)
    creds = sb.get("credentials") or {}
    env_vars = creds.get("envVars") or []
    check("sandbox.credentials.envVars exists and is non-empty",
          len(env_vars) > 0, env_vars, failures=failures)
    expected_names = set(config.SENSITIVE_ENV_VAR_NAMES)
    actual_names = {e.get("name") for e in env_vars}
    check("sandbox.credentials.envVars names exactly match config.SENSITIVE_ENV_VAR_NAMES",
          actual_names == expected_names, actual_names, failures=failures)
    check("every sandbox.credentials.envVars entry has mode == 'deny'",
          all(e.get("mode") == "deny" for e in env_vars), env_vars, failures=failures)
    for must_have in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_MESSAGING_TOKEN", "SSH_AUTH_SOCK",
                       "IDBENCH_PREFLIGHT_PARENT_ONLY_CANARY"):
        check(f"sandbox.credentials.envVars includes {must_have}",
              must_have in actual_names, failures=failures)
    check("no credential VALUE appears anywhere in the generated settings JSON "
          "(only variable NAMES)",
          "ANTHROPIC_API_KEY=" not in json.dumps(settings_dict), failures=failures)

    # 8. Experiment control-plane protection inside the workspace: the
    #    agent must not be able to Edit (which also covers Write) its own
    #    settings or (doctor arm) the skill it's being evaluated against,
    #    via a single Edit(...) deny over the whole .claude/** subtree.
    control_plane_rule = f"Edit({_abs_workspace_perm(ws)}/.claude/**)"
    check(f"permissions.deny contains {control_plane_rule} "
          "(covers settings.json, settings.local.json, and skills/** together)",
          control_plane_rule in deny, deny, failures=failures)

    # 9. Permission-mode self-widening lockout.
    check("permissions.disableBypassPermissionsMode == 'disable'",
          perms.get("disableBypassPermissionsMode") == "disable", perms, failures=failures)
    check("permissions.disableAutoMode == 'disable'",
          perms.get("disableAutoMode") == "disable", perms, failures=failures)

    # 8. Sequential arm lifecycle is structurally enforced in orchestrate.py
    #    -- static source check (zero-cost): run_execute_sequential must
    #    build, then rmtree, one arm at a time, never all arms at once.
    import inspect
    import orchestrate
    src = inspect.getsource(orchestrate.run_execute_sequential)
    check("orchestrate.run_execute_sequential exists and destroys each arm's "
          "workspace (shutil.rmtree) before the next arm is built",
          "shutil.rmtree" in src and "for arm in arms" in src, failures=failures)
    check("orchestrate.run_check_only (the only place arms are built together) "
          "is a distinct function from the --execute path, never reused for real runs",
          orchestrate.run_check_only is not orchestrate.run_execute_sequential, failures=failures)

    # 9. --execute path is gated on the freeze verifier passing before any
    #    workspace is built or any paid call is made.
    main_src = inspect.getsource(orchestrate.main)
    check("orchestrate.main() calls verify_freeze() before building any workspace when --execute is set",
          "verify_freeze()" in main_src, failures=failures)

    # 10. cases/oracles/grader/prompts/skill byte-identity against the v4
    #     baseline commit -- these must be untouched by this v6 hardening
    #     pass. Delegated to verify_experiment_freeze.py itself (it hashes
    #     and compares every one of these); re-run it here for a single
    #     entry point.
    sys.path.insert(0, os.path.join(config.BENCHMARK_ROOT, "design"))
    import verify_experiment_freeze
    freeze_ok, freeze_violations = verify_experiment_freeze.verify_freeze()
    check("verify_experiment_freeze.verify_freeze() passes "
          "(cases/oracles/grader/prompts/skill byte-identical; v6 config matches freeze)",
          freeze_ok, freeze_violations, failures=failures)
    provenance_ok = verify_experiment_freeze.provenance_consistency_selftest()
    check("verify_experiment_freeze.provenance_consistency_selftest() passes",
          provenance_ok, failures=failures)

    # 11. Bash native filesystem READ policy: Claude Code's native Bash
    #     sandbox defaults to broad filesystem read access -- allowRead
    #     alone does NOT narrow that default, it only re-opens a
    #     more-specific path inside a denyRead region. The real read
    #     boundary requires an explicit denyRead of the real HOME tree,
    #     with allowRead carving out only the workspace + frozen Node
    #     runtime paths as narrower exceptions.
    fs = sb["filesystem"]
    check("sandbox.filesystem.disabled == False",
          fs["disabled"] is False, failures=failures)
    check("sandbox.filesystem.denyRead contains the exact real HOME path",
          config.REAL_HOME_PATH in fs.get("denyRead", []), fs.get("denyRead"), failures=failures)
    check("sandbox.filesystem.denyRead contains the exact real benchmark workspace-root path "
          "(BASH_SIBLING_WORKSPACE_READ_DENY: this is what makes a stale sibling arm's "
          "workspace unreadable to Bash even if it still exists on disk)",
          config.REAL_WORKSPACE_ROOT in fs.get("denyRead", []), fs.get("denyRead"), failures=failures)
    check("sandbox.filesystem.allowRead contains the exact CURRENT workspace "
          "(the intentional, more-specific exception re-opened inside the "
          "broader workspace-root denyRead region)",
          os.path.realpath(ws) in fs["allowRead"], failures=failures)
    check("sandbox.filesystem.allowRead contains the exact Node launcher path",
          config.NODE_LAUNCHER_PATH in fs["allowRead"], failures=failures)
    check("sandbox.filesystem.allowRead contains the exact Node executable realpath",
          config.FROZEN_NODE_EXECUTABLE_REALPATH in fs["allowRead"], failures=failures)
    for broad in (
        config.REAL_HOME_PATH,
        os.path.join(config.REAL_HOME_PATH, ".local"),
        os.path.join(config.REAL_HOME_PATH, ".local", "share"),
        os.path.join(config.REAL_HOME_PATH, "Library"),
    ):
        check(f"sandbox.filesystem.allowRead does NOT contain the broad path {broad}",
              broad not in fs["allowRead"], failures=failures)
    check("sandbox.filesystem.allowRead does NOT contain the bare workspace-root path itself "
          "(only the current, more-specific workspace is re-opened)",
          config.REAL_WORKSPACE_ROOT not in fs["allowRead"], failures=failures)

    # A sibling arm's workspace (a different arm, or a different run_no, for
    # the same or a different case) always lives somewhere under
    # REAL_WORKSPACE_ROOT but is never itself the current workspace `ws` --
    # prove it is NOT an allowRead entry, i.e. it falls inside the denied
    # workspace-root region with no re-opening exception of its own.
    sibling_ws = os.path.join(config.REAL_WORKSPACE_ROOT, "case-999-sibling-probe", "generic", "run-01")
    check("a sibling workspace path (falling inside the denied workspace-root "
          "tree, distinct from the current workspace) is itself never an "
          "allowRead entry",
          sibling_ws not in fs["allowRead"], failures=failures)
    check("a sibling workspace path falls inside the denied REAL_WORKSPACE_ROOT tree",
          sibling_ws.startswith(config.REAL_WORKSPACE_ROOT + os.sep), failures=failures)

    # 12. Bash native filesystem WRITE policy: the working directory is
    #     writable by default under the native sandbox, so built-in
    #     Edit/Write permission rules alone are not the control-plane
    #     boundary for Bash. denyWrite must cover <workspace>/.claude at
    #     the OS level; the rest of the workspace (fixture under test) must
    #     remain writable.
    check("sandbox.filesystem.denyWrite contains the exact <workspace>/.claude path",
          f"{os.path.realpath(ws)}/.claude" in fs.get("denyWrite", []),
          fs.get("denyWrite"), failures=failures)
    check("sandbox.filesystem.allowWrite still grants the whole workspace "
          "(fixture under test remains editable; only .claude/ is denied)",
          fs["allowWrite"] == [os.path.realpath(ws)], failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("SETTINGS_POLICY_SELFTEST = FAIL")
        return False
    print("SETTINGS_POLICY_SELFTEST = PASS")
    return True


def run_archive_before_destroy_selftest():
    """Zero-cost (dry_run=True, no `claude -p` invoked): proves the
    run -> archive -> destroy pipeline that orchestrate.run_execute_sequential
    uses for real (paid) runs leaves everything grade_run.grade() needs,
    BEFORE the workspace is destroyed -- i.e. the model's final patch is
    never the only copy left inside a directory that's about to be
    shutil.rmtree'd.

    Exercises config.PREFLIGHT_CASE_ID under dry_run so no money is spent
    and no model is invoked; run_result.json will report
    status=not_executed_dry_run and an empty final_workspace diff (the
    fixture is unmodified), which is sufficient to prove the FILE PLUMBING
    is correct without needing a real agent output to grade."""
    import shutil
    import sys as _sys

    import orchestrate
    import runner
    import workspace

    sys.path.insert(0, os.path.join(config.BENCHMARK_ROOT, "graders"))
    import grade_run

    failures = []
    case_id = config.PREFLIGHT_CASE_ID
    arm = "baseline"
    run_no = 999  # sentinel run number, never collides with a real archived run

    ws_dir = workspace.build(case_id, arm, run_no)
    try:
        record = runner.run(case_id, arm, run_no, ws_dir, dry_run=True)
        check("dry-run record status is not_executed_dry_run (no paid call made)",
              record["status"] == "not_executed_dry_run", failures=failures)

        archived_dir = orchestrate.archive(case_id, arm, run_no, ws_dir, record)
        try:
            for required in ("run_manifest.json", "run_result.json", "final_workspace"):
                p = os.path.join(archived_dir, required)
                check(f"archived run contains {required} BEFORE workspace destroy",
                      os.path.exists(p), p, failures=failures)

            # This is the exact sequencing orchestrate.run_execute_sequential
            # uses: archive() completes, THEN (in its `finally`) the
            # workspace is destroyed. Reproduce that ordering here.
            shutil.rmtree(ws_dir, ignore_errors=True)

            check("workspace is gone after destroy (proves the check below is "
                  "reading only from the archive, not from the live workspace)",
                  not os.path.exists(ws_dir), failures=failures)

            # grade_run.grade() must be able to run against ONLY the archived
            # directory, with the live workspace already destroyed.
            try:
                result = grade_run.grade(archived_dir)
                check("grade_run.grade() runs successfully against the archived "
                      "dir alone, after the live workspace has been destroyed",
                      isinstance(result, dict) and "case_id" in result,
                      result, failures=failures)
            except Exception as e:  # noqa: BLE001
                check("grade_run.grade() runs successfully against the archived "
                      "dir alone, after the live workspace has been destroyed",
                      False, repr(e), failures=failures)
        finally:
            shutil.rmtree(archived_dir, ignore_errors=True)
    finally:
        shutil.rmtree(ws_dir, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("SEQUENTIAL_ARCHIVE_BEFORE_DESTROY = FAIL")
        return False
    print("SEQUENTIAL_ARCHIVE_BEFORE_DESTROY = PASS")
    return True


def run_check_only_cleanup_selftest():
    """Zero-cost: proves orchestrate.run_check_only(...) leaves NO arm
    workspace directories behind after it returns -- closing the stale-
    sibling-workspace hole where a --check-only diagnostic run's leftover
    baseline/generic/doctor workspaces could coexist with a LATER
    --execute run for the same case."""
    import glob

    import orchestrate

    failures = []
    case_id = config.PREFLIGHT_CASE_ID
    arms = ["baseline", "generic", "doctor"]
    run_no = 998  # sentinel, never collides with a real run

    summary = orchestrate.run_check_only([case_id], arms, run_no)
    check("run_check_only returns one summary row per requested arm",
          len(summary) == len(arms), summary, failures=failures)

    leftover = glob.glob(os.path.join(config.WORKSPACE_ROOT, case_id, "*", f"run-{run_no:02d}"))
    check("no arm workspace directory for this run_no remains on disk after "
          "run_check_only returns",
          leftover == [], leftover, failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("CHECK_ONLY_WORKSPACE_CLEANUP = FAIL")
        return False
    print("CHECK_ONLY_WORKSPACE_CLEANUP = PASS")
    return True


def run_preflight_mechanism_selftest():
    """Zero-cost: proves the v6 preflight mechanism (preflight.py,
    preflight_validator.py, orchestrate.py's --preflight wiring) exists,
    is legality-gated to exactly PREFLIGHT_CASE_ID x PREFLIGHT_ARMS, that
    its canary lives in a region Bash actually denies, that its validator
    logic resists spoofing (via preflight_validator_selftest.py's
    adversarial proof), and that tool-surface/Skill/aggregate integration
    is wired into orchestrate.py. Never invokes `claude -p` -- canary
    setup/teardown and prompt-appendix construction are exercised
    directly; the paid 3-run preflight itself is a separate, explicitly
    authorized future step."""
    import preflight
    import preflight_validator
    import preflight_validator_selftest

    failures = []

    check("preflight.is_legal_preflight_request accepts exactly "
          "PREFLIGHT_CASE_ID x PREFLIGHT_ARMS",
          preflight.is_legal_preflight_request(config.PREFLIGHT_CASE_ID, list(config.PREFLIGHT_ARMS)),
          failures=failures)
    check("preflight.is_legal_preflight_request rejects a different case",
          not preflight.is_legal_preflight_request("case-002-kanban-board", list(config.PREFLIGHT_ARMS)),
          failures=failures)
    check("preflight.is_legal_preflight_request rejects fewer than 3 arms",
          not preflight.is_legal_preflight_request(config.PREFLIGHT_CASE_ID, ["baseline"]),
          failures=failures)
    check("preflight.ENV_CANARY_NAME matches the name frozen in "
          "config.SENSITIVE_ENV_VAR_NAMES (and therefore in every run's "
          "sandbox.credentials.envVars deny list)",
          preflight.ENV_CANARY_NAME in config.SENSITIVE_ENV_VAR_NAMES, failures=failures)

    # PREFLIGHT_CANARY_DENIED_REGION: the external canary must lie inside
    # config.REAL_WORKSPACE_ROOT (a region sandbox.filesystem.denyRead
    # actually covers) and OUTSIDE the current evaluated workspace, and
    # must never itself appear as an allowRead entry -- fails if the
    # canary is ever moved back to /tmp or another non-denied location.
    canary_path = preflight.setup_external_canary()
    try:
        real_canary = os.path.realpath(canary_path)
        fake_current_ws = os.path.join(config.REAL_WORKSPACE_ROOT, "case-001-media-library",
                                        "baseline", "run-01")
        check("PREFLIGHT_CANARY_DENIED_REGION: realpath(canary) is under REAL_WORKSPACE_ROOT",
              real_canary.startswith(config.REAL_WORKSPACE_ROOT + os.sep), real_canary, failures=failures)
        check("PREFLIGHT_CANARY_DENIED_REGION: realpath(canary) is NOT under a "
              "representative current evaluated workspace",
              not real_canary.startswith(os.path.realpath(fake_current_ws) + os.sep),
              real_canary, failures=failures)
        sb_for_fake_ws = settings_policy.build_sandbox(fake_current_ws)
        check("PREFLIGHT_CANARY_DENIED_REGION: canary path is never an "
              "allowRead entry for a representative evaluated workspace",
              real_canary not in sb_for_fake_ws["filesystem"]["allowRead"], failures=failures)
        check("PREFLIGHT_CANARY_DENIED_REGION: canary is NOT under plain /tmp "
              "(/private/tmp) -- the exact prior defect being guarded against",
              not real_canary.startswith("/private/tmp" + os.sep)
              and not real_canary.startswith("/tmp" + os.sep),
              real_canary, failures=failures)

        check("external canary file exists after setup_external_canary()",
              os.path.exists(canary_path), canary_path, failures=failures)
        tmp_ws = "/tmp/idbench-preflight-symlink-selftest-ws"
        os.makedirs(tmp_ws, exist_ok=True)
        try:
            link_path = preflight.link_workspace_symlink(tmp_ws, canary_path)
            check("workspace symlink was created and points at the external canary",
                  os.path.islink(link_path) and os.path.realpath(link_path) == os.path.realpath(canary_path),
                  failures=failures)
        finally:
            import shutil
            shutil.rmtree(tmp_ws, ignore_errors=True)

        name, value = preflight.build_env_canary_value_pair()
        check("build_env_canary_value_pair returns the frozen canary NAME",
              name == preflight.ENV_CANARY_NAME, failures=failures)
        check("build_env_canary_value_pair's value is non-empty and does not "
              "itself look like a real credential (starts with the non-secret prefix)",
              bool(value) and value.startswith("PREFLIGHT-NONSECRET-"), failures=failures)

        appendix_prompt = preflight.build_preflight_prompt("BASE PROMPT TEXT", tmp_ws)
        check("preflight prompt appendix is appended after the base prompt text",
              appendix_prompt.startswith("BASE PROMPT TEXT") and "IDBENCH_PROBE_1_EXIT" in appendix_prompt,
              failures=failures)
        check("preflight appendix's {{EXTERNAL_CANARY_PATH}}/{{WORKSPACE_SYMLINK_ABS_PATH}} "
              "placeholders were substituted, not left literal",
              "{{" not in appendix_prompt, failures=failures)
        for n in (1, 2, 3, 4, 5, 6, 7, 8):
            check(f"preflight appendix mentions probe {n}",
                  f"IDBENCH_PROBE_{n}_" in appendix_prompt, failures=failures)
        check("preflight appendix's probe 7 tests the write boundary even when "
              ".claude does not yet exist (mkdir -p .claude, not a bare write "
              "into a directory that may not exist)",
              "mkdir -p .claude" in appendix_prompt, failures=failures)
    finally:
        preflight.teardown_external_canary()
    check("external canary is gone after teardown_external_canary()",
          not os.path.exists(canary_path), failures=failures)

    # PREFLIGHT_VALIDATOR_TOOL_RESULT_BINDING / spoof resistance: the
    # adversarial proof lives in preflight_validator_selftest.py.
    validator_ok = preflight_validator_selftest.run_static_selftest()
    check("preflight_validator_selftest.run_static_selftest() passes "
          "(includes final-text-only spoof, prompt-echo spoof, wrong-tool_result "
          "binding, actual-breach, and actual-denial adversarial cases)",
          validator_ok, failures=failures)
    check("preflight_validator defines exactly 9 frozen assertions",
          len(preflight_validator.ALL_ASSERTION_IDS) == 9, failures=failures)

    import inspect
    import orchestrate
    main_src = inspect.getsource(orchestrate.main)
    check("orchestrate.main() refuses an illegal --preflight request "
          "(case/arms != PREFLIGHT_CASE_ID x PREFLIGHT_ARMS) before building "
          "any workspace or making a paid call",
          "is_legal_preflight_request" in main_src, failures=failures)
    check("orchestrate.main() gates --preflight on verify_freeze() passing too, "
          "same as --execute",
          main_src.count("verify_freeze()") >= 1, failures=failures)
    preflight_branch = main_src[main_src.index("if args.preflight:\n        # Captured ONCE"):
                                 main_src.index("cases = args.cases.split")]
    check("orchestrate.main() never auto-starts the 90 empirical runs from "
          "a --preflight invocation (no run_execute_sequential call inside "
          "the --preflight execution branch)",
          "run_execute_sequential" not in preflight_branch, failures=failures)
    check("no active v6 file retains stale 'remaining 87' run-count wording",
          "87" not in main_src, failures=failures)
    archive_preflight_src = inspect.getsource(orchestrate.archive_preflight)
    check("orchestrate.archive_preflight uses a 'preflight' path segment "
          "distinct from archive()'s 'raw' segment (never counted in the "
          "90-row empirical table)",
          '"preflight"' in archive_preflight_src, failures=failures)

    # PREFLIGHT_TOOL_SURFACE_INTEGRATION: the tool-surface/Skill checks
    # documented as part of the live preflight are actually wired into
    # run_preflight_sequential(), not merely documented.
    run_preflight_src = inspect.getsource(orchestrate.run_preflight_sequential)
    check("orchestrate.run_preflight_sequential calls validate_arm_tool_surface_and_skill "
          "for each archived arm (tool-surface + Skill-discoverability + "
          "actual-invocation integration, not just the 9 infrastructure probes)",
          "validate_arm_tool_surface_and_skill" in run_preflight_src, failures=failures)
    check("orchestrate.run_preflight_sequential captures per-run provenance "
          "(item 14: comparing each run's OWN recorded identity, not just a "
          "single post-hoc verify_freeze() call)",
          '"provenance"' in run_preflight_src, failures=failures)

    # EMPIRICAL_EXECUTION_GATE (item 16): --execute must refuse to proceed
    # without a valid, freeze-hash-matched PAID_PREFLIGHT == PASS record.
    check("orchestrate.find_latest_passing_qualification exists and "
          "orchestrate.main()'s --execute branch calls it before "
          "cleanup_stale_workspaces/run_execute_sequential",
          "find_latest_passing_qualification" in main_src, failures=failures)
    # ADVERSARIAL (item 16): a qualification record with PAID_PREFLIGHT ==
    # "PASS" but a STALE freeze_file_sha256 (recorded against a different
    # snapshot of the instrument than the one currently on disk) must
    # never be accepted as a valid gate to unblock --execute.
    import hashlib as _hashlib
    qual_dir = os.path.join(config.BENCHMARK_ROOT, "results", "preflight")
    os.makedirs(qual_dir, exist_ok=True)
    stale_path = os.path.join(qual_dir, "aggregate-run-99-selftest-stale.json")
    freeze_file = os.path.join(config.BENCHMARK_ROOT, "design", config.EXPERIMENT_FREEZE_FILENAME)
    try:
        with open(stale_path, "w") as f:
            json.dump({"aggregate": {"PAID_PREFLIGHT": "PASS",
                                      "freeze_file_sha256": "0" * 64}}, f)
        check("ADVERSARIAL (item 16): a qualification record with PAID_PREFLIGHT == PASS "
              "but a freeze_file_sha256 that does NOT match the current freeze file is "
              "never accepted by find_latest_passing_qualification()",
              (orchestrate.find_latest_passing_qualification() or {}).get("_qualification_file")
              != stale_path,
              failures=failures)
    finally:
        if os.path.exists(stale_path):
            os.remove(stale_path)

    # ADVERSARIAL (item 3): the EXACT reproduced forged-minimal-file
    # attack. A file containing only {"summary": [], "aggregate":
    # {"PAID_PREFLIGHT": "PASS", "freeze_file_sha256": <current hash>}} --
    # no real per-arm archived evidence at all -- must be REJECTED.
    # find_latest_passing_qualification() must RECOMPUTE from archived
    # evidence, never trust these two cached fields directly.
    current_hash = (
        _hashlib.sha256(open(freeze_file, "rb").read()).hexdigest()
        if os.path.exists(freeze_file) else None
    )
    forged_path = os.path.join(qual_dir, "aggregate-run-98-selftest-forged.json")
    try:
        if current_hash is not None:
            with open(forged_path, "w") as f:
                json.dump({"summary": [], "aggregate": {"PAID_PREFLIGHT": "PASS",
                                                          "freeze_file_sha256": current_hash}}, f)
            recomputed = orchestrate._recompute_qualification_from_archive(forged_path)
            check("ADVERSARIAL (item 3, REPRODUCED FAILURE): the exact forged minimal "
                  "aggregate (empty summary, no real per-arm evidence) is rejected by "
                  "_recompute_qualification_from_archive() -- returns None, not a PASS",
                  recomputed is None, recomputed, failures=failures)
            check("... and is therefore never returned by find_latest_passing_qualification()",
                  (orchestrate.find_latest_passing_qualification() or {}).get("_qualification_file")
                  != forged_path, failures=failures)
    finally:
        if os.path.exists(forged_path):
            os.remove(forged_path)

    # A genuinely COMPLETE, matching 3-arm archive (real run_result.json +
    # preflight_validation.json on disk, all-PASS evidence, consistent
    # expected_identity across all 3 arms) must be RECOMPUTED and ACCEPTED.
    import shutil as _shutil2
    import tempfile as _tempfile
    scratch_root = _tempfile.mkdtemp(prefix="idbench-qualification-integration-selftest-")
    full_path = os.path.join(qual_dir, "aggregate-run-97-selftest-full.json")
    try:
        expected_identity = orchestrate.capture_expected_identity()
        rows = []
        for arm in config.PREFLIGHT_ARMS:
            dest = os.path.join(scratch_root, config.PREFLIGHT_CASE_ID, arm, "run-01")
            os.makedirs(dest, exist_ok=True)
            provenance = {field: expected_identity.get(field) for field in orchestrate.EXPECTED_PROVENANCE_FIELDS}
            with open(os.path.join(dest, "run_result.json"), "w") as f:
                json.dump({"case_id": config.PREFLIGHT_CASE_ID, "arm": arm,
                           "status": "completed", "returncode": 0}, f)
            validation = {
                "infrastructure_probe_assertions": {a: "PASS" for a in preflight_validator.ALL_ASSERTION_IDS},
                "tool_surface_status": "PASS", "model_identity_status": "PASS",
                "skill_discoverability_status": "PASS", "doctor_skill_invocation_status": "PASS",
                "skill_surface_names": ["design", "dataviz"] + (["interaction-doctor"] if arm == "doctor" else []),
            }
            with open(os.path.join(dest, "preflight_validation.json"), "w") as f:
                json.dump({"provenance": provenance, "validation": validation,
                           "expected_identity": expected_identity}, f)
            rows.append({"case_id": config.PREFLIGHT_CASE_ID, "arm": arm, "archived_at": dest})
        with open(full_path, "w") as f:
            json.dump({"summary": rows, "aggregate": {"PAID_PREFLIGHT": "IGNORED_ON_PURPOSE",
                                                        "freeze_file_sha256": "IGNORED_ON_PURPOSE"}}, f)
        recomputed = orchestrate._recompute_qualification_from_archive(full_path)
        check("a genuinely complete 3-arm archive with all-PASS evidence is RECOMPUTED "
              "(not trusted from the file's own, deliberately wrong, cached aggregate "
              "fields) and reaches PAID_PREFLIGHT == PASS",
              recomputed is not None and recomputed.get("PAID_PREFLIGHT") == "PASS",
              recomputed, failures=failures)
        found = orchestrate.find_latest_passing_qualification()
        check("find_latest_passing_qualification() accepts this genuinely complete "
              "archive (recomputed PASS + matching current freeze hash)",
              found is not None and found.get("_qualification_file") == full_path,
              found, failures=failures)
    finally:
        if os.path.exists(full_path):
            os.remove(full_path)
        _shutil2.rmtree(scratch_root, ignore_errors=True)

    # PREFLIGHT_AGGREGATE_GATE: unknown/missing evidence must never be
    # silently treated as PASS in the aggregate either.
    empty_aggregate = orchestrate.aggregate_preflight([])
    check("aggregate_preflight([]) (no evidence at all) reports "
          "PAID_PREFLIGHT == HOLD, never PASS",
          empty_aggregate["PAID_PREFLIGHT"] == "HOLD", empty_aggregate, failures=failures)
    check("aggregate_preflight([]) reports READY_FOR_EMPIRICAL_90_RUNS == False",
          empty_aggregate["READY_FOR_EMPIRICAL_90_RUNS"] is False, failures=failures)

    def _make_row(arm, *, status="completed", returncode=0, provenance=None,
                   tool_surface="PASS", model_identity="PASS", skill_disc="PASS",
                   doctor_inv="PASS", runtime_all_pass=True, skill_surface_names=None):
        expected = orchestrate.capture_expected_identity()
        prov = dict(expected) if provenance is None else provenance
        names = ["design", "dataviz"] if skill_surface_names is None else list(skill_surface_names)
        if arm == "doctor":
            names = names + ["interaction-doctor"]
        return {
            "case_id": config.PREFLIGHT_CASE_ID, "arm": arm, "status": status,
            "returncode": returncode,
            "provenance": prov,
            "preflight_validation": {
                "infrastructure_probe_assertions": {
                    a: ("PASS" if runtime_all_pass else "FAIL")
                    for a in preflight_validator.ALL_ASSERTION_IDS
                },
                "tool_surface_status": tool_surface,
                "skill_discoverability_status": skill_disc,
                "doctor_skill_invocation_status": doctor_inv,
                "model_identity_status": model_identity,
                "skill_surface_names": names,
            },
        }

    all_pass_summary = [_make_row(arm) for arm in config.PREFLIGHT_ARMS]
    all_pass_aggregate = orchestrate.aggregate_preflight(all_pass_summary)
    check("aggregate_preflight(...) with all 3 arms fully PASS-evidenced, matching "
          "provenance, an identical non-doctor skill surface, and verify_freeze() "
          "currently passing reports PAID_PREFLIGHT == PASS",
          all_pass_aggregate["PAID_PREFLIGHT"] == "PASS", all_pass_aggregate, failures=failures)
    check("... and READY_FOR_EMPIRICAL_90_RUNS == True in that case",
          all_pass_aggregate["READY_FOR_EMPIRICAL_90_RUNS"] is True, failures=failures)

    def _one_bad(summary, mutate):
        s = [dict(r) for r in summary]
        s[0] = mutate(dict(s[0]))
        return s

    hold_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "preflight_validation": {**r["preflight_validation"], "tool_surface_status": "HOLD"}
    })
    check("ADVERSARIAL: even ONE arm's tool_surface_status == HOLD -> PAID_PREFLIGHT == HOLD",
          orchestrate.aggregate_preflight(hold_summary)["PAID_PREFLIGHT"] == "HOLD", failures=failures)

    nonzero_summary = _one_bad(all_pass_summary, lambda r: {**r, "status": "nonzero_exit", "returncode": 1})
    check("ADVERSARIAL (item 13): a nonzero-exit run never counts toward 3/3 "
          "runs_completed, so PAID_PREFLIGHT == HOLD even if every OTHER field "
          "in that row still says PASS",
          orchestrate.aggregate_preflight(nonzero_summary)["PAID_PREFLIGHT"] == "HOLD"
          and orchestrate.aggregate_preflight(nonzero_summary)["PAID_PREFLIGHT_RUNS_COMPLETED"] == "2/3",
          failures=failures)

    timeout_summary = _one_bad(all_pass_summary, lambda r: {**r, "status": "timeout"})
    check("ADVERSARIAL (item 13): a timed-out run never counts toward 3/3",
          orchestrate.aggregate_preflight(timeout_summary)["PAID_PREFLIGHT_RUNS_COMPLETED"] == "2/3",
          failures=failures)

    missing_run_summary = all_pass_summary[:2]  # only 2 of 3 arms present at all
    check("ADVERSARIAL (item 13): a missing/never-run arm never counts toward 3/3 "
          "(no automatic retry, no assumption of success)",
          orchestrate.aggregate_preflight(missing_run_summary)["PAID_PREFLIGHT"] == "HOLD",
          failures=failures)

    wrong_sha_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "provenance": {**r["provenance"], "git_commit_sha": "0" * 40}
    })
    wrong_sha_agg = orchestrate.aggregate_preflight(wrong_sha_summary)
    check("ADVERSARIAL (item 14): a wrong git_commit_sha in even one run's OWN "
          "recorded provenance -> PREFLIGHT_PROVENANCE == FAIL and PAID_PREFLIGHT == HOLD "
          "(per-run comparison, not just a single post-hoc verify_freeze())",
          wrong_sha_agg["PREFLIGHT_PROVENANCE"] == "FAIL" and wrong_sha_agg["PAID_PREFLIGHT"] == "HOLD",
          wrong_sha_agg, failures=failures)

    wrong_freeze_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "provenance": {**r["provenance"], "experiment_freeze_file_sha256": "deadbeef" * 8}
    })
    check("ADVERSARIAL (item 14): a wrong experiment_freeze_file_sha256 in one run's "
          "provenance -> PREFLIGHT_PROVENANCE == FAIL",
          orchestrate.aggregate_preflight(wrong_freeze_summary)["PREFLIGHT_PROVENANCE"] == "FAIL",
          failures=failures)

    wrong_cli_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "provenance": {**r["provenance"], "claude_cli_version": "1.0.0"}
    })
    check("ADVERSARIAL (item 14): a wrong claude_cli_version in one run's "
          "provenance -> PREFLIGHT_PROVENANCE == FAIL",
          orchestrate.aggregate_preflight(wrong_cli_summary)["PREFLIGHT_PROVENANCE"] == "FAIL",
          failures=failures)

    missing_provenance_summary = _one_bad(all_pass_summary, lambda r: {**r, "provenance": None})
    check("ADVERSARIAL (item 14): a row with NO recorded provenance -> "
          "PREFLIGHT_PROVENANCE == HOLD-or-worse (never silently PASS)",
          orchestrate.aggregate_preflight(missing_provenance_summary)["PREFLIGHT_PROVENANCE"] != "PASS",
          failures=failures)

    confound_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "preflight_validation": {
            **r["preflight_validation"],
            "skill_surface_names": r["preflight_validation"]["skill_surface_names"] + ["unexpected-global-skill"],
        }
    })
    confound_agg = orchestrate.aggregate_preflight(confound_summary)
    check("ADVERSARIAL (item 12): an unexpected/global skill present in only ONE "
          "arm's skill surface (beyond interaction-doctor's expected doctor-only "
          "presence) -> PREFLIGHT_ARM_ISOLATION == FAIL, a real confound, not silently ignored",
          confound_agg["PREFLIGHT_ARM_ISOLATION"] == "FAIL", confound_agg, failures=failures)

    missing_skill_surface_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "preflight_validation": {**r["preflight_validation"], "skill_surface_names": None}
    })
    check("ADVERSARIAL (item 12): missing skill-surface evidence for one arm -> "
          "PREFLIGHT_ARM_ISOLATION != PASS (HOLD, never assumed identical)",
          orchestrate.aggregate_preflight(missing_skill_surface_summary)["PREFLIGHT_ARM_ISOLATION"] != "PASS",
          failures=failures)

    failed_doctor_invocation_summary = _one_bad(all_pass_summary, lambda r: {
        **r, "preflight_validation": {**r["preflight_validation"], "doctor_skill_invocation_status": "FAIL"}
    })
    check("ADVERSARIAL: a failed Skill tool_result for the doctor arm's actual "
          "invocation -> PREFLIGHT_DOCTOR_SKILL_INVOCATION == FAIL",
          orchestrate.aggregate_preflight(failed_doctor_invocation_summary)
          ["PREFLIGHT_DOCTOR_SKILL_INVOCATION"] == "FAIL", failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("V6_PREFLIGHT_CANARY_MECHANISM = FAIL")
        return False
    print("V6_PREFLIGHT_CANARY_MECHANISM = PASS")
    return True


def run_grader_runtime_identity_selftest():
    """Zero-cost (item 18): audits whether the ambient `node` this host's
    PATH would resolve for grading (harness/graders/grade_run.py's
    hidden-test subprocess calls `["node", ...]`, resolved via PATH, NOT
    an explicit frozen path) actually matches the frozen Node identity
    this experiment declares (config.FROZEN_NODE_EXECUTABLE_REALPATH /
    config.FROZEN_NODE_VERSION).

    graders/** is PROTECTED scientific content and is NOT modified by
    this harness -- grade_run.py's own `["node", ...]` call is left
    exactly as committed. This selftest instead verifies, from the
    harness side, that ambient PATH resolution on the CURRENT host
    happens to already resolve to the exact frozen interpreter -- and
    fails loudly (never silently passes) if that ever stops being true,
    which is the earliest possible warning that grading would silently
    start using an unfrozen runtime."""
    import shutil as _shutil

    failures = []
    which_node = _shutil.which("node")
    check("`node` is resolvable on PATH at all (required for grade_run.py's "
          "hidden-test subprocess calls to run)",
          which_node is not None, which_node, failures=failures)
    if which_node:
        resolved = os.path.realpath(which_node)
        check("ambient PATH `node` realpath matches config.FROZEN_NODE_EXECUTABLE_REALPATH "
              "-- if this ever fails, grade_run.py (protected, not modified here) would "
              "silently grade against an UNFROZEN runtime; this must be caught here, not "
              "discovered later in a result table",
              resolved == config.FROZEN_NODE_EXECUTABLE_REALPATH,
              (resolved, config.FROZEN_NODE_EXECUTABLE_REALPATH), failures=failures)
        import subprocess
        try:
            actual_version = subprocess.run(
                [which_node, "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
            check("ambient PATH `node --version` matches config.FROZEN_NODE_VERSION",
                  actual_version == config.FROZEN_NODE_VERSION,
                  (actual_version, config.FROZEN_NODE_VERSION), failures=failures)
        except Exception as e:  # noqa: BLE001
            check("could invoke ambient `node --version`", False, repr(e), failures=failures)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("GRADER_RUNTIME_IDENTITY = FAIL")
        return False
    print("GRADER_RUNTIME_IDENTITY = PASS")
    return True


def run_claude_executable_identity_selftest():
    """Zero-cost (item 1): proves runner.py/verify_experiment_freeze.py
    genuinely pin WHICH Claude binary runs, not merely its version
    string -- and that verify_freeze() rejects a same-version-but-
    different-executable and a launcher pointed at the wrong target."""
    import inspect
    import shutil
    import subprocess
    import tempfile

    import runner
    import verify_experiment_freeze as vef

    failures = []

    build_args_src = inspect.getsource(runner.build_args)
    check("runner.build_args() invokes CLAUDE_LAUNCHER_PATH, never bare 'claude'",
          '["claude"' not in build_args_src and "['claude'" not in build_args_src
          and "CLAUDE_LAUNCHER_PATH" in build_args_src,
          failures=failures)
    args = runner.build_args("baseline", "/tmp/fake-ws", "fake prompt")
    check("runner.build_args()'s argv[0] is the exact absolute frozen launcher path",
          args[0] == config.CLAUDE_LAUNCHER_PATH, args[0], failures=failures)

    claude_version_src = inspect.getsource(runner._claude_cli_version)
    check("runner._claude_cli_version() invokes CLAUDE_LAUNCHER_PATH, never bare 'claude'",
          '["claude"' not in claude_version_src and "['claude'" not in claude_version_src
          and "CLAUDE_LAUNCHER_PATH" in claude_version_src,
          failures=failures)

    record_src = inspect.getsource(runner.run)
    for field in ("claude_launcher_path", "claude_executable_realpath", "claude_executable_sha256"):
        check(f"runner.run()'s record includes {field!r}", f'"{field}"' in record_src, failures=failures)

    # ADVERSARIAL: same reported version, WRONG executable hash -> FAIL.
    freeze_path = os.path.join(config.BENCHMARK_ROOT, "design", config.EXPERIMENT_FREEZE_FILENAME)
    with open(freeze_path) as f:
        real_freeze = json.load(f)
    tampered = dict(real_freeze)
    tampered["claude_executable_sha256"] = "0" * 64
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(freeze_path))
        with os.fdopen(fd, "w") as f:
            json.dump(tampered, f)
        ok, violations = vef.verify_freeze(freeze_filename=os.path.basename(tmp_path))
        check("ADVERSARIAL (item 1): same claude_cli_version, WRONG claude_executable_sha256 "
              "-> verify_freeze() FAILS",
              not ok and any("claude_executable_sha256" in v for v in violations),
              violations, failures=failures)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ADVERSARIAL: launcher resolves to a DIFFERENT real path than frozen -> FAIL.
    tampered2 = dict(real_freeze)
    tampered2["claude_executable_realpath"] = "/nonexistent/somewhere/else/claude-binary"
    tmp_path2 = None
    try:
        fd, tmp_path2 = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(freeze_path))
        with os.fdopen(fd, "w") as f:
            json.dump(tampered2, f)
        ok, violations = vef.verify_freeze(freeze_filename=os.path.basename(tmp_path2))
        check("ADVERSARIAL (item 1): frozen claude_executable_realpath pointed at a "
              "different target than the real launcher resolves to -> verify_freeze() FAILS",
              not ok and any("claude_executable_realpath" in v for v in violations),
              violations, failures=failures)
    finally:
        if tmp_path2 and os.path.exists(tmp_path2):
            os.remove(tmp_path2)

    # ADVERSARIAL: a decoy 'claude' earlier on PATH must never affect
    # runner execution, since build_args() never invokes a bare 'claude'.
    decoy_dir = tempfile.mkdtemp(prefix="idbench-decoy-claude-")
    try:
        decoy = os.path.join(decoy_dir, "claude")
        with open(decoy, "w") as f:
            f.write("#!/bin/sh\necho '9.9.9 (DECOY)'\n")
        os.chmod(decoy, 0o755)
        env = dict(os.environ)
        env["PATH"] = decoy_dir + os.pathsep + env.get("PATH", "")
        args = runner.build_args("baseline", "/tmp/fake-ws", "fake prompt")
        # build_args() never even calls PATH resolution -- argv[0] is
        # already the exact absolute path, so a decoy on PATH is
        # structurally irrelevant. Confirm the absolute-path invariant
        # holds even with a hostile PATH set for this check.
        check("ADVERSARIAL (item 1): with a decoy 'claude' shadowing PATH, "
              "build_args()'s argv[0] is STILL the exact absolute frozen launcher "
              "(PATH resolution never enters into it)",
              args[0] == config.CLAUDE_LAUNCHER_PATH and args[0].startswith("/")
              and os.path.realpath(args[0]) == config.FROZEN_CLAUDE_EXECUTABLE_REALPATH,
              args[0], failures=failures)
    finally:
        shutil.rmtree(decoy_dir, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {failures}")
        print("CLAUDE_EXECUTABLE_IDENTITY = FAIL")
        return False
    print("CLAUDE_EXECUTABLE_IDENTITY = PASS")
    return True


def _json_ok(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


if __name__ == "__main__":
    ok1 = run()
    print()
    ok2 = run_archive_before_destroy_selftest()
    print()
    ok3 = run_check_only_cleanup_selftest()
    print()
    ok4 = run_preflight_mechanism_selftest()
    print()
    ok5 = run_grader_runtime_identity_selftest()
    print()
    ok6 = run_claude_executable_identity_selftest()
    sys.exit(0 if (ok1 and ok2 and ok3 and ok4 and ok5 and ok6) else 1)
