"""Fixed, shared experiment configuration.

Every value here is held constant across all three arms (A/B/C) and all
cases. The only thing that legitimately differs between arms is:
  - whether the task prompt has the generic quality instruction appended
  - whether the workspace contains a copy of the frozen interaction-doctor
    skill directory

Nothing else (model, effort, tool surface, permission mode, setting
sources) may differ between arms. If you need to change an experimental
parameter, change it here so it applies identically to every arm.
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
# --allowedTools does NOT define which tools are available to the model --
# it only affects permission/approval behavior (this was confirmed against
# the benchmark's own archived Doctor event log: the system/init event
# listed WebFetch, WebSearch, Task, and ToolSearch as available despite
# none of them appearing in --allowedTools). --permission-mode
# bypassPermissions makes the approval question moot anyway, which is
# exactly why relying on --allowedTools as an AVAILABILITY boundary was
# wrong. The actual availability boundary is `--tools`, documented by
# `claude --help` as: "Specify the list of available tools from the
# built-in set." That is the mechanism used here.
#
# The experiment tool surface is exactly: Read, Edit, Write, Glob, Grep,
# Bash, Skill. Skill is included and identical across all three arms --
# A/B retain Claude Code's normal built-in skill capability, and C
# additionally discovers the project-local interaction-doctor skill
# through the ordinary skill-discovery mechanism (workspace.py places it
# at .claude/skills/interaction-doctor/ in only the doctor workspace).
# Skill discoverability, not tool availability, is what differs between
# arms.
TOOLS = "Read,Edit,Write,Glob,Grep,Bash,Skill"

# Explicitly excluded by omission from TOOLS above: WebSearch, WebFetch,
# Task/Agent, ToolSearch, and any MCP-provided tool (MCP servers are
# additionally removed entirely by --strict-mcp-config below). --tools is
# already an allowlist -- anything not named is unavailable -- so this
# list exists only as documented, belt-and-suspenders redundancy passed
# via --disallowedTools, and must never be relied upon as the actual
# boundary.
DISALLOWED_TOOLS = "WebSearch,WebFetch"

# Kept for approval-semantics compatibility only (see docstring above) --
# NEVER relied upon as the availability boundary. Superseded by TOOLS.
ALLOWED_TOOLS = "Read,Edit,Write,Glob,Grep,Bash,Skill"

# Hard per-run spend cap. These are small, self-contained fixtures with a
# tight task; a run that blows past this is almost certainly looping, not
# doing legitimately expensive work. Applied identically to every arm.
MAX_BUDGET_USD_PER_RUN = "1.00"

COMMON_CLAUDE_ARGS = [
    "--model", MODEL,
    "--effort", EFFORT,
    "--output-format", "json",
    "--permission-mode", "bypassPermissions",
    "--strict-mcp-config",
    "--setting-sources", "project",
    "--tools", TOOLS,
    "--allowedTools", ALLOWED_TOOLS,
    "--disallowedTools", DISALLOWED_TOOLS,
    "--no-session-persistence",
    "--max-budget-usd", MAX_BUDGET_USD_PER_RUN,
]

# Tool-surface invariants a live preflight (tool_surface_preflight.py) must
# confirm against each arm's ACTUAL system/init event before the 90-run
# batch is allowed to proceed -- never assumed from CLI flags alone.
FORBIDDEN_TOOLS = ("WebSearch", "WebFetch", "Task", "Agent", "ToolSearch")
REQUIRED_TOOLS_ALL_ARMS = ("Skill",)
DOCTOR_REQUIRED_SKILL_SUBSTRING = "interaction-doctor"

ARMS = ("baseline", "generic", "doctor")

RUN_TIMEOUT_SECONDS = 20 * 60

# --- Sandboxing / network isolation -------------------------------------
#
# Every evaluated-agent process (all three arms, identically) is executed
# inside an OS-level sandbox (see sandbox.py) that makes it technically
# unable to read anything outside its own workspace directory or make
# arbitrary outbound network connections -- not merely "instructed not to."
# The sandbox itself permits reaching ONLY a local allowlisting proxy
# (egress_proxy.py); the proxy alone may reach the real network, and only
# to MODEL_SERVICE_EGRESS_HOST:MODEL_SERVICE_EGRESS_PORT exactly (a
# specific host AND port -- not any port on that host). This indirection
# exists because sandbox-exec on this platform cannot express a per-host
# network rule directly (confirmed by testing: it accepts only the
# literal tokens "*" or "localhost" as the host term).
#
# There is NO wildcard HTTPS fallback (e.g. (remote ip "*:443")) anywhere
# in this configuration or in sandbox.py, and none is permitted. If the
# proxy mechanism does not work with Claude Code during the live
# preflight, the ONLY allowed response is to HOLD: do not weaken
# arbitrary-egress isolation, do not allow a wildcard :443 destination, do
# not continue to the 90-run experiment. WILDCARD_EGRESS_FALLBACK_ALLOWED
# below exists so this can be asserted, not just stated in prose.
MODEL_SERVICE_EGRESS_HOST = "api.anthropic.com"
MODEL_SERVICE_EGRESS_PORT = 443
MODEL_SERVICE_EGRESS_HOSTS = (MODEL_SERVICE_EGRESS_HOST,)  # back-compat alias
WILDCARD_EGRESS_FALLBACK_ALLOWED = False

# --- Live preflight: exactly ONE representative case x THREE arms = 3
# paid runs, never fewer (a single run cannot produce "every arm"
# evidence) and never more (case selection is fixed here, not chosen
# dynamically after seeing any result). case-001-media-library is the
# already-established representative smoke case (see
# benchmark/reports/smoke-test-report.md).
PREFLIGHT_CASE_ID = "case-001-media-library"
PREFLIGHT_ARMS = ("baseline", "generic", "doctor")
PREFLIGHT_EXPECTED_RUN_COUNT = 3

EXPERIMENT_PREFLIGHT_REQUIRED = (
    "Before the remaining 87 empirical runs: commit the immutable "
    "snapshot -> verify_experiment_freeze.py must pass -> run the live "
    "preflight as EXACTLY PREFLIGHT_EXPECTED_RUN_COUNT (3) paid "
    "`claude -p` invocations: PREFLIGHT_CASE_ID under each of "
    "PREFLIGHT_ARMS (baseline, generic, doctor), each executed under the "
    "identical hardened sandbox+proxy mechanism (sandbox.run_sandboxed "
    "with allowed_egress_hosts=MODEL_SERVICE_EGRESS_HOSTS), same model, "
    "same effort, same budget cap, same tool surface, same event logging "
    "-> tool_surface_preflight.py must be run against ALL THREE archived "
    "system/init events, confirming FORBIDDEN_TOOLS are absent and "
    "REQUIRED_TOOLS_ALL_ARMS are present on every one, that the doctor "
    "arm's skill list contains DOCTOR_REQUIRED_SKILL_SUBSTRING while "
    "baseline/generic's does not, and that the doctor arm's event log "
    "contains an actual Skill tool_use for interaction-doctor (not merely "
    "discoverability) -> the installed `claude --version` on all three "
    "runs must equal FROZEN_CLAUDE_CLI_VERSION -> only if EVERY ONE of "
    "the 3 runs satisfies all of the above may the remaining 87 runs "
    "proceed. If ANY of the 3 fails, or if Claude Code is found to need "
    "any network destination other than MODEL_SERVICE_EGRESS_HOST:"
    "MODEL_SERVICE_EGRESS_PORT, the result is HOLD: report the exact "
    "failure (including the exact attempted destination, if network) and "
    "do not proceed. Do not silently add a destination to the allowlist "
    "during the paid preflight -- any allowlist expansion must be "
    "explicitly reviewed and the instrument refrozen before continuing. "
    "This entire check cannot be proven zero-cost -- it is the one "
    "required paid step, and it is exactly 3 runs, never 1."
)

# Environment variables the evaluated process must NEVER see, reset before
# every sandboxed launch regardless of what's present in the harness's own
# environment. See sandbox.py's ALLOWED_ENV_PASSTHROUGH for the converse:
# the explicit, minimal allowlist of variables that ARE passed through.
STRIPPED_ENV_VAR_PREFIXES = (
    "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy",
    "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
    "ANTHROPIC_BASE_URL", "ANTHROPIC_",
    "AWS_", "AWS_BEDROCK", "BEDROCK_",
    "GOOGLE_", "GCLOUD_", "VERTEX_",
    "AZURE_",
)

# Phase 1 used --output-format json, which returns only a single
# end-of-run summary object -- no per-turn tool-call trace, so whether the
# doctor arm actually invoked the Skill tool could not be verified post-hoc
# (see benchmark/reports/phase1-validation-report.md, S2). EVENT_LOG_MODE
# is now True: the runner requests --output-format stream-json --verbose,
# archives every event line, and still parses the final `type: "result"`
# line with the exact same code path plain --output-format json returns
# (stream-json's last line has the same shape). This is required for the
# tool-surface preflight in section 1 above, which inspects the archived
# system/init event.
EVENT_LOG_MODE = True

# Pinned by reading `claude --version` at freeze time (never assumed to
# remain current -- tool availability, built-in skills, permission
# behavior, and Skill discovery are all Claude Code version-dependent).
# verify_experiment_freeze.py re-reads the installed version at every
# --execute invocation and aborts before any paid call on a mismatch.
FROZEN_CLAUDE_CLI_VERSION = "2.1.270"

# The ONE authoritative freeze filename, shared by verify_experiment_freeze.py
# (what gets verified before --execute) and runner.py (what gets hashed into
# every run_result.json's experiment_freeze_file_sha256). Both modules read
# this constant rather than independently hardcoding a versioned filename --
# that duplication is exactly what let runner.py silently keep recording a
# stale v2 hash after the verifier had already moved on to v3. Bump this
# alongside creating a new benchmark/design/experiment-freeze-vN.json; there
# is deliberately no second place this name is spelled out.
EXPERIMENT_FREEZE_FILENAME = "experiment-freeze-v4.json"
