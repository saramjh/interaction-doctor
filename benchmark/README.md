# Interaction Doctor Benchmark

An independent, isolation-first benchmark measuring whether the frozen
`interaction-doctor` skill (v1) actually improves a frontier coding
agent's handling of interaction-defect tasks, versus the same agent with
no skill (baseline) or a generic "be careful" prompt (control for mere
thoroughness). See `DESIGN.md` for the full experimental design,
including contamination controls, statistical method, and threats to
validity. This directory is independent of, and does not modify, the
frozen skill at `.claude/skills/interaction-doctor/`.

## Layout

```
benchmark/
  README.md              this file
  DESIGN.md              hypothesis, variables, controls, stats, limitations
  prompts/
    baseline.md           (no injected instruction — documents that fact)
    generic.md             generic rigor instruction, arm B
    doctor.md               "use interaction-doctor" instruction, arm C
  cases/<case-id>/
    task.md                agent-visible task description
    fixture/                agent-visible starting source tree
  cases-private/<case-id>/   NEVER copied into any agent workspace
    ground_truth.json
    hidden-tests/test.js
  harness/
    config.py               single source of truth for everything held constant
    workspace.py             builds an isolated per-run workspace
    contamination_check.py   zero-cost isolation gate, run before every paid call
    runner.py                invokes `claude -p ...` for one run
    orchestrate.py           CLI entrypoint: build + gate + (optionally) execute
  graders/
    grade_run.py             scores one archived run against private ground truth
  results/
    raw/                     immutable per-run archives (never overwritten)
    summary.json / .csv       (produced by a future aggregation pass)
  reports/
    pilot-report.md
```

## How isolation works (short version — full detail in DESIGN.md)

Every run gets a brand-new directory under
`$TMPDIR/interaction-doctor-bench/<case>/<arm>/run-NN/`, entirely outside
this git repository, populated with *only* what that arm is allowed to
see:

- **baseline**: fixture files only, no `.claude/`
- **generic**: fixture files + the generic instruction text appended to
  the prompt (not a file), no `.claude/`
- **doctor**: fixture files + a verbatim copy of
  `.claude/skills/interaction-doctor/` inside the workspace's own `.claude/skills/`

`claude` is invoked with `cwd` pinned to that workspace, `--add-dir`
limited to that same workspace, `--setting-sources project` (never
`user`, so nobody's global `~/.claude` config leaks in),
`--strict-mcp-config` with no MCP servers configured, and an identical
`--tools` list for every arm — `--tools` is the actual tool-AVAILABILITY
boundary (`--allowedTools`/`--disallowedTools` only affect
permission/approval behavior and were confirmed, against this
benchmark's own archived Doctor event log, NOT to remove a tool from
availability; both are still passed, but only as redundant
belt-and-suspenders, never relied on as the boundary). See
`harness/config.py: TOOLS` and `harness/tool_surface_preflight.py` for
the static selftest and the required live preflight against each arm's
actual `system/init` event.

**Before the remaining 87 empirical runs**, the required sequence is:
commit the immutable snapshot → `verify_experiment_freeze.py` passes →
exactly 3 paid `claude -p` runs (`config.PREFLIGHT_CASE_ID` ×
`config.PREFLIGHT_ARMS` — baseline, generic, doctor; never 1, never
chosen dynamically) under the identical hardened sandbox/proxy → inspect
all 3 archived `system/init` events with `tool_surface_preflight.py` →
confirm the doctor run's event log shows an actual Skill tool_use for
interaction-doctor → only then may the remaining 87 runs proceed. No
paid preflight run is ever sufficient on its own, and the network egress
allowlist (`api.anthropic.com:443`, via the local proxy) is never
widened during the preflight — a genuine need for another destination is
a HOLD, not a silent addition. **The skill/slash-command subsystem
is left enabled for all three arms** — the only thing that differs is
whether `.claude/skills/interaction-doctor/` exists in that arm's
workspace, which is the real product condition ("Interaction Doctor
installed" vs. not) rather than an artificial document-injection
workaround. `harness/contamination_check.py` inspects the built workspace
and refuses to let `orchestrate.py` invoke `claude` on it if it finds any
of: a `.claude/` dir or any `interaction-doctor`/`SKILL.md` trace in an
A/B workspace, a byte-level mismatch between arm C's skill copy and the
real frozen source, Interaction-Doctor terminology anywhere in an
A/B-visible file, a reference to `cases-private/`, or a path belonging to
another arm's workspace.

Ground truth and hidden tests live only in `cases-private/`, addressed by
absolute path from the grader, which runs against a copy of the
*finished* workspace archived to `results/raw/` after the agent process
has already exited — the agent itself never has a path to that data.

## Reproducing

```bash
cd benchmark/harness

# 1. Dry run: build every workspace and run the contamination gate for
#    every (case, arm) pair. Costs nothing, invokes no claude process.
python3 orchestrate.py --cases case-001-media-library,case-002-kanban-board,case-003-drawing-canvas \
                        --arms baseline,generic,doctor

# 2. Only after reviewing the isolation gate output and the cost estimate
#    (see reports/pilot-report.md), actually execute (costs real API $):
python3 orchestrate.py --cases case-001-media-library --arms baseline --execute

# 3. Grade one archived run:
python3 ../graders/grade_run.py ../results/raw/case-001-media-library/baseline/run-01-<timestamp>
```

`orchestrate.py` never overwrites a prior archived run (`results/raw/.../run-NN-<UTC timestamp>/`
is created fresh every time with `os.makedirs(..., exist_ok=False)`).

## Metrics (computed from `results/raw/` + `cases-private/`, per DESIGN.md §3/§7)

1. **Defect Detection Recall** — of cases with `defect_present: true`, fraction where the agent's diff addresses the defect (hidden test passes).
2. **False Positive Rate** — of `case_type: negative_control` cases, fraction where the agent made a functional change anyway.
3. **Correct Repair Rate** — of defective cases, fraction passing hidden tests AND not touching anything in `forbidden_repairs`.
4. **Regression Rate** — fraction of cases where a previously-passing hidden-test assertion (present pre-fix) now fails post-fix.
5. **Intent-Guessing Violation Rate** — of `intent_status: ambiguous` cases, fraction where the agent made an unrequested behavioral choice instead of surfacing the ambiguity.
6. **False-Closure Rate** — fraction of runs where the agent's final message claims success/completion but the hidden grading disagrees.
7. **Cost** — tokens, wall-clock seconds, tool-call count, $ (all captured per-run in `run_result.json` when the CLI exposes them via `--output-format json`).

Reported per arm, and as paired A-vs-B / B-vs-C / A-vs-C deltas with
contingency tables — never collapsed into one score as the primary
output (an optional secondary aggregate may accompany them).

## Status

Phase 1 (harness validation) scaffolding is in place with 3
harness-validation cases (`case-001-media-library` — real pairwise
conflict, `case-002-kanban-board` — lifecycle/stale-async defect,
`case-003-drawing-canvas` — negative control). Each fixture+hidden-test
pair has been verified directly with `node` (buggy fixture fails, a valid
fix passes, the clean fixture already passes) — independent of any
`claude` invocation. No paid `claude` run has been executed yet. See
`reports/pilot-report.md` for current status and the next-step command.
