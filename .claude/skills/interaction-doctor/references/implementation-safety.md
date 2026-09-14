# Implementation Safety (Secondary)

This document holds two secondary concerns that support the normative
Ownership & Integrity Core (`ownership-model.md`,
`competition-and-relations.md`, `closure-contract.md`) without being part of
it. Neither concern may override correct interaction semantics, and neither
may be folded into an Interaction Closure claim.

## Generation Surface Minimization

When implementing a fix, prefer code shapes that minimize avoidable
generation-error surface — patterns that are easy for a code-generating
agent (or a human editing by hand) to get subtly wrong through repetition or
implicit structure:

- repeated manual indexes into the same collection, instead of a bound
  reference obtained once
- repeated positional arguments where a named/structured parameter would
  remove the chance of transposing two values
- duplicated identifiers (the same literal string/id typed in more than one
  place, instead of a single declared constant)
- fragile token repetition (the same magic number or string appearing
  independently in multiple call sites)
- avoidable structural ambiguity (e.g. a chained `arr[i].prop[j].prop2` where
  a destructured, layer-by-layer binding would make each step's type and
  identity explicit)

Apply this only as a tie-breaker among implementations that are already
correct per the ownership model. If the safer-surface implementation would
change interaction semantics (e.g. change *when* a Claim activates, not just
*how* the code expresses it), the ownership model wins — do not simplify
code at the cost of correctness, and do not present a semantics-preserving
refactor as required by this section when the task did not call for a
refactor.

## Secondary Interaction-Quality Checks

Interaction Doctor may note advisory, non-ownership HCI observations
alongside an audit:

- feedback visibility (does the user get a visible signal that a Claim
  activated)
- accessibility target size
- viewport occlusion (is the interactive region actually visible/reachable)
- perceived responsiveness (latency between input and visible effect)
- discoverability (can a user find the interaction at all)

These are useful, but they are **not** part of the Ownership & Integrity
Core and MUST be presented separately from it in any report
(`closure-contract.md` § output contract). Specifically:

- Do not include these checks' results inside a claimed `Closure: COMPLETE`
  status — that status is defined entirely in terms of Claims, relationships,
  and group constraints reaching a closed disposition (`SAFE` or `RESOLVED`,
  per `closure-contract.md`).
- Do not claim these checks reach "100%" coverage of anything unless you
  have separately and explicitly defined what universe they cover — the
  same denominator discipline from `closure-contract.md` applies here too,
  independently.
- If asked to run a full audit, surface these as a clearly labeled
  supplementary section, not mixed into the Ownership & Integrity findings
  list.
