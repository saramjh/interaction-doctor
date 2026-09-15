# Closure Contract

Closure is a specific, checkable claim, not a vibe. This document defines two
independent axes — **disposition** and **verification level** — the two
closure statements, the required report shape, and what "100%" is allowed to
mean in this project.

## Two independent axes — do not collapse them

Earlier drafts of this contract used a single word, `VERIFIED`, for two
different things: "this ownership question has a settled answer" and "this
was exercised in a live runtime." Collapsing them let a merely self-reviewed
item silently read as if it had been runtime-tested. Keep them separate.

### Disposition — the ownership/integrity answer

```text
SAFE           — examined; no interference, broken lifecycle path, broken
                 effect-lifetime path, or group-constraint violation was
                 found. Never was a CONFLICT.
RESOLVED       — was CONFLICT or NEEDS_INTENT; has since been corrected or
                 decided, and recursively revalidated. No open issue remains.
CONFLICT       — a COMPETES relationship, a broken Ownership Lifecycle path,
                 a broken Effect Lifetime path, or a violated Ownership
                 Constraint Group policy has been detected and not yet
                 resolved.
NEEDS_INTENT   — detection is complete, but disposition requires product
                 intent that has not yet been obtained.
UNMODELED      — a relevant Claim, relationship, group constraint, or
                 effect-lifetime chain exists but has not been normalized
                 into the model yet.
```

**Closed dispositions** are `SAFE` and `RESOLVED`. Only these two count
toward closure. Never treat `UNKNOWN`, `UNEXAMINED`, `UNMODELED`, or
`AMBIGUOUS` as equivalent to a closed disposition — each blocks the relevant
closure statement until resolved.

State transitions:

- `CONFLICT` → `RESOLVED` only after correction **and** recursive
  revalidation (`audit-modes.md`).
- `NEEDS_INTENT` → `RESOLVED` only after user intent is obtained, implemented
  if the intent requires a change, and revalidated.
- An item that is examined and found to have no issue at all goes straight
  to `SAFE` — it does not pass through `CONFLICT` or `NEEDS_INTENT` first.
- `UNMODELED` never transitions directly to a closed disposition — it must
  first be normalized (becoming `SAFE`, `CONFLICT`, or `NEEDS_INTENT` on
  inspection, then proceeding as above), or explicitly declared out of the
  audit's declared universe (see § Denominator below). An `UNMODELED` item
  that does not fit the six relations, an Ownership Constraint Group, or the
  Effect Lifetime construct is never given a private, ad hoc relation name to
  force it closed — see `competition-and-relations.md` § canonical vocabulary
  discipline and `index-and-tooling.md` § Canonical vocabulary discipline.

### Verification level — the evidence behind the disposition

```text
STATIC   — the disposition rests on reading source/config and confirming the
           ownership-model logic holds. No live execution.
RUNTIME  — the disposition was additionally exercised in a live
           environment (a test run, a driven browser/simulator/device, an
           interactive check) and the exercised behavior matched the
           disposition.
```

Every disposed item carries a verification level — at minimum `STATIC`,
since even assigning `SAFE`/`CONFLICT`/etc. requires reading the relevant
source. Never report a disposition without also stating its verification
level, and never state `RUNTIME` for an item that was only read, not
exercised.

**A `STATIC`-only disposition is not a lesser or provisional disposition —
it is a complete disposition with a stated evidence level.** A Claim that has
never been runtime-tested can still legitimately reach `RESOLVED`/`SAFE` and
count toward closure, *unless* the task or project has explicitly made
runtime verification part of the declared audit universe (§ Denominator).
Do not require runtime execution merely to call the ownership/integrity
graph structurally closed when nothing asked for that.

## Affected Interaction Closure (Targeted scope)

May be declared **COMPLETE** only when:

- the affected graph (`audit-modes.md` § Targeted scope) is stable under
  recursive revalidation
- every Claim, relationship, group constraint, and relevant effect-lifetime
  chain in that graph carries a closed disposition (`SAFE` or `RESOLVED`)
- no `CONFLICT`, `NEEDS_INTENT`, or `UNMODELED` item remains **within that
  graph's boundary**
- Ownership Lifecycle checks and Effect Lifetime checks
  (`ownership-model.md` § Ownership Lifecycle, § Effect Lifetime) pass for
  every acquired Claim and every spawned effect **within that boundary** —
  the same two checks Project Interaction Closure requires, just scoped to
  the affected graph instead of the whole project

Report the achieved verification coverage (`STATIC`, `RUNTIME`, or mixed)
alongside the closure status — it does not gate COMPLETE unless runtime
verification was part of the declared universe for this task.

This closure statement says nothing about scopes outside the affected graph.
Do not imply broader coverage than was actually audited.

## Project Interaction Closure (Full scope)

May be declared **COMPLETE** only when all of the following hold:

- every relevant interaction-capable scope in the declared audit universe
  was classified into Claims
- every relevant supported environment/capability combination was evaluated
- every discovered relationship and group constraint has an explicit
  disposition, closed to `SAFE` or `RESOLVED`
- no unresolved `CONFLICT` remains
- no unresolved `NEEDS_INTENT` remains
- no `UNMODELED` interaction mechanism, group constraint, or effect-lifetime
  chain remains inside the claimed coverage
- Ownership Lifecycle checks (`ownership-model.md` § Ownership Lifecycle,
  including scope/resource invalidation) and Effect Lifetime checks
  (`ownership-model.md` § Effect Lifetime) pass for every acquired Claim and
  every spawned effect
- the final graph remains stable after another full revalidation pass

As with Affected Interaction Closure, state the achieved verification
coverage separately; it does not gate COMPLETE unless the task's declared
denominator explicitly requires runtime verification.

## The denominator problem — declare the audit universe

"100%" is meaningless without a stated denominator. Before claiming either
closure statement, state explicitly what was declared in scope: which
directories/modules/screens, which runtimes, which capability combinations,
which environments, and — since this hardening pass — whether group
constraints and effect-lifetime chains were part of the declared universe for
this audit, and whether runtime verification was required as part of it. A
claim of closure over an undeclared or implicit universe is not a valid
closure claim — restate the universe alongside the closure status.

Closing every item that was *discovered* is not the same as closing the
*denominator*. State the denominator independently of what was found —
finding zero conflicts in a universe that was never fully enumerated is not
closure, it is an unexamined universe with a lucky sample.

## Final observable output contract

A completed audit (of either scope) MUST produce a report the developer can
read without seeing private reasoning. Use this shape:

```text
Audit scope:               <targeted | full>
Analysis strategy:         <fresh | incremental>
Affected interface/scope:  <what was in the declared universe>
Environments evaluated:    <capability combinations / runtimes actually checked>
Interaction scopes examined: <count / list>
Relationships found:       <count by type — COMPETES/COOPERATES/PREEMPTS/
                             CONDITIONAL/SEQUENCES/DERIVES_FROM>
Group constraints found:   <count / list, if any N-ary constraints applied>
Conflicts:                 <list, each with its final disposition>
Intent-dependent items:    <list, each with resolution — obtained or still open>
Unmodeled items:           <list, if any remain — these block the relevant closure>
Changes made:              <what was actually edited>
Verification coverage:     <STATIC | RUNTIME | mixed — per audit-modes.md's
                             fixpoint requirement; state this honestly and
                             separately from closure status>
Closure status:            <COMPLETE (scoped as stated above) | OPEN, with
                             the specific blocking items named>
```

`Closure status` and `Verification coverage` are reported independently.
`COMPLETE` + `STATIC` is a valid, honest combination — it means every
ownership/integrity question in the declared universe has a settled answer
by source inspection, and none of it has yet been exercised live. Do not
inflate a `STATIC` result to look like `RUNTIME`, and do not withhold
`COMPLETE` just because verification is only `STATIC`, unless the task's
denominator required `RUNTIME`.

Do not require disclosure of chain-of-thought to fill this in — every field
is about externally observable evidence (what was found, what changed, what
was checked), not about how you reasoned internally.

## Meaning of "100%" in this project

Interaction Doctor does not guarantee all conceivable UX quality. The
guarantee is narrower and specific:

> Within the declared audit universe, every relevant Interaction Ownership &
> Integrity relationship (pairwise, group, and effect-lifetime) receives an
> explicit, closed disposition before closure is certified.

This means:

```text
100% ownership/integrity examination and closure
```

It explicitly does **not** mean:

```text
100% automatic fixing         (NEEDS_INTENT items require a human answer)
100% runtime-verified         (closure only requires STATIC unless the task's
                                denominator required RUNTIME — see above)
100% of all conceivable HCI quality   (see implementation-safety.md §
                                        Secondary Interaction-Quality Checks,
                                        which are advisory and separately
                                        scoped — never folded into this
                                        closure claim)
```

Ambiguous product intent is an expected, first-class part of the protocol,
not a failure of the audit:

```text
detect → explain with locatable context → ask user → record intent →
implement → revalidate → close
```

An `UNMODELED` interaction mechanism, group constraint, or effect-lifetime
chain blocks the relevant closure statement. It is never silently ignored or
waved through as "probably fine."
