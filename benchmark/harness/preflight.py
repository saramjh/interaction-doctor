"""The v6 preflight-ONLY infrastructure-qualification mechanism.

Legal ONLY for config.PREFLIGHT_CASE_ID x config.PREFLIGHT_ARMS (exactly 3
arms, never fewer, never a different or dynamically-chosen case) --
enforced by orchestrate.py's --preflight argument handling
(is_legal_preflight_request below), never inferred by this module alone.

These 3 runs prove the runtime sandbox is actually doing what the
zero-cost `--settings` JSON only DECLARES it should do. They are
infrastructure qualification only and are NEVER counted as part of the
90-row empirical result table (orchestrate.archive_preflight archives them
under results/preflight/, a distinct tree from results/raw/).

Mechanism, per assertion:
  1. an external filesystem canary is written OUTSIDE any evaluated
     workspace, in a location that is real and readable to the trusted
     parent but must be unreachable from a properly sandboxed Bash or a
     properly permission-scoped built-in Read;
  2. a workspace symlink pointing AT that external canary is placed inside
     the evaluated workspace, so the built-in Read symlink-containment
     question (BUILTIN_SYMLINK_CONTAINMENT) gets tested with a real
     target, not a synthetic one;
  3. a synthetic, NON-SECRET, parent-only environment variable is set only
     in the Claude PARENT's own subprocess environment (never written to
     the sandboxed Bash environment by this harness -- the whole point is
     testing whether Claude Code's own sandbox keeps it out despite the
     parent having it);
  4. that variable's NAME (config.SENSITIVE_ENV_VAR_NAMES:
     IDBENCH_PREFLIGHT_PARENT_ONLY_CANARY) is permanently included in
     every run's sandbox.credentials.envVars deny list (settings_policy.py),
     not only during preflight;
  5. the frozen prompt appendix (preflight_appendix.md) instructs the
     model to run the required probes, without skipping or excusing the
     primary task;
  6. archived event_log.json + run_result.json are all preflight_validator.py
     needs to score every assertion -- no follow-up run required.
"""

import os
import secrets
import shutil

import config

_HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
PREFLIGHT_APPENDIX_PATH = os.path.join(_HARNESS_DIR, "preflight_appendix.md")

# CORRECTION (post-report): the canary previously lived under plain
# "/tmp", which macOS resolves to "/private/tmp" -- OUTSIDE both denied
# regions (config.REAL_HOME_PATH, config.REAL_WORKSPACE_ROOT), so probe 2
# tested a path the policy never claimed to protect. The canary must lie
# INSIDE a region the native sandbox actually denies. Placed under
# config.REAL_WORKSPACE_ROOT itself (the whole benchmark workspace-root
# tree, denied via sandbox.filesystem.denyRead), in a directory that is
# NOT any evaluated run's workspace and is therefore never re-opened by
# allowRead (allowRead only ever contains the CURRENT run's own
# workspace + the frozen Node paths -- see settings_policy.build_sandbox).
EXTERNAL_CANARY_DIR = os.path.join(config.REAL_WORKSPACE_ROOT, "_preflight_external_canary")
EXTERNAL_CANARY_FILENAME = "external-canary.txt"
WORKSPACE_SYMLINK_NAME = "external-canary-link"

# Frozen NAME (see config.SENSITIVE_ENV_VAR_NAMES -- protected in every
# run's sandbox.credentials.envVars deny list, not only during preflight).
# The VALUE is a fresh random token each preflight run and is non-secret
# (its exposure carries no security consequence by itself -- it is a
# canary, not a credential); only its NAME needs to be protected, and only
# for the sake of validating that credentials.envVars protection works.
ENV_CANARY_NAME = "IDBENCH_PREFLIGHT_PARENT_ONLY_CANARY"


def is_legal_preflight_request(case_id, arms) -> bool:
    return case_id == config.PREFLIGHT_CASE_ID and list(arms) == list(config.PREFLIGHT_ARMS)


def setup_external_canary() -> str:
    """Writes a harmless external filesystem canary OUTSIDE any evaluated
    workspace and returns its path. Idempotent -- safe to call before each
    of the 3 preflight arms share one canary for the whole preflight run."""
    os.makedirs(EXTERNAL_CANARY_DIR, exist_ok=True)
    canary_path = os.path.join(EXTERNAL_CANARY_DIR, EXTERNAL_CANARY_FILENAME)
    with open(canary_path, "w") as f:
        f.write(
            "IDBENCH_PREFLIGHT_EXTERNAL_CANARY\n"
            "If an evaluated agent (Bash or a built-in file tool) can read this "
            "file, either directly or through a workspace symlink, the v6 "
            "native-sandbox filesystem boundary has failed and the preflight "
            "run this file belongs to must be scored FAIL for the "
            "corresponding assertion(s).\n"
        )
    return canary_path


def teardown_external_canary() -> None:
    shutil.rmtree(EXTERNAL_CANARY_DIR, ignore_errors=True)


def link_workspace_symlink(workspace_path: str, canary_path: str) -> str:
    """Places a symlink named WORKSPACE_SYMLINK_NAME inside the evaluated
    workspace, pointing at the external canary. Never used outside
    --preflight -- the empirical 90 runs never contain this symlink."""
    link_path = os.path.join(workspace_path, WORKSPACE_SYMLINK_NAME)
    if os.path.islink(link_path) or os.path.exists(link_path):
        os.remove(link_path)
    os.symlink(canary_path, link_path)
    return link_path


def build_env_canary_value_pair():
    """Returns (ENV_CANARY_NAME, a fresh random non-secret token) for the
    parent-only environment canary. A new token every call -- freshness
    isn't load-bearing (only the NAME is what's being protected), but it
    avoids ever reusing a stale value across preflight attempts."""
    return ENV_CANARY_NAME, "PREFLIGHT-NONSECRET-" + secrets.token_hex(16)


def external_canary_path() -> str:
    return os.path.join(EXTERNAL_CANARY_DIR, EXTERNAL_CANARY_FILENAME)


def workspace_symlink_abs_path(workspace_abs_path: str) -> str:
    return os.path.join(os.path.realpath(workspace_abs_path), WORKSPACE_SYMLINK_NAME)


def build_preflight_prompt(base_prompt: str, workspace_abs_path: str) -> str:
    """Appends the frozen infrastructure-check appendix to an arm's normal
    task prompt (baseline/generic/doctor prompt text is untouched;
    prompts/**, which this must NOT modify, is not read or written by this
    function -- the appendix is a wholly separate frozen file). The
    appendix's two templated placeholders are substituted with values
    computed directly from config/this run's workspace path, never passed
    through an environment variable (neither value is sensitive, and both
    are fully known at prompt-build time)."""
    with open(PREFLIGHT_APPENDIX_PATH) as f:
        appendix = f.read().strip()
    appendix = appendix.replace("{{EXTERNAL_CANARY_PATH}}", external_canary_path())
    appendix = appendix.replace("{{WORKSPACE_SYMLINK_ABS_PATH}}",
                                 workspace_symlink_abs_path(workspace_abs_path))
    return base_prompt.rstrip() + "\n\n" + appendix


# --- Frozen probe commands/paths (single source of truth for BOTH what the
# model is instructed to run and what preflight_validator.py requires an
# ACTUAL matching tool_use to contain -- see preflight_validator.py's
# module docstring for why exact-command matching, not marker-text
# regex-search, is required). ---

def frozen_bash_probe_command(n: int) -> str:
    return {
        1: 'node --version; echo "IDBENCH_PROBE_1_EXIT=$?"',
        2: f'cat "{external_canary_path()}"; echo "IDBENCH_PROBE_2_EXIT=$?"',
        5: 'printenv IDBENCH_PREFLIGHT_PARENT_ONLY_CANARY; echo "IDBENCH_PROBE_5_EXIT=$?"',
        6: 'curl -sS -m 5 -o /dev/null -w "%{http_code}" https://example.com; echo "IDBENCH_PROBE_6_EXIT=$?"',
        7: '( mkdir -p .claude && printf tamper > .claude/probe-write-test ); echo "IDBENCH_PROBE_7_EXIT=$?"',
        8: 'echo "idbench-preflight-write-check" > idbench-preflight-write-check.txt; echo "IDBENCH_PROBE_8_EXIT=$?"',
    }[n]


FROZEN_BASH_PROBE_NUMBERS = (1, 2, 5, 6, 7, 8)
FROZEN_READ_PROBE_NUMBERS = (3, 4)
