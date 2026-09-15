---
name: interaction-doctor
description: >
  Audits and fixes interaction ownership and integrity defects in any
  interaction-capable codebase — not just touch/pointer web UI. Use it
  whenever input ownership is ambiguous or broken: a drag competing with
  scroll or with another drag/reorder gesture; a long-press racing a
  native context menu, text selection, or another long-press-triggered
  action on the same element; tap/double-tap/drag recognition order;
  pinch/rotate vs. pan; pointer capture never released, or a drag/rotate
  that keeps running after pointer-cancel, focus loss, device disconnect,
  or a mode switch; a modal command (CAD/3D/DAW-style: grab, axis
  constraint, tool mode) that never exits; keyboard shortcuts competing
  with a focused text field or with IME composition; a screen
  reader/switch-control activation path that doesn't exist for a
  pointer-only interaction; multiple gamepads or XR controllers whose
  inputs are indistinguishable; nested scroll containers fighting each
  other; a synthesized/compatibility event (touch→mouse→click,
  keyboard→semantic activation) being treated as an independent
  competing input instead of the same user action. Also use it when
  building a new interaction from a reference/design with no stated
  mechanism, or when asked for a full interaction/UX audit before a
  release. Works across web/DOM, React/Vue/Svelte, SwiftUI, Jetpack
  Compose, Flutter, Unity, Godot, Qt, CAD/3D tools, and other custom
  interaction runtimes — the programming language and framework are not
  the boundary of this skill; interaction/runtime semantics are.
---

# interaction-doctor

Interaction Doctor is a post-generation **Interaction Ownership & Integrity
Audit**. It does not reason in terms of gesture names ("swipe", "long
press"). It reasons in terms of **Interaction Claims** — hypotheses about how
a user action could own input resources — and the relationships between
them. Gesture names are labels for common Claim shapes, never the model
itself.

## Core principle

> Every interaction-capable scope and every relevant ownership relationship
> within the audited scope must be accounted for before the interaction can
> be certified.

Interaction Doctor MUST NOT, at any point:

- silently ignore an interaction-capable scope
- assume an ambiguous ownership priority
- certify an unexamined relationship as safe
- invent product intent
- assume existing functionality must be preserved by default
- collapse an unknown product decision into an arbitrary predefined choice
- declare success right after a code change without rebuilding and
  revalidating the affected interaction graph

## Reference map

This file is the operational entry point. Depth lives in `references/` —
read the relevant one before acting, don't re-derive it from memory:

| File | Covers |
|---|---|
| `references/ownership-model.md` | The Interaction Claim schema: source, activation expression, recognition state, claimed resources, routing, provenance, effect, state transitions, ownership lifecycle (with generalized scope/resource invalidation), and Effect Lifetime for deferred/async effects that outlive their Claim. |
| `references/competition-and-relations.md` | The six relations (COMPETES, COOPERATES, PREEMPTS, CONDITIONAL, SEQUENCES, DERIVES_FROM), the pairwise competition predicate, and Ownership Constraint Groups for N-ary (3+) arbitration. |
| `references/environment-model.md` | Environmental/native claims, capability-based environments, raw→transformed→semantic input, analog input, multi-identity input. |
| `references/intent-and-ambiguity.md` | Source-of-truth hierarchy, product-intent evidence hierarchy, the ambiguity rule, the user-question protocol, the resolution protocol. |
| `references/audit-modes.md` | Audit Scope (TARGETED/FULL) vs. Analysis Strategy (FRESH/INCREMENTAL) — orthogonal dimensions — and the recursive/fixpoint revalidation loop. |
| `references/closure-contract.md` | Disposition (SAFE/RESOLVED/CONFLICT/NEEDS_INTENT/UNMODELED) vs. verification level (STATIC/RUNTIME) as separate axes, the two closure statements, the output-report contract, what "100%" means here. |
| `references/runtime-modeling.md` | Where each Claim field lives in specific runtimes (DOM, SwiftUI, Compose, Flutter, Unity, Godot, Qt, CAD/3D, XR, a11y). |
| `references/implementation-safety.md` | Generation Surface Minimization and secondary (non-normative) HCI checks. |
| `references/index-and-tooling.md` | The `.interaction-doctor/` cache format and the LLM/deterministic-tooling division of responsibility. |
| `references/adversarial-validation.md` | The adversarial case log this architecture was validated against — read it to see why a new gesture-specific rule is almost never the right fix. |

## Execution protocol

### 1. Pick the audit scope and analysis strategy

Read `references/audit-modes.md`. These are two independent choices — do not
let one determine the other:

- **Audit scope** — what the task actually asks for: **TARGETED** (a
  specific reported problem; scope to the affected graph, don't sweep the
  whole repo) or **FULL** (cleanup, release readiness, or an explicit
  request for a complete audit; cover the whole declared universe).
- **Analysis strategy** — whether a `.interaction-doctor/` index exists for
  this project: **FRESH** (no trustworthy index — build from source) or
  **INCREMENTAL** (an index exists — use it to locate/seed the graph, but
  invalidate and rebuild anything touching changed source; the index is a
  cache, source is truth). An index existing does not narrow a `FULL`
  request, and a narrow bug report does not become `FULL` just because an
  index is available.

### 2. Identify scopes and extract Claims

Find every interaction-capable scope relevant to the chosen scope's
boundary. For each, extract Claims per `references/ownership-model.md`. Use
`references/runtime-modeling.md` to know where to look in the specific
runtime.

If a reference/design image is the only spec, a visual affordance (e.g. a
drag-handle icon) may provide evidence that *some* interaction capability
exists — it does not by itself establish the exact activation expression,
ownership priority, or complete interaction contract (exact timing, input
source, immediate vs. delayed activation, keyboard equivalence, priority
over surrounding input). Record what the affordance actually establishes —
`capability evidence: present, exact mechanism: unresolved` — and route the
unresolved mechanism through `references/intent-and-ambiguity.md` as
`NEEDS_INTENT`. Do not treat a visual affordance as license to infer a
complete mechanism; that reintroduces exactly the invented-intent failure
mode this skill exists to prevent.

### 3. Add environmental Claims

Per `references/environment-model.md`, add the platform/runtime Claims that
apply — native scroll, native context menu, IME, accessibility activation
paths, OS gestures, etc. — for every capability combination relevant to the
scope (not a single assumed device class). A scope audited without its
environmental claims cannot reach closure.

### 4. Build relationships

For every pair of Claims sharing a resource, apply the competition predicate
in `references/competition-and-relations.md` and classify: `COMPETES`,
`COOPERATES`, `PREEMPTS`, `CONDITIONAL`, `SEQUENCES`, or `DERIVES_FROM`.
Resolve provenance (`DERIVES_FROM`) before judging competition — a
compatibility/synthesized event is not an independent competitor of its
origin. **Also** check for Ownership Constraint Groups
(`references/competition-and-relations.md` § Ownership Constraint Groups) —
N-ary (3+) participant constraints that no pairwise check can see (e.g. any
two of three Claims coexist safely, but all three together violate a
capacity limit). If no such group exists for the scope, pairwise analysis
alone is sufficient; do not invent group constraints where none exist. A
relationship that fits none of the six relations, and is not a group
constraint, stays `UNMODELED` — never invent a private, one-off relation
name to force it closed (`references/competition-and-relations.md` §
canonical vocabulary discipline).

### 5. Check ownership lifecycle and effect lifetime

For every Claim that reaches `acquire`, verify a release/transfer path
exists for each baseline category (completion, cancellation, focus loss,
device loss, mode change, runtime interruption) *and* for every reachable
scope/resource invalidation condition specific to the runtime (component
unmount, target deletion, route change, permission loss, etc. — the six
baseline categories are a mandatory floor, not the entire list; see
`references/ownership-model.md` § Ownership Lifecycle). A missing path is a
`CONFLICT`, not `UNMODELED`.

Separately, for every Claim with a delayed/scheduled/asynchronous
`spawned_effects` entry (a timer, a debounce, a promise, a queued command,
an animation-completion handler), verify it carries its own
cancellation/invalidation path tied to the Claim's termination
(`references/ownership-model.md` § Effect Lifetime). A Claim can pass every
lifecycle check and still fail this one — audit both, they are not the same
check.

### 6. Resolve

Per `references/intent-and-ambiguity.md`:

- If intent is established (explicit instruction, spec, recorded decision,
  clear test, strong in-app convention, then platform convention, then
  general heuristic — in that order) — make the smallest robust fix that
  satisfies it, and nothing more.
- If intent is not established — stop that resolution path, ask using the
  user-question protocol (locatable context first, no invented option menus
  unless asked), record the decision, then continue.

### 7. Recursively revalidate

Per `references/audit-modes.md` § Recursive Revalidation:

```text
analyze → modify → rebuild affected graph → rediscover relationships →
validate → repeat
```

until the affected graph is stable. Re-check the original relationship, its
neighbors, state transitions, other capability combinations, lifecycle
termination, effect lifetime, group constraints, and any relationship the
fix itself introduced. A fix is not done because the reported symptom
disappeared — it is done when the graph reaches a fixpoint with no open item
inside its boundary.

For every item, record both its **disposition** (`SAFE` / `RESOLVED` /
`CONFLICT` / `NEEDS_INTENT` / `UNMODELED`) and its **verification level**
(`STATIC` — read the code, the logic holds; or `RUNTIME` — actually
exercised: a test run, a driven browser/simulator, an interactive check).
These are independent axes (`references/closure-contract.md`) — never call
`STATIC`-only work `RUNTIME`-verified, and never withhold a closed
disposition just because verification is only `STATIC` unless the task
explicitly required runtime verification.

### 8. Report and certify closure

Use the output contract in `references/closure-contract.md`. Certify
"Affected Interaction Closure" (TARGETED) or "Project Interaction Closure"
(FULL) only when every item inside the declared universe carries a closed
disposition (`SAFE` or `RESOLVED`) — no `CONFLICT`, `NEEDS_INTENT`, or
`UNMODELED` left inside that boundary. State the declared universe
explicitly; a closure claim with no stated denominator is not valid. Report
verification coverage (`STATIC`/`RUNTIME`/mixed) alongside closure status,
as two separate facts.

## MUST / MUST NOT summary

- MUST express every interaction as one or more Claims, never as a bare
  gesture name.
- MUST resolve provenance (`DERIVES_FROM`) before judging competition.
- MUST NOT report a `COMPETES` finding for a pair that fails the
  competition predicate (reachability, resource overlap, effect
  interference) — that manufactures conflicts that cannot occur.
- MUST check for N-ary Ownership Constraint Groups in addition to pairwise
  relationships; MUST NOT assume every integrity constraint is pairwise.
- MUST check the Ownership Lifecycle invariant (baseline categories plus any
  reachable scope/resource invalidation) for every acquired Claim, AND
  separately check Effect Lifetime for every spawned deferred/async effect —
  these are two distinct checks, not one.
- MUST ask, with locatable context, when intent evidence tiers 1–5 are all
  silent — MUST NOT guess, MUST NOT invent a binary choice menu, MUST NOT
  assume all existing capabilities must be preserved. A visual affordance is
  evidence a capability exists, never evidence of its exact mechanism.
- MUST recursively revalidate after every fix; MUST NOT declare closure
  immediately after a symptom disappears.
- MUST record disposition and verification level as two separate facts for
  every item; MUST NOT report `STATIC`-only work as `RUNTIME`-verified, and
  MUST NOT withhold a closed disposition solely for lacking runtime
  verification unless the task's declared denominator required it.
- MUST NOT invent a new relation, disposition, or construct ad hoc during an
  audit — an unmodeled relationship stays `UNMODELED` until the canonical
  vocabulary is deliberately extended (`references/competition-and-relations.md`).
- MUST NOT fold advisory HCI checks (`implementation-safety.md`) into a
  Closure claim.
- MUST NOT let Generation Surface Minimization override correct interaction
  semantics.

## What this skill does not attempt

It does not guarantee all conceivable UX quality. Per
`references/closure-contract.md` § Meaning of "100%", the guarantee is:
within the declared audit universe, every relevant Interaction Ownership &
Integrity relationship (pairwise, group, and effect-lifetime) gets an
explicit, closed disposition before closure is certified — not that every
fix is automatic, not that everything has been runtime-verified (`STATIC`
alone can close, unless the task required otherwise), and not that every
advisory HCI concern is covered.
