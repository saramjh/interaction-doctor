# Interaction Doctor Benchmark — Design

## 1. Hypothesis

**H1 (primary):** Giving a frontier coding agent the frozen Interaction
Doctor v1 skill (Arm C) improves interaction-defect outcomes (recall,
correct-repair rate, false-positive rate, intent-guessing rate,
false-closure rate) over the same agent with no skill (Arm A), by more
than can be explained by simply telling the model to be careful (Arm B).

**H0:** Arm C performs no better than Arm B (any improvement over Arm A is
attributable to "be thorough," not to Interaction Doctor's specific
ownership/closure model).

This is a falsification exercise, not a demonstration. A result showing
C ≈ B, or C < B on some metrics, is a valid and reportable outcome.

## 2. Independent variable

Exactly one factor varies across the three runs of a case: **which of
{nothing, a generic quality instruction, the frozen Interaction Doctor v1
skill} the agent has**. Concretely, the only differences in a run's launch
are:

- Arm A: task prompt only, no `.claude/` in the workspace.
- Arm B: task prompt + `prompts/generic.md` text appended, no `.claude/`.
- Arm C: task prompt + `prompts/doctor.md` text appended, `.claude/skills/interaction-doctor/` copied verbatim into the workspace.

**The skill/slash-command subsystem is left enabled for every arm,
including A and B** (`build_args()` in `harness/runner.py` no longer
passes `--disable-slash-commands` at all). This is a correction from an
earlier draft that disabled the whole subsystem for all three arms and
had arm C read the frozen skill as plain files via the `Read` tool
instead of the real skill mechanism — that measured "the effect of extra
reference documents in the agent's context," not the actual product
condition under test, which is **"Claude Code with the Interaction Doctor
skill installed."** With the subsystem enabled uniformly:

- all three arms have identical access to whatever built-in default
  skills ship with Claude Code itself (design, dataviz, code-review, ...)
  — this is now a constant across arms, not a confound, precisely because
  it no longer differs between them;
- arm C additionally has `.claude/skills/interaction-doctor/` inside its
  own workspace, discovered through the normal project-local skill
  mechanism (the same mechanism that made this skill available in the
  actual Claude Code session that authored this benchmark, whose context
  listed `interaction-doctor` as an available skill purely from this
  repo's `.claude/skills/` directory being present — no special flag was
  needed for that to happen);
- arms A/B have no `.claude/` directory anywhere in their workspace at
  all (enforced by `workspace.build()` and independently verified by
  `contamination_check.check()`), so there is nothing for the (enabled)
  skill subsystem to discover there regardless.

`contamination_check.check()` additionally verifies, byte-for-byte, that
arm C's copy of the skill exactly matches the frozen source at
`.claude/skills/interaction-doctor/` (no missing file, no extra file, no
modified byte, ignoring only OS junk like a stray `.DS_Store`), and that
arm A/B's workspace contains zero trace of `SKILL.md` or any
`interaction-doctor`-named path. Both checks were verified against
deliberately broken inputs (a tampered `SKILL.md` byte, and the check's
own initial false-positive from matching against `WORKSPACE_ROOT`'s own
name) to confirm they actually fail when they should, not just pass by
construction.

**What is not yet empirically verified, because verifying it costs a real
`claude` invocation:** that the model, when given the skill and told to
"use the interaction-doctor skill," actually invokes it via the Skill
tool rather than ignoring it or reasoning about the task some other way.
This is exactly the kind of fact the Phase 1 smoke test itself will
surface (inspectable post-hoc from each archived run's transcript/tool
calls) — it is not something that can or should be proven before spending
the first dollar of the experiment.

Model, `--effort` (medium — the agreed first-pass baseline configuration),
tool allowlist (`Read,Edit,Write,Glob,Grep,Bash`), permission mode,
`--setting-sources`, MCP config (none), `--max-budget-usd` cap, fixture
content, and task text are identical across arms for a given case
(`harness/config.py` is the single source of truth for everything held
constant). The exact CLI argument list built for each arm was printed and
diffed directly — the only difference between arms' argument lists is the
`--add-dir`/cwd workspace path, nothing else.

## 3. Dependent variables (see README.md metrics section for formulas)

1. Defect Detection Recall
2. False Positive Rate (clean cases wrongly flagged/changed)
3. Correct Repair Rate (hidden tests pass without violating forbidden_repairs)
4. Regression Rate
5. Intent-Guessing Violation Rate (ambiguous cases where a behavior was silently chosen)
6. False-Closure / False-Success Rate (agent claims done/success but hidden grading disagrees)
7. Cost (tokens, wall-clock, tool calls, $ if exposed)

All seven are reported individually per arm; no single blended score is
authoritative (a secondary aggregate may be shown alongside, never in
place of them).

## 4. Contamination controls

See `README.md` "Isolation" section for the mechanism. In short:

- Every run gets a fresh workspace under `$TMPDIR/interaction-doctor-bench/`,
  never inside this git repository, so no ambient `CLAUDE.md`/skill from
  this project tree can be discovered by cwd-walking.
- `--setting-sources project` (never `user`) so a user's global `~/.claude`
  config cannot leak into any arm.
- `--strict-mcp-config` with no `--mcp-config` supplied removes all MCP
  servers for every arm.
- Ground truth and hidden tests live in `cases-private/`, addressed only
  by the grader, on the host machine, never inside `$TMPDIR/interaction-doctor-bench/`.
- `harness/contamination_check.py` is a mandatory, zero-cost gate run
  before every real (paid) `claude` invocation; it fails closed (blocks
  the run) if it finds a `.claude/` dir in an A/B workspace, doctor
  terminology in an A/B-visible file, a private path (`ground_truth.json`,
  `scoring.json`, any `hidden-tests/` path) referenced anywhere **in any
  arm's workspace, doctor included**, or cross-arm path bleed.
  `orchestrate.py` builds all requested arms for a case, runs
  `check_no_cross_arm_leakage()` across all of them, and refuses to invoke
  `claude` for any pair in a case where that check (or the per-arm check)
  fails — one contaminated arm blocks the whole case, not just itself.
- Each arm's Claude process runs with `cwd` = its own workspace and
  `--add-dir` limited to that same workspace, so it has no path back to
  another arm's workspace, the source repo, or `cases-private/`.
- Fresh process per run; `--no-session-persistence`; no `--resume`/`--continue`
  ever used, so no arm's context can carry into another's.

## 5. Case composition (target: 30, pilot currently ships 3 harness-validation cases)

| category | count |
|---|---|
| real pairwise interaction conflicts | 8 |
| lifecycle / cancellation / deferred-effect defects | 4 |
| environment / IME / accessibility / transformed-input defects | 4 |
| state-machine / N-ary interaction cases | 4 |
| ambiguous product-intent cases | 5 |
| safe-cooperation / negative controls | 5 |
| **total** | **30** |

Fixtures are named after their domain (`media-library`, `kanban-board`,
`drawing-canvas`, ...), never after the defect they contain, and are not
copies of `adversarial-validation.md`'s examples — they instantiate the
same underlying abstractions (ownership conflict, stale async completion,
mode-gated mutual exclusion, ...) in different surface form.

Fixtures in this pilot are deliberately dependency-free Node modules with
a tiny synthetic event-dispatch shim (`dom-shim.js`-style) rather than a
real browser DOM, so hidden tests are deterministic `node` scripts with no
Playwright/browser flakiness risk. This trades some realism for pilot
reliability — see Limitations.

## 6. Scoring

`graders/grade_run.py` reads only `results/raw/<case>/<arm>/<run>/final_workspace/`
(the archived post-run fixture tree) plus `cases-private/<case>/`.

**Diffing excludes the harness-injected `.claude/` tree.** Arm C's
workspace always contains a copy of the frozen skill under
`.claude/skills/interaction-doctor/` — that is the experimental
condition, not an agent edit. `_hash_tree()` skips any top-level
`.claude` path on both the "before" (original fixture) and "after" (final
workspace) sides before computing `changed`/`added`/`removed`, so a
doctor-arm run that makes zero fixture edits is correctly scored as
`made_functional_change: false`, exactly like baseline/generic. (Verified
directly: a synthetic doctor-arm negative-control run with the skill
files present but no fixture edits grades as `correct_no_op`, not
`false_positive_over_diagnosis`.)

**Two behavioral metrics are computed separately, not conflated:**

- `repair_success` — every `target_assertions` key (from `ground_truth.json`)
  is `true` on the hidden test run against the agent's final output, AND no
  regression (see below).
- `has_regression` — the hidden test is run **twice**: once against the
  original, unmodified fixture (`hidden_test_baseline`) and once against
  the agent's final output (`hidden_test_final`). Any assertion key that
  is `true` at baseline, is *not* in `target_assertions`, and is `false`
  in the final run counts as a regression. This is computed generically
  from `target_assertions` in ground truth — no case-specific grader code
  is needed per case; each case's hidden test just needs its assertions
  named so the harness-vs-target distinction is explicit.

**Detection is separated from repair.** `hidden_test_pass`/`repair_success`
answer "did the final code behave correctly," which conflates "the agent
never noticed the real defect" with "the agent understood it but the fix
didn't work." `detection_heuristic` is a best-effort, keyword-group
match (`detection_keyword_groups` in ground truth — e.g. requiring the
final message to mention the two competing surfaces *and* an
ownership/staleness-type mechanism word) against the agent's final
message text, independent of `repair_success`. It is explicitly a
heuristic, not a semantic judgment, and is reported as such; it is a
stopgap pending a transcript-reading judge pass.

**False-closure heuristic.** `false_closure_heuristic` flags a run where
the agent's final message matches a completion-claim pattern
(`fixed`/`resolved`/`done`/`complete`/...) with no hedging language
(`could not`/`ambiguous`/`need more information`/...) while
`hidden_test_pass` is `false` — i.e., the agent said it succeeded when the
hidden grading disagrees. Same caveat: keyword heuristic, not semantic
judgment. **Confirmed against all 9 Phase 1 smoke-test runs** (`claude
-p --output-format json`, CLI version in use at time of the smoke test,
`claude-sonnet-5` / effort `medium`): the top-level JSON object returned
on stdout is a single, non-streaming result record (`"type": "result"`,
`"subtype": "success"` on all 9 runs) with these confirmed fields:

- **final assistant response**: `result` (string) — confirmed present
  and populated on all 9 runs; the previously-guessed alternates
  (`final_result`, `text`, `message`) never appeared and have been
  dropped from `_extract_final_message_text()`, which now reads `result`
  directly with a raw-JSON-dump fallback only if it's ever absent.
- **model**: not a top-level field; per-model usage/cost is broken out
  under `modelUsage` (keyed by model id, e.g. `"claude-sonnet-5"`,
  `"claude-haiku-4-5-20251001"` for an internal helper call) with
  `inputTokens`/`outputTokens`/`cacheReadInputTokens`/
  `cacheCreationInputTokens`/`costUSD`/`canonicalModel` per entry.
- **token usage**: `usage` (object): `input_tokens`, `output_tokens`,
  `cache_creation_input_tokens`, `cache_read_input_tokens`,
  `output_tokens_details.thinking_tokens`, plus a per-iteration
  breakdown under `usage.iterations`.
- **API cost**: `total_cost_usd` (float, top-level) — sum of the
  per-model `costUSD` entries in `modelUsage`.
- **session/result status**: `is_error` (bool), `subtype` (`"success"`
  on all 9 runs), `stop_reason` (`"end_turn"` on all 9), `terminal_reason`
  (`"completed"` on all 9), `num_turns` (int), `session_id`.
- **timing**: `duration_ms`, `duration_api_ms`, `ttft_ms` (top-level,
  milliseconds); the harness separately records wall-clock time around
  the subprocess call in `run_result.json`'s `wall_clock_seconds`.
- **tool/event metadata**: **none.** `--output-format json` returns only
  this single end-of-run summary object — no per-turn tool-call log, no
  Skill/Read/Edit/Bash event trace, not even a tool-call count broken out
  by tool name (`num_turns` counts turns, not tool invocations). This is
  the reason Phase 1's Skill-invocation check could not be answered from
  existing archives — see the runner-hardening note below and the Phase 1
  report's §2.

`_extract_final_message_text()` in `graders/grade_run.py` has been
updated to read `result_json["result"]` directly (with the raw-dump
fallback retained only as a defensive default, not because any
alternate field name was ever observed).

**Runner hardening (post-Phase-1):** `harness/runner.py` now defaults to
`EVENT_LOG_MODE = True` (`harness/config.py`), requesting
`--output-format stream-json --verbose` instead of the single end-of-run
summary; the final single JSON summary above is still parsed identically
regardless, since Claude Code's stream-json mode terminates with the same
`type: "result"` object as the last line of the stream. Every real run
archives the full event stream (one JSON object per line, including
`tool_use`/`tool_result` content blocks) as `event_log.json` alongside
`run_result.json` (`orchestrate.py`'s `archive()`), so Skill-invocation
and other tool-level questions are answerable without a follow-up run.
**v6 sandbox architecture (current, active).** The Claude Code PARENT
process runs completely unsandboxed by the harness (ordinary
`subprocess.run(cwd=workspace)`, normal host auth, normal model-service
networking). Built-in file tools are governed by a trusted, per-run
inline `--settings` JSON policy (`harness/settings_policy.py`) under
`--permission-mode dontAsk` -- absolute filesystem paths in `Read(...)`/
`Edit(...)` rules use Claude Code's `//<path>` syntax; `Glob`/`Grep` are
covered by `Read` rules and `Write` by `Edit` rules, so no separate
`Glob(...)`/`Grep(...)`/`Write(...)` path rules are used.
`permissions.disableBypassPermissionsMode`/`disableAutoMode` are both set
to `"disable"`. Bash (and everything it spawns) runs under Claude Code's
OWN native Seatbelt sandbox (`sandbox.*` keys, confirmed present in the
exact installed 2.1.270 binary via `strings`), fail-closed
(`failIfUnavailable=true`, `allowUnsandboxedCommands=false`,
`excludedCommands=[]`). The native sandbox defaults to broad filesystem
read access, so the real read boundary is `sandbox.filesystem.denyRead`
of the real `$HOME` and the real benchmark workspace-root tree, with
`sandbox.filesystem.allowRead` re-opening only the current workspace and
the frozen Node runtime paths as narrower exceptions; `denyWrite` covers
`<workspace>/.claude` at the OS level, since the sandbox's working
directory is writable by default and built-in permission rules alone
don't close a Bash-originated write to the control plane. Credential
protection uses the documented native `sandbox.credentials.envVars` key
(name + `mode: "deny"` per protected variable, never a value) --
real enforcement, not a harness-side convention. `--allowedTools` is
absent entirely; `--tools` remains the availability boundary. Arm
workspaces are strictly sequential during `--execute`: build, run,
archive, destroy one arm completely before the next arm's workspace is
even built (`orchestrate.run_execute_sequential`) -- no sibling
coexistence during real execution. `--check-only`'s cross-arm-leakage
diagnostic is the only place arms are ever built together, and it cleans
up every workspace it builds before returning.

A prior custom OUTER Seatbelt sandbox wrapping the entire Claude Code
parent process (`harness/sandbox.py`, `harness/egress_proxy.py`,
allowlisted via a local CONNECT proxy to `api.anthropic.com:443`) was
designed, tested, and rejected: it created an unresolvable conflict
between the parent's own OAuth/Keychain authentication needs and Bash's
isolation needs, and a second, nested `sandbox_apply` from inside an
already-sandboxed process proved unreliable under live testing (including
a false-positive "Keychain revoked" result later traced to an unrelated
profile-file-read failure). Those files are preserved on disk as inactive
historical code -- not imported anywhere in the active v6 execution path.

`harness/tool_surface_preflight.py` is the required live-preflight check
against each arm's archived `system/init` event before the 90-run batch
is allowed to proceed (see its module docstring). `harness/preflight.py`
and `harness/preflight_validator.py` implement the v6 preflight-only
infrastructure-qualification mechanism: an external filesystem canary, a
workspace symlink to it, a parent-only synthetic non-secret environment
canary (its NAME protected via `sandbox.credentials.envVars`), and a
frozen infrastructure-check prompt appendix instructing the model to
exercise 9 frozen probes without skipping the primary task; the validator
reads the archived event log and run record and assigns each of the 9
assertions PASS/FAIL/HOLD deterministically -- never inferring PASS
merely because the `--settings` JSON contains the intended values. That
preflight is EXACTLY 3 paid runs -- `config.PREFLIGHT_CASE_ID` under each
of `config.PREFLIGHT_ARMS` (baseline, generic, doctor), same model/
effort/budget/sandbox/tool-surface/event-logging as the real 90-run batch
-- never 1 run and never a dynamically-chosen case, legal only via
`orchestrate.py --preflight`. The required sequence: commit the immutable
snapshot, `verify_experiment_freeze.py` passes, the 3 preflight runs
execute, `preflight_validator.py` scores all 9 infrastructure assertions,
all 3 archived `system/init` events are inspected, the doctor run's event
log is confirmed to contain an actual Skill tool_use for
interaction-doctor, only then are the 90 FRESH empirical runs
authorized. The Bash network allowlist is empty (`strictAllowlist=true`,
`allowedDomains=[]`) -- Bash needs no network destination for any
fixture; only the unsandboxed parent reaches the model service directly.
A genuine need for a Bash network destination during preflight is a HOLD,
reported with the exact attempted destination, not a silent addition; see
`config.EXPERIMENT_PREFLIGHT_REQUIRED` for the authoritative statement.
The preflight runs are infrastructure qualification only and are never
counted as part of the 90-row empirical result table.

Ambiguity-case grading (intent-guessing violations) cannot be fully
automated from a file diff alone: the correct outcome is often "no
behavioral change plus a clear statement that intent is required," which
requires reading the agent's final message. The grader flags these
`needs_manual_review_ambiguity` and routes them to manual review rather
than deciding itself. That manual review is now a frozen protocol --
`design/needs-intent-scoring-v2.md` and `.json` -- covering all 6
NEEDS_INTENT cases with a per-case rubric, a blind (anonymized-transcript)
review procedure, and a common output schema, written before any
experiment response was inspected. This is no longer an open item.

## 7. Statistical method

Paired design: every case runs under all three arms from the same
snapshot. For each binary outcome (e.g. "hidden test passed"), report:

- raw numerator/denominator per arm
- percentage per arm
- absolute percentage-point difference between arm pairs (A-vs-B, B-vs-C, A-vs-C)
- a paired contingency table (both-pass / A-only / C-only / both-fail style) per pairwise comparison, suitable for McNemar's test
- McNemar's exact test p-value where the discordant-pair count is large enough to be meaningful; otherwise report the contingency table only and explicitly withhold a significance claim

With n=30 per arm (one repetition), the pilot is explicitly underpowered
for most individual metrics at conventional significance thresholds. The
report will state this rather than imply significance from small-n
percentage differences.

## 8. Threats to validity

- **Single repetition per arm per case (Phase 2 pilot).** No LLM sampling-seed
  control is exposed by the CLI; a single run conflates model variance with
  arm effect. Documented deviation from the ideal design; a future rep-3
  follow-up would separate these.
- **Synthetic Node fixtures instead of real DOM/browser.** Reduces
  ecological validity for web-DOM cases; chosen for pilot determinism and
  cost. Real-world OSS cases (section 16 of the parent task) are the
  intended follow-up for ecological validity.
- **Generic-prompt strength is a judgment call.** Arm B's prompt is
  designed to be "strong but architecture-free"; if it under- or
  over-shoots realistic best-practice prompting, it changes the width of
  the B-vs-C gap without changing the A-vs-C gap. Both comparisons are
  reported so this is visible.
- **Ambiguity-case grading is only partially automatable**, per section 6.
- **Fixture authorship by the same process building the benchmark** risks
  fixtures that are unconsciously shaped to fit the ownership model's
  vocabulary. Mitigated by writing fixtures in plain interaction-domain
  language (task.md never uses Interaction Doctor terms) and by having
  the negative-control and ambiguity cases authored to the same standard
  of rigor as the defect cases.
- **n=30 pilot is for effect-size estimation, not a significance claim**,
  per section 7.

## 9. What this benchmark explicitly does NOT do

- It does not modify Interaction Doctor v1 under any circumstance,
  including when a failure suggests the spec could not represent a case
  (classified as `POSSIBLE_SPEC_GAP` and reported, never patched — see
  `reports/pilot-report.md` template).
- It does not optimize case selection to make Arm C win.
- It does not run any paid Claude Code invocation without the harness
  operator explicitly passing `--execute` after reviewing a cost estimate.
