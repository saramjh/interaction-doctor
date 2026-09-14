"""Builds the harness-controlled, trusted security policy for one evaluated
run, delivered to Claude Code via `--settings '<inline JSON>'` -- never as a
file inside the evaluated workspace.

Why inline, not a file: the evaluated agent (Read/Edit/Write/Bash, all
running against the workspace) can never modify a policy that was never
written to disk inside its reach in the first place. A per-run settings
FILE placed outside the workspace was considered and rejected in favor of
inline JSON specifically because it removes an entire class of "can the
agent reach the policy file" questions -- there is no file to reach. This
also matches confirmed behavior of sandbox.credentials.envVars deny/mask
entries specifically, which a `strings` pass on the installed binary shows
are "[o]nly honored from user, managed/policy, or CLI (--settings)
settings -- not project settings."

Security model (see config.py's module docstring for the full v6
architecture rationale):
  - permissions.allow/deny + defaultMode="dontAsk" governs the BUILT-IN
    tools (Read/Edit/Write/Glob/Grep/Skill). Anything not explicitly
    allowed is denied outright, never prompted for. Claude Code's
    path-scoped permission rules only recognize Read(...) and Edit(...) --
    Read rules also cover read-like tools (Glob/Grep); Edit rules also
    cover Write. Glob(...)/Grep(...)/Write(...) path-scoped rules are not
    a real enforcement mechanism and are never used here. Absolute
    filesystem paths in these rules use Claude Code's `//<path>` syntax --
    a single leading `/` is relative to the settings source, not absolute.
    permissions.disableBypassPermissionsMode and permissions.disableAutoMode
    are both set to "disable" as defense-in-depth against a wider
    permission mode becoming active mid-experiment.
  - sandbox.* governs Bash specifically, via Claude Code's OWN native
    macOS Seatbelt implementation (confirmed present in the exact
    installed 2.1.270 binary -- see config.py). Configured fail-closed:
    sandbox.enabled=true, failIfUnavailable=true,
    allowUnsandboxedCommands=false, excludedCommands=[]. NOTE:
    sandbox.filesystem uses ORDINARY absolute paths (plain "/path", never
    "//path") -- this is a DIFFERENT path syntax from the built-in
    permissions.allow/deny rules above; do not conflate the two.
  - sandbox.credentials.envVars is the real, documented native enforcement
    mechanism for keeping specific environment variable NAMES out of the
    sandboxed Bash process (one {"name": ..., "mode": "deny"} entry per
    protected name, never a value) -- confirmed via `strings` on the
    installed binary. This replaced an earlier draft's "_env_protect_names"
    key, which was never a real Claude Code settings key and enforced
    nothing.

This module produces PURE DATA (a dict, or the JSON string built from it)
-- it never touches the filesystem itself.
"""

import json
import os

import config


def _abs_perm_path(path: str) -> str:
    """Converts a real absolute filesystem path into Claude Code's
    permission-rule absolute-path syntax: a DOUBLE leading slash
    (`//<path>`). A single leading `/` in a Read(...)/Edit(...) rule is
    relative to the settings source, never an absolute filesystem path --
    conflating the two silently narrows (or widens) a rule to the wrong
    location. `os.path.realpath` already returns a path starting with a
    single `/`, so prefixing one more `/` yields the correct `//` form.
    """
    p = os.path.realpath(path)
    return f"/{p}"


def _abs_perm_glob(path: str, pattern: str = "**") -> str:
    """`_abs_perm_path(path)` joined with a glob pattern, e.g.
    "//Users/x/ws/**" for "everything under this absolute directory."."""
    base = _abs_perm_path(path).rstrip("/")
    return f"{base}/{pattern}" if pattern else base


def build_permissions(workspace_path: str) -> dict:
    """Built-in tool authorization: Read/Edit cover the workspace (Read
    also covers Glob/Grep; Edit also covers Write -- there is no separate
    Glob(...)/Grep(...)/Write(...) path-rule mechanism to rely on). Bash
    itself is authorized here (auto-allowed once sandboxed, per
    sandbox.autoAllowBashIfSandboxed) but its OWN capabilities are
    separately constrained by the native sandbox below, not by this
    permission list. Skill is allowed generally -- which skill is actually
    DISCOVERABLE is a filesystem question (whether
    .claude/skills/interaction-doctor/ exists in this arm's workspace),
    not a permission-rule question.
    """
    ws = os.path.realpath(workspace_path)
    allow = [
        f"Read({_abs_perm_glob(ws)})",
        f"Edit({_abs_perm_glob(ws)})",
        "Skill",
        "Bash",  # availability gated by --tools; capability gated by sandbox.* below
    ]
    deny = [
        # Defense-in-depth: explicit denies for the most sensitive paths,
        # even though dontAsk already denies anything unmatched by `allow`
        # above. Named explicitly per the frozen requirement, not left to
        # implicit default-deny alone.
        f"Read({_abs_perm_glob(config.REPO_ROOT)})",
        f"Edit({_abs_perm_glob(config.REPO_ROOT)})",
        f"Read({_abs_perm_glob(config.CASES_PRIVATE_DIR)})",
        "Read(~/.claude/**)",
        "Read(~/.claude.json)",
        "Read(~/.ssh/**)",
        "Read(~/.aws/**)",
        "Read(~/Library/Keychains/**)",
        # The agent must not be able to widen or rewrite its own
        # experiment condition, or (doctor arm) tamper with the skill it's
        # being evaluated against. A single Edit(...) deny on the whole
        # .claude/** subtree covers settings.json, settings.local.json,
        # and skills/** alike -- Edit rules cover Write too, so no
        # separate Write(...) rule is needed (or effective).
        f"Edit({_abs_perm_glob(ws, '.claude/**')})",
    ]
    return {
        "defaultMode": config.PERMISSION_MODE,
        "allow": allow,
        "deny": deny,
        "disableBypassPermissionsMode": config.PERMISSIONS_DISABLE_BYPASS_PERMISSIONS_MODE,
        "disableAutoMode": config.PERMISSIONS_DISABLE_AUTO_MODE,
    }


def build_sandbox(workspace_path: str) -> dict:
    """Native Bash sandbox configuration -- fail-closed.

    Filesystem READ: Claude Code's native Bash sandbox defaults to BROAD
    filesystem read access. sandbox.filesystem.allowRead does not by
    itself narrow that default -- it only re-opens a more-specific path
    inside a denyRead region. The real read boundary is therefore
    denyRead=[REAL_HOME_PATH, REAL_WORKSPACE_ROOT] (the real $HOME tree,
    AND the real benchmark workspace-root tree where every case/arm/run's
    temp workspace lives -- this second entry is what makes a stale
    sibling-arm workspace, e.g. left behind by an interrupted diagnostic,
    unreadable to Bash even if it still exists on disk), with allowRead
    carving out only the CURRENT evaluated workspace (more specific than
    REAL_WORKSPACE_ROOT, so it is the intentional exception) plus the
    exact frozen Node launcher/runtime paths. Credential-path denies
    (~/.claude, ~/.ssh, ~/.aws, ~/Library/Keychains, etc., in
    build_permissions) are kept explicitly too, as defense-in-depth, even
    though they already fall inside the HOME-level denyRead.

    Filesystem WRITE: denyWrite covers <workspace>/.claude at the OS
    level -- the native sandbox's working directory is writable by
    default, so the built-in Edit permission rule denying .claude/** (see
    build_permissions) is not sufficient on its own; Bash itself (e.g.
    `echo ... > .claude/settings.json`) is a separate write path that only
    an OS-level denyWrite closes. The rest of the workspace (the fixture
    under test) remains writable -- only <workspace>/.claude is denied.

    Credentials: sandbox.credentials.envVars is the real, documented
    native mechanism (confirmed via `strings` on the installed binary) --
    one {"name": <NAME>, "mode": "deny"} entry per config.SENSITIVE_ENV_VAR_NAMES
    entry, names only, never values.
    """
    ws = os.path.realpath(workspace_path)
    return {
        "enabled": config.SANDBOX_ENABLED,
        "failIfUnavailable": config.SANDBOX_FAIL_IF_UNAVAILABLE,
        "allowUnsandboxedCommands": config.SANDBOX_ALLOW_UNSANDBOXED_COMMANDS,
        "autoAllowBashIfSandboxed": config.SANDBOX_AUTO_ALLOW_BASH_IF_SANDBOXED,
        "excludedCommands": list(config.SANDBOX_EXCLUDED_COMMANDS),
        "filesystem": {
            "disabled": config.SANDBOX_FILESYSTEM_DISABLED,
            "denyRead": [config.REAL_HOME_PATH, config.REAL_WORKSPACE_ROOT],
            "allowRead": [ws] + list(config.NODE_RUNTIME_READONLY_PATHS),
            "allowWrite": [ws],
            "denyWrite": [f"{ws}/.claude"],
        },
        "network": {
            "strictAllowlist": config.SANDBOX_NETWORK_STRICT_ALLOWLIST,
            "allowedDomains": list(config.SANDBOX_NETWORK_ALLOWED_DOMAINS),
        },
        "credentials": {
            "envVars": [
                {"name": name, "mode": config.SANDBOX_CREDENTIALS_ENV_MODE}
                for name in config.SENSITIVE_ENV_VAR_NAMES
            ],
        },
    }


def build_settings(workspace_path: str) -> dict:
    """The complete trusted policy for one evaluated run -- exactly what
    is sent via --settings, nothing else. (An earlier draft included a
    non-enforcing "_env_protect_names" bookkeeping key directly in this
    payload; real enforcement now lives in sandbox.credentials.envVars
    above, so nothing masquerading as a security key remains here.)"""
    return {
        "permissions": build_permissions(workspace_path),
        "sandbox": build_sandbox(workspace_path),
    }


def build_settings_json(workspace_path: str) -> str:
    return json.dumps(build_settings(workspace_path))
