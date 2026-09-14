# Interaction Doctor Benchmark — Pilot Report

Status as of this report: **harness built and statically validated; zero
paid `claude` runs executed.** No experimental result exists yet — this
report currently documents harness readiness and the cost decision point
required before spending API budget, per the parent task's instruction to
stop and report before any paid execution.

## HARNESS RESULT

**Hardening pass (post-review, zero API cost):** an external review of the
first draft found several issues that would have distorted results if the
9-run smoke test had been launched as-is. All were fixed and re-verified
before any real `claude` invocation:

- `EFFORT` was `high`; changed to the agreed baseline `medium`.
- `--disable-slash-commands` was arm-conditional (A/B only), leaving arm C
  able to reach every other built-in skill (design, dataviz, code-review,
  ...) that A/B could not — an unintended second independent variable. Now
  applied identically to all three arms; arm C is instead told to `Read`
  the frozen skill files directly, using the same tool every arm has.
- The grader hashed the entire final workspace against the entire original
  fixture, including arm C's injected `.claude/skills/interaction-doctor/`
  tree — which would have scored every doctor-arm run as
  `made_functional_change: true` regardless of whether the agent touched
  the fixture, corrupting the false-positive metric specifically for the
  arm the benchmark exists to evaluate. Fixed: `.claude/` is excluded from
  both sides of the diff. Verified with a synthetic doctor-arm run that
  makes zero fixture edits — grades as `correct_no_op`, not
  `false_positive_over_diagnosis`.
- `check_no_cross_arm_leakage()` existed but was never called by
  `orchestrate.py`, and its path-membership check was a no-op (compared a
  directory path against individual file paths, which can't match). Fixed
  and wired in: `orchestrate.py` now builds all requested arms for a case
  first, then runs this check across them before allowing any execution.
- `grade_run.py` only computed hidden-test-pass and a raw diff; "Detection
  Recall," "Regression Rate," "Intent-Guessing," and "False-Closure" were
  named in DESIGN.md/README.md but not implemented. Implemented all four:
  regression is computed generically from a `target_assertions` field
  added to each case's `ground_truth.json` (hidden test runs against both
  the original fixture and the agent's output; a non-target assertion
  that flips true→false is a regression); repair success now requires
  target assertions true *and* no regression; detection and false-closure
  are explicit, clearly-labeled keyword heuristics against the agent's
  final message pending a transcript-judge pass.
- `case-002-kanban-board`'s forbidden repair ("always ignore save
  responses") was not actually catchable — the existing hidden tests would
  pass a "no-op" fix trivially, since the optimistic write already gave
  the right answer. Fixed by extending the fixture so `resolve()` carries
  an explicit server payload and adding a `server_rejection_is_honored_when_current`
  assertion (a legitimate server response must still apply when it's for
  the card's current, unsuperseded request). Verified directly: the buggy
  fixture fails only the target assertion; a proper latest-request-id fix
  passes all three; the "ignore everything" hack now fails the new
  assertion specifically.
- `case-001-media-library`'s ground truth listed "pointer capture
  semantics" as an allowed repair, but the fixture's fake DOM has no
  pointer-capture concept to actually implement or test — removed.
- `case-003-drawing-canvas`'s ground truth allowed "pure refactor with no
  functional diff," which the grader can't cheaply distinguish from an
  unnecessary change — tightened to strict no-source-change.
- Contamination check's private-data check (`ground_truth.json`,
  `scoring.json`, `hidden-tests/`) was scoped to baseline/generic only;
  moved to apply to all three arms, since there is no legitimate reason
  private data should ever reach arm C either.

All fixes were re-verified with the same method as before — direct `node`
execution against fixtures and synthetic archived runs — never by
executing a real `claude` process, so this pass cost nothing.

**Second hardening pass (post-review #2, zero API cost): the C-arm skill
exposure mechanism itself was wrong.** The first hardening pass disabled
the skill/slash-command subsystem for all three arms (to remove the
built-in-skill-access asymmetry) and had arm C read the frozen skill as
plain files via `Read`. External review correctly identified that this
no longer measures the actual product condition of interest —
"Claude Code with Interaction Doctor installed" — but instead measures
"the effect of extra reference documents in context." Corrected:

- `--disable-slash-commands` removed entirely from `runner.build_args()`;
  the skill/slash-command subsystem is now enabled identically for A, B,
  and C. Verified by printing and comparing the exact argument list built
  for each arm on the same case: identical apart from the `--add-dir`
  workspace path.
- `prompts/doctor.md` reverted to instructing "use the interaction-doctor
  skill" (the real product-facing instruction), not "Read these files
  manually."
- Investigated the installed CLI (`claude --help`, `claude doctor`,
  `claude plugin --help`) for a way to enumerate discovered skills without
  an API call; none exists. Relied instead on: (a) the CLI's own
  documented semantics for `--disable-slash-commands` ("Disable all
  skills" — confirming its removal restores the standard subsystem
  uniformly), and (b) this benchmark-authoring session's own observed
  behavior, where `interaction-doctor` appeared in the available-skills
  list purely because this repo's `.claude/skills/interaction-doctor/`
  directory was present in the working tree — the same project-local
  discovery mechanism arm C's workspace now relies on. Whether the model
  actually *invokes* the skill via the Skill tool once discoverable is
  not something that can be proven without a real run; that will be
  checked post-hoc from Phase 1's archived transcripts, not asserted in
  advance.
- Strengthened `contamination_check.py`: arm C's skill copy is now
  verified byte-for-byte against the real frozen source (no missing file,
  no extra file, no modified byte, ignoring only OS junk such as a stray
  `.DS_Store` found in the source skill directory itself), and arm A/B
  workspaces are checked for zero trace of `SKILL.md` or any
  `interaction-doctor`-named path anywhere. Both checks were verified
  against deliberately broken inputs: a tampered byte in a copied
  `SKILL.md` was correctly caught; and the new A/B check's own first
  implementation had a false-positive bug (matching against
  `WORKSPACE_ROOT`'s own name, `interaction-doctor-bench`, since it
  contains the substring `interaction-doctor`) which was caught by
  actually running it, not just by inspection, and fixed by checking
  workspace-relative paths instead of absolute ones.
- `workspace.build()` now excludes `.DS_Store`/`Thumbs.db` when copying
  the skill directory, so arm C's copy is exactly the documented
  `SKILL.md` + `references/*.md` content, not incidental OS files.
- Confirmed `harness/config.py` actually contains `EFFORT = "medium"`
  (it already did — the `effort (\`high\`)` line elsewhere in this report
  was stale prose from before the first hardening pass and has been
  corrected to `medium`).

All of the above was re-verified at zero API cost: `py_compile` on every
harness file, a full dry-run contamination gate across all 9 (case × arm)
pairs (`all clean: True`), a direct print-and-diff of the exact CLI
argument list built for each arm, direct filesystem inspection proving
A/B have no `.claude/` trace while C has the skill at the normal
project-local path, and the two negative tests described above.

Also built and passing, at zero API cost:

- Directory scaffold (`benchmark/{cases,cases-private,prompts,harness,graders,results,reports}`) per spec.
- `harness/config.py` — single source of truth for model (`claude-sonnet-5`), effort (`medium`), tool allowlist, permission mode, setting sources, MCP isolation, and a `--max-budget-usd 1.00` per-run spend cap.
- `harness/workspace.py` — builds an isolated workspace per (case, arm, run) outside the repo tree; refuses to build if a fixture accidentally ships a `.claude/` dir.
- `harness/contamination_check.py` — automated, zero-cost gate. Run for all 9 (case × arm) pairs across the 3 pilot cases: **all 9 reported `clean`**.
- Independently re-verified by direct filesystem inspection (not just the gate's own self-report): baseline/generic workspaces contain no `.claude/`; doctor workspace contains a verbatim `.claude/skills/interaction-doctor/SKILL.md` + `references/`; baseline prompt is exactly `task.md`; generic prompt is `task.md` + `prompts/generic.md` with no Interaction-Doctor terminology present.
- `harness/runner.py` + `harness/orchestrate.py` — invocation and archival path exercised in `--check-only` (dry-run) mode for all 9 pairs; `--execute` path not yet exercised (no real `claude` call made).
- 3 harness-validation fixtures authored and verified directly with `node` (no `claude` involved):
  - `case-001-media-library` (real pairwise conflict: scrub-drag vs. carousel-drag ownership): buggy fixture **fails** the hidden test as shipped; a hand-applied plausible fix (`stopPropagation` on the scrubber) **passes** it.
  - `case-002-kanban-board` (lifecycle/stale-async defect: out-of-order save-response race): buggy fixture **fails**; a hand-applied plausible fix (latest-request-id guard) **passes**.
  - `case-003-drawing-canvas` (negative control: mode-gated draw/pan mutual exclusion, already correct): fixture **passes as shipped**, with no changes.
- `graders/grade_run.py` implemented (hidden-test execution + diff-vs-original-fixture false-positive detection + per-case-type verdict); not yet run against a real archived agent run since none exists.

## EXACT FINAL INVOCATION (A/B/C), for approval

Printed directly from `runner.build_args()` for `case-001-media-library`
(other cases differ only in the workspace path and prompt text; the
argument list shape is identical for every case):

```
baseline: claude -p <task.md text> \
  --add-dir .../case-001-media-library/baseline/run-01/workspace \
  --model claude-sonnet-5 --effort medium --output-format json \
  --permission-mode bypassPermissions --strict-mcp-config \
  --setting-sources project --allowedTools Read,Edit,Write,Glob,Grep,Bash \
  --no-session-persistence --max-budget-usd 1.00

generic:  same as baseline, except:
  --add-dir .../case-001-media-library/generic/run-01/workspace
  prompt = <task.md text> + "\n\n" + <prompts/generic.md text>

doctor:   same as baseline, except:
  --add-dir .../case-001-media-library/doctor/run-01/workspace
  prompt = <task.md text> + "\n\n" + <prompts/doctor.md text>
  workspace additionally contains .claude/skills/interaction-doctor/
  (verbatim, byte-verified copy of the frozen skill)
```

No arm passes `--disable-slash-commands`; the skill/slash-command
subsystem is enabled identically for all three. This is the corrected
design from the second hardening pass above — awaiting approval before
this is actually executed.

## EXPERIMENTAL RESULT

None yet. No `claude` process has been invoked by this harness. Reporting
a result now would require either fabricating data or running unbudgeted
paid API calls — both are excluded by the task's constraints.

## LIMITATIONS

- Only 3 of the planned 30 cases exist (1 conflict, 1 lifecycle, 1
  negative control). Ambiguity, environment/IME/accessibility, and N-ary
  state-machine categories are not yet represented — see DESIGN.md §5 for
  the target distribution and next-step authoring plan.
- Single repetition per arm is planned per the parent task's instruction
  ("one repetition ... is sufficient for this first pilot"); this
  conflates model sampling variance with arm effect (DESIGN.md §8).
- Ambiguity-case grading cannot be fully automated from a file diff; it
  needs a transcript-level check not yet built (DESIGN.md §6).
- Cost per run is not yet empirically known for this specific harness
  configuration (model, effort, tool set, fixture size) — see below.

## COST ESTIMATE AND NEXT STEP

**No empirical cost data exists yet** because no run has executed. Rather
than guess a dollar figure, the responsible next step is:

1. Run the **Phase 1 smoke test** (9 runs: 3 cases × 3 arms, 1 rep each) with the per-run `--max-budget-usd 1.00` cap already wired in, bounding worst-case spend for this step at **$9.00** and typically far less for tasks this small:

   ```bash
   cd benchmark/harness
   python3 orchestrate.py \
     --cases case-001-media-library,case-002-kanban-board,case-003-drawing-canvas \
     --arms baseline,generic,doctor \
     --execute
   ```

2. After Phase 1 completes, read the actual cost/token/wall-clock fields
   captured in each `results/raw/.../run_result.json` (from
   `--output-format json`), extrapolate ×10 to estimate the 90-run Phase 2
   pilot, and report that estimate here before running:

   ```bash
   python3 orchestrate.py --arms baseline,generic,doctor --execute   # all 30 cases, once Phase 2 fixtures exist
   ```

This report will be updated with real numbers once Phase 1 is authorized
and executed. Until then, no experimental claim about Interaction Doctor's
effect is made.
