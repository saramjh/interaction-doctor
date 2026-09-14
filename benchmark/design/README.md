# Benchmark Design v3.1 — Frozen Specification

```
BENCHMARK_DESIGN_V3_1 = FROZEN
```

This directory holds the **design/authoring metadata** for the 30-case
Interaction Doctor empirical efficacy pilot: the frozen manifest and its
validator. It is separate from both `benchmark/cases/` (the public,
agent-visible fixtures) and `benchmark/cases-private/` (ground truth and
hidden tests).

**`benchmark/design/manifest-v3.1.json` is authoring metadata, not
agent-visible task context.** It must never be copied into a case's
`fixture/` directory, referenced from a `task.md`, or otherwise made
reachable from an evaluated agent's workspace. `harness/workspace.py`
only ever copies `cases/<case-id>/fixture/` into a run's workspace, so
this directory is structurally outside that path by construction — but
that structural fact does not remove the obligation to keep it that way
deliberately.

## Files

- `manifest-v3.1.json` — the exact 30-entry case manifest validated in
  the v3.1 design-review pass. Not redesigned, renamed, or rebalanced
  since that approval.
- `validate_manifest.py` — recreates the deterministic checks that
  produced `ALL_CHECKS_PASS = True` for this manifest. Reads the JSON
  from disk; computes every count and coverage check from the actual
  data; does not hard-code a pass result. Run it with:

  ```
  python3 benchmark/design/validate_manifest.py
  ```

## What this manifest is for

It is the traceability record connecting the design-review conversation
(three rounds of correction: v1 → v2 → v3 → v3.1) to what actually gets
built as fixtures. Each of the 30 entries records, per case: outcome,
difficulty tier, runtime, the Interaction Doctor constructs (relations /
N-ary group policy / lifecycle categories / effect-lifetime categories /
environmental claims) the scenario is *designed* to exercise, its
contamination-risk classification against
`references/adversarial-validation.md`, and the primary hidden-test
oracle(s) fixture authoring must implement.

It is not itself a scoring rubric an agent should see, and it is not a
substitute for the actual `ground_truth.json` / `hidden-tests/` pair each
case gets under `cases-private/` during fixture authoring.

## Interpretation limits (binding on scoring and reporting)

- **Semantic runtime shims test ownership-semantics transfer, not full
  native framework/compiler competence.** Cases built against a SwiftUI-,
  Compose-, Flutter-, or Qt-flavored shim exercise correct reasoning
  about that framework's real ownership/priority/lifecycle primitives
  (named identically to the real API surface), never an actual
  compiler/toolchain/platform build. Do not report a result from these
  cases as evidence of native framework competence.

- **`VERIFIED_UNMODELED_COUNT = 0`.** After a rigorous adversarial-reduction
  pass (all nine reduction questions, applied to every UNMODELED
  candidate produced across the design process), no case in this 30-case
  set survives as a genuine UNMODELED oracle — each candidate reduced to
  an existing frozen-v1 construct (COOPERATES via its actual
  interference predicate, CONDITIONAL over transformed/semantic input, or
  ordinary scope/resource-invalidation plus NEEDS_INTENT). This pilot
  therefore contains **no case that measures an arm's ability to
  correctly report a genuine UNMODELED relationship.** A result from this
  pilot is silent on that axis, not passing on it. A separate
  model-boundary / UNMODELED challenge set is a distinct future design
  effort, out of scope here.

- **Construct labels are diagnostic metadata, not efficacy-scoring
  requirements.** A case's `relations` / `group_policy` /
  `lifecycle_categories` / `effect_lifetime_categories` fields describe
  what the *scenario* is designed to exercise. They do not mean the
  evaluated agent must name, invoke, or conceptualize that construct to
  score correctly. Every `primary_hidden_oracles` entry is phrased as an
  observable behavioral assertion for exactly this reason.

- **Cross-arm efficacy scoring is behavior-first and vocabulary-blind.**
  A baseline or generic-audit transcript that reaches the correct
  behavioral outcome (a passing hidden test for YES/NO cases; a
  well-formed escalation with locatable context for NEEDS_INTENT cases)
  receives identical credit to a Doctor-arm transcript reaching the same
  outcome via Interaction Doctor's own vocabulary. Doctor-specific
  disposition/construct terminology appearing in a transcript is logged
  separately as protocol-conformance metadata and carries zero weight in
  cross-arm efficacy comparison.

- **One repetition per case/arm is a pilot limitation.** With n=1 per
  (case, arm) cell, individual case results are indicative, not
  statistically powered. Aggregate patterns across the 30-case set carry
  more evidentiary weight than any single case's outcome.

- **Hidden behavioral tests, not golden-patch similarity, are the repair
  oracle.** Every YES/NO case is graded by executing
  `cases-private/<case-id>/hidden-tests/test.js` against the agent's
  final workspace and comparing target/regression assertion results to
  the same test run against the original fixture — never by diffing
  against a reference patch.

- **NEEDS_INTENT cases use semantic transcript/manual grading.** These
  cases have no fixed code-level "correct" diff; `intent_status:
  "ambiguous"` in `ground_truth.json` routes grading to manual/semantic
  review (per `graders/grade_run.py`'s `needs_manual_review_ambiguity`
  verdict), applying the behavioral criteria recorded during design: the
  transcript must (1) recognize the decision point, (2) not silently
  resolve it, (3) surface it usably with locatable context — scored
  identically regardless of which arm produced it or what vocabulary it
  used. A silent no-op (no code change, no acknowledgment of the open
  question) is not sufficient credit.
