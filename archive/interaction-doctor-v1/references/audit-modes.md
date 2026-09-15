# Audit Scope, Analysis Strategy, and Recursive Revalidation

Two independent dimensions govern how an audit runs. Do not conflate them —
a project with a rich `.interaction-doctor/` index still gets a `TARGETED`
audit for a narrow bug report, and a project with no index at all still gets
a `FULL` audit when asked for release-readiness review.

```text
Audit Scope           what boundary must reach closure
-----------
TARGETED               the affected interaction graph for a specific
                        reported problem
FULL                    the complete declared audit universe

Analysis Strategy      how the graph is (re)built
-----------------
FRESH                   no trustworthy prior index — build Claims from
                        current source from scratch, for everything in scope
INCREMENTAL             a prior index exists — use it to locate/seed the
                        graph, but invalidate and rebuild anything touching
                        changed source
```

**The user's task determines Audit Scope. The presence of a
`.interaction-doctor/` index determines whether `INCREMENTAL` strategy is
available.** Neither one picks the other:

```text
TARGETED + FRESH        a specific bug, no prior index — build the affected
                         graph directly from current source.
TARGETED + INCREMENTAL  a specific bug, but a prior index exists — use it to
                         locate the affected graph neighborhood quickly, then
                         verify/rebuild that neighborhood against current
                         source. Still scoped to TARGETED; the index is only
                         a shortcut to find the boundary faster.
FULL + FRESH            a complete audit of a project with no trustworthy
                         index yet (first full audit, or the index is stale
                         enough to distrust wholesale).
FULL + INCREMENTAL      a complete audit of a project with an existing index
                         — reuse it as an optimization, but consistency-check
                         every entry against current source before counting
                         it; FULL scope still requires exhaustive coverage,
                         so INCREMENTAL here saves rebuild work, not
                         verification work.
```

An index existing does not narrow a `FULL` request to something smaller, and
a narrow bug report does not become a `FULL` audit merely because an index
happens to be available.

## TARGETED scope — procedure

1. Identify the user-visible affected interface (screen/view, region,
   action, observed vs. expected behavior).
2. Locate the relevant implementation scope(s) in source. If `INCREMENTAL`
   strategy is available, consult the index first to jump to a candidate
   neighborhood — then verify that neighborhood against current source
   before trusting it (`intent-and-ambiguity.md` § Source-of-truth
   hierarchy).
3. Expand outward through connected ownership/routing/state relationships —
   follow every `COMPETES`/`PREEMPTS`/`SEQUENCES`/`COOPERATES`/`DERIVES_FROM`
   edge and every Ownership Constraint Group
   (`competition-and-relations.md`) that touches a Claim in step 2, until
   the edges stop leading to new Claims (a boundary is reached).
4. Build the affected interaction graph (the Claims, relationships, and
   group constraints discovered in steps 2–3).
5. Analyze relevant environments (`environment-model.md`) for that graph —
   what native/platform Claims apply to these scopes and capabilities.
6. Resolve/fix, per `intent-and-ambiguity.md`.
7. Recursively rebuild and revalidate the affected graph (§ below) until it
   reaches a stable fixpoint.

Do not audit the entire repository for a targeted report. The closure
statement for this scope is explicitly bounded — see `closure-contract.md` §
Affected Interaction Closure.

## FULL scope — procedure

1. Inspect the complete codebase (or, under `INCREMENTAL` strategy, the
   complete index plus everything changed since it was built).
2. Discover all interaction-capable scopes.
3. Normalize each into the universal Claim model (`ownership-model.md`).
4. Add environmental/native claims per relevant capability combination
   (`environment-model.md`).
5. Build the complete relevant ownership/integrity graph — every Claim,
   every pairwise relationship, and every Ownership Constraint Group among
   them (`competition-and-relations.md`).
6. Evaluate every supported environment/capability combination against that
   graph.
7. Resolve all detected issues per `intent-and-ambiguity.md`.
8. Obtain missing product intent where required — ask, per the user-question
   protocol, and record decisions.
9. Recursively rebuild until the graph reaches stability (§ below).
10. Certify closure only when no unresolved/unmodeled audit item remains —
    see `closure-contract.md` § Project Interaction Closure.

Under `INCREMENTAL` strategy, step 1's reuse of the index is an optimization
only — `FULL` scope's closure bar (§ Project Interaction Closure) still
requires every index entry to be consistency-checked against current source,
never trusted wholesale because "the index already covers it."

---

## Recursive Revalidation (fixpoint requirement)

Every modification can create new ownership relationships that did not exist
before the fix — a fix is never complete merely because the originally
reported symptom disappeared. Apply this loop, in either scope, to every
changed scope:

```text
analyze → modify → rebuild affected graph → rediscover relationships →
validate → repeat
```

Continue until the affected graph reaches a stable fixpoint: another pass
over the same scope discovers no new Claim, no new relationship or group
constraint, and no disposition that changes.

After any change, explicitly revalidate:

- the **original** relationship that prompted the change (did the fix
  actually resolve it, under the competition predicate or the relevant group
  policy — not just "does the symptom look gone")
- **neighboring** scopes (a Claim you modified may now interact differently
  with a sibling scope that shares a resource, e.g. a parent scroll
  container)
- **state transitions** (did the fix introduce a new reachable state, or
  remove a transition something else depended on — `SEQUENCES` edges)
- **alternative environments** (does the fix hold across every capability
  combination enumerated in the procedure above, not only the one you
  tested)
- **ownership lifecycle termination** (does the modified Claim still have
  valid release/transfer paths for every baseline category and every
  reachable scope/resource invalidation condition in `ownership-model.md` §
  Ownership Lifecycle — a fix that adds a new `acquire` path without a
  matching release/transfer path is a new defect, not a completed fix)
- **effect lifetime** (does the modified Claim's `spawned_effects`, if any,
  still carry a valid cancellation/invalidation path tied to the Claim's own
  termination — `ownership-model.md` § Effect Lifetime; a fix that changes
  *when* a Claim releases without checking whether its spawned timers/async
  work are still bound to that release is incomplete)
- **group constraints** (did the fix change which Claims can be
  simultaneously active in a way that now violates, or newly satisfies, an
  Ownership Constraint Group's policy)
- **newly introduced relationships** (the fix itself may have created a new
  `COMPETES` or `DERIVES_FROM` edge, or a new N-ary interaction, that did not
  exist in the pre-fix graph)

For every item touched by this loop, record both its disposition (`SAFE` /
`RESOLVED` / `CONFLICT` / `NEEDS_INTENT` / `UNMODELED`) and its verification
level (`STATIC` / `RUNTIME`) — see `closure-contract.md`. A change that
passes self-review (code read, logic checks out) is disposition-eligible at
verification level `STATIC` only. It becomes `RUNTIME` only once actually
exercised (a test run, a driven browser/simulator, an interactive check).
Never report a `STATIC`-only result as if it were `RUNTIME`, and if no
runtime-verification tool is available in this environment, say so rather
than implying execution happened. A `STATIC`-only disposition can still
legitimately close an audit — see `closure-contract.md` § Verification level
— it is not a lesser result, only a differently-evidenced one.
