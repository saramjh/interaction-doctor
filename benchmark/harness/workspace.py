"""Builds an isolated per-run workspace for one (case, arm, run) triple.

Isolation invariants enforced here (see benchmark/DESIGN.md section on
contamination controls):
  - workspace lives under WORKSPACE_ROOT, never inside REPO_ROOT
  - only the case's public fixture/ contents are copied in (never
    cases-private/, never task.md's private notes, never another arm's
    workspace)
  - the doctor arm gets a verbatim copy of the frozen skill; baseline and
    generic get no .claude/ directory at all
  - no top-level CLAUDE.md is ever written into a baseline/generic workspace
"""

import json
import os
import shutil

from config import CASES_DIR, SKILL_SRC, WORKSPACE_ROOT


def run_dir(case_id: str, arm: str, run_no: int) -> str:
    return os.path.join(WORKSPACE_ROOT, case_id, arm, f"run-{run_no:02d}")


def build(case_id: str, arm: str, run_no: int) -> str:
    case_dir = os.path.join(CASES_DIR, case_id)
    fixture_src = os.path.join(case_dir, "fixture")
    if not os.path.isdir(fixture_src):
        raise FileNotFoundError(f"missing fixture/ for case {case_id}: {fixture_src}")

    ws = run_dir(case_id, arm, run_no)
    if os.path.exists(ws):
        shutil.rmtree(ws)
    workspace = os.path.join(ws, "workspace")
    os.makedirs(workspace)

    # 1. Public fixture only.
    shutil.copytree(fixture_src, workspace, dirs_exist_ok=True)

    # 2. Arm-specific skill exposure.
    if arm == "doctor":
        dest_skill = os.path.join(workspace, ".claude", "skills", "interaction-doctor")
        # ignore OS junk (e.g. a stray .DS_Store in the source skill dir)
        # so the copy is exactly the documented SKILL.md + references/*.md
        # content, nothing incidental.
        shutil.copytree(
            SKILL_SRC, dest_skill,
            ignore=shutil.ignore_patterns(".DS_Store", "Thumbs.db"),
        )
    elif arm in ("baseline", "generic"):
        leaked = os.path.join(workspace, ".claude")
        if os.path.exists(leaked):
            raise RuntimeError(
                f"fixture for {case_id} ships a .claude/ dir; that would leak "
                f"into arm {arm}. Fixtures must not contain .claude/."
            )
    else:
        raise ValueError(f"unknown arm {arm}")

    # 3. Assemble task prompt text (kept OUT of the workspace filesystem;
    #    passed only as the CLI prompt argument) and record what was
    #    assembled for auditability.
    with open(os.path.join(case_dir, "task.md"), "r") as f:
        task_text = f.read().strip()

    prompt = task_text
    if arm == "generic":
        with open(os.path.join(os.path.dirname(CASES_DIR), "prompts", "generic.md")) as f:
            prompt = task_text + "\n\n" + f.read().strip()
    elif arm == "doctor":
        with open(os.path.join(os.path.dirname(CASES_DIR), "prompts", "doctor.md")) as f:
            prompt = task_text + "\n\n" + f.read().strip()

    manifest = {
        "case_id": case_id,
        "arm": arm,
        "run_no": run_no,
        "workspace": workspace,
        "prompt": prompt,
        "fixture_files": sorted(
            os.path.relpath(os.path.join(dp, f), workspace)
            for dp, _, fs in os.walk(workspace)
            for f in fs
        ),
    }
    with open(os.path.join(ws, "run_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return ws
