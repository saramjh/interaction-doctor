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
    preflight/               v6 infrastructure-qualification archives (3 runs + aggregate gate; NOT part of the 90-row table)
    summary.json / .csv       (produced by a future aggregation pass)
  reports/
    pilot-report.md
```

**Note for the future aggregation pass:** a row's `run_result.json` `status`
field distinguishes experiment-infrastructure outcomes
(`not_executed_dry_run`, `timeout`, `nonzero_exit`, `ABORTED_FREEZE_DRIFT`)
from a genuine completed observation (`status == "completed"`). Any future
aggregation/statistics code must gate on `status == "completed"` before
treating a row as a behavioral observation for H1/H0 -- an infrastructure
failure (timeout, crash, sandbox unavailable) is not a model behavioral
result and must never be silently scored as one (e.g. as a defect miss or
a false-closure) unless a specific metric definition explicitly requires
that treatment.

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

**v6 architecture (current, active).** The Claude Code PARENT process is
launched completely unsandboxed by the harness — ordinary
`subprocess.run(cwd=workspace)`, normal host authentication, normal
model-service networking. Isolation is delegated to Claude Code's OWN
native architecture, confirmed present in the exact installed 2.1.270
binary via `strings`:

- **Built-in file tools** (`Read`/`Edit`/`Write`/`Glob`/`Grep`/`Skill`) are
  governed by a trusted, per-run `--settings` policy
  (`harness/settings_policy.py`), delivered as **inline JSON** (never a
  file the evaluated agent could reach) under `--permission-mode dontAsk`.
  Claude Code path-scoped permission rules only recognize `Read(...)` and
  `Edit(...)` — `Read` rules also cover read-like tools such as
  `Glob`/`Grep`; `Edit` rules also cover `Write`. `Glob(...)`/`Grep(...)`/
  `Write(...)` path-scoped rules are not a real enforcement mechanism and
  are not used. Absolute filesystem paths in these rules use Claude Code's
  `//<path>` absolute-path syntax (a single leading `/` is relative to the
  settings source, not absolute) — e.g. `Read(//Users/.../workspace/**)`.
  `permissions.disableBypassPermissionsMode` and `permissions.disableAutoMode`
  are both set to `"disable"` as defense-in-depth against a wider
  permission mode becoming active mid-experiment.
- **Bash** (and every process it spawns) runs under Claude Code's own
  native Seatbelt sandbox (`sandbox.*` keys in the same `--settings`
  payload), configured fail-closed: `sandbox.enabled=true`,
  `failIfUnavailable=true`, `allowUnsandboxedCommands=false`,
  `excludedCommands=[]`. The native sandbox defaults to BROAD filesystem
  read access — `sandbox.filesystem.allowRead` alone does not narrow that
  default, it only re-opens a more-specific path inside a `denyRead`
  region — so the real read boundary is an explicit
  `sandbox.filesystem.denyRead` of the real `$HOME` and the real
  benchmark workspace-root tree, with `allowRead` carving out only the
  current evaluated workspace and the exact frozen Node launcher/runtime
  paths as narrower exceptions. `sandbox.filesystem.denyWrite` covers
  `<workspace>/.claude` at the OS level (the sandbox's working directory
  is writable by default, so built-in Edit/Write permission rules alone
  are not sufficient to protect the experiment control plane from a
  Bash-originated write); the rest of the workspace (the fixture under
  test) remains writable. Credential protection uses the documented
  native key `sandbox.credentials.envVars`, one `{"name": ..., "mode":
  "deny"}` entry per protected variable NAME (never a value) — this is
  real enforcement, unlike a harness-side denylist convention. Network is
  `sandbox.network.strictAllowlist=true` with an empty `allowedDomains`
  set for Bash (no fixture needs Bash-originated networking; only the
  unsandboxed parent needs model-service access).
- **`--allowedTools` is absent entirely.** `--tools` remains the actual
  tool-AVAILABILITY boundary (`--allowedTools`/`--disallowedTools` only
  affect permission/approval behavior and were confirmed, against this
  benchmark's own archived Doctor event log, NOT to remove a tool from
  availability); `--disallowedTools` is kept as redundant
  belt-and-suspenders only, never relied on as the boundary. Real
  authorization for built-in tools is the trusted `--settings` policy
  above. See `harness/config.py: TOOLS` and `harness/tool_surface_preflight.py`
  for the static selftest and the required live preflight against each
  arm's actual `system/init` event.
- **Arm workspaces are sequential during `--execute`**: one arm's
  workspace is built, run, archived, and destroyed completely before the
  next arm's workspace is even built (`orchestrate.run_execute_sequential`)
  — no two evaluated arm workspaces for a case ever coexist during a real
  run. `--check-only`'s cross-arm-leakage diagnostic (the only place arms
  are ever built together) cleans up every workspace it builds before
  returning.

A prior custom OUTER Seatbelt sandbox around the entire Claude Code parent
process (`harness/sandbox.py`, `harness/egress_proxy.py`) was designed,
tested, and **rejected**: it created an unresolvable conflict between the
parent's own authentication needs and Bash's isolation needs, and a
second, nested `sandbox_apply` proved unreliable under live testing.
Those files are preserved on disk as inactive historical code — not
imported anywhere in the active v6 execution path — see their own module
docstrings and `harness/config.py`'s module docstring for the full
rationale.

**Before the 90 FRESH empirical runs** (the 3 preflight runs above are infrastructure qualification only and are never among them -- see the explicit run-count model in `harness/config.py`: `PAID_PREFLIGHT_RUN_COUNT = 3`, `EMPIRICAL_RUN_COUNT = 90`, `TOTAL_PAID_RUNS_IF_ALL_SUCCESSFUL = 93`), the required sequence is:
commit the immutable snapshot → `verify_experiment_freeze.py` passes →
the v6 preflight mechanism (`harness/preflight.py`,
`harness/preflight_validator.py`) runs exactly 3 paid `claude -p` runs
(`config.PREFLIGHT_CASE_ID` × `config.PREFLIGHT_ARMS` — baseline, generic,
doctor; never 1, never chosen dynamically), legal only via
`orchestrate.py --preflight`, under the identical native-sandbox
architecture described above, with external/symlink/env canaries and a
frozen infrastructure-check prompt appendix → `preflight_validator.py`
scores all 9 frozen infrastructure assertions PASS/FAIL/HOLD from the
archived event log, never inferring PASS merely from the `--settings` JSON
content → `tool_surface_preflight.py` inspects all 3 archived
`system/init` events → confirms the doctor run's event log shows an
actual Skill tool_use for interaction-doctor → only then may the
90 empirical runs proceed. No paid preflight run is ever sufficient on
its own. The preflight runs are infrastructure qualification only and are
never counted as part of the 90-row empirical result table. **The
skill/slash-command subsystem
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

The real order, matching what the harness actually gates on (not merely a
suggested order -- `--execute` refuses to run at all without step 3
having produced a passing qualification record, and grading should go
through the trusted gate in step 6, not `grade_run.py` directly):

```bash
cd benchmark/harness

# 1. Zero-cost verification: static selftests, no claude process invoked.
python3 tool_surface_preflight.py
python3 settings_policy_selftest.py
python3 grade_empirical_selftest.py
python3 ../design/validate_manifest.py
python3 ../graders/grade_run_selftest.py
python3 ../design/verify_experiment_freeze.py

# 2. Commit the immutable instrument snapshot (only after all of the above
#    pass). This benchmark's own workflow does this manually, not via
#    orchestrate.py.

# 3. Post-commit freeze verification, then the 3-run paid preflight --
#    infrastructure qualification ONLY, never counted as part of the 90
#    empirical runs (see harness/config.py: PAID_PREFLIGHT_RUN_COUNT=3,
#    EMPIRICAL_RUN_COUNT=90, TOTAL_PAID_RUNS_IF_ALL_SUCCESSFUL=93):
python3 orchestrate.py --preflight
#    Inspect the printed PAID_PREFLIGHT / READY_FOR_EMPIRICAL_90_RUNS gate.
#    Anything other than PAID_PREFLIGHT == PASS means STOP -- do not
#    proceed, do not weaken the policy to force a pass.

# 4. Only once PAID_PREFLIGHT == PASS is on record (find_latest_passing_qualification()
#    in orchestrate.py verifies this itself, by recomputing from the
#    archived per-arm evidence -- not by trusting a cached verdict), the
#    90 fresh empirical runs may begin, case by case:
python3 orchestrate.py --cases case-001-media-library --arms baseline --execute
# ... repeated for all 30 cases x 3 arms; --execute refuses to start at
#     all if no valid qualification record is found.

# 5. NEEDS_INTENT review: manual review of every ambiguous-case run's
#    transcript against benchmark/design/needs-intent-scoring-v2.md
#    (cannot be fully automated from a file diff alone -- see DESIGN.md).

# 6. Trusted grading gate (NOT grade_run.py directly -- grade_run.py's
#    hidden-test subprocess calls plain `node` resolved via ambient PATH,
#    and does not know how to distinguish an infrastructure failure from
#    a genuine behavioral observation):
python3 grade_empirical.py
#    Refuses to produce a score table unless it finds exactly one valid,
#    current-provenance observation for every (30 cases x 3 arms) = 90
#    slot; excludes historical smoke/diagnostic archives already under
#    results/raw/ by the same provenance check, and refuses on any
#    duplicate rather than silently picking one by timestamp.

# 7. Aggregation/statistics over the resulting score table (a future pass;
#    see Metrics below).
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

All 30 cases are authored, reviewed, and frozen (`design/manifest-v3.1.json`).
Historical smoke/diagnostic `claude` runs already exist under
`results/raw/` from earlier harness-validation passes (Phase 1, plus
pre-v6 architecture diagnostics) -- these predate the current
`experiment-freeze-v6.json` instrument's provenance fields entirely and
are excluded from the 90-row empirical table by `grade_empirical.py`'s
provenance check, not by any special-cased date/path logic. No run
against the CURRENT frozen v6 instrument -- preflight or empirical -- has
been executed yet: `READY_FOR_PAID_PREFLIGHT` remains `FALSE` until the
instrument itself is committed. See `reports/pilot-report.md` for the
historical Phase 1 record and `DESIGN.md`/`harness/config.py`'s
`EXPERIMENT_PREFLIGHT_REQUIRED` for the authoritative next-step sequence.
