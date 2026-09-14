#!/usr/bin/env python3
"""Zero-cost network-egress selftest, using the SAME sandbox.run_sandboxed()
path runner.py uses for real runs. Proves: local execution works, arbitrary
external egress is blocked, and the dynamic hostname-resolved allowlist
mechanism generalizes to a real public host -- all WITHOUT ever calling
Claude or spending money.

Documents the one limitation that genuinely cannot be proven zero-cost:
see LIMITATION_NOTE below and config.EXPERIMENT_PREFLIGHT_REQUIRED.
"""
import os
import shutil
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox
import workspace
from config import EXPERIMENT_PREFLIGHT_REQUIRED, MODEL_SERVICE_EGRESS_HOSTS

FAILURES = []


def check(label, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def run_node(ws, script_relpath, allowed_egress_hosts=(), timeout=8):
    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", script_relpath],
        workspace_path=ws,
        allowed_egress_hosts=allowed_egress_hosts,
        cwd=ws,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc


if not sandbox.sandbox_available():
    print("[FAIL] sandbox-exec not available on this host")
    print("AGENT_ARBITRARY_EGRESS_BLOCKED = HOLD")
    sys.exit(1)

case = "case-001-media-library"
ws_dir = workspace.build(case, "baseline", 901)
ws = os.path.join(ws_dir, "workspace")

# --- 1. local fixture access works -------------------------------------
with open(os.path.join(ws, "readtest.js"), "w") as f:
    f.write("console.log(require('fs').readFileSync('app.js', 'utf8').length > 0);")
proc = run_node(ws, "readtest.js")
check("local fixture access works (no egress allowed)",
      proc.returncode == 0 and proc.stdout.strip() == "true", proc.stdout + proc.stderr)

# --- 2. local node/python execution works -------------------------------
with open(os.path.join(ws, "exectest.js"), "w") as f:
    f.write("console.log(2 + 2);")
proc = run_node(ws, "exectest.js")
check("local node execution works (no egress allowed)",
      proc.returncode == 0 and proc.stdout.strip() == "4", proc.stdout + proc.stderr)

# --- 3. arbitrary external HTTP/TCP attempt is blocked ------------------
with open(os.path.join(ws, "blocktest.js"), "w") as f:
    f.write("""
const net = require('net');
const s = net.createConnection({ host: '93.184.216.34', port: 443, timeout: 3000 }, () => {
  console.log('CONNECTED');
  process.exit(1);
});
s.on('error', () => { console.log('BLOCKED'); process.exit(0); });
s.on('timeout', () => { console.log('BLOCKED'); process.exit(0); });
""")
proc = run_node(ws, "blocktest.js")  # no allowed_egress_hosts -> fully denied
check("arbitrary external network attempt is blocked (no allowlist)",
      proc.returncode == 0 and "BLOCKED" in proc.stdout, proc.stdout + proc.stderr)

# --- 4. proxy allowlist mechanism: the sandboxed process can ONLY reach
#     localhost:<proxy_port> at the OS-sandbox layer (see sandbox.py's
#     docstring for why -- sandbox-exec cannot express per-host rules on
#     this platform). This proves the PROXY ITSELF, which is the actual
#     enforcement point, correctly allows a request CONNECTing to an
#     allowlisted host and denies one CONNECTing to a different host --
#     by speaking the CONNECT protocol directly over the one permitted
#     destination, exactly as a proxy-aware HTTP client would. This does
#     NOT depend on Node's net module doing its own DNS/routing (which the
#     sandbox blocks unconditionally regardless of the allowlist).
ALLOWLIST_TEST_HOST = "example.com"
DISALLOWED_TEST_HOST = "neverssl.com"
try:
    socket.getaddrinfo(ALLOWLIST_TEST_HOST, 443, proto=socket.IPPROTO_TCP)
    socket.getaddrinfo(DISALLOWED_TEST_HOST, 443, proto=socket.IPPROTO_TCP)
    allowlist_resolvable = True
except socket.gaierror:
    allowlist_resolvable = False

CONNECT_SCRIPT = """
const net = require('net');
const proxyUrl = new URL(process.env.HTTPS_PROXY);
const target = process.argv[2];
const targetPort = process.argv[3] || '443';
const s = net.createConnection({ host: proxyUrl.hostname, port: Number(proxyUrl.port), timeout: 5000 }, () => {
  s.write(`CONNECT ${target}:${targetPort} HTTP/1.1\\r\\nHost: ${target}:${targetPort}\\r\\n\\r\\n`);
});
let buf = '';
s.on('data', (d) => {
  buf += d.toString();
  if (buf.includes('\\r\\n\\r\\n') || buf.length > 0) {
    const status = buf.split(' ')[1];
    console.log(status === '200' ? 'ALLOWED' : ('DENIED:' + status));
    s.destroy();
    process.exit(0);
  }
});
s.on('error', (e) => { console.log('ERROR:' + (e.code || e.message)); process.exit(1); });
s.on('timeout', () => { console.log('ERROR:timeout'); process.exit(1); });
"""

if allowlist_resolvable:
    with open(os.path.join(ws, "connecttest.js"), "w") as f:
        f.write(CONNECT_SCRIPT)

    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", "connecttest.js", ALLOWLIST_TEST_HOST],
        workspace_path=ws, allowed_egress_hosts=(ALLOWLIST_TEST_HOST,),
        cwd=ws, capture_output=True, text=True, timeout=10,
    )
    check(f"[production profile] proxy ALLOWS CONNECT to the allowlisted host:443 ({ALLOWLIST_TEST_HOST})",
          proc.returncode == 0 and proc.stdout.strip() == "ALLOWED", proc.stdout + proc.stderr)

    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", "connecttest.js", DISALLOWED_TEST_HOST],
        workspace_path=ws, allowed_egress_hosts=(ALLOWLIST_TEST_HOST,),
        cwd=ws, capture_output=True, text=True, timeout=10,
    )
    check(f"[production profile] proxy DENIES CONNECT to a different, non-allowlisted host "
          f"({DISALLOWED_TEST_HOST}) while one host is allowlisted",
          proc.returncode == 0 and proc.stdout.strip().startswith("DENIED"), proc.stdout + proc.stderr)

    # --- port restriction: an allowlisted HOST on a non-allowlisted PORT
    #     must still be denied -- host+port is the actual frozen
    #     destination, not host alone.
    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", "connecttest.js", ALLOWLIST_TEST_HOST, "8443"],
        workspace_path=ws, allowed_egress_hosts=(ALLOWLIST_TEST_HOST,),
        cwd=ws, capture_output=True, text=True, timeout=10,
    )
    check(f"[production profile] proxy DENIES CONNECT to the allowlisted host on a "
          f"NON-allowlisted port ({ALLOWLIST_TEST_HOST}:8443, only :443 is allowlisted)",
          proc.returncode == 0 and proc.stdout.strip().startswith("DENIED"), proc.stdout + proc.stderr)

    # --- production-mode direct-egress tests: with the proxy ACTIVE
    #     (allowed_egress_hosts non-empty, so proxy_port is set), the
    #     sandbox must STILL block (a) a direct connection to a real
    #     external host bypassing the proxy entirely, and (b) a
    #     connection to some OTHER localhost port the proxy isn't
    #     listening on -- the sandbox rule is localhost:<this exact
    #     proxy port>, not localhost:* or a blanket network allowance.
    direct_script = os.path.join(ws, "directtest.js")
    with open(direct_script, "w") as f:
        f.write("""
const net = require('net');
const s = net.createConnection({ host: '93.184.216.34', port: 443, timeout: 3000 }, () => {
  console.log('CONNECTED'); process.exit(1);
});
s.on('error', () => { console.log('BLOCKED'); process.exit(0); });
s.on('timeout', () => { console.log('BLOCKED'); process.exit(0); });
""")
    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", "directtest.js"],
        workspace_path=ws, allowed_egress_hosts=(ALLOWLIST_TEST_HOST,),
        cwd=ws, capture_output=True, text=True, timeout=10,
    )
    check("[production profile, proxy active] direct TCP to an external host is STILL blocked "
          "(sandbox only permits localhost:<proxy_port>, never the real network directly)",
          proc.returncode == 0 and "BLOCKED" in proc.stdout, proc.stdout + proc.stderr)

    unrelated_local_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    unrelated_local_listener.bind(("127.0.0.1", 0))
    unrelated_local_listener.listen(1)
    unrelated_port = unrelated_local_listener.getsockname()[1]
    unrelated_script = os.path.join(ws, "unrelatedlocaltest.js")
    with open(unrelated_script, "w") as f:
        f.write(f"""
const net = require('net');
const s = net.createConnection({{ host: '127.0.0.1', port: {unrelated_port}, timeout: 2000 }}, () => {{
  console.log('CONNECTED'); process.exit(1);
}});
s.on('error', () => {{ console.log('BLOCKED'); process.exit(0); }});
s.on('timeout', () => {{ console.log('BLOCKED'); process.exit(0); }});
""")
    proc = sandbox.run_sandboxed(
        ["/usr/bin/env", "node", "unrelatedlocaltest.js"],
        workspace_path=ws, allowed_egress_hosts=(ALLOWLIST_TEST_HOST,),
        cwd=ws, capture_output=True, text=True, timeout=10,
    )
    unrelated_local_listener.close()
    check("[production profile, proxy active] connection to an UNRELATED localhost port "
          "(not the proxy's own port) is blocked",
          proc.returncode == 0 and "BLOCKED" in proc.stdout, proc.stdout + proc.stderr)
else:
    print("[SKIP] allowlist generalization test -- no network in THIS (parent) environment to resolve test hosts")

shutil.rmtree(ws_dir, ignore_errors=True)

print()
print("LIMITATION_NOTE:", EXPERIMENT_PREFLIGHT_REQUIRED)
print(f"Production egress hosts configured: {MODEL_SERVICE_EGRESS_HOSTS}")
print("This selftest deliberately never contacts an Anthropic host or spends any money.")

print()
if FAILURES:
    print(f"FAILED: {FAILURES}")
    print("AGENT_ARBITRARY_EGRESS_BLOCKED = HOLD")
    sys.exit(1)
else:
    print("AGENT_ARBITRARY_EGRESS_BLOCKED = PASS")
    sys.exit(0)
