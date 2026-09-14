# Interaction Doctor Benchmark — Phase 1 Smoke Test Validation Report

Scope: validate the completed 9-run smoke test (3 cases × 3 arms, 1 rep
each, `claude-sonnet-5` / effort `medium`) and harden the benchmark
instrumentation. **No new Claude runs were executed for this report.**
This is a harness-validation exercise, not an effectiveness comparison —
see the Phase 1 Pass/Fail gate at the end for why the 9-run result is not
being read as evidence Interaction Doctor is better or worse than
baseline.

## 0. A grader bug was found and fixed during this validation

Before any of the results below could be trusted, grading all 9 runs
naively (passing a relative archive path, the way the documented CLI
usage `grade_run.py <archived-run-dir>` invites) produced **9/9
`hidden_test_pass: false`**, including the negative-control case, which
the pre-execution pilot report had already verified passes as shipped.
That is impossible unless the grader itself is broken.

**Root cause:** `graders/grade_run.py` shells out to each case's
`hidden-tests/test.js`, which loads the target fixture via
`require(path.join(workspace, 'app.js'))`. Node's `require()` resolves a
bare (non-`./`, non-`/`) path argument as a *package specifier*, not a
relative file path — so a relative `workspace` argument silently fails
to load the module (`Cannot find module ...`) instead of erroring
loudly, and the grader recorded that as "hidden test fails," i.e. "agent
did not fix the defect." This is a false-negative bug in the harness,
not a fact about the runs.

**Fix applied:** `grade()` now normalizes `run_archive_dir` with
`os.path.abspath()` unconditionally at the top of the function, so
grading is correct regardless of whether the caller passes a relative or
absolute path. Verified directly: re-running `grade_run.py` with a
relative path against `case-003-drawing-canvas/doctor` now correctly
returns `correct_no_op` / `hidden_test_pass: true`, matching the
absolute-path result.

All results below are from the **fixed** grader.

## 1. Graded results for all 9 runs

Outputs written: `results/smoke-summary.json`, `results/smoke-summary.csv`.

| case | arm | rc | hidden_test_pass | repair_success | regressions | made_functional_change | verdict | detection_heuristic | false_closure_heuristic |
|---|---|---|---|---|---|---|---|---|---|
| case-001-media-library | baseline | 0 | true | true | none | true | correct_repair | true | false |
| case-001-media-library | generic  | 0 | true | true | none | true | correct_repair | true | false |
| case-001-media-library | doctor   | 0 | true | true | none | true | correct_repair | true | false |
| case-002-kanban-board  | baseline | 0 | true | true | none | true | correct_repair | true | false |
| case-002-kanban-board  | generic  | 0 | true | true | none | true | correct_repair | true | false |
| case-002-kanban-board  | doctor   | 0 | true | true | none | true | correct_repair | true | false |
| case-003-drawing-canvas | baseline | 0 | true | true | none | false | correct_no_op | n/a | false |
| case-003-drawing-canvas | generic  | 0 | true | true | none | false | correct_no_op | n/a | false |
| case-003-drawing-canvas | doctor   | 0 | true | true | none | false | correct_no_op | n/a | false |

All 9 runs executed and returned normally (`returncode: 0`,
`is_error: false`, `subtype: "success"`, `terminal_reason: "completed"`).
No timeouts, no nonzero exits, no budget-cap trips.

Per-file diff vs. original fixture, all consistent with the ground truth:

- case-001: every arm changed only `app.js` (added `e.stopPropagation()`
  to the scrubber's pointer handlers). Doctor and generic applied it only
  to `pointerdown` (minimal); baseline additionally added it to
  `pointermove`/`pointerup` (broader than strictly necessary, but not a
  forbidden repair and produced no regression).
- case-002: every arm changed only `board.js`, each using a distinct but
  equally allowed mechanism — baseline: latest-request-id gate at
  resolution time; generic and doctor: `scheduler.cancel()` of the
  superseded request plus a request-id guard. None used the forbidden
  "always ignore server responses" hack (confirmed both by diff
  inspection and by the `server_rejection_is_honored_when_current` hidden
  assertion passing in all three).
- case-003: zero source changes in all three arms (`diff.changed/added/
  removed` all empty), matching the negative-control's only allowed
  repair ("no change to canvas.js at all").

## 2. Skill invocation verification

**Cannot be directly verified from the existing archives.**

Inspected `run_result.json` for all three doctor-arm runs: the only
artifact captured is the single end-of-run JSON object from `claude -p
--output-format json`. Its complete key set (confirmed identical across
all three doctor runs) is:

```
api_error_status, duration_api_ms, duration_ms, fast_mode_disabled_reason,
fast_mode_state, first_content_frame_ms, is_error, modelUsage, num_turns,
permission_denials, queued_turn_count, result, result_index, session_id,
stop_reason, subagent_stats, subtype, terminal_reason, time_to_request_ms,
total_cost_usd, ttft_ms, ttft_stream_ms, type, usage, uuid
```

There is no per-turn tool-call log, no tool-name breakdown, and
`num_turns` (9, 9, 7 for the three doctor runs) counts conversation turns,
not tool invocations — it cannot distinguish "invoked the Skill tool"
from "read `SKILL.md` via `Read`" from "never touched the skill files at
all and just used the vocabulary because the prompt told it to write like
Interaction Doctor." The doctor arm's final messages use Interaction
Doctor terminology (Claims, ownership, Effect Lifetime, closure
certification) and the workspace's skill copy is verified byte-identical
to the frozen source (see §5), but per the task's own instruction, neither
of those is proof of actual invocation.

**Runner hardened for future runs, not rerun now.** `claude --help` was
inspected (not guessed from memory): `--output-format stream-json`
exists and is documented as the realtime per-message streaming format;
`--include-partial-messages` and related flags note they "only work with
--print and --output-format=stream-json." `harness/runner.py` and
`harness/config.py` were updated:

- `config.EVENT_LOG_MODE` (default `False`, so Phase 1's exact invocation
  shape is not silently altered retroactively) — when `True`,
  `runner.build_args()` swaps `--output-format json` for `--output-format
  stream-json --verbose` (confirmed by direct comparison of the built
  argument list for both modes — identical except that one substitution)
  and `runner.run()` archives every parsed event line to a new
  `event_log.json` alongside the existing `run_result.json`, while still
  extracting the same final `type: "result"` object stream-json
  terminates with, so all existing downstream parsing (grader, cost
  fields) is unaffected.
- Verified with `py_compile` on all 5 harness modules and a direct call
  to `build_args()` in both modes — normal mode's output is byte-for-byte
  identical to the args actually used in the 9 archived runs; event-log
  mode differs only in the flagged substitution.

**`SKILL_INVOCATION_TRACE = UNVERIFIED`**

## 3. Claude JSON schema, confirmed from real runs

Checked against all 9 archived `run_result.json` files, not just one:

- **Final assistant response** → `result` (string). Present, non-empty,
  populated on all 9 runs. The other guessed field names
  (`final_result`, `text`, `message`) never appeared in any run.
- **Model** → not a single top-level field; per-model breakdown lives
  under `modelUsage` (keyed by model id — every run shows both
  `claude-sonnet-5` and an internal `claude-haiku-4-5-20251001` helper
  call), each with `inputTokens`/`outputTokens`/`cacheReadInputTokens`/
  `cacheCreationInputTokens`/`costUSD`/`canonicalModel`.
- **Token usage** → `usage.input_tokens`, `usage.output_tokens`,
  `usage.cache_creation_input_tokens`, `usage.cache_read_input_tokens`,
  `usage.output_tokens_details.thinking_tokens`.
- **API cost** → `total_cost_usd` (float, top-level; equals the sum of
  `modelUsage[*].costUSD`).
- **Session/result status** → `is_error` (bool), `subtype` (`"success"`
  on all 9), `stop_reason` (`"end_turn"` on all 9), `terminal_reason`
  (`"completed"` on all 9), `num_turns`, `session_id`.
- **Tool/event metadata** → none available in this output mode (see §2).

`graders/grade_run.py`'s `_extract_final_message_text()` has been
updated to read `result` directly instead of probing four guessed field
names; `DESIGN.md` has been updated with this confirmed schema and the
runner-hardening note.

## 4. Manual audit vs. automatic grades

| case | arm | automatic verdict | manual verdict | agree? | notes |
|---|---|---|---|---|---|
| case-001 | baseline | correct_repair | correct repair | yes | `stopPropagation` on 3 scrubber handlers; broader than needed but harmless; independent carousel drag confirmed unaffected by the hidden test's `carousel_drag_still_works` assertion |
| case-001 | generic | correct_repair | correct repair | yes | minimal `stopPropagation` on `pointerdown` only |
| case-001 | doctor | correct_repair | correct repair | yes | same minimal fix as generic; final message explicitly certifies "Affected Interaction Closure" per the skill's closure-contract vocabulary |
| case-002 | baseline | correct_repair | correct repair | yes | latest-request-id check at resolution time; stale response no longer overwrites newer state; current/legitimate server response (including rejection) still honored — confirmed via diff and via the `server_rejection_is_honored_when_current` hidden assertion passing |
| case-002 | generic | correct_repair | correct repair | yes | `scheduler.cancel()` of superseded request + guard; "ignore everything" hack not present (diff shows a conditional, not an unconditional skip) |
| case-002 | doctor | correct_repair | correct repair | yes | same mechanism as generic; final message frames it explicitly as an ownership/Effect-Lifetime finding |
| case-003 | baseline | correct_no_op | correct no-op | yes | zero diff; no invented conflict in final message |
| case-003 | generic | correct_no_op | correct no-op | yes | zero diff |
| case-003 | doctor | correct_no_op | correct no-op | yes | zero diff; final message explicitly states the mode-gate is already correct by design (space-vs-drag ordering resolved at `pointerdown`), not merely silent — this is the intent-and-ambiguity protocol working as intended on a case where no escalation was warranted |

**Automatic and manual grading agree on all 9/9 runs.** The one
disagreement that did occur during this validation pass — the pre-fix
grader reporting 9/9 failures — was diagnosed as a grader bug (§0) and
fixed, per the task's instruction to fix the grader/oracle rather than
reinterpret the run.

## 5. Experimental isolation, verified post-hoc

Checked directly against the archived `final_workspace/` trees and the
still-present pre-run tmp workspaces (`/var/folders/.../interaction-doctor-bench/`),
plus a live re-run of `harness/contamination_check.check()` against all 9
pre-run workspace directories:

- **`contamination_check.check()` reports CLEAN for all 9 (case, arm)
  pairs**, re-run directly for this validation (not just trusted from the
  pilot report).
- **Baseline / generic**: no `.claude` directory in any of the 6
  archived `final_workspace/` trees (`find -iname "*interaction-doctor*"
  -o -iname SKILL.md` → 0 matches in all 6). No trace of
  `ground_truth.json`, `hidden-tests/`, `cases-private`, or
  `scoring.json` in any of the 9 archived workspaces (`grep -rl` across
  all 9 → empty).
- **Doctor**: `.claude/skills/interaction-doctor/` present in all 3
  archived workspaces, and `diff -rq` against the live frozen source
  (`.claude/skills/interaction-doctor/` at repo root) shows **zero
  differences** for all 3 — byte-identical, not just present.
- **CLI args**: extracted and compared the full argument list for all 9
  runs (stripping only the prompt text and workspace path). Every run
  shares identical `--model claude-sonnet-5 --effort medium
  --output-format json --permission-mode bypassPermissions
  --strict-mcp-config --setting-sources project --allowedTools
  Read,Edit,Write,Glob,Grep,Bash --no-session-persistence --max-budget-usd
  1.00`. No arm-specific tool/permission/budget deviation found.
- **Fixture snapshot**: each arm's pre-edit files hash-match the same
  `cases/<case>/fixture/` source for a given case (confirmed via the
  grader's before/after diff, which is computed against the one shared
  `CASES_DIR` fixture for all three arms of a case).
- **Fresh session per run**: `--no-session-persistence` present in every
  run's args; each run has a distinct `session_id`.

**No isolation deviation found.**

## 6. Cost and performance sanity check

Computed directly from the 9 archived `run_result.json` files (`total_cost_usd`, `wall_clock_seconds`):

| arm | n | total cost | mean cost/run | total wall-clock | mean wall-clock/run |
|---|---|---|---|---|---|
| baseline | 3 | $0.3313 | $0.1104 | 114.5s | 38.2s |
| generic | 3 | $0.3897 | $0.1299 | 154.7s | 51.6s |
| doctor | 3 | $0.5860 | $0.1953 | 252.3s | 84.1s |
| **all** | **9** | **$1.3070** | **$0.1452** | **521.5s** | **57.9s** |

This is reported purely as a cost/time observation, per instructions —
**not** an effectiveness comparison; sample size is 1 rep per (case, arm)
cell, which conflates model sampling variance with arm effect. (The
doctor arm's higher cost/time is expected on its face — reading the
skill's reference files adds tokens — and is not being read as a
negative finding at n=1.)

**Projected Phase 2 cost (30 cases × 3 arms = 90 runs), using this
smoke test's per-run costs as the only available empirical basis:**

- Mean-based: 90 × $0.1452 ≈ **$13.07**
- Range across the 9 observed per-run costs ($0.093–$0.253): 90 ×
  min/max ≈ **$8.36 – $22.77**
- Wall-clock, if run serially: 90 × 57.9s ≈ **87 minutes** (parallelizable
  across cases/arms if the runner supports concurrent invocation, which
  was not exercised here)

These are rough projections from 9 data points on 3 small fixtures, not a
committed budget — Phase 2's 27 new cases are unauthored and may have
different size/complexity, which would shift these numbers.

## 7. Phase 1 Pass/Fail gate

- All 9 runs executed normally: **yes** (§1)
- Grader and manual review agree: **yes, 9/9**, after fixing a real
  grader bug found during this validation (§0, §4)
- Isolation confirmed: **yes** (§5)
- Real Skill invocation directly verified: **no** — the existing output
  format cannot prove it (§2)

## **PHASE_1_PASS_WITH_TRACE_FOLLOWUP**

## 8. Exact minimal next action

Do **not** rerun the 9 smoke-test cases. The minimum follow-up to resolve
the one open item (§2) is:

1. Set `harness/config.EVENT_LOG_MODE = True` (already implemented and
   compile-verified in this pass; not yet exercised against a real
   `claude` process).
2. Run **one** additional paid doctor-arm invocation — reuse
   `case-001-media-library` (smallest/cheapest fixture observed: $0.093
   at baseline) — with event-log mode on, e.g.:
   ```
   cd benchmark/harness
   python3 orchestrate.py --cases case-001-media-library --arms doctor --execute
   ```
   bounded by the existing `--max-budget-usd 1.00` cap.
3. Inspect the archived `event_log.json` for a `tool_use` content block
   naming the Skill tool (or the CLI's documented equivalent event) to
   settle §2 directly, and record the exact field/event name found (or
   confirmed absent) back into `DESIGN.md`.

This is 1 additional run, not another 9- or 90-run batch, and does not
touch Interaction Doctor v1, the frozen prompts, or the existing 9
archived results.

---

**Do not create the remaining 27 Phase 2 cases. Do not execute the
90-run Phase 2 batch. Interaction Doctor v1 was not modified by this
validation pass — only `graders/grade_run.py`, `harness/runner.py`,
`harness/config.py`, and `DESIGN.md` were changed, all benchmark
instrumentation, none of it the product spec under test.**
