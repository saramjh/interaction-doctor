# The Interaction Claim Model

This document defines the universal unit of analysis for Interaction Doctor: the
**Interaction Claim**. Everything the audit reasons about — a tap, a CAD modal
command, a gamepad axis, a screen-reader activation, an IME composition step —
is expressed as one or more Claims. Gesture names ("long press", "swipe") are
never the model; they are labels humans use for common Claim shapes. Do not
special-case a gesture name anywhere in the audit logic — reduce it to a Claim.

A Claim is a hypothesis about how one user action could take ownership of one
or more resources in the interface. Claims are extracted from source code
(implementation truth) and from environment knowledge (§ see
`environment-model.md`). A Claim is not asserted to be correct or safe by the
mere act of extracting it — that judgment happens in
`competition-and-relations.md` and `intent-and-ambiguity.md`.

## Minimal schema

Every Claim SHOULD be describable with these fields. Not all fields apply to
every Claim — omit what is genuinely absent, but do not skip a field because
it is inconvenient to determine.

```yaml
claim_id: <stable identifier scoped to the audit>
scope: <the interaction-capable scope this claim is attached to — a DOM node,
        a SwiftUI view, a Compose composable, an ECS entity, a CAD tool mode, ...>
source: {...}              # § Source
activation: <expression>   # § Activation Expression
recognition: {...}         # § Recognition State
claimed_resources: [...]   # § Claimed Resources
routing: {...}             # § Routing
provenance: <DERIVES_FROM chain, or "independent">   # § Provenance
effect: [...]              # § Effect
state_machine: {...}       # § State Transition (optional — only for modal claims)
lifecycle: {...}           # § Ownership Lifecycle
spawned_effects: [...]     # § Effect Lifetime (optional — timers, async work, deferred
                            # callbacks this claim causes, which may outlive it)
```

Treat this as a checklist when extracting a Claim from code, not as a literal
file format you must produce for every claim in every audit — see
`closure-contract.md` for what the audit is actually required to record.

---

## Source

What produces the raw signal the Claim activates on.

- **Physical input**: mouse, touch, pen/stylus, keyboard, trackpad, gamepad,
  MIDI/HID device, SpaceMouse, XR controller, articulated hand, gaze tracker,
  microphone (speech), digitizer (handwriting).
- **Transformed input**: input that has passed through a runtime
  transformation before the Claim sees it (IME composition output, gesture
  recognizer output, dead-zone-applied analog value). See
  `environment-model.md` for the raw→transformed→semantic pipeline.
- **Semantic/synthesized input**: input with no corresponding physical event
  at all — an accessibility activation (`role=button` invoked by a
  screen reader), a scripted/programmatic dispatch, a synthesized compatibility
  event.
- **Device class vs. device instance**: "a gamepad" is a class; "the gamepad
  at index 1" is an instance. A Claim that says "Button A" without specifying
  which device instance is under-specified — see § Multiple Input Identities
  in `environment-model.md`.
- **Actor/player**: in multi-actor contexts (local multiplayer, multi-user
  whiteboards, multiple simultaneous touches treated as independent actors),
  record which actor owns the source.

Record source at the most specific level the code actually distinguishes. If
the code cannot tell two device instances apart, that is itself a finding
(see `competition-and-relations.md` on resource overlap).

---

## Activation Expression

An Activation Expression is an arbitrary logical/temporal predicate over the
input stream and current state — never assume one Claim corresponds to one
event.

Support, conceptually:

- Boolean combination: AND, OR, NOT
- Modifier combinations (Shift, Ctrl, secondary button, etc.)
- Sequences ("A then B within window")
- Timing constraints and hold durations
- Movement thresholds (distance, velocity)
- State predicates and mode predicates (`Mode == GRAB`)
- Numeric ranges over continuous signals (§ `environment-model.md` § Analog input)
- Pointer cardinality (single pointer vs. two-finger vs. N-finger)
- Pointer/device identity constraints (`Gamepad[0]` vs `Gamepad[1]`)
- Grouping/binding of multiple simultaneous inputs into one logical activation

Examples:

```text
Shift AND MiddleMouseDown AND PointerDelta != 0 AND ViewportHovered
```

```text
Mode == GRAB AND PointerMove AND AxisConstraint == X
```

An activation expression is evaluated against a *reachable* input/state space,
not against a single anecdotal trace — this matters for the competition
predicate in `competition-and-relations.md`.

---

## Recognition State

Many Claims are provisional before they are confirmed. Model at least these
states:

```
possible → began → active → ended
possible → failed
active   → cancelled
```

Also model **recognizer dependencies** between Claims, since this is where
most real defects live:

- `waitsForFailureOf(other)` — this Claim cannot become `active` until
  `other` reaches `failed`.
- `simultaneousWith(other)` — both Claims may be `active` at once without
  either failing the other.
- `promotesAfter(condition)` — a Claim moves from `possible`/`began` to
  `active` once a threshold is crossed (distance, time, pressure).
- `preemptsAfterRecognition(other)` — once this Claim reaches `active`, it
  forces `other` from `possible`/`began` to `cancelled`.

This state machine is required to model tap vs. double-tap vs. long-press vs.
drag recognition, and to model native platform gesture recognizers (UIKit
`UIGestureRecognizer`, Android `GestureDetector`, Compose `PointerInputScope`,
web `PointerEvent` + custom recognizers) uniformly, without hand-writing a
special case per platform.

---

## Claimed Resources

What the Claim owns or affects while active. Resources may be claimed
**partially** — this is the mechanism that separates true competition from
harmless overlap (see `competition-and-relations.md`).

Resource categories (non-exhaustive — extend when a runtime exposes something
not listed here, and record the extension):

- pointer device / pointer identity / pointer button
- an axis or sub-dimension of a resource (e.g. `translation.X` but not `.Y`/`.Z`)
- pointer movement (raw delta stream)
- wheel/scroll channel
- keyboard key or chord
- focus domain
- hover/locality domain
- spatial region / hit-test area
- scroll ownership (which ancestor, in a nested-scroll chain, is scrolling)
- text editing / caret / selection
- gesture recognizer slot (a platform may allow only one recognizer per
  region to be "the" active one)
- semantic command (a named action, independent of the input that invoked it)
- game input axis
- a 3D transform dimension (translation/rotation/scale, per-axis)
- application mode (global modal state)
- other runtime-specific resources — record them explicitly rather than
  forcing them into this list

**Partial-overlap example (cooperation, not competition):**

```text
W            → translation.Z
Mouse XY     → yaw / pitch
```

Two Claims, two disjoint resource slices, one composite user action (fly
navigation). This is `COOPERATES`, not `COMPETES` — see
`competition-and-relations.md`.

---

## Routing

How the raw signal reaches this Claim at all. Do not assume DOM-style
capture/bubble — every runtime routes differently, and the audit must record
which mechanism actually applies:

- hit testing / hierarchy propagation
- capture / target / bubble phases
- pointer capture (`setPointerCapture` or the platform's equivalent)
- focus routing (keyboard/semantic events go to the focused element, not the
  hit-tested one)
- semantic dispatch (accessibility tree activation)
- polling (games routinely poll device state once per frame instead of
  receiving events)
- native/system input brokers (OS-level gesture recognizers that sit above
  the app, e.g. edge-swipe-back)
- UI raycasting / 3D ray-collider targeting (game engines, XR)
- relative pointer / pointer-lock mode (FPS-style camera control)
- modal dispatch (an open modal/dialog/mode intercepts all routing)
- custom runtime routing (engine-specific input managers)

Record routing per Claim. Two Claims that look like they compete for the same
element may in fact never both receive the input, because routing sends the
event to only one of them (e.g. capture phase) — that is `CONDITIONAL` or
non-competing, not `COMPETES`.

---

## Provenance (causal lineage)

Multiple software-level events can originate from a single physical or
semantic user action. Model this with a `DERIVES_FROM` edge, always pointing
from the derived event to its origin:

```text
physical touch → pointer event → compatibility mouse event → click
```

```text
keyboard activation (Enter/Space on a focused control)
  → semantic button activation
  → click
```

```text
IME: keydown → composition update → composition end → text input
```

A Claim built on a *derived* event must never be treated as an independent
competitor of a Claim built on its *origin* event — see `DERIVES_FROM` in
`competition-and-relations.md`. Failing to track provenance is the single
most common source of false "conflicts" the audit could otherwise report
(double-counting one user action as two).

---

## Effect

What the Claim does once active. A Claim may:

observe · mutate · consume · suppress · capture · redirect · delay ·
transform · activate another Claim/state · terminate another Claim

Two Claims reading the same raw input stream are **not** automatically
competitors — competition requires overlapping resources *and* interfering
effects (formalized in `competition-and-relations.md` § Competition
Predicate). A tooltip that only *observes* the pointer stream does not
compete with a drag Claim that *captures* it, even though both react to the
same `pointermove` events.

---

## State Transition (modal claims)

Some interaction systems are best modeled as an explicit state machine rather
than a flat set of independent Claims — this is the normal shape for CAD, 3D
modeling, games, editors, and DAWs:

```text
IDLE
  --G--> GRAB_MODE

GRAB_MODE
  --X--> X_CONSTRAINED
  --Y--> Y_CONSTRAINED
  --Enter--> COMMIT
  --Esc--> CANCEL
```

When a scope exhibits this shape, model the whole machine, not each
transition as an isolated Claim — the ownership question ("what happens to
the mouse Claim while in GRAB_MODE") only makes sense in terms of the current
state.

---

## Ownership Lifecycle

Ownership is not static. Model the lifecycle explicitly:

```
acquire → provisional → promote → transfer → preempt → cancel → release
```

### Core lifecycle invariant

> Every acquired ownership MUST have a valid termination or transfer path for
> every reachable condition under which the owner, the target, the claimed
> resource, the activation context, or the supporting runtime state ceases to
> be valid.

This is the general form. It is not itself a checklist — the checklist is the
baseline categories below, which MUST always be checked, plus whatever
scope/resource invalidation conditions (§ below) are actually reachable for
the runtime in question.

**Baseline categories (mandatory minimum, not the entire universe):**
normal completion, user cancellation, focus loss, device loss (disconnect),
application mode change, and runtime interruption (e.g. tab backgrounded, app
suspended, scene unloaded).

| Termination condition missing | Resulting defect class |
|---|---|
| completion | stuck interaction that never reports done |
| cancellation | drag/gesture continues after the user clearly aborted |
| focus loss | movement/drag continues after window/tab/view loses focus |
| device loss | input state stays "active" after device disconnects |
| mode change | dangling modal state when the app mode switches underneath it |
| runtime interruption | capture/lock never released when the runtime suspends the scope |

### Scope/resource invalidation — the open category

The six baseline categories above are a mandatory floor, not a closed
ceiling. Many real defects come from a runtime-specific way for the owner,
target, or resource to stop being valid that does not fit any of the six
labels above. Treat these as instances of one generic category —
**scope/resource invalidation** — rather than inventing a seventh, eighth,
ninth named baseline every time a new runtime shows up:

- component unmount / node or object destruction / target deletion
- scene or entity removal
- resource replacement (the claimed resource itself is swapped for a
  different instance)
- route/screen replacement or navigation away
- the ownership target being reparented into a context where the claim no
  longer makes sense
- permission/capability loss (e.g. camera/mic revoked mid-interaction)
- document/session replacement
- a remote collaborator removing the target (multi-user/collaborative
  runtimes)
- device/input mapping reassignment (a controller reassigned to a different
  player, a MIDI device rebound to a different control)

When auditing a specific runtime, enumerate the scope/resource invalidation
conditions that are actually reachable there (see `runtime-modeling.md` for
per-runtime starting points) and check each one for a release/transfer path,
exactly as you would for a baseline category. Do not treat "not one of the
six baseline labels" as a reason to skip the check — the invariant covers
*any* reachable invalidation, named or not.

For every Claim that reaches `acquire`, the audit MUST check every baseline
category above *and* every reachable scope/resource invalidation condition
for a defined transition to `release` or a valid `transfer` (directly or via
`cancel`). A Claim with an acquire path and no matching release/transfer path
for a *reachable* invalidation condition is a `CONFLICT`, not `UNMODELED` —
the ownership relationship *was* examined, and found broken.

**Release of ownership is necessary but not always sufficient.** A Claim can
correctly release ownership and still leave behind a causal descendant
(a timer, an async task, a queued command) that mutates interaction state
later, after the Claim itself is gone. That failure mode is not covered by
the Ownership Lifecycle alone — see § Effect Lifetime below.

---

## Effect Lifetime (Causal Lifetime)

A Claim can spawn effects that outlive it: timers, delayed callbacks,
debounce/throttle callbacks, animation-completion handlers, promises/futures,
network responses, worker/task results, queued commands, deferred UI
updates, asynchronous snap/settle calculations, callbacks from external
devices or services. Releasing the Claim's ownership does not automatically
cancel these — they are causally descended from the Claim
(`ownership-model.md` § Provenance / `DERIVES_FROM`, or `SEQUENCES` when the
spawning Claim establishes context the deferred effect depends on), but they
are not bound to its lifecycle unless something explicitly binds them.

**Example — cancelled timer fires anyway:**

```text
long press begins → timer created → pointer cancelled → ownership released
→ timer fires later → context menu opens anyway
```

Ownership was released correctly. The invariant it violated is a different
one: the timer, a causal descendant of the Claim, had no cancellation path
tied to the Claim's own `cancel`/`release` transition.

**Example — stale result mutates a gone target:**

```text
interaction starts → async operation spawned → target component disappears
→ async completion mutates the obsolete target
```

### Required invariant

> Every delayed, scheduled, asynchronous, or externally completed effect
> created by an Interaction Claim MUST retain a valid causal context when it
> executes, or MUST be cancelled/ignored once its originating Claim, target,
> scope, state, generation, or resource is no longer valid.

Model a spawned effect as a **child claim/effect** with its own validity
condition and its own cancellation/invalidation path, causally linked back to
the parent via `DERIVES_FROM` (it is not an independent input) — do not force
this into the Ownership Lifecycle's acquire/release pair when the effect has
no input-ownership semantics of its own; it has a narrower causal-validity
semantics instead:

```text
Claim
  ↓ spawns / causes
Deferred Effect (child)
  ↓ has
validity condition (is my originating Claim/target/scope/state/generation
                     still the current one when I fire?)
  ↓ if invalid
cancellation / no-op path
```

A "generation" or "epoch" counter (or equivalent — a request token, a version
stamp, a component-instance identity) is a common, runtime-agnostic way to
express the validity condition: the deferred effect captures the generation
it was spawned under, and checks it against the current generation before
applying any mutation.

**This is a distinct check from the Ownership Lifecycle invariant above.** A
Claim can pass every lifecycle check (clean acquire, clean release on every
reachable condition) and still fail this one, because the defect lives in a
causal descendant that was never bound to the Claim's own transitions. Audit
both, separately, for any Claim whose `effect` includes a delayed, scheduled,
or asynchronous component. See `adversarial-validation.md` § Effect Lifetime
and Deferred Escape for worked cases.

---

## Worked example

A long-press that opens a context action on a list item, expressed as Claims
(illustrative — see `runtime-modeling.md` for how this looks in a specific
runtime):

```yaml
claim_id: list-item.context-action
scope: ListItem[i]
source: {kind: physical, device: touch, instance: single-pointer}
activation: "PointerDown AND Hold(500ms) AND MovementSince(down) < 8px"
recognition:
  states: [possible, began, active, cancelled]
  waitsForFailureOf: [list-item.drag-reorder]     # if a drag handle exists
claimed_resources: [pointer.identity, gesture-recognizer-slot]
routing: {mechanism: hit-test, capture: none}
provenance: independent
effect: [activate: "context-action-sheet", suppress: "native contextmenu"]
lifecycle:
  acquire: began
  release_on: [pointerup, pointercancel, movement>8px, focus-loss]
```
