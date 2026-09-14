# Runtime Modeling Notes

The Claim model (`ownership-model.md`) is runtime-independent by design, but
an agent auditing a specific codebase still needs to know where to look for
each field in that specific runtime. This document is a lookup table, not a
new model — every row below is an instance of the same schema, never a
special case that bypasses it. When a runtime is not listed here, derive its
mapping the same way these were derived: find its routing mechanism, its
recognizer/state-machine primitives, its resource types, and its
environmental claims, then fill the schema.

## Web / DOM

- **Routing**: hit-test → capture phase → target → bubble phase; explicit
  `setPointerCapture`/`releasePointerCapture` overrides hit-test routing for
  the capturing element.
- **Recognition primitives**: none built in for gestures beyond
  click/dblclick — custom recognizers are typically hand-rolled or via a
  library (dnd-kit, Hammer, use-gesture); `touch-action` CSS declares
  activation-distance intent to the browser's own scroll/zoom recognizers.
- **Resources**: pointer identity (`PointerEvent.pointerId`), focus (DOM
  focus target), scroll ownership (per scrollable ancestor), text
  selection, native drag (`draggable`/`dragstart`).
- **Environmental claims to add**: native scroll/zoom, native text
  selection, native context menu (`contextmenu`), IME composition
  (`compositionstart/update/end`), browser back-gesture (edge swipe on
  mobile browsers), native drag-and-drop.
- **Provenance chains**: touch → pointer → compatibility mouse → click;
  keyboard activation on a focusable control → synthesized `click`.

## React / Vue / Svelte (and similar component frameworks)

- These sit **on top of** DOM routing — do not model a separate routing
  layer unless the framework changes event dispatch semantics (e.g.
  synthetic event pooling, portal-based re-parenting of the DOM hierarchy
  which changes bubble order relative to visual nesting).
- **Recognition primitives**: usually still library-provided (framework
  bindings around dnd-kit/use-gesture/Reanimated-gesture-handler, etc.) —
  model the library's recognizer states, not the framework's render cycle.
- **New resource to watch**: component re-render can silently reset
  closures/refs holding Claim state (e.g. a `useRef` re-initialized) —
  treat an unintended state reset as a lifecycle defect
  (`ownership-model.md` § Ownership Lifecycle), not a framework quirk to
  ignore.

## SwiftUI

- **Routing**: view hierarchy hit-testing; `.highPriorityGesture`,
  `.simultaneousGesture`, and `.gesture` express `PREEMPTS`/`COOPERATES`
  directly as API — map them onto the relation taxonomy rather than
  treating them as opaque modifiers.
- **Recognition primitives**: `UIGestureRecognizer` (UIKit-bridged) /
  SwiftUI `Gesture` types have built-in `possible/began/changed/ended/
  cancelled/failed` states and native `require(toFail:)` — this is a direct
  match for `waitsForFailureOf`.
- **Resources**: focus (`@FocusState`), first responder, drag-and-drop
  (`onDrag`/`onDrop`), scroll ownership (`ScrollView` nesting).
- **Environmental claims**: system edge-swipe-back, system context menu
  (long-press), VoiceOver activation (semantic, no physical event),
  keyboard shortcuts via hardware keyboard on iPad.

## Jetpack Compose

- **Routing**: `Modifier` chain order determines hit-test and gesture
  priority; `pointerInput` + `awaitPointerEventScope` gives raw access to
  recognition state.
- **Recognition primitives**: `detectTapGestures`,
  `detectDragGesturesAfterLongPress`, etc. — their composition already
  encodes `waitsForFailureOf`/`promotesAfter`; a custom
  `awaitPointerEventScope` block must declare these relations explicitly
  since nothing does it for you.
- **Resources**: focus (`FocusRequester`), nested scroll (`NestedScrollConnection`
  — this is the direct primitive for declaring scroll-ownership priority
  between parent/child, i.e. `CONDITIONAL`/`PREEMPTS` between scroll Claims).
- **Environmental claims**: system back gesture, TalkBack activation,
  system context menu, IME composition.

## Flutter

- **Routing**: `GestureDetector`/`Listener` hit-testing with an explicit
  `GestureArenaManager` — the arena *is* the recognition-state machine;
  competing recognizers register with the arena and it resolves the winner,
  which is a direct runtime implementation of `waitsForFailureOf`/`PREEMPTS`.
  When more than two recognizers register in the same arena, the arena's
  resolution is a native instance of an Ownership Constraint Group
  (`competition-and-relations.md` § Ownership Constraint Groups), not a
  chain of independent pairwise checks — model it as one group with an
  `exclusive` policy across all registered participants.
- **Resources**: focus (`FocusNode`), scroll ownership
  (`NotificationListener<ScrollNotification>`), semantics tree
  (accessibility) as an independent source of activation.
- **Environmental claims**: platform back gesture, system context menu,
  screen-reader (TalkBack/VoiceOver via Flutter semantics), IME.

## Unity

- **Routing**: `EventSystem` + `Raycaster` (UI) or physics raycasts (world
  objects, including XR); polling-based `Input`/`Input System` package for
  device state — most game input is polled once per frame, not
  event-dispatched, so "recognition state" is usually hand-rolled per
  script rather than provided by the engine.
- **Resources**: input action maps (device-and-binding agnostic action
  names — a good match for `claimed_resources: [semantic command]`), per
  `PlayerInput`/device-pairing in local multiplayer (device instance
  identity matters heavily here — see `environment-model.md` § Multiple
  Input Identities).
- **Environmental claims**: platform OS-level shortcuts are usually not
  relevant in full-screen games, but console/OS overlay gestures
  (screenshot chord, home button) can still preempt input — check per
  target platform.

## Godot

- **Routing**: `_input`/`_unhandled_input` propagate through the scene tree
  with explicit `accept_event()`/`set_input_as_handled()` — this is a direct
  primitive for declaring "this Claim consumes the input, stop propagation,"
  i.e. an explicit `effect: consume`.
- **Resources**: similar to Unity — polled `Input` singleton for analog
  axes, action names (`InputMap`) as semantic-command resources.

## Qt / desktop toolkits

- **Routing**: widget hit-testing with explicit event filters
  (`installEventFilter`) that can intercept before the target widget sees
  the event — model this as a routing-level `PREEMPTS`.
- **Resources**: focus policy, modal dialog stacks (application mode as a
  first-class resource), keyboard shortcut/action tables (often global,
  cutting across widget hierarchy — check for `COMPETES` between a global
  shortcut and a focused widget's own key handling).

## CAD / 3D modeling / DAW-style applications

- Model as an explicit **state machine** (`ownership-model.md` § State
  Transition) rather than a flat Claim set — tool modes (GRAB, ROTATE,
  SCALE), axis constraints, and modal numeric entry are the normal shape
  here, and most of this domain's real defects are lifecycle defects
  (a modal command left uncommitted when focus moves to another window,
  an axis constraint that survives a mode switch it shouldn't).
- **Resources**: per-axis transform dimensions (translation/rotation/scale
  × X/Y/Z, each independently claimable — this is where partial resource
  overlap, i.e. `COOPERATES`, matters most).
- **Environmental claims**: OS-level modifier-key chords the application
  cannot intercept (rare but check), multi-monitor focus routing.

## Game engines generally (local multiplayer)

- Multiple actors with independently-indexed devices is the default
  assumption, not an edge case — every Claim's `source` MUST specify device
  *instance*, not just class, or `resource_overlap()` in
  `competition-and-relations.md` cannot be evaluated correctly across
  players.

## XR (gaze, pose, hand tracking, controllers)

- **Routing**: ray/collider targeting from gaze direction, controller pose,
  or hand-tracking skeleton — often multiple simultaneous ray sources
  (two controllers, or a controller plus gaze) targeting the same
  interactable, which is a direct `COMPETES`/`COOPERATES` question per
  interactable.
- **Source**: pose data is continuous (§ Analog input in
  `environment-model.md`) — a "grab" Claim is typically `pose within volume
  AND trigger past threshold`, not a discrete event.
- **Resources**: per-controller/per-hand claim identity is mandatory (two
  controllers grabbing the same object is a real, common `COMPETES` case).
  When an object explicitly supports two-handed manipulation but not a third
  simultaneous controller, model that capacity limit as an Ownership
  Constraint Group with `capacity(2)`, not as three independent pairwise
  `COMPETES` checks — the three-way case is exactly the shape pairwise
  analysis alone cannot see (`competition-and-relations.md` § Ownership
  Constraint Groups).

## Accessibility (cross-runtime)

Do not model accessibility as a separate audit track. Every runtime above
exposes a semantic activation path (VoiceOver, TalkBack, switch control,
screen readers, voice control) that can produce an `effect` with no
corresponding physical Source event. Every Claim whose only Source is a raw
pointer/key event and which has no semantic-activation counterpart is an
audit finding under `environment-model.md` § Raw → transformed → semantic
input — not an optional enhancement.
