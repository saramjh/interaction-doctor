# Environment Model

The audited project's source code is not the entire interaction universe.
This document defines how Interaction Doctor accounts for input capabilities,
environmental/native claims, transformation pipelines, continuous input, and
multi-identity input — all without assuming a specific runtime.

## 1. Environment expansion — claims that are not in the project's source

Lack of explicit source code for a behavior does not mean lack of a
competing interaction owner. The runtime and platform own Claims of their
own, and the audit MUST enumerate the ones relevant to the affected scope
before certifying it. Treat these as virtual/environmental Claims with the
same schema as any other Claim (`ownership-model.md`), typically with
`source: {kind: semantic/native}` and `routing: {mechanism: native/system
broker}`.

Representative environmental claim owners (not exhaustive — extend per
runtime, see `runtime-modeling.md`):

- browser/page scrolling and page zoom
- native text selection
- context menu / callout (native long-press or right-click menu)
- OS-level navigation gestures (edge-swipe-back, home gesture, app-switcher)
- native focus behavior and focus ring
- IME/composition behavior
- accessibility services (screen reader gestures, switch control scanning)
- platform window-management shortcuts
- built-in runtime gesture recognizers (native pinch-zoom, native pull-to-refresh)
- native drag-and-drop
- system-level device arbitration (e.g. OS reserving a chord for screenshots)

An audit that only inspects application source and never asks "what does the
platform already own here" cannot reach closure — an environmental Claim that
was never considered is `UNMODELED`, not passed by default.

## 2. Capability-based environment, not device labels

Do not reduce the environment to `desktop` / `mobile`. Reason about
**capabilities**, since one physical device commonly exposes several at once
(e.g. a touch laptop has fine pointer, coarse pointer, hover, and keyboard
all available depending on which input the user picks up):

- fine pointer / coarse pointer
- hover / no-hover
- keyboard present
- trackpad / mouse / touch / pen present
- multi-pointer capable
- gamepad present
- XR present
- accessibility input active (screen reader, switch control, voice control)
- mixed-device sessions (a session can transition between capabilities
  mid-interaction — e.g. a user switches from touch to a connected keyboard)

When evaluating environments (`audit-modes.md`), enumerate the *reachable
capability combinations* for the affected scope, not a single assumed device
class. A Claim whose activation is only sound under one capability
combination but is reachable under another is a candidate `CONFLICT` or
`NEEDS_INTENT` item, not an oversight to silently ignore.

## 3. Raw → transformed → semantic input

Do not infer interaction intent directly from a raw key/pointer event without
checking what transformation state it passed through. Model the pipeline
explicitly with `DERIVES_FROM` edges (`ownership-model.md` § Provenance).

**IME composition.** `keydown → composition update → composition end → text
input`. An `Enter` keydown that arrives *during* composition typically means
"confirm the composed text," not "submit the form" — a Claim on `Enter` that
does not check composition state will misfire. This is a `CONFLICT` between
the form-submit Claim and the IME-confirm Claim if both can be reachable
simultaneously (apply the competition predicate).

**Accessibility activation.** A semantic activation (e.g. a screen reader
invoking a control) can produce an effect with no corresponding physical
input event at all. A Claim that only activates on `pointerdown`/`click` and
ignores the semantic activation path is missing a Source variant, not merely
missing a nice-to-have — this is required coverage under
`closure-contract.md`, not an advisory check.

**Synthesized compatibility events.** A pointer action may generate
compatibility events at the platform level (`touch → pointer → mouse →
click`) purely for legacy compatibility. Treat these strictly via
`DERIVES_FROM` — never as an independently competing input.

## 4. Analog and continuous input

Activation is not Boolean-only. Support predicates over continuous/analog
signals: joystick axes, trigger pull, pen pressure, pen tilt, MIDI control
values, SpaceMouse axes, XR pose values, other continuous sensor input.

Account for, conceptually:

- thresholds (activate once magnitude crosses a value)
- dead zones (ignore magnitude below a floor, to absorb noise/drift)
- hysteresis (different thresholds for activation vs. deactivation, to avoid
  flicker at the boundary)
- ranges (activate only within a numeric band)
- direction and magnitude as separate predicate axes

A Claim gated on a continuous signal without a stated dead zone or hysteresis
policy is a legitimate audit finding when that signal is known to be noisy
(analog sticks, pen pressure) — flag it rather than assuming a bare threshold
is safe.

## 5. Multiple input identities and grouping

The same device *class* does not imply the same *resource*. Support
reasoning about multiple simultaneous, independently identified sources:

- multiple pointers (multi-touch)
- multiple gamepads, each independently indexed
- multiple actors/players sharing one runtime
- pen and touch active at once (palm rejection scenarios)
- two hands / two XR controllers
- multiple HID/MIDI devices

Example: `Gamepad[0].A != Gamepad[1].A` — these are different resources even
though they share a device class and a button name. A Claim that identifies
its resource only as `"Button A"` without a device-instance qualifier is
under-specified whenever more than one instance of that device class can be
present — this is exactly the kind of ambiguity `resource_overlap()` in
`competition-and-relations.md` needs the instance qualifier to evaluate
correctly.

Pointer cardinality (single-finger vs. two-finger vs. N-finger) must also be
modeled as part of the activation expression, not inferred after the fact
from how many `pointermove` events arrived.

When a resource can validly be held by more than one but fewer than all
reachable claimants (e.g. an object supporting two-handed manipulation but
not three simultaneous manipulators), model that as an **Ownership
Constraint Group** (`competition-and-relations.md` § Ownership Constraint
Groups) rather than as a chain of pairwise checks — pairwise checks cannot
detect a constraint that only appears at three or more participants.
