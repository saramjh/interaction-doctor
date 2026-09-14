"""Static, automated proof of isolation for a built workspace.

Run this against every (case, arm, run) workspace BEFORE invoking claude on
it. If any check fails, the harness must refuse to launch that run
(fail closed).

This intentionally does NOT invoke Claude or any network call — it only
inspects the filesystem the agent would see, plus the CLI args the harness
is about to pass, so it costs nothing to run and can gate every launch.
"""

import hashlib
import json
import os
import sys

from config import CASES_PRIVATE_DIR, SKILL_SRC, WORKSPACE_ROOT

_IGNORED_JUNK = {".DS_Store", "Thumbs.db"}


def _hash_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _diff_against_frozen_skill(skill_dir: str) -> list:
    """Proves the doctor arm's skill copy is exactly the frozen source --
    same files, same bytes, nothing added or missing (other than ignored
    OS junk on the source side)."""
    violations = []
    src_files = {
        os.path.relpath(os.path.join(dp, f), SKILL_SRC): os.path.join(dp, f)
        for dp, _, fs in os.walk(SKILL_SRC)
        for f in fs
        if f not in _IGNORED_JUNK
    }
    dst_files = {
        os.path.relpath(os.path.join(dp, f), skill_dir): os.path.join(dp, f)
        for dp, _, fs in os.walk(skill_dir)
        for f in fs
        if f not in _IGNORED_JUNK
    }
    missing = sorted(set(src_files) - set(dst_files))
    extra = sorted(set(dst_files) - set(src_files))
    for m in missing:
        violations.append(f"doctor skill copy is missing frozen file {m}")
    for e in extra:
        violations.append(f"doctor skill copy has an extra file not in the frozen source: {e}")
    for rel in set(src_files) & set(dst_files):
        if _hash_file(src_files[rel]) != _hash_file(dst_files[rel]):
            violations.append(f"doctor skill copy of {rel} does not byte-match the frozen source")
    return violations


FORBIDDEN_STRINGS_BASELINE_GENERIC = [
    "Interaction Claim",
    "COMPETES",
    "COOPERATES",
    "Ownership Constraint Group",
    "Effect Lifetime",
    "interaction-doctor",
]


def _walk_files(root):
    for dp, _, fs in os.walk(root):
        for f in fs:
            yield os.path.join(dp, f)


def check(ws_dir: str, arm: str) -> list:
    """Returns a list of violation strings; empty list == clean."""
    violations = []
    workspace = os.path.join(ws_dir, "workspace")

    if not workspace.startswith(WORKSPACE_ROOT):
        violations.append(f"workspace {workspace} is not under WORKSPACE_ROOT {WORKSPACE_ROOT}")

    if os.path.commonpath([os.path.abspath(workspace)]) == os.path.commonpath(
        [os.path.abspath(workspace), os.path.abspath(CASES_PRIVATE_DIR)]
    ) and os.path.abspath(workspace).startswith(os.path.abspath(CASES_PRIVATE_DIR)):
        violations.append("workspace is nested inside cases-private/")

    claude_dir = os.path.join(workspace, ".claude")

    # Private-data leakage must be checked for EVERY arm, including doctor
    # -- there is no legitimate reason ground truth or hidden tests should
    # ever be copied into ANY agent-visible workspace.
    for fp in _walk_files(workspace):
        base = os.path.basename(fp)
        if base in ("ground_truth.json", "scoring.json"):
            violations.append(f"{arm} workspace contains private file: {fp}")
        if "hidden-tests" in fp.split(os.sep):
            violations.append(f"{arm} workspace contains hidden-tests path: {fp}")

    if arm in ("baseline", "generic"):
        if os.path.exists(claude_dir):
            violations.append(f"{arm} workspace contains a .claude/ dir: {claude_dir}")
        # top-level CLAUDE.md leaking product-root instructions
        for name in ("CLAUDE.md",):
            p = os.path.join(workspace, name)
            if os.path.exists(p):
                violations.append(f"{arm} workspace contains {name}")
        # skill terminology must not appear anywhere in the visible fixture
        # (doctor is exempt: it legitimately contains this terminology via
        # the skill files it was given on purpose)
        for fp in _walk_files(workspace):
            if fp.endswith(("run_manifest.json",)):
                continue
            try:
                with open(fp, "r", errors="ignore") as f:
                    text = f.read()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for term in FORBIDDEN_STRINGS_BASELINE_GENERIC:
                if term in text:
                    violations.append(f"{arm} workspace file {fp} contains forbidden term {term!r}")

    if arm == "doctor":
        skill_dir = os.path.join(claude_dir, "skills", "interaction-doctor")
        if not os.path.isdir(skill_dir):
            violations.append("doctor workspace is missing the interaction-doctor skill dir")
        else:
            violations.extend(_diff_against_frozen_skill(skill_dir))
    else:
        # baseline/generic must have zero trace of the skill anywhere.
        # Check paths RELATIVE to the workspace, not absolute paths -- the
        # harness's own WORKSPACE_ROOT is named "interaction-doctor-bench",
        # so an absolute-path substring check false-positives on every file.
        for fp in _walk_files(workspace):
            rel = os.path.relpath(fp, workspace)
            if os.path.basename(fp) == "SKILL.md" or "interaction-doctor" in rel:
                violations.append(f"{arm} workspace unexpectedly contains {fp}")

    # no arm's workspace may reference cases-private at all, ever
    for fp in _walk_files(workspace):
        try:
            with open(fp, "r", errors="ignore") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        if "cases-private" in text:
            violations.append(f"{fp} references cases-private/ path")

    return violations


def check_no_cross_arm_leakage(ws_dir_for_arm: dict) -> list:
    """Given {arm: run_dir} for the SAME case, ensure no arm's run_dir is
    nested inside another arm's run_dir, and no arm's workspace contains a
    copy of another arm's run_manifest.json / run_result.json (which would
    prove that arm's prompt or output leaked across)."""
    violations = []
    abs_dirs = {arm: os.path.abspath(ws) for arm, ws in ws_dir_for_arm.items()}

    for arm, ws in abs_dirs.items():
        for other_arm, other_ws in abs_dirs.items():
            if other_arm == arm:
                continue
            if ws == other_ws:
                violations.append(f"{arm} and {other_arm} share the same run dir: {ws}")
            elif ws.startswith(other_ws + os.sep) or other_ws.startswith(ws + os.sep):
                violations.append(f"{arm} run dir ({ws}) is nested inside {other_arm}'s ({other_ws})")

    for arm, ws in abs_dirs.items():
        workspace = os.path.join(ws, "workspace")
        if not os.path.isdir(workspace):
            continue
        for fp in _walk_files(workspace):
            base = os.path.basename(fp)
            if base in ("run_manifest.json", "run_result.json"):
                # only the arm's OWN manifest may exist inside its own
                # run_dir (one level up from workspace/); one appearing
                # INSIDE the agent-visible workspace/ tree itself is
                # always a leak, for every arm.
                violations.append(f"{arm} agent-visible workspace contains {base} at {fp}")
    return violations


def main():
    if len(sys.argv) != 3:
        print("usage: contamination_check.py <run_dir> <arm>", file=sys.stderr)
        sys.exit(2)
    ws_dir, arm = sys.argv[1], sys.argv[2]
    violations = check(ws_dir, arm)
    if violations:
        print(json.dumps({"clean": False, "violations": violations}, indent=2))
        sys.exit(1)
    print(json.dumps({"clean": True, "violations": []}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
