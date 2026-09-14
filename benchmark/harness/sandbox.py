"""Real OS-level process sandbox for evaluated-agent execution, using
macOS's native Seatbelt (`sandbox-exec`).

This is the enforcement layer contamination_check.py cannot provide:
contamination_check.py proves forbidden files were never COPIED into a
workspace; this module proves the evaluated PROCESS is technically unable
to read anything outside its own workspace directory, and unable to make
arbitrary outbound network connections, regardless of what commands
(including Bash) the agent runs inside its workspace.

Design:
  - filesystem: (deny default) + (import "system.sb") for normal process
    execution (dyld/libSystem/etc.) + a single (allow file-read* file-write*
    (subpath <workspace>)) grant. Nothing else is readable -- not the
    source repo, not cases-private/, not a sibling arm's workspace. This is
    a real syscall-level guarantee (EPERM on open()), not a convention.

  - network: denied by default, with ONE exception:
    (allow network-outbound (remote ip "localhost:<proxy_port>")). This is
    a hard PLATFORM CONSTRAINT, confirmed by direct testing on this host:
    sandbox-exec's (remote ip "...") host term accepts ONLY the literal
    tokens "*" or "localhost" -- any actual hostname or IP literal is
    rejected outright ("sandbox-exec: host must be * or localhost in
    network address"). Arbitrary per-destination-host allowlisting is
    therefore NOT expressible at this OS-sandbox layer alone on this
    platform (this is also why sandbox-exec's own man page marks it
    DEPRECATED). The real enforcement of "model-service allowed, arbitrary
    egress blocked" is delegated to egress_proxy.py: a small local
    HTTP-CONNECT forward proxy, running OUTSIDE the sandbox in the trusted
    parent process, that allowlists destination hostnames at the
    application layer. The sandboxed process can reach NOTHING on the
    real network directly -- only localhost:<proxy_port> -- and the proxy
    is the only thing that can actually open an external connection, only
    to allowlisted hosts.

  - documented limitation: this requires Claude Code's CLI to honor
    HTTPS_PROXY/HTTP_PROXY for its own model-service traffic. That is a
    live-execution property; see config.EXPERIMENT_PREFLIGHT_REQUIRED for
    the required preflight smoke-test before the first paid run.

  - environment: the evaluated process does NOT inherit the parent
    harness's environment. A real check of THIS session's own environment
    during hardening found CLAUDE_CODE_MESSAGING_TOKEN (a live IPC secret
    for the CURRENT interactive session) among ordinary-looking
    CLAUDE_CODE_* variables -- proof that a denylist of "known bad" names
    is not a safe approach here (a denylist can never be proven complete).
    Instead, ALLOWED_ENV_PASSTHROUGH below is an explicit ALLOWLIST: only
    these names are ever copied from the harness's environment, and HOME
    is remapped to the sandboxed workspace itself rather than passed
    through, so nothing outside the workspace is even nominally "home."
    Nothing matching ANTHROPIC_*, CLAUDE_*, AWS_*, GOOGLE_*/GCLOUD_*/
    VERTEX_*, AZURE_*, or any proxy override the harness itself might have
    set is ever forwarded -- the only HTTPS_PROXY/HTTP_PROXY values the
    child ever sees are the ones THIS module sets, pointing at its own
    local proxy.

  - UNRESOLVED, DOCUMENTED LIMITATION (do not silently accept): the
    filesystem sandbox in this module restricts reads to the workspace
    subpath ONLY -- and Claude Code's own credential storage (OAuth
    session state and/or macOS Keychain access under the real $HOME) lives
    OUTSIDE that subpath. This module does not know, and cannot determine
    zero-cost, whether `claude`'s current login mechanism on this host
    requires a file/keychain read that this sandbox would also block. If
    the live preflight smoke-test (config.EXPERIMENT_PREFLIGHT_REQUIRED)
    fails because Claude Code cannot authenticate inside the sandbox, the
    required next step is to identify the MINIMAL additional grant needed
    (e.g. a single read-only credential file, explicitly named and
    justified) or to confirm ANTHROPIC_API_KEY-based auth (a single env
    var, addable to ALLOWED_ENV_PASSTHROUGH by name, no filesystem grant
    needed) -- never to broaden filesystem access generally to work around
    it.
"""

import os
import shutil
import subprocess
import tempfile

import egress_proxy

SANDBOX_EXEC = shutil.which("sandbox-exec")

# Explicit ALLOWLIST of environment variable names ever copied from the
# harness's own environment into the evaluated process. Everything else is
# dropped, regardless of what it is -- see module docstring for why this
# is an allowlist, not a denylist. HOME is remapped (not passed through);
# see run_sandboxed().
ALLOWED_ENV_PASSTHROUGH = ("PATH", "TERM", "LANG", "LC_ALL")

# Names/prefixes that must NEVER appear in the evaluated process's
# environment under any circumstances -- checked defensively by
# isolation_selftest.py even though ALLOWED_ENV_PASSTHROUGH's allowlist
# design already excludes them by construction.
FORBIDDEN_ENV_PREFIXES = (
    "ANTHROPIC_", "CLAUDE_", "AWS_", "BEDROCK_", "GOOGLE_", "GCLOUD_",
    "VERTEX_", "AZURE_", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
)


def sandbox_available() -> bool:
    return SANDBOX_EXEC is not None


def build_profile(workspace_path: str, proxy_port: int = None) -> str:
    """Writes a Seatbelt profile restricting filesystem access to exactly
    `workspace_path` (resolved to its real path, since macOS symlinks
    /tmp -> /private/tmp and a subpath rule must match the resolved path).
    If `proxy_port` is given, the ONLY permitted network destination is
    localhost:<proxy_port> (see module docstring); otherwise network is
    fully denied. Returns the profile file path.
    """
    ws_real = os.path.realpath(workspace_path)

    lines = [
        "(version 1)",
        "(deny default)",
        '(import "system.sb")',
        "",
        ";; process execution machinery",
        "(allow process-fork)",
        "(allow process-exec)",
        "(allow signal (target self))",
        "(allow sysctl-read)",
        "(allow mach-lookup)",
        "(allow file-read-metadata)",
        "",
        ";; the ONE readable+writable directory: this run's evaluated workspace",
        f'(allow file-read* file-write* (subpath "{ws_real}"))',
        "",
        ";; minimal stdio/dev nodes",
        '(allow file-read* file-write* (literal "/dev/null"))',
        '(allow file-read* (literal "/dev/urandom"))',
        '(allow file-read* (literal "/dev/random"))',
        '(allow file-ioctl (literal "/dev/dtracehelper"))',
        "",
    ]

    if proxy_port is not None:
        lines.append(";; ALL real network access is denied. The only reachable")
        lines.append(";; destination is the local allowlisting proxy (egress_proxy.py),")
        lines.append(";; which alone may reach the real network, and only to")
        lines.append(";; allowlisted hosts. See module docstring for why this proxy")
        lines.append(";; indirection exists instead of a direct per-host sandbox rule.")
        lines.append(f'(allow network-outbound (remote ip "localhost:{proxy_port}"))')
    else:
        lines.append(";; no proxy configured -- network fully denied")

    profile_text = "\n".join(lines) + "\n"

    fd, path = tempfile.mkstemp(prefix="idbench-sandbox-", suffix=".sb")
    with os.fdopen(fd, "w") as f:
        f.write(profile_text)
    return path


def build_sandboxed_env(workspace_path, extra=None):
    """Builds the evaluated process's environment from ALLOWED_ENV_PASSTHROUGH
    only -- never a copy of the harness's own environment. HOME is remapped
    to the sandboxed workspace itself. `extra` (e.g. proxy vars) is merged
    in last."""
    ws_real = os.path.realpath(workspace_path)
    run_env = {name: os.environ[name] for name in ALLOWED_ENV_PASSTHROUGH if name in os.environ}
    run_env["HOME"] = ws_real
    if extra:
        run_env.update(extra)
    return run_env


def run_sandboxed(args, workspace_path, allowed_egress_hosts=(),
                   egress_port=None, cwd=None, **subprocess_kwargs):
    """Runs `args` (a full argv list, e.g. the claude CLI invocation) inside
    a Seatbelt sandbox scoped to `workspace_path`, with an environment built
    ONLY from ALLOWED_ENV_PASSTHROUGH (see module docstring -- never a copy
    of the harness's own environment). If `allowed_egress_hosts` is
    non-empty, starts a local allowlisting proxy (egress_proxy.py) scoped
    to exactly host:egress_port for each host (default
    config.MODEL_SERVICE_EGRESS_PORT -- an allowlisted host on any OTHER
    port is denied) for the duration of the call, and points the child
    process at it via HTTPS_PROXY/HTTP_PROXY; the sandbox itself only ever
    permits reaching that local proxy, never the real network directly.
    Raises RuntimeError if sandbox-exec is unavailable -- this is a hard
    isolation requirement, never silently falls back to unsandboxed
    execution."""
    if not sandbox_available():
        raise RuntimeError(
            "sandbox-exec is not available on this host; refusing to run an "
            "evaluated-agent process without OS-level filesystem/network "
            "isolation. See benchmark/harness/sandbox.py."
        )

    if egress_port is None:
        import config
        egress_port = config.MODEL_SERVICE_EGRESS_PORT

    proxy_server = None
    proxy_port = None
    extra_env = {}
    if allowed_egress_hosts:
        allowed_destinations = {(h, egress_port) for h in allowed_egress_hosts}
        proxy_server, _thread, proxy_port = egress_proxy.start_proxy(allowed_destinations)
        proxy_url = f"http://127.0.0.1:{proxy_port}"
        extra_env = {
            "HTTPS_PROXY": proxy_url, "https_proxy": proxy_url,
            "HTTP_PROXY": proxy_url, "http_proxy": proxy_url,
        }

    run_env = build_sandboxed_env(workspace_path, extra=extra_env)

    profile_path = build_profile(workspace_path, proxy_port=proxy_port)
    try:
        full_args = [SANDBOX_EXEC, "-f", profile_path] + list(args)
        return subprocess.run(full_args, cwd=cwd, env=run_env, **subprocess_kwargs)
    finally:
        try:
            os.remove(profile_path)
        except OSError:
            pass
        if proxy_server is not None:
            egress_proxy.stop_proxy(proxy_server)
