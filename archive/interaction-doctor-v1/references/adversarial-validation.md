# Adversarial Validation Log

This document is the record required before this architecture could be
considered finished: every listed case was checked against the model in
`ownership-model.md`, `competition-and-relations.md`, `environment-model.md`,
and `closure-contract.md`, asking "does the existing general model already
express this, or does the model need a new special-case rule?" The goal was
never to accumulate examples — it was to verify that examples reduce to the
general model. Where a case reduces cleanly, no new rule was added. No case
below required a gesture-specific patch to the model; each is resolved by
naming which existing mechanism applies — the pairwise competition
predicate, an Ownership Constraint Group, the Ownership Lifecycle invariant,
or the Effect Lifetime invariant.

This document was extended once, in a later spec-hardening pass, to add
Ownership Constraint Groups (N-ary arbitration), Effect Lifetime (deferred/
async escape), generalized scope/resource invalidation, and the Audit
Scope/Analysis Strategy split. § Re-validation note below records that the
pre-existing cases were re-checked against those additions and needed no
changes.

Format per case: **Case** — **Reduction** (which mechanism in the model
already covers it).

## Basic UI

- **Click/tap** — A single Claim: `activation: PointerDown then PointerUp
  within the same target, no intervening cancel`. No special model needed;
  it is the simplest possible activation expression.
- **Hover** — A Claim with `effect: observe` only and `claimed_resources:
  []` (or a hover/locality-domain resource if it changes visual state). Per
  the competition predicate, an effect-only-observe Claim never competes
  with anything — this is why hover-triggered tooltips coexisting with drag
  is not a special case, it's `ownership_interference() == false`.
- **Focus** — `claimed_resources: [focus domain]`, routing via focus
  routing (not hit-test) per `environment-model.md`. Focus-dependent
  keyboard Claims are naturally `CONDITIONAL` on which scope currently holds
  the focus resource.
- **Nested scrolling** — Each scrollable ancestor is a Claim on `scroll
  ownership` for its own axis; the reachable-intersection + resource-overlap
  test in the competition predicate is exactly the mechanism that decides
  whether a vertical list inside a horizontal carousel produces a real
  `COMPETES` (same axis, both reachable) or a harmless `COOPERATES`
  (orthogonal axes, `CONDITIONAL` on which axis the gesture's initial
  direction locks to).
- **Drag vs. scroll** — The canonical `COMPETES` example in
  `competition-and-relations.md`: same resource (`pointer.movement`),
  reachable jointly, interfering effects (reposition vs. scroll). Resolved
  via `intent-and-ambiguity.md`, not invented rules.
- **Long-press vs. native behavior** — The native behavior (context menu,
  callout, text selection) is an environmental Claim
  (`environment-model.md` § 1). The custom long-press Claim's `effect`
  includes `suppress: <the native claim>` — an ordinary `PREEMPTS` edge
  against an environmental Claim, not a new relation type.
- **Global keyboard shortcuts** — `claimed_resources: [keyboard key/chord]`
  at a scope broader than any single focused widget; a focused text field's
  own key handling is `CONDITIONAL` against it (mutually exclusive on
  "is a text field focused"), unless both are reachable together, in which
  case it is a genuine `COMPETES` requiring a disposition — exactly the
  IME-vs-submit case in `environment-model.md` § 3.
- **Text editing** — Selection and caret are `claimed_resources` like any
  other; multiple Claims writing to the same caret (e.g. autocomplete
  insertion racing user typing) is `COMPETES` on the text-editing resource.

## Complex gestures

- **Single/double-tap recognition** — Direct instance of Recognition State
  (`ownership-model.md` § Recognition State): the single-tap Claim
  `waitsForFailureOf` the double-tap Claim's window; double-tap
  `promotesAfter` a second tap within the window. No special "double tap"
  concept is needed beyond the generic recognizer-dependency vocabulary.
- **Drag promotion / long-press promotion** — Both are `promotesAfter`
  transitions from `possible`/`began` to `active` once a threshold
  (distance or hold-time) is crossed. Same mechanism, different threshold
  variable — not two different model features.
- **Pinch/rotate** — Activation expression over pointer cardinality (two
  pointers) and a derived continuous signal (inter-pointer distance/angle
  delta) — an instance of § Analog and continuous input applied to a
  computed value rather than a raw device axis. `claimed_resources` are
  scale and rotation, which can be independently claimed (`COOPERATES`)
  from an unrelated single-pointer pan Claim on translation, exactly like
  the CAD per-axis example in `runtime-modeling.md`.
- **Pointer capture** — A routing mechanism (`ownership-model.md` §
  Routing) that overrides hit-test routing for the capturing Claim; release
  of capture is a lifecycle `release` transition. A Claim that captures a
  pointer and never releases it on `pointercancel` is a direct violation of
  the Ownership Lifecycle invariant (device/runtime-interruption
  termination path missing) — already covered, not a new case.
- **Pointer cancellation** — `pointercancel` (or a runtime's equivalent) is
  a Recognition State transition to `cancelled` and a required lifecycle
  `release` trigger. A Claim without a `cancelled`-triggered release is a
  `CONFLICT` under the lifecycle invariant.
- **Nested recognizers** — Modeled as a graph of `waitsForFailureOf` /
  `simultaneousWith` / `preemptsAfterRecognition` edges among Claims sharing
  overlapping resources — arbitrarily deep nesting is just a longer chain of
  the same edges, not a new structure.

## Complex desktop applications

- **CAD / 3D modeling modal commands** — Explicit State Transition
  (`ownership-model.md` § State Transition): GRAB/ROTATE/SCALE modes with
  per-axis constraints are literally the worked example in that section.
- **Key + mouse chords** — Ordinary Activation Expression AND-combination
  (`Shift AND MiddleMouseDown AND Move`), same as the Orbit/Pan
  `CONDITIONAL` example in `competition-and-relations.md`.
- **Simultaneous translation/rotation** — Disjoint `claimed_resources`
  slices of one composite resource (transform), `COOPERATES` — same
  mechanism as `W + mouse-look` in the flight-navigation example.
- **Focus-dependent shortcuts** — `CONDITIONAL` on the focus resource, as
  in Basic UI § Focus above; a desktop app's many focus-scoped shortcut
  tables are the same mechanism repeated per scope, not a new mechanism per
  table.

## Games

- **Keyboard + mouse simultaneous control** — `COOPERATES` via disjoint
  resource slices (movement axes from keyboard, look axes from mouse),
  identical mechanism to the CAD/flight example.
- **Multiple gamepads** — Requires device-*instance* qualified resources
  (`environment-model.md` § Multiple Input Identities): `Gamepad[0].A` and
  `Gamepad[1].A` are different resources despite the same class/button
  name, so `resource_overlap()` correctly reports no overlap between two
  players' identical inputs.
- **Analog axes** — § Analog and continuous input: activation as a
  numeric-range/threshold/dead-zone/hysteresis predicate over a continuous
  signal, not a boolean event.
- **Local multiplayer** — Same device-instance-qualified resource
  requirement as multiple gamepads, generalized to "actor" as a Source
  field (`ownership-model.md` § Source).
- **Polling-based input** — Routing mechanism variant (`ownership-model.md`
  § Routing: "polling"); Recognition State still applies, it is simply
  evaluated once per frame against polled device state instead of per
  dispatched event. The state machine itself is unchanged by the delivery
  mechanism.

## Text / input systems

- **Korean/Japanese/Chinese IME, composition** — The raw→transformed→
  semantic pipeline (`environment-model.md` § 3) with an explicit
  `DERIVES_FROM` chain (`keydown → composition update → composition end →
  text input`); the composition-vs-submit conflict is an ordinary
  `COMPETES` requiring a composition-state check as its resolution.
- **Speech** — A `source.kind: semantic/synthesized` Claim with no physical
  pointer/key event at all — covered by § Source's semantic/synthesized
  input category directly.
- **Handwriting** — Same as speech: digitizer/handwriting-recognition
  output is transformed input feeding a semantic Claim, per the same
  pipeline as IME.

## Accessibility

- **Semantic activation** — Covered directly by § Source (semantic/
  synthesized input) and reinforced in `runtime-modeling.md` § Accessibility:
  any Claim whose only Source is a raw pointer/key event and which has no
  semantic-activation counterpart is a first-class audit finding, not an
  optional add-on.
- **Simulated keyboard activation** (e.g. a screen reader dispatching a
  synthetic `Enter`) — Modeled as `DERIVES_FROM`: `screen-reader activation
  → synthesized key event → semantic command`. Same provenance mechanism as
  touch→mouse compatibility events, not a separate concept for
  accessibility specifically.
- **Screen-reader / switch-control style interaction** — Switch scanning
  (a single switch cycling focus, then activating) is a sequence of
  `SEQUENCES`-related Claims (each scan step establishes the context the
  next activation depends on) over the focus resource — no new relation
  type required.

## Specialized hardware

- **MIDI** — `source.kind: physical, device: MIDI`; control values are
  continuous input per § Analog and continuous input; `claimed_resources`
  are whatever semantic/game parameters the MIDI CC is bound to.
- **Raw HID** — Same as MIDI: an unlisted device class is added to Source
  and reasoned about with the same schema; the model does not enumerate
  every possible device, it enumerates the *fields* a device's Claims fill.
- **Pen pressure/tilt** — Continuous signals exactly like joystick axes;
  pressure crossing a threshold is a `promotesAfter` transition (e.g. light
  touch = hover Claim, pressure past threshold = draw Claim) — same
  recognizer-promotion mechanism as long-press promotion.
- **SpaceMouse** — Multiple simultaneous continuous axes (6 degrees of
  freedom) claimed as disjoint transform-dimension resources —
  `COOPERATES`, same mechanism as the CAD per-axis example.

## XR

- **Gaze** — A continuous pose signal (§ Analog input) used for ray
  routing (`environment-model.md`/`runtime-modeling.md` § XR); "dwell to
  select" is a `promotesAfter(hold duration)` transition, same mechanism as
  long-press promotion.
- **Pose** — Continuous signal; a "grab" Claim's activation is `pose within
  volume AND trigger past threshold` — an AND-combination of a continuous
  spatial predicate and a continuous button predicate, both already
  supported by § Activation Expression.
- **Hand tracking** — Same as pose, with the device producing semantically
  richer continuous data (per-joint positions); still reduces to continuous
  Source data feeding an Activation Expression.
- **Two controllers, multi-source interaction** — Two independently
  device-instance-qualified ray-routed Claims targeting the same
  interactable is exactly the multi-gamepad reduction: `resource_overlap()`
  correctly reports overlap only if the *same* interactable's resource is
  claimed by both, and the disposition (which controller wins, or whether
  both cooperate for two-handed manipulation) is an ordinary
  `COMPETES`/`COOPERATES` classification.

## Lifecycle failures

Every case in this category reduces to the same single mechanism: the
Ownership Lifecycle invariant (`ownership-model.md` § Ownership Lifecycle) —
"every acquired ownership needs a valid termination or transfer path for
every reachable condition under which the owner, target, resource,
activation context, or supporting runtime state ceases to be valid," with
completion/cancellation/focus-loss/device-loss/mode-change/runtime-
interruption as the mandatory baseline categories and scope/resource
invalidation as the open category for everything else. Naming which
condition is missing is the entire diagnosis; no per-case special rule is
needed:

- **Focus loss** — missing `focus-loss → release` transition.
- **Pointer cancel** — missing `cancelled → release` transition (see
  Complex gestures § Pointer cancellation above).
- **Device disconnect** — missing `device-loss → release` transition.
- **Stuck key** (a key-down Claim with no matching key-up because the key-up
  event was lost, e.g. focus moved to another window while held) — this is
  simultaneously a focus-loss lifecycle gap and, at the routing level, an
  argument for treating "window/view lost focus while a key is physically
  down" as an implicit synthetic key-up source the Claim must also listen
  for.
- **Unreleased capture** — missing `runtime-interruption → release`
  transition on a Claim holding pointer/input capture (see Complex gestures
  § Pointer capture above).
- **Modal state never exiting** — a State Transition (§ State Transition)
  with no edge back to a non-modal state under some reachable condition;
  diagnosed the same way any missing lifecycle edge is diagnosed, just
  applied to a state-machine transition instead of a flat Claim's
  acquire/release pair.
- **Component unmount / target deletion / route change** (not one of the six
  named baseline conditions) — an instance of the generic scope/resource
  invalidation category (`ownership-model.md` § Ownership Lifecycle), added
  in this hardening pass precisely because runtimes keep producing
  invalidation events that don't fit any of the six original labels. See §
  Generalized Lifecycle Invalidation below for a worked case; the diagnosis
  is identical in shape to the six baseline cases — name the missing
  release/transfer path — only the triggering condition differs.

## Event provenance

- **Touch → pointer → mouse compatibility events** — The canonical
  `DERIVES_FROM` chain (`ownership-model.md` § Provenance); a Claim on the
  compatibility `click` must never be evaluated as independent of the
  originating `pointerdown`.
- **Keyboard → semantic activation → synthesized click** — Same mechanism,
  different origin: `Enter/Space on a focused control → semantic activation
  → synthesized click`. Treating this identically to the touch chain is
  precisely why accessibility activation does not need a separate
  provenance concept.

## Ownership Constraint Groups (N-ary)

**Case — pairwise-safe, triple-invalid ownership.** A shared whiteboard
object supports manipulation by up to two simultaneous pointers (two-handed
resize, or two collaborators dragging opposite corners), but a third
simultaneous manipulator produces an undefined transform. Checking pairs
alone cannot find this: `PointerA + PointerB` is valid, `PointerA +
PointerC` is valid, `PointerB + PointerC` is valid — every pairwise
competition-predicate check passes. Only the three-way combination is
invalid.

**Reduction.** This is exactly the shape `competition-and-relations.md` §
Ownership Constraint Groups exists for: `participants: [PointerA, PointerB,
PointerC]`, `resources: [object.transform]`, `policy: capacity(2)`. The
group construct is checked as its own unit, not derived from the pairwise
graph — the pairwise graph correctly reports no conflict, and the group
constraint correctly reports one. No pairwise-only model can represent this;
no gesture-specific rule was needed either — the group construct is generic
across device classes (this works identically for three touch pointers,
three XR controllers, or two touch pointers plus one stylus).

**Same reduction, different domain.** A native gesture arena that admits at
most one winning recognizer among N registered recognizers
(`runtime-modeling.md` § Flutter) is `participants: [all registered
recognizers in this arena]`, `policy: exclusive` — the N=2 case degenerates
to ordinary pairwise `COMPETES`, confirming pairwise competition is the
`participants=[A,B], capacity(1)` special case of this construct, not a
separate mechanism.

## Effect Lifetime and Deferred Escape

**Case 1 — cancelled long-press timer fires anyway.**

```text
long press begins → timer created → pointer cancelled → ownership released
→ timer fires later → context menu opens anyway
```

*Reduction.* The Ownership Lifecycle check alone would report this Claim as
fine — it released cleanly on `pointercancel`. The defect is in the timer, a
`spawned_effects` entry causally `DERIVES_FROM` the Claim, which was never
given a cancellation path tied to the Claim's own `cancel`/`release`
transition. This is precisely why Effect Lifetime (`ownership-model.md` §
Effect Lifetime) is audited as a distinct check from Ownership Lifecycle,
not folded into it — a Claim can pass one and fail the other.

**Case 2 — stale async response mutates a removed/replaced scope.**

```text
interaction active → target removed/replaced/unmounted →
ownership/effect remains active → async completion mutates the
obsolete target
```

*Reduction.* Same Effect Lifetime invariant: the async completion is a child
effect whose validity condition (does my target still exist / is it still
the current one) was never checked before it mutated state. See §
Generalized Lifecycle Invalidation below for the companion case where the
*ownership itself* (not a spawned effect) fails to release on target
removal — the two are related but distinct failure points, and both are
worth checking independently for the same Claim.

**Case 3 — animation/snap completion fires after a mode change.**

A drag-to-position interaction ends by kicking off a snap/settle animation
(`spawned_effects: [snap-animation]`). Before the animation completes, the
application switches modes (e.g. from "edit" to "view"). The animation's
completion handler still fires and applies its final position write,
clobbering whatever the new mode set up.

*Reduction.* Same invariant again: the animation-completion handler is a
deferred effect that needs a validity check against current mode/generation
before applying its mutation, exactly like the async-response case. Three
superficially different domains (a timer, a network response, an animation
callback) all reduce to the one Effect Lifetime invariant — confirming it
generalizes rather than needing a per-effect-type rule.

## Generalized Lifecycle Invalidation

**Case — target invalidation without a spawned effect.** An interaction is
actively dragging a list item (ownership acquired, no timers or async work
involved at all). The list item is removed from the underlying data source
mid-drag (e.g. a real-time sync deletes it). The drag Claim has no
`pointercancel`, no focus loss, no device loss, no mode change, and no
runtime interruption — none of the six baseline categories fired — yet its
target no longer exists, and the Claim's ownership remains formally
"active," capable of continuing to mutate a now-nonexistent target.

*Reduction.* This is the scope/resource invalidation category
(`ownership-model.md` § Ownership Lifecycle), added specifically because the
six baseline categories, while mandatory, are not exhaustive. "Target
deletion" is one of the explicitly enumerated instances of that category.
The fix is the same shape as any lifecycle fix — add a release/transfer path
triggered by the invalidation condition — the only novelty is that the
triggering condition (a remote deletion) is not one of the six original
labels. No new invariant was needed, only the explicit acknowledgment that
the six labels were a floor, not a ceiling.

## Async Stale-Generation Result

**Case.** A Claim starts async work under generation/epoch `A` (e.g. a
search-as-you-type Claim fires a network request for the query at that
moment). Before the response returns, the relevant state advances to
generation `B` (the user typed more, changing the query). The generation-`A`
response arrives and, without a generation check, overwrites generation-`B`
state with stale results.

*Reduction.* Same Effect Lifetime invariant as Case 2 above, with the
validity condition made concrete: the spawned effect (the network response)
captures the generation it was spawned under and must compare it to the
current generation before mutating anything. This is the general,
runtime-agnostic form of what React keys, request-cancellation tokens, and
"ignore stale responses" patterns all implement ad hoc per-framework — the
model needed no framework-specific rule, only the generation/epoch concept
already named in `ownership-model.md` § Effect Lifetime.

## Audit Scope × Analysis Strategy

**Case — indexed project, narrow bug report.** A project has a full
`.interaction-doctor/` index from a previous full audit. The user reports
one specific broken interaction.

*Reduction.* Audit Scope is `TARGETED` — set by the user's task, not by the
index's existence. Analysis Strategy is `INCREMENTAL` — set by the index's
existence, not by the task's narrowness. The two combine as `TARGETED +
INCREMENTAL` (`audit-modes.md`): the index is consulted only to locate the
affected graph neighborhood faster; the neighborhood is still verified
against current source, and closure is still only claimed over the affected
graph, not the whole project. Confirms the two dimensions do not collapse
into each other even when both are present at once.

**Case — indexed project, full release audit.** The same indexed project
instead receives a request for a complete pre-release interaction audit.

*Reduction.* Audit Scope is `FULL` (the task asks for complete coverage).
Analysis Strategy is `INCREMENTAL` (the index exists and is reused as an
optimization). The combination is `FULL + INCREMENTAL`: every index entry is
consistency-checked against current source (per `audit-modes.md`, `FULL`
scope's closure bar is not weakened by reusing a cache), and Project
Interaction Closure is only certified once that full check-and-rebuild pass
is complete. Confirms `FULL` scope's exhaustiveness requirement survives the
presence of an optimization strategy — the index makes the audit faster, not
shallower.

## Re-validation note (v1 hardening pass)

All cases in the sections above this one (Basic UI through Event
provenance) were re-checked against the four constructs added in this
hardening pass — Ownership Constraint Groups, Effect Lifetime, generalized
scope/resource invalidation, and the Audit Scope/Analysis Strategy split —
and none required modification:

- Pairwise cases (drag vs. scroll, orbit vs. pan, etc.) are unaffected
  because they are the `participants=[A,B], capacity(1)` special case of the
  group construct, which is definitionally identical to the prior pairwise
  predicate.
- The pinch/rotate case (two pointers) generalizes cleanly to N-finger
  gestures via pointer cardinality in the activation expression, as already
  noted there; where an interactable's *capacity* (not just its activation
  predicate) is limited across many simultaneous manipulators, that is now
  explicitly an Ownership Constraint Group rather than an unstated
  assumption.
- The XR two-controller case and the local-multiplayer/multiple-gamepad
  cases are now formally instances of Ownership Constraint Groups
  (`capacity(2)` or `exclusive` policies) rather than informal appeals to
  "the multi-gamepad reduction" — the informal reduction and the formal
  construct agree.
- The lifecycle-failure cases (focus loss, pointer cancel, device
  disconnect, stuck key, unreleased capture, modal state never exiting) are
  unaffected because they are all instances of the *baseline* categories,
  which this pass explicitly preserved as a mandatory floor rather than
  replacing.
- No previously-`SAFE`/`RESOLVED` case became `CONFLICT` or `UNMODELED`
  under the revised model, and no case required a new gesture- or
  framework-specific rule — the four additions are genuine generalizations
  of the existing mechanisms, not patches bolted alongside them.

## Outcome

No case in this document required extending the model with a gesture- or
framework-specific rule. Every case resolved to one of: an Activation
Expression combination, a Recognition State/recognizer-dependency edge, a
claimed-resource overlap/disjointness judgment, a Routing mechanism, a
`DERIVES_FROM` provenance edge, a State Transition, the Ownership Lifecycle
invariant (baseline or scope/resource-invalidation category), the Effect
Lifetime invariant, or an Ownership Constraint Group. This is the intended
shape of coverage: breadth of examples reducing to a small, fixed set of
mechanisms, not a growing list of recipes.

If a future case is found that genuinely does not reduce to one of these
mechanisms, that is a signal to extend `ownership-model.md` or
`competition-and-relations.md` itself, deliberately and canonically (see §
canonical vocabulary discipline in `competition-and-relations.md`), and
re-run this log against the extended model — not to add a special case here
or in `SKILL.md`, and not to record a one-off relation name in a single
project's local index.

## Final freeze self-review (v1)

Performed adversarially, as if reviewing someone else's work, against eight
attack vectors:

| Attack | Representable? | Classifiable? | Can an open state block closure? | Avoids guessing intent? | Fits the shared IR? |
|---|---|---|---|---|---|
| Three-way conflict, no pairwise conflict | Yes — Ownership Constraint Group | Yes — `CONFLICT` until a policy is declared | Yes — `UNMODELED`/`CONFLICT` until modeled | Yes — policy choice routes through intent evidence like any disposition | Yes — group schema is part of the shared Claim/relation IR |
| Delayed action fires after cancellation | Yes — Effect Lifetime | Yes — `CONFLICT` on missing invalidation path | Yes | Yes — no intent question here, it's a correctness invariant | Yes — `spawned_effects` field is in the shared schema |
| Interaction target ceases to exist | Yes — scope/resource invalidation | Yes | Yes | Yes | Yes |
| Owner unchanged, resource identity changes (e.g. resource swapped for a new instance) | Yes — an instance of scope/resource invalidation ("resource replacement") | Yes | Yes | Yes | Yes |
| Stale async result | Yes — Effect Lifetime, generation/epoch validity | Yes | Yes | Yes — generation mismatch is mechanical, not a product-intent question | Yes |
| Static-only validation, no runtime test | Yes — verification level `STATIC` | Yes — closes as `SAFE`/`RESOLVED` at `STATIC` | No, correctly — `STATIC` alone does not block closure unless the task's denominator required `RUNTIME` | Yes — orthogonal concern | Yes — verification level is a first-class, separate field |
| Indexed project, targeted request | Yes — `TARGETED + INCREMENTAL` | Yes | Yes, scoped to the affected graph | Yes | Yes |
| Indexed project, full audit | Yes — `FULL + INCREMENTAL` | Yes | Yes, scoped to the full declared universe | Yes | Yes |
| A genuinely new relation not in the current vocabulary | Yes — stays `UNMODELED` | Yes — `UNMODELED` is itself a valid classification | Yes — blocks closure until the Core is deliberately extended | Yes — extension is a modeling decision, not a product-intent guess | Yes, once formally added; correctly *not* representable as a private ad hoc type before that |

Every row answers all five columns affirmatively (or, for the `STATIC`-only
row, correctly in the negative on the "blocks closure" column — that "no" is
the intended, hardened behavior, not a gap). No row required a further model
change.
