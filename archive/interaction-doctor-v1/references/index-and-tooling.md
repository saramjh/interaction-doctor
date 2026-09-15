# Interaction Index and Deterministic Tooling

## The interaction index

The skill may maintain a project-local derived index:

```text
.interaction-doctor/
    ownership-map.json     # last-known Claims and relationships, by scope
    decisions.json         # recorded product-intent decisions, keyed by the
                            # relationship they resolved
```

Purpose:

- avoid rebuilding known graph areas on every request
- preserve explicit user/product decisions so the same `NEEDS_INTENT`
  question is never asked twice for the same relationship
- support the `INCREMENTAL` analysis strategy (`audit-modes.md`) — under
  either `TARGETED` or `FULL` audit scope
- let a `TARGETED` diagnosis locate the right graph neighborhood quickly
  instead of re-scanning the whole project

### The one rule that governs the index

> The index is a cache, not truth. Current source code is always
> authoritative over it (`intent-and-ambiguity.md` § Source-of-truth
> hierarchy).

Consequences:

- Any scope the index claims to already know about MUST still be checked
  against current source before its cached disposition is reused. If source
  has changed since the index entry was written, rebuild that entry.
- `decisions.json` entries about *product intent* remain valid even when
  source changes, unless the change itself alters the situation the decision
  was about — use judgment, and when in doubt, treat the decision as
  evidence (tier 3 in the product-intent hierarchy) rather than as an
  automatic override.
- A `FULL AUDIT` must rebuild or consistency-check the complete index — it
  cannot certify Project Interaction Closure while trusting unchecked cache
  entries.

### Suggested shape (illustrative, not a fixed schema)

```json
// ownership-map.json
{
  "scopes": {
    "ListItem": {
      "claims": ["list-item.drag-reorder", "list-item.context-action"],
      "relationships": [
        {"a": "list-item.drag-reorder", "b": "list-item.context-action",
         "relation": "PREEMPTS", "disposition": "SAFE", "verification": "STATIC"}
      ],
      "group_constraints": [],
      "last_checked_against_source": "<commit or content hash>"
    }
  }
}
```

`disposition` is one of `SAFE` / `RESOLVED` / `CONFLICT` / `NEEDS_INTENT` /
`UNMODELED`; `verification` is `STATIC` or `RUNTIME` — the two axes defined
in `closure-contract.md`. Never merge them back into a single field; that is
exactly the ambiguity this hardening pass removed.

```json
// decisions.json
{
  "list-item.drag-reorder__vs__list-item.context-action": {
    "decision": "movement > 8px always wins over the pending context-action timer",
    "evidence_tier": 1,
    "recorded_at": "<timestamp>"
  }
}
```

Adjust field names freely to fit the project's conventions — the schema is
not the contract; the two invariants above (cache-not-truth, decisions
persist as evidence) are.

### Canonical vocabulary discipline

The index MUST only use the canonical vocabulary: the six relations in
`competition-and-relations.md`, the Ownership Constraint Group construct, the
Effect Lifetime construct, and the disposition/verification values in
`closure-contract.md`. A single project's index is never the place to invent
a new relation name or a new disposition value for something that does not
fit — that is exactly the ad hoc mutation `competition-and-relations.md`'s
canonical-vocabulary-discipline section prohibits. If something in this
project genuinely does not fit the canonical vocabulary, record it as
`UNMODELED` with a free-text note, not as a new typed field — a new type
enters the vocabulary only through the deliberate process described there,
shared across the whole specification, never through one project's cache.

## Deterministic tooling integration

A future deterministic analyzer/validator (e.g. a standalone binary) may
extract Claims and build the ownership graph mechanically. The skill MUST
work correctly both with and without such tooling present.

**Division of responsibility**, if tooling is available:

| Tooling does | The skill (LLM) always does |
|---|---|
| deterministic Claim extraction from source | semantic interpretation of what a Claim means |
| ownership graph generation | product-intent evidence analysis |
| candidate relationship analysis (applying the competition predicate mechanically where inputs are fully known) | user communication (the ambiguity protocol) |
| lifecycle invariant verification | implementation strategy and code modification |
| post-fix revalidation (re-running the same mechanical checks) | ambiguity resolution and recording decisions |

Tooling MUST NOT independently invent product intent, even when it detects a
`COMPETES` relationship with high confidence. A mechanical tool can tell you
two Claims interfere; it cannot tell you which one the product wants to win.
That judgment always routes through `intent-and-ambiguity.md`.

**Shared IR.** Design any future tooling to consume and produce the same
Claim schema defined in `ownership-model.md` (source, activation,
recognition, claimed_resources, routing, provenance, effect, state_machine,
lifecycle, spawned_effects), the same relation taxonomy and Ownership
Constraint Group construct in `competition-and-relations.md`, the same
Effect Lifetime construct in `ownership-model.md`, and the same
disposition/verification-level pair in `closure-contract.md` — so the LLM
and the deterministic tool reason over one shared graph rather than two
incompatible representations. Do not design tooling against a separate, ad
hoc schema "for now" — that guarantees a future migration cost for no
benefit, since the schema here is already runtime-independent.

This document specifies the integration contract only. Building the Rust
tooling itself is a separate, later task.
