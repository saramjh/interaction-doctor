# Relationships Between Claims

Do not reduce every relationship between two Claims to `COMPETES`. Most pairs
of Claims that touch the same input stream do not actually conflict. This
document defines the relationship taxonomy and the predicate used to decide
which relationship applies.

## Taxonomy

| Relation | Meaning |
|---|---|
| `COMPETES` | Both Claims can become simultaneously eligible, and their ownership/effects interfere — only one disposition can hold. |
| `COOPERATES` | Both Claims may be active simultaneously and are intended to compose into one user action. |
| `PREEMPTS` | One Claim intentionally takes ownership from another once some condition is met. |
| `CONDITIONAL` | Claims use overlapping resources but are mutually exclusive because their activation/state predicates cannot overlap. |
| `SEQUENCES` | One Claim establishes state or context that another Claim requires to activate. |
| `DERIVES_FROM` | One Claim's triggering event is causally synthesized from another's — not an independent input. |

This taxonomy — plus the Ownership Constraint Group construct below — is the
canonical vocabulary, and it is not extended casually during a single audit.
If a relationship genuinely does not fit one of the six relations or a group
constraint:

1. mark it `UNMODELED` and do not certify closure for it — see
   `closure-contract.md`.
2. analyze whether the Core abstraction is actually insufficient, or whether
   the relationship in fact reduces to an existing mechanism on closer
   reading (most apparent misfits do — see `adversarial-validation.md`).
3. if the Core genuinely needs extending: modify the canonical model itself
   (this document and/or `ownership-model.md`), formally define the new
   relation/construct, update every affected reference document and the
   tooling contract in `index-and-tooling.md`, add adversarial cases for it,
   and rerun the complete adversarial validation suite.
4. only after that deliberate process may the new construct enter the
   canonical vocabulary.

A one-off relation name invented mid-audit and recorded only in one
project's local index is not a valid outcome — see `index-and-tooling.md` §
Canonical vocabulary discipline. Canonical IR evolution is deliberate and
shared, never ad hoc and project-local.

### `COMPETES`

The default hard case. Example: a single-finger drag on a card that both
scrolls its ancestor list and reorders the card. Both Claims can reach
`active` from the same physical gesture, both claim `pointer.movement`, and
their effects (scroll the list vs. reposition the card) cannot both apply to
the same movement. This needs an explicit disposition — see
`intent-and-ambiguity.md`.

### `COOPERATES`

Example: `W` (translation.Z) and mouse XY (yaw/pitch) in a first-person
navigation mode — two Claims, disjoint resource slices, one composite user
action. Also covers a tooltip that tracks the pointer purely by observing
(`effect: observe`) while a drag Claim captures the same pointer stream for
movement (`effect: capture`) — no interference because the effects don't
collide even though the resource (`pointer.movement`) formally overlaps.

### `PREEMPTS`

Example: in the long-press triple-conflict shape (reorder vs. multi-select
vs. context menu on the same list item), a movement Claim that recognizes
before the hold timer fires deliberately cancels the pending
context-menu/multi-select Claims. This is a designed, declared preemption —
not an accident of code order.

### `CONDITIONAL`

Example, orbit vs. pan in a 3D viewport:

```text
Orbit: Shift AND MiddleMouseDown AND Move
Pan:   NOT Shift AND MiddleMouseDown AND Move
```

Both claim `pointer.movement` while `MiddleMouseDown` is true, but their
activation predicates are mutually exclusive on `Shift` — there is no
reachable state where both are simultaneously `active`. This is not
competition; it requires no runtime arbitration, only correct predicate
authoring. If both predicates could ever be true together (e.g. `Shift` is
read inconsistently in two places), that is a `COMPETES` finding, not
`CONDITIONAL`.

### `SEQUENCES`

Example: entering `GRAB_MODE` (one Claim/transition) is a precondition for
the `X_CONSTRAINED` Claim to even have a defined activation. The second
Claim's activation expression is only meaningful in the context the first
established. Model this explicitly rather than writing the second Claim's
activation as if it could fire from `IDLE`.

### `DERIVES_FROM`

Example: `touch → pointer event → compatibility mouse event → click`. A
Claim built on the compatibility `click` must never be evaluated as an
independent competitor of a Claim built on the originating `pointerdown` —
doing so double-counts one physical touch as two competing user inputs. When
in doubt whether two Claims are really one causal chain or two independent
inputs, resolve provenance first (`ownership-model.md` § Provenance) before
asking whether they compete.

A deferred/spawned effect (`ownership-model.md` § Effect Lifetime) that fires
after its originating Claim has ended is itself a `DERIVES_FROM` descendant
of that Claim, not an independent competitor — its validity is governed by
the Effect Lifetime invariant, not by the competition predicate below.

---

## Ownership Constraint Groups (N-ary arbitration)

The competition predicate below is pairwise by construction. Keep it — most
real conflicts are pairwise. But do not let the model imply that *every*
integrity constraint is pairwise. Some runtimes have constraints that only
appear at three or more participants:

```text
A + B      valid
A + C      valid
B + C      valid
A + B + C  invalid
```

No pairwise check ever observes this — each pair looks fine in isolation.
Examples: a recognizer-group capacity limit (a viewport allows at most two
simultaneous active recognizers, not one, but not unlimited either), a
resource with capacity greater than one but less than N (an interactable
that supports two-handed XR manipulation but not three-controller
manipulation), collaborative/multi-controller interactions with a group
arbitration policy, or a runtime-defined simultaneous-recognition limit.

Model this with a generic **Ownership Constraint Group**, composed with the
Claim graph rather than replacing it:

```yaml
group_id: <stable identifier>
participants: [ClaimA, ClaimB, ClaimC, ...]
resources: [<affected resources>]
activation: <group reachability condition — when is this group's
             constraint even in play>
policy:
  exclusive            # at most 1 of the participants may be active at once
  # or: capacity(N)    # at most N of the participants may be active at once
  # or: simultaneous   # all participants may be active together
  # or: ordered        # participants must activate in a defined order
  # or: runtime-defined # delegate to a named runtime/engine arbitration
                        # mechanism (e.g. a native gesture arena) — record
                        # which mechanism, don't leave it unstated
```

**Pairwise `COMPETES` is the special case `participants = [A, B], policy:
exclusive` (equivalently `capacity(1)`).** The ordinary competition predicate
remains the right tool whenever a group has exactly two participants and an
exclusive policy — do not route two-participant cases through the group
machinery unnecessarily. Reach for a group constraint specifically when a
resource or recognizer slot can validly host more than one but fewer than
all reachable participants, or when a policy genuinely depends on three or
more Claims jointly (the `A+B+C` shape above cannot be discovered by
checking `A+B`, `A+C`, and `B+C` independently — it must be checked as its
own group).

**Audit requirement:** evaluate pairwise relationships (the competition
predicate below) *and* any runtime- or application-level ownership
constraint involving three or more Claims. If no N-ary constraint exists for
a scope/runtime, ordinary pairwise analysis remains sufficient and nothing
further is required — do not manufacture group constraints where none
exist. See `adversarial-validation.md` § Ownership Constraint Groups for a
worked pairwise-safe-but-group-invalid case, and `runtime-modeling.md` for
runtimes (e.g. Flutter's gesture arena) that implement group arbitration
natively.

---

## The Competition Predicate

Two Claims `A` and `B` are competition **candidates** only if all three hold:

```text
reachable(A.activation == true AND B.activation == true)
AND resource_overlap(A.claimed_resources, B.claimed_resources)
AND ownership_interference(A.effect, B.effect)
```

Read each conjunct literally:

1. **`reachable(...)`** — there exists some input/state assignment, reachable
   from the scope's actual state space, under which both activation
   expressions evaluate true at once. Overlapping *event types* is not
   enough; overlapping *event types with satisfiable joint predicates* is
   required. This is what rules out false conflicts like Orbit/Pan above.

2. **`resource_overlap(...)`** — the claimed-resource sets intersect. A
   shared *axis* is overlap; disjoint axes of the same logical resource
   (`translation.X` vs `translation.Z`) are not.

3. **`ownership_interference(...)`** — the effects, applied together, would
   produce an inconsistent or undefined result (e.g. two Claims both trying
   to set the same scroll offset from different deltas). Two `observe`
   effects never interfere. An `observe` and a `capture` on the same
   resource do not interfere (the observer doesn't need exclusive access). A
   `capture` and a `capture` on the same resource do interfere.

If any conjunct is false, the pair is **not** `COMPETES` — classify it as one
of the other five relations, or as no relevant relationship at all. Do not
report a finding for a pair that fails this predicate; that would violate
the "ignore lack of an interaction surface" rule in the opposite direction —
manufacturing conflicts that cannot occur.

### Common false positives this predicate rules out

- **Event overlap without resource overlap.** A logging/analytics Claim that
  observes every `pointerdown` on the page does not compete with anything —
  it claims no resource at all (`effect: observe` only, `claimed_resources:
  []`).
- **Resource overlap without reachability.** Two Claims that both claim
  `Keyboard.Enter`, one active only in a text field and one active only when
  no text field is focused, cannot both be reachable simultaneously if focus
  is exclusive in that runtime.
- **Provenance chains mistaken for independent inputs.** See `DERIVES_FROM`
  above — always resolve this before applying the predicate.

### What the predicate does not decide

The predicate only detects that two Claims **can** interfere. It says
nothing about **which one should win**. That is a product-intent question —
see `intent-and-ambiguity.md`. Do not let a detected `COMPETES` relationship
silently resolve itself by code order, framework default, or convenience;
every `COMPETES` finding requires an explicit disposition sourced from the
intent-evidence hierarchy.
