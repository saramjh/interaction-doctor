#!/usr/bin/env python3
"""Zero-cost selftest proving the actual sandbox mechanism (sandbox.py's
sandbox-exec profiles) -- not merely the workspace-copying convention in
workspace.py -- makes an evaluated process technically unable to read
outside its own workspace. No Claude execution.

Exercises the SAME run_sandboxed() path runner.py uses for real runs.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox
import workspace
from config import CASES_PRIVATE_DIR, REPO_ROOT, SKILL_SRC

FAILURES = []


def check(label, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def can_read(ws, target_path):
    """Runs `cat target_path` inside the sandbox scoped to ws; returns True
    iff the read succeeds (exit 0, no permission error)."""
    proc = sandbox.run_sandboxed(
        ["/bin/cat", target_path],
        workspace_path=ws,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return proc.returncode == 0


def can_write(ws, target_path, content="isolation-selftest-write"):
    proc = sandbox.run_sandboxed(
        ["/bin/sh", "-c", f"echo '{content}' > {target_path}"],
        workspace_path=ws,
        capture_output=True,
        text=True,
        timeout=15,
    )
    ok = proc.returncode == 0
    if ok:
        try:
            with open(target_path) as f:
                ok = content in f.read()
        except Exception:
            ok = False
    return ok


if not sandbox.sandbox_available():
    print("[FAIL] sandbox-exec not available on this host")
    print("FILESYSTEM_ISOLATION_SELFTEST = FAIL")
    sys.exit(1)

case = "case-001-media-library"

baseline_ws_dir = workspace.build(case, "baseline", 900)
generic_ws_dir = workspace.build(case, "generic", 900)
doctor_ws_dir = workspace.build(case, "doctor", 900)

baseline_ws = os.path.join(baseline_ws_dir, "workspace")
generic_ws = os.path.join(generic_ws_dir, "workspace")
doctor_ws = os.path.join(doctor_ws_dir, "workspace")

source_repo_claude_md = os.path.join(REPO_ROOT, ".claude", "CLAUDE.md")
source_repo_skill_md = os.path.join(SKILL_SRC, "SKILL.md")
cases_private_gt = os.path.join(CASES_PRIVATE_DIR, case, "ground_truth.json")
doctor_local_skill_md = os.path.join(doctor_ws, ".claude", "skills", "interaction-doctor", "SKILL.md")
public_fixture_file = os.path.join(baseline_ws, "app.js")

print("=== BASELINE sandbox ===")
check("public workspace file -> readable", can_read(baseline_ws, public_fixture_file))
check("public workspace file -> writable", can_write(baseline_ws, os.path.join(baseline_ws, "selftest.txt")))
check("Doctor skill (source repo) -> NOT readable", not can_read(baseline_ws, source_repo_skill_md))
check("source repo CLAUDE.md -> NOT readable", not can_read(baseline_ws, source_repo_claude_md))
check("cases-private ground_truth.json -> NOT readable", not can_read(baseline_ws, cases_private_gt))
check("generic workspace -> NOT readable", not can_read(baseline_ws, os.path.join(generic_ws, "app.js")))
check("doctor workspace -> NOT readable", not can_read(baseline_ws, os.path.join(doctor_ws, "app.js")))
check("doctor's local skill copy -> NOT readable from baseline", not can_read(baseline_ws, doctor_local_skill_md))

print("\n=== GENERIC sandbox ===")
check("public workspace file -> readable", can_read(generic_ws, os.path.join(generic_ws, "app.js")))
check("public workspace file -> writable", can_write(generic_ws, os.path.join(generic_ws, "selftest.txt")))
check("Doctor skill (source repo) -> NOT readable", not can_read(generic_ws, source_repo_skill_md))
check("source repo CLAUDE.md -> NOT readable", not can_read(generic_ws, source_repo_claude_md))
check("cases-private ground_truth.json -> NOT readable", not can_read(generic_ws, cases_private_gt))
check("baseline workspace -> NOT readable", not can_read(generic_ws, os.path.join(baseline_ws, "app.js")))
check("doctor workspace -> NOT readable", not can_read(generic_ws, os.path.join(doctor_ws, "app.js")))

print("\n=== DOCTOR sandbox ===")
check("public workspace file -> readable", can_read(doctor_ws, os.path.join(doctor_ws, "app.js")))
check("public workspace file -> writable", can_write(doctor_ws, os.path.join(doctor_ws, "selftest.txt")))
check("local COPIED Doctor skill -> readable", can_read(doctor_ws, doctor_local_skill_md))
check("source-repo Doctor skill (live) -> NOT readable", not can_read(doctor_ws, source_repo_skill_md))
check("cases-private ground_truth.json -> NOT readable", not can_read(doctor_ws, cases_private_gt))
check("baseline workspace -> NOT readable", not can_read(doctor_ws, os.path.join(baseline_ws, "app.js")))
check("generic workspace -> NOT readable", not can_read(doctor_ws, os.path.join(generic_ws, "app.js")))

# --- Environment leakage: this session's OWN environment was checked
#     during hardening and found CLAUDE_CODE_MESSAGING_TOKEN among
#     CLAUDE_CODE_* variables -- a live IPC secret for THIS session, not a
#     hypothetical. Prove the sandboxed child never sees it, or any
#     forbidden-prefix variable, regardless of what's set in the parent. ---
print("\n=== ENVIRONMENT sanitization ===")
os.environ.setdefault("_ISOLATION_SELFTEST_CANARY", "should-never-leak")
proc = sandbox.run_sandboxed(
    ["/usr/bin/env"], workspace_path=baseline_ws, capture_output=True, text=True, timeout=15,
)
child_env_names = {line.split("=", 1)[0] for line in proc.stdout.splitlines() if "=" in line}
check("sandboxed child does not see CLAUDE_CODE_MESSAGING_TOKEN (real var, this session)",
      "CLAUDE_CODE_MESSAGING_TOKEN" not in child_env_names, sorted(child_env_names))
check("sandboxed child does not see the harness-only canary var",
      "_ISOLATION_SELFTEST_CANARY" not in child_env_names)
leaked_forbidden = [n for n in child_env_names if any(n.startswith(p) for p in sandbox.FORBIDDEN_ENV_PREFIXES)]
check("sandboxed child exposes no variable matching any FORBIDDEN_ENV_PREFIXES entry",
      leaked_forbidden == [], leaked_forbidden)
check("sandboxed child's HOME is remapped to the workspace, not the real $HOME",
      f"HOME={os.path.realpath(baseline_ws)}" in proc.stdout, proc.stdout)

# --- Filesystem escape: symlink/hardlink attempts from inside the
#     workspace must not be able to reach outside it. ---
print("\n=== FILESYSTEM ESCAPE ===")
symlink_path = os.path.join(baseline_ws, "escape-symlink")
try:
    os.symlink(source_repo_claude_md, symlink_path)
    check("symlink inside workspace -> source-repo file: read via symlink MUST fail",
          not can_read(baseline_ws, symlink_path))
finally:
    if os.path.islink(symlink_path):
        os.remove(symlink_path)

# The real threat model is the SANDBOXED AGENT attempting to hardlink a
# private file it cannot already read into its own workspace -- not the
# trusted parent harness creating one (which would trivially succeed
# regardless of any sandbox, and proves nothing about agent-reachable
# isolation). So the `ln` command itself must run INSIDE the sandbox.
hardlink_path = os.path.join(baseline_ws, "escape-hardlink")
proc = sandbox.run_sandboxed(
    ["/bin/ln", cases_private_gt, hardlink_path],
    workspace_path=baseline_ws, capture_output=True, text=True, timeout=15,
)
hardlink_created_by_sandboxed_agent = proc.returncode == 0 and os.path.exists(hardlink_path)
if hardlink_created_by_sandboxed_agent:
    check("hardlink created BY THE SANDBOXED AGENT from a private file: read via it MUST fail",
          not can_read(baseline_ws, hardlink_path))
    os.remove(hardlink_path)
else:
    check("sandboxed agent's own hardlink-creation attempt on a private file is refused "
          "(creation itself denied -- satisfies 'creation or read must fail')",
          True)

# cleanup
for d in (baseline_ws_dir, generic_ws_dir, doctor_ws_dir):
    shutil.rmtree(d, ignore_errors=True)

print()
if FAILURES:
    print(f"FAILED: {FAILURES}")
    print("FILESYSTEM_ISOLATION_SELFTEST = FAIL")
    sys.exit(1)
else:
    print("FILESYSTEM_ISOLATION_SELFTEST = PASS")
    sys.exit(0)
