"""Fixed, shared experiment configuration.

Every value here is held constant across all three arms (A/B/C) and all
cases. The only thing that legitimately differs between arms is:
  - whether the task prompt has the generic quality instruction appended
  - whether the workspace contains a copy of the frozen interaction-doctor
    skill directory

Nothing else (model, effort, tool surface, permission mode, setting
sources) may differ between arms. If you need to change an experimental
parameter, change it here so it applies identically to every arm.

--- v6 ARCHITECTURE CHANGE -----------------------------------------------
v4/v5 wrapped the ENTIRE Claude Code parent process in a custom outer
Seatbelt sandbox (harness/sandbox.py). That was rejected: the parent needs
normal host authentication (OAuth/Keychain-backed), which repeated live
diagnosis showed requires filesystem + environment + Seatbelt-capability
access that could not be narrowly and reliably isolated, and a SECOND,
nested Seatbelt sandbox_apply from within an already-sandboxed process
proved unreliable (see the v5 diagnostic history, preserved but inactive).

v6 instead uses Claude Code's OWN documented, natively-implemented
architecture (confirmed present in this exact installed binary via
`strings` on 2.1.270 -- real setting keys AND real bundled
implementation source calling `/usr/bin/sandbox-exec` directly from the
unsandboxed parent for each Bash invocation, plus real exception classes
SandboxInitFailedError/SandboxBridgeUnavailableError/
SandboxUnavailableForShellError/SandboxPolicyRefusalError):
  - the Claude Code PARENT process runs completely unsandboxed by us,
    with normal host auth and normal model-service networking.
  - built-in file tools (Read/Edit/Write/Glob/Grep) are constrained by
    Claude Code's OWN permission engine (`permissions.allow`/`deny` rules,
    `defaultMode: "dontAsk"`), not by a custom OS sandbox.
  - Bash (and everything Bash spawns) runs under Claude Code's NATIVE
    macOS Seatbelt sandbox (`sandbox.*` settings), configured fail-closed.
This eliminates the auth-vs-isolation conflict entirely: the parent that
needs to authenticate is never sandboxed by us, and the tool (Bash) that
must never see credentials is sandboxed by Claude Code itself, using an
implementation that does not need to nest a second sandbox inside a first.

sandbox.py/egress_proxy.py (the v4/v5 custom outer sandbox) are preserved
on disk as inactive historical code -- see their module docstrings -- but
are NOT imported or called anywhere in the active v6 execution path
(runner.py). isolation_selftest.py/network_selftest.py, which tested that
retired architecture specifically, are likewise preserved but excluded
from the v6 freeze's active file list; see settings_policy_selftest.py for
their v6 replacement.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
BENCHMARK_ROOT = os.path.join(REPO_ROOT, "benchmark")
SKILL_SRC = os.path.join(REPO_ROOT, ".claude", "skills", "interaction-doctor")

CASES_DIR = os.path.join(BENCHMARK_ROOT, "cases")
CASES_PRIVATE_DIR = os.path.join(BENCHMARK_ROOT, "cases-private")
RESULTS_RAW_DIR = os.path.join(BENCHMARK_ROOT, "results", "raw")
PROMPTS_DIR = os.path.join(BENCHMARK_ROOT, "prompts")

# Workspaces live OUTSIDE the source repo tree entirely, per spec section 4.
WORKSPACE_ROOT = os.path.join(
    os.environ.get("TMPDIR", "/tmp").rstrip("/"), "interaction-doctor-bench"
)

MODEL = "claude-sonnet-5"
EFFORT = "medium"

# --- Tool surface -----------------------------------------------------
#
# --tools is the actual tool-AVAILABILITY boundary (documented by
# `claude --help`: "Specify the list of available tools from the built-in
# set"). --allowedTools/--disallowedTools only affect permission/approval
# behavior, confirmed by inspecting this benchmark's own archived Doctor
# event log in an earlier pass (WebFetch/WebSearch/Task/ToolSearch were
# all listed as AVAILABLE despite none of them being in --allowedTools).
#
# v6 correction: the v4/v5 harness additionally passed a BROAD
# --allowedTools covering the entire TOOLS list, under bypassPermissions,
# which made --allowedTools a no-op rubber stamp rather than a real
# authorization boundary. v6 removes --allowedTools entirely. Tool
# AVAILABILITY is --tools; tool AUTHORIZATION is now the trusted
# --settings permissions.allow/deny policy (settings_policy.py) evaluated
# under --permission-mode dontAsk, which denies anything not explicitly
# pre-authorized rather than prompting.
TOOLS = "Read,Edit,Write,Glob,Grep,Bash,Skill"
DISALLOWED_TOOLS = "WebSearch,WebFetch"  # belt-and-suspenders; --tools is authoritative

FORBIDDEN_TOOLS = ("WebSearch", "WebFetch", "Task", "Agent", "ToolSearch")
REQUIRED_TOOLS_ALL_ARMS = ("Skill",)
DOCTOR_REQUIRED_SKILL_SUBSTRING = "interaction-doctor"

# --- Permission mode ----------------------------------------------------
#
# v6 correction: bypassPermissions approved everything unconditionally,
# making the trusted settings policy moot. dontAsk is a real permission
# mode confirmed present in this exact installed binary (a literal
# `"defaultMode": "default" | "plan" | "acceptEdits" | "dontAsk"` type
# string found via `strings` on the 2.1.270 executable) -- under dontAsk,
# anything not explicitly pre-authorized by the trusted settings policy is
# DENIED, not prompted for (there is no human to answer a prompt in a
# non-interactive `-p` run anyway).
PERMISSION_MODE = "dontAsk"

ARMS = ("baseline", "generic", "doctor")

RUN_TIMEOUT_SECONDS = 20 * 60

MAX_BUDGET_USD_PER_RUN = "1.00"

EVENT_LOG_MODE = True

# --- Claude Code native sandbox (Bash only) ------------------------------
#
# Confirmed present in the exact installed 2.1.270 binary via `strings`:
# real setting keys (sandbox.enabled, sandbox.failIfUnavailable,
# sandbox.allowUnsandboxedCommands, sandbox.autoAllowBashIfSandboxed,
# sandbox.excludedCommands, sandbox.filesystem.allowRead/allowWrite,
# sandbox.filesystem.disabled, sandbox.network.deniedDomains,
# sandbox.network.allowManagedDomainsOnly, sandbox.network.strictAllowlist,
# sandbox.network.tlsTerminate) AND real bundled implementation source
# constructing a Seatbelt profile and invoking
# `/usr/bin/sandbox-exec -p <profile> <shell> -c <command>` directly from
# the (unsandboxed) parent for each Bash call.
SANDBOX_ENABLED = True
SANDBOX_FAIL_IF_UNAVAILABLE = True  # no silent unconfined fallback
SANDBOX_ALLOW_UNSANDBOXED_COMMANDS = False
SANDBOX_AUTO_ALLOW_BASH_IF_SANDBOXED = True
SANDBOX_EXCLUDED_COMMANDS = ()  # empty: no command may skip sandboxing
SANDBOX_FILESYSTEM_DISABLED = False  # never disable the filesystem layer
SANDBOX_NETWORK_STRICT_ALLOWLIST = True
SANDBOX_NETWORK_ALLOWED_DOMAINS = ()  # empty: no fixture needs Bash networking

# --- Native Bash sandbox filesystem read policy --------------------------
#
# CORRECTION (post-report): Claude Code's native Bash sandbox defaults to
# BROAD filesystem read access; sandbox.filesystem.allowRead only re-opens
# a more-specific path inside a denyRead region, it does not narrow the
# default on its own. The real read boundary is therefore
# denyRead=[REAL_HOME_PATH, REAL_WORKSPACE_ROOT] with allowRead carving
# out exactly the current workspace + frozen Node runtime paths -- see
# settings_policy.build_sandbox. REAL_WORKSPACE_ROOT additionally closes
# the stale-sibling-workspace hole: it denies the ENTIRE benchmark
# workspace-root tree (where every case/arm/run's temp workspace lives),
# so a leftover sibling arm's workspace from a --check-only diagnostic (or
# an interrupted prior run) is unreadable to Bash even if it happens to
# still exist on disk -- only the CURRENT run's workspace, re-opened via
# allowRead, is an exception.
REAL_HOME_PATH = os.path.expanduser("~")
REAL_WORKSPACE_ROOT = os.path.realpath(WORKSPACE_ROOT)

# --- Native Bash sandbox credential env protection (real enforcement) ---
#
# CORRECTION (post-report): the original v6 draft's "_env_protect_names"
# was internal harness bookkeeping only -- it was never a documented
# Claude Code settings key, so it enforced nothing. Confirmed via
# `strings` on the exact installed 2.1.270 binary: the real, documented
# enforcement key is sandbox.credentials.envVars, an array of
# {"name": <VAR_NAME>, "mode": "deny"} entries (mode "deny"/"mask" are the
# only accepted values -- literal validator found:
# `r.mode==="deny"` / entries "with mode \"mask\"..."). Also confirmed:
# this key is "[o]nly honored from user, managed/policy, or CLI
# (--settings) settings -- not project settings", which independently
# confirms this harness's choice to deliver the trusted policy via CLI
# --settings rather than a project-local settings file.
SANDBOX_CREDENTIALS_ENV_MODE = "deny"

# --- Permission-mode self-widening lockout (defense-in-depth) -----------
#
# Confirmed via `strings` on the exact installed 2.1.270 binary: both
# permissions.disableBypassPermissionsMode and permissions.disableAutoMode
# are real settings keys, each accepting exactly the literal string
# "disable" (a single-value zod enum: `K(["disable"])`). Setting both
# means this experiment's fixed dontAsk permission mode cannot be widened
# to bypassPermissions or auto mode mid-run by any mechanism the trusted
# --settings policy controls.
PERMISSIONS_DISABLE_BYPASS_PERMISSIONS_MODE = "disable"
PERMISSIONS_DISABLE_AUTO_MODE = "disable"

# --- Frozen Node runtime (the only interpreter the 30 fixtures use) -----
# Re-resolved and verified live at freeze time; never assumed. Granted
# read-only to the native Bash sandbox's filesystem.allowRead -- nothing
# broader (not ~/.local, not ~/.local/share, not mise generally).
NODE_LAUNCHER_PATH = "/Users/ojihun/.local/share/mise/installs/node/24/bin/node"
FROZEN_NODE_EXECUTABLE_REALPATH = "/Users/ojihun/.local/share/mise/installs/node/24.19.0/bin/node"
FROZEN_NODE_VERSION = "v24.19.0"
NODE_RUNTIME_READONLY_PATHS = (
    NODE_LAUNCHER_PATH,
    FROZEN_NODE_EXECUTABLE_REALPATH,
)

# --- Sensitive environment variable names (NAMES only, never values) ----
# Bash must not see these merely because the (unsandboxed, authenticated)
# parent has them. Includes both the documented always-protect list and
# names actually found present (by NAME only) on this host during
# hardening: CLAUDE_CODE_MESSAGING_TOKEN (a live IPC secret for the
# current interactive session -- concrete proof a denylist approach must
# be deliberately curated, not assumed) and SSH_AUTH_SOCK.
SENSITIVE_ENV_VAR_NAMES = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "SSH_AUTH_SOCK",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN", "GH_TOKEN",
    "STARSHIP_SESSION_KEY",
    # The v6 live-preflight's parent-only synthetic, non-secret env
    # canary (see harness/preflight.py: ENV_CANARY_NAME). Its NAME is
    # frozen and permanently protected here -- present in every run's
    # sandbox.credentials.envVars deny list, not only during preflight --
    # since the name itself carries no information and protecting it
    # unconditionally is simpler and strictly safer than conditionally
    # adding it only for preflight runs.
    "IDBENCH_PREFLIGHT_PARENT_ONLY_CANARY",
)

# --- Live preflight: exactly ONE representative case x THREE arms = 3
# paid runs, never fewer (a single run cannot produce "every arm"
# evidence) and never more (case selection is fixed here, not chosen
# dynamically after seeing any result). case-001-media-library is the
# already-established representative smoke case (see
# benchmark/reports/smoke-test-report.md). The 3 v4/v5 failed preflight
# attempts (infrastructure diagnostics only, $0, no system/init) do NOT
# count toward this; the v6 preflight is 3 FRESH runs.
PREFLIGHT_CASE_ID = "case-001-media-library"
PREFLIGHT_ARMS = ("baseline", "generic", "doctor")
PREFLIGHT_EXPECTED_RUN_COUNT = 3

# --- Explicit run-count model (CORRECTION: the preflight materially
# changes prompt/environment via canary probes -- it is infrastructure
# qualification, NEVER one of the 90 empirical observations, so
# case-001-media-library is run a SECOND time, fresh, with the ordinary
# unmodified prompt, as part of the 90. A prior draft's "remaining 87"
# wording incorrectly implied the 3 preflight runs counted toward the
# 90-row table; that wording is retired everywhere in the ACTIVE v6
# instrument (config.py/orchestrate.py/tool_surface_preflight.py/
# README.md/DESIGN.md/selftests). Historical v1-v5 material may keep its
# original wording -- it is not re-read by any active code path.) ---
EMPIRICAL_CASE_COUNT = 30  # cross-checked against manifest-v3.1.json by validate_manifest.py
EMPIRICAL_RUN_COUNT = EMPIRICAL_CASE_COUNT * len(ARMS)  # 30 * 3 = 90
PAID_PREFLIGHT_RUN_COUNT = len(PREFLIGHT_ARMS)  # 3
TOTAL_PAID_RUNS_IF_ALL_SUCCESSFUL = PAID_PREFLIGHT_RUN_COUNT + EMPIRICAL_RUN_COUNT  # 93

EXPERIMENT_PREFLIGHT_REQUIRED = (
    "Before any of the 90 fresh empirical runs: commit the immutable "
    "snapshot -> verify_experiment_freeze.py passes -> exactly 3 paid "
    "`claude -p` runs (PREFLIGHT_CASE_ID x PREFLIGHT_ARMS) under the v6 "
    "native-sandbox architecture, run via `orchestrate.py --preflight` -> "
    "each run must have record status == 'completed' (returncode == 0); "
    "timeout/nonzero-exit/missing-record never counts toward 3/3, and "
    "there is no automatic retry -> inspect all 3 archived system/init "
    "events with tool_surface_preflight.py -> confirm the doctor run's "
    "event log shows an actual Skill tool_use for interaction-doctor, "
    "with a matching tool_result indicating successful invocation, and "
    "that baseline/generic show NO such invocation -> confirm, from real "
    "bound tool_use/tool_result evidence (never assistant prose or prompt "
    "echo), that the native Bash sandbox was genuinely active for every "
    "Bash invocation (never an unsandboxed fallback), that a parent-only "
    "synthetic env canary and an external filesystem canary (direct and "
    "via a workspace symlink) are both unreachable from Bash and from "
    "built-in Read, that an arbitrary Bash network request fails, that "
    "Bash cannot write <workspace>/.claude, and that the normal fixture "
    "source remains writable -> confirm EACH of the 3 runs' recorded "
    "identity (git_commit_sha, experiment_freeze_file_sha256, "
    "claude_cli_version, active_sandbox_architecture, "
    "custom_outer_sandbox_active, model, effort) matches what this "
    "instrument expects, individually per run, not merely a single "
    "verify_freeze() call after all three finish -> only if EVERY ONE of "
    "the 3 runs satisfies all of the above may the 90 empirical runs "
    "(a FRESH batch, run-numbered independently of the preflight) "
    "proceed, gated by orchestrate.py's frozen qualification-state check "
    "(--execute refuses to start without a valid, freeze-hash-matched "
    "PAID_PREFLIGHT == PASS record under results/preflight/). If any "
    "check fails: HOLD. Do not weaken the settings policy or "
    "filesystem/network grants to make a run 'succeed' -- report the "
    "exact failure. Whether the trusted --settings policy is actually "
    "applied at runtime cannot be proven zero-cost -- this preflight is "
    "what proves it. Even a full PASS is a REPORTED state only: no code "
    "path in this harness auto-starts the 90 empirical runs."
)

# The ONE authoritative freeze filename, shared by verify_experiment_freeze.py
# and runner.py (see design/verify_experiment_freeze.py's own docstring for
# why duplicating this independently in two places is exactly the bug class
# that broke provenance between v2 and v3).
EXPERIMENT_FREEZE_FILENAME = "experiment-freeze-v6.json"

# Pinned by reading `claude --version` at freeze time (never assumed to
# remain current -- tool availability, built-in skills, permission
# behavior, native sandbox behavior, and Skill discovery are all Claude
# Code version-dependent). verify_experiment_freeze.py re-reads the
# installed version at every --execute invocation and aborts before any
# paid call on a mismatch.
#
# CORRECTION (post-report): pinning the version string alone does not
# freeze WHICH BINARY runs -- runner.py previously invoked bare "claude"
# resolved through PATH, so a different binary at the same reported
# version, or a PATH entry shadowing the frozen launcher, could silently
# execute instead. runner.build_args() now invokes CLAUDE_LAUNCHER_PATH
# by its exact absolute path (never bare "claude"), and
# FROZEN_CLAUDE_EXECUTABLE_SHA256 pins the exact installed binary's
# content, not merely its self-reported version string.
FROZEN_CLAUDE_CLI_VERSION = "2.1.270"
FROZEN_CLAUDE_EXECUTABLE_REALPATH = "/Users/ojihun/.local/share/claude/versions/2.1.270"
CLAUDE_LAUNCHER_PATH = "/Users/ojihun/.local/bin/claude"
FROZEN_CLAUDE_EXECUTABLE_SHA256 = "a506b6d970a4cf44f6abdb53a81ddcd5d3b0ce042a95c502fe9d1f946bdb8807"

ACTIVE_SANDBOX_ARCHITECTURE = "CLAUDE_NATIVE_BASH_SANDBOX"
CUSTOM_OUTER_SANDBOX_ACTIVE = False

# --- Real archived-event schema evidence (item 5/7) ----------------------
#
# Confirmed via a real, already-archived 2.1.270 run in this repo
# (results/raw/case-001-media-library/doctor/run-01-20260913T120647469326Z/
# event_log.json), a genuine successful Skill invocation of
# interaction-doctor: the tool_result bound to the Skill tool_use carries
# NO `is_error` field at all, only a content string
# "Launching skill: interaction-doctor". Frozen here as the exact expected
# content prefix so the validator recognizes this real success shape
# without depending on an invented is_error=False shape that the real CLI
# never actually produces for this event.
DOCTOR_SKILL_SUCCESS_CONTENT_PREFIX = "Launching skill: interaction-doctor"

# Confirmed via the same real archived run's terminal `result` event:
# result.modelUsage[<requested model>].canonicalModel and .provider are
# real, deterministic fields the installed 2.1.270 CLI actually emits.
# For config.MODEL == "claude-sonnet-5", the real observed evidence is
# canonicalModel == "claude-sonnet-5" (the requested alias and the
# canonical identifier are identical on this evidence -- not assumed,
# observed) and provider == "firstParty". No claim is made about
# underlying model weights the CLI does not expose -- only these two
# observable, deterministic fields are frozen/validated.
FROZEN_CANONICAL_MODEL = "claude-sonnet-5"
FROZEN_MODEL_PROVIDER = "firstParty"
