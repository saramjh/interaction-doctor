## Interaction work in this repo

All interaction-capable code in this project (any input-driven UI or
runtime behavior — pointer/touch, keyboard, gamepad, XR, accessibility
activation, etc.) goes through the `interaction-doctor` skill before it is
considered done:

- `.claude/skills/interaction-doctor/SKILL.md` — the audit protocol
- `.claude/skills/interaction-doctor/references/` — the full model
  (Interaction Claims, ownership relationships, environment/runtime
  modeling, intent-and-ambiguity protocol, audit modes, closure contract)

### Absolute rules

1. **No guessing when product intent is undetermined.** Follow
   `references/intent-and-ambiguity.md` — ask the user, with locatable
   context, rather than inventing a mechanism or a binary choice.
2. **Every ownership finding needs a disposition**, not a silent default:
   `SAFE` / `RESOLVED` / `CONFLICT` / `NEEDS_INTENT` / `UNMODELED`, per
   `references/closure-contract.md`. Don't report a change as closing an
   audit while any item is `CONFLICT`, `NEEDS_INTENT`, or `UNMODELED` inside
   the declared scope.
3. **Disposition and verification level are separate facts — report both.**
   `STATIC` (read the code, the logic holds) and `RUNTIME` (actually
   exercised — a test run, a driven browser/simulator, a live check) are
   independent of whether an item is closed. A `STATIC`-only item can
   legitimately close as `SAFE`/`RESOLVED`; never report it as `RUNTIME`-
   verified, and never withhold closure solely for lacking runtime
   verification unless the task explicitly required it.
4. **Revalidate recursively after every fix.** A fix is not done because
   the reported symptom disappeared — rebuild the affected ownership graph
   and check neighbors, lifecycle termination, and any relationship the fix
   itself introduced (`references/audit-modes.md`).
5. **The `.interaction-doctor/` index, if present, is a cache — never
   truth.** Current source always wins over a cached ownership map.

This project previously used a different, mobile-web-specific gesture
threshold architecture (fixed px/ms constants, a fixed cluster taxonomy).
That approach was discarded in favor of the runtime-independent ownership
model above — do not resurrect the old thresholds/clusters as if they were
still normative; anything reused from them now exists only as a labeled
instance inside the new model (see
`references/adversarial-validation.md`).
