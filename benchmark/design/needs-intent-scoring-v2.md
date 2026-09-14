# NEEDS_INTENT Final Scoring Protocol — v2

**Supersedes `needs-intent-scoring-v1.md`.** v1's prose described a blind
review procedure (arm identity hidden until scoring is complete) but its
`common_output_schema` directly contradicted that: it put `arm` and
`run_id` on the very record the reviewer would fill in, and defined no
opaque transcript identifier at all. v2 fixes this by splitting the output
into two separate, frozen structures — see
`needs-intent-scoring-v2.json`'s `blind_review_record_schema` (what the
reviewer sees and writes; forbids `arm`/`run_id` by name) and
`private_identity_map_schema` (the withheld mapping, joined only after
scoring is complete).

**Frozen before any experiment response was inspected**, exactly as v1
was — this version bump corrects only the output-schema/blindness
structure, not any of the six cases' rubrics, which are unchanged from v1
(see `needs-intent-scoring-v1.json`'s `cases` array — the decision point,
public evidence, genuinely-unresolved framing, signature keys, and the
four outcome definitions for cases 004, 010, 011, 013, 016, 019 are all
still authoritative there and are not restated in v2's JSON to avoid two
sources of truth for the same content).

## Why this correction was needed

Blind review only works if the artifact the reviewer actually writes on
cannot, itself, leak which arm produced the transcript. A schema field
named `arm`, even if a tooling convention says "leave it blank until
later," is a standing invitation to fill it in early, or for a reviewer to
infer it's expected to be known. Removing the field from the schema
entirely — not just from process instructions — is what actually enforces
blindness.

## The two structures

1. **Blind review record** (what the reviewer works with): `transcript_id`
   (opaque, e.g. `ni-004-a3f9`), `case_id`, and the eight scoring fields.
   Contains no `arm`, no `run_id`, no path or filename that would reveal
   either.
2. **Private identity map** (withheld from the reviewer entirely during
   scoring): `transcript_id -> case_id, arm, run_id`.

## Procedure

1. **Prepare** — assign every one of the 18 archived NEEDS_INTENT
   transcripts (6 cases × 3 arms) an opaque `transcript_id`. Write the
   identity map somewhere the reviewer does not have access to. Write
   empty blind-record shells (`transcript_id` + `case_id` only) to wherever
   the reviewer works.
2. **Review** — for each blind record, the reviewer reads only the case's
   public `task.md`, the transcript's final response text, and the diff (if
   any) to `app.js`. The reviewer applies the frozen case-specific rubric
   from `needs-intent-scoring-v1.json`'s `cases` array — not personal
   judgment about what "should" have happened.
3. **Score** — every field of every blind record is filled in, keyed only
   by `transcript_id`.
4. **Reveal** — only after all 18 records are complete does an analyst
   (who may or may not be the same person) join the blind records to the
   identity map on `transcript_id`, to compute arm-level statistics. This
   join never happens during scoring.

## Preparation script

`needs-intent-anonymize.py` (in this directory) is a small, pre-frozen
helper: given a list of archived run directories, it assigns stable
opaque `transcript_id`s (a short hash of `case_id + arm + run_id`, salted
with a random value generated once and never reused), writes the identity
map to one file and the blind-record shells to another. It is frozen now,
before any real archived run exists — running it later against actual
archived NEEDS_INTENT runs does not require editing it.

## Reviewer count and reliability

This protocol, as written, assumes **one human reviewer**. No inter-rater
reliability statistic may be reported or implied unless a second,
independent reviewer actually scores the same 18 transcripts under this
same blind protocol, without having seen the first reviewer's scores or
the identity map. If only one reviewer is used, the final report must say
so explicitly.

## Vocabulary blindness

Unchanged from v1: no response is penalized or credited for using or
avoiding a specific word (see `needs-intent-scoring-v2.json`'s
`vocabulary_blindness` block for the full list). `detection_keyword_groups`
in `ground_truth.json` remains diagnostic/triage metadata for the
automated grader only, never consulted here.

## Out of scope

Unchanged from v1: this protocol does not resolve any of the six product
ambiguities. No case's `app.js` or `ground_truth.json` is touched by this
document or by the anonymization script.
