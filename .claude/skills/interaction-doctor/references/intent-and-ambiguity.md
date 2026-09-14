# Intent, Evidence, and Ambiguity

Detecting a `COMPETES` relationship (`competition-and-relations.md`) never by
itself proves which Claim should win. This document separates **detection**
(an ownership-model question) from **product-intent judgment** (a separate
question that requires its own evidence), and defines what to do when intent
cannot be established.

## Source-of-truth hierarchy

Roles, in order of authority — never invert this order:

```text
Current source code
    = implementation truth

Explicit current user requirement
    = strongest product-intent evidence

Project specifications / tests / recorded decisions
    = product-intent evidence

Interaction ownership index (.interaction-doctor/*)
    = derived cache/index — never authoritative over current source

Platform/runtime knowledge
    = environmental interaction semantics
```

An existing ownership index entry MUST NOT override what current source
actually does. If the index says a Claim resolves one way and the current
code says otherwise, the code wins and the index entry is stale — update it
(`index-and-tooling.md`), do not act on the stale entry.

## Product-intent evidence hierarchy

When a `COMPETES` (or otherwise intent-dependent) finding needs a
disposition, gather evidence in roughly this order and stop at the first
tier that actually answers the question:

1. explicit current user instruction (this conversation, this task)
2. explicit current product specification
3. previously recorded interaction decision (`.interaction-doctor/decisions.json`)
4. tests that clearly express the intended behavior
5. strong existing convention *within this application* (how this same app
   resolves the same shape of conflict elsewhere)
6. platform/runtime convention (OS/HIG/Material-level behavior, when the
   audited scope's target platform is known)
7. general HCI heuristic

A lower tier MUST NOT override a higher tier that is actually present. Do not
reach for tier 6 or 7 heuristics while tier 1–3 evidence is available but
merely inconvenient to use.

## Critical ambiguity rule

When product intent cannot be established from the hierarchy above, do
**not**:

- guess
- invent a missing requirement
- assume every currently existing capability must be preserved unchanged
- automatically propose a "capability-preserving" redesign as the default
- reduce an unknown decision to an arbitrary predefined menu of choices
  (e.g. inventing "Option A vs. Option B" when the actual decision space is
  not known)
- decide based only on general UX convention when the ambiguity is really
  about *this product's* intent

Instead: explain the ambiguity with enough concrete, locatable context that
the user can immediately identify what you mean, and ask. Record whatever
they decide (`index-and-tooling.md`) so the same ambiguity is never re-asked
for the same relationship.

## User-question protocol

A user must be able to identify which interface you mean **before** you ask
them to decide anything. Include, as applicable:

- screen / page / view
- visible UI region and any visible label
- component role
- device/environment and application state/mode
- the exact user action
- the currently observed behavior
- the competing or suppressed behavior
- a short reproduction cue
- code location — as *secondary* developer context, not the primary
  identifier

Do not invent a menu of possible desired behaviors unless the actual decision
space is genuinely known, or the user explicitly asks you to recommend
options.

### Example — well-formed question

```text
The affected area is the message body in the chat screen.

On touch devices, long-pressing the message currently opens the message
context action and prevents the platform's normal text-selection behavior.

You can reproduce it by long-pressing directly on the message text.

What behavior do you intend for long press in this area?
```

### Example — malformed question (do not do this)

```text
There's a long-press conflict. Do you want option A (context menu wins) or
option B (text selection wins)?
```

This is malformed for two independent reasons: it gives no locatable context
(screen, region, reproduction cue), and it collapses an open decision space
into two arbitrary options the user never asked to be limited to.

## Resolution protocol

**If intent is sufficiently established** (tier 1–4, or a strong tier-5
convention with no counter-evidence):

- make the smallest robust change that satisfies the intent
- preserve unrelated behavior — do not use a `COMPETES` finding as license to
  redesign adjacent, unaffected interactions
- respect the routing/lifecycle semantics of the actual runtime
  (`environment-model.md`, `runtime-modeling.md`)
- avoid introducing new interaction design beyond what the intent requires

**If intent is not established:**

- stop the resolution path for that specific relationship — do not partially
  implement a guess "for now"
- ask, using the protocol above
- record the resulting decision in the interaction index
  (`index-and-tooling.md`)
- only then continue: implement, and recursively revalidate
  (`audit-modes.md` § Recursive Revalidation)

Do not turn Interaction Doctor into an unsolicited UX redesign system. A
`COMPETES` finding licenses fixing that specific interference — it does not
license redesigning the surrounding interaction because a "better" pattern
occurred to you along the way.
