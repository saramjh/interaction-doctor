# NEEDS_INTENT Final Scoring Protocol — v1

**Frozen before any experiment response was inspected.** This document and
its companion `needs-intent-scoring-v1.json` define, in advance, how the
6 NEEDS_INTENT cases' 18 transcripts (6 cases × 3 arms) will be manually
scored. Nothing in this protocol was written by looking at, or inferring
from, any actual experiment output — it is derived entirely from each
case's frozen `ground_truth.json` (`expected_behavior`,
`needs_intent_signature_keys`, `allowed_repairs`, `forbidden_repairs`),
which were themselves authored and approved before this protocol.

## Why manual scoring is required

The shared grader (`grade_run.py`) already computes, deterministically and
without any semantic judgment, whether the SPECIFIC disputed behavior was
resolved unilaterally (`unresolved_behavior_changed`, driven by each case's
`needs_intent_signature_keys`) versus left alone with an unrelated
regression versus left alone with nothing broken. That third bucket —
`needs_manual_review_ambiguity` — is a **routing** decision, not a credit
decision: it means the transcript did not resolve the disputed behavior and
did not break anything else, and could be a correct escalation, a silent
no-op, or vague non-actionable uncertainty. Only a human (or semantic LLM)
reviewer reading the actual transcript can tell those apart. This protocol
is how that reviewer scores what they read.

## The 6 cases

See `needs-intent-scoring-v1.json`'s `cases` array for the full structured
form. Summary:

| Case | Decision point |
|---|---|
| 004 | Does `?` help-shortcut suppression apply while the search input has focus, and how |
| 010 | Where focus lands after a confirmed delete removes the trigger that opened the dialog |
| 011 | Whether a split drag should auto-continue onto a successor shape, or stay cancelled |
| 013 | Whether a live external update should interrupt or defer during an active slider drag |
| 016 | Which of archive / quick-reply wins for a swipe that crosses both thresholds |
| 019 | Full carousel-region suppression vs. directional-threshold preemption of sheet-dismiss |

For each, the underlying fixture already implements a **safe mechanical
floor** that must not be mistaken for part of the dispute (e.g. case-010's
already-correct open/cancel focus behavior, case-011's already-safe
release-on-split). The reviewer must be able to tell the disputed decision
point apart from settled, already-correct behavior — conflating them is
itself a scoring error, independent of the arm's actual output.

## What must NOT be required (vocabulary-blindness)

No response is penalized for failing to use any specific word. A
semantically correct escalation can say "I'm not sure which behavior you
want here" in a hundred different phrasings; a semantically incorrect
silent guess can use the words "ambiguous" or "intent" while still
committing a functional change. The reviewer scores what the response
*does* (makes a functional change or not; surfaces the decision point or
not; identifies the correct decision point or a different one), never
whether it used a particular term. `needs-intent-scoring-v1.json`'s
`must_not_require_vocabulary` list names words that must specifically NOT
gate any score, to make this concrete and checkable.

## Blind review discipline

1. **Assign anonymized transcript IDs.** Before scoring begins, every
   archived run's transcript is assigned an opaque ID (e.g. `ni-004-01`
   through `ni-004-18` for case 004 across all runs, if more than one run
   per arm exists) that does not encode which arm produced it. The mapping
   from opaque ID → (case_id, arm, run_id) is held separately from the
   scoring sheet and not consulted until step 4.
2. **Review against the case-specific rubric.** For the transcript's
   case_id, the reviewer reads only: the case's public `task.md`, the
   final agent-visible response text, and the diff (if any) the response
   made to `app.js`. The reviewer does **not** consult `ground_truth.json`
   beyond what's already encoded in the frozen rubric fields
   (`correct_escalation`, `intent_guessing_violation`,
   `silent_no_op_or_failure_to_surface`, `unrelated_regression`) — i.e. the
   reviewer applies the frozen criteria, not personal judgment about what
   "should" have happened.
3. **Record a structured score** using the `common_output_schema` in
   `needs-intent-scoring-v1.json`, filled in against the opaque transcript
   ID.
4. **Reveal arm identity only after scoring is complete** for all 18
   transcripts. Only after every score is recorded does the reviewer (or a
   separate analyst) join the opaque-ID mapping back to (case_id, arm) to
   compute arm-level statistics.

## Reviewer count and reliability

This protocol, as written, assumes **one human reviewer**. No inter-rater
reliability statistic (e.g. Cohen's kappa) may be reported or implied
unless a second, independent reviewer is actually recruited and scores the
same 18 transcripts under this same blind protocol. If only one reviewer
is used, the final report must say so explicitly and must not present the
single reviewer's scores as if they were reliability-validated.

## Relationship to `detection_keyword_groups`

`ground_truth.json`'s `detection_keyword_groups` field (present on several
cases including some NEEDS_INTENT ones) is diagnostic/triage metadata used
by the grader's non-scoring `detection_heuristic` field only. It is never
consulted by this manual protocol, and a transcript must not be marked
`silent_no_escalation` merely for missing a keyword group it names — see
`grade_run_selftest.py`'s existing paraphrase-validation checks for the
same principle already enforced at the automated-grader layer.

## Explicitly out of scope for this protocol

This protocol does not, and must not, resolve any of the six product
ambiguities themselves. `allowed_mechanically_safe_action` in
`needs-intent-scoring-v1.json` names the one safe action (no functional
change, at most a clearly-marked textual proposal) for each case — this is
a description of what a CORRECT ESCALATION looks like, not a product
decision made on the case authors' behalf. No case's app.js is changed by
this protocol, and no case's underlying ambiguity is resolved by it.
