# Interaction Doctor Benchmark

> **STATUS: PRODUCT DISCONTINUED &bull; BENCHMARK &amp; EMPIRICAL CORPUS RETAINED**  
> Interaction Doctor was an experimental coding-agent skill for auditing interaction ownership, gesture conflicts, and UI event lifecycles.  
> In a 30-case, 90-run empirical controlled benchmark, the skill **provided no repair advantage over the baseline frontier model** (19/19 in all arms) and imposed **~1.91&times; token cost** and **~2.44&times; execution latency**.  
> The skill has therefore been **discontinued**. This directory preserves the independent benchmark, evaluation harness, hidden oracles, and empirical dataset as an enduring research asset.

---

## 1. The Research Question

When frontier coding agents (such as `claude-sonnet-5`) encounter subtle, cross-cutting UI interaction bugs—such as nested drag-vs-scroll collisions, unmount debounce leaks, focus loss after element deletion, or conflicting multi-touch gestures—does injecting a formal, domain-specialized interaction-ownership skill improve diagnostic accuracy and repair success enough to justify its execution cost?

---

## 2. Three Experimental Arms

The benchmark maintains identical model configuration (`claude-sonnet-5`, medium effort, fail-closed Seatbelt sandboxing) and varies only the intervention injected into the agent environment:

- **Arm A (Baseline):** The pure coding model provided solely with the task prompt (`task.md`) and the starting fixture. Measures natural capability on interaction defects.
- **Arm B (Generic Rigor):** The same model with a generic "careful review and edge-case audit" prompt appended (`prompts/generic.md`), strictly devoid of Interaction Doctor terminology. Controls for prompt length, verbosity, and diligence bias.
- **Arm C (Doctor v1):** The same model with the frozen Interaction Doctor v1 skill injected into the workspace's `.claude/skills/` directory and instructed via `prompts/doctor.md` to execute the skill protocol.

---

## 3. Case Distribution & Scope

The benchmark contains exactly **30 test cases** across a rigorous taxonomy:

| Outcome Category | Count | Primary Evaluation Focus |
| :--- | :---: | :--- |
| **YES (Defective)** | 19 | Defect present in fixture. Scored on whether the model diagnoses and repairs the flaw according to hidden test assertions. |
| **NO (Benign Control)** | 5 | Benign interaction pattern with non-defective behavior. Scored on whether the model correctly leaves the logic alone (no-op) without introducing functional false positives. |
| **NEEDS_INTENT (Ambiguous)** | 6 | Requirements are fundamentally underspecified. Scored on whether the model halts and requests clarification rather than unilaterally guessing a product policy. |
| **UNMODELED (Unsupported)** | **0** | **Explicit scope boundary:** The benchmark contains **zero unmodeled cases**. It makes no empirical claims regarding an agent's ability to handle unmodeled hardware or input modalities. |

### Case Topologies Covered
- **Pairwise Conflicts:** Scrubber drag nested in carousel swipe (`case-001`), hotkey vs literal text entry (`case-004`).
- **N-ary Event Competition:** Split canvas drag vs delete (`case-011`), simultaneous swipe actions (`case-016`).
- **Lifecycle & Interruption:** Backgrounded tab drag release (`case-006`), unmount debounce timer leak (`case-009`), grabmouse focus leak on Alt+Tab (`case-025`).
- **Async Causal Staleness:** Kanban drag reorder under out-of-order responses (`case-002`), autosave queue with target deletion (`case-007`), timeline autoscroll staleness (`case-030`).
- **Negative Controls:** Spacebar drag modifier (`case-003`), IME composition guard (`case-005`), MIDI dual-channel blend (`case-008`), independent toast stack (`case-014`), physics arena routing (`case-024`).

---

## 4. Scoring & Hidden Oracles

Grading is executed via `benchmark/graders/grade_run.py` against private fixtures in `cases-private/`. The evaluated model never has filesystem access to `cases-private/`:

1. **Repair Success:** All target assertions in private `hidden-tests/test.js` pass on the model's final workspace.
2. **Regression Freedom:** All non-target assertions that held on the unmodified baseline fixture continue to hold.
3. **Source Churn vs. Functional Change:** Graders distinguish cosmetic text/whitespace edits from genuine behavioral changes verified by state probes.
4. **Behavioral Oracles, Not Terminology Matching:** An agent is never scored on whether it recited Interaction Doctor terminology ("claims", "dispositions", "arenas"). Scoring is based strictly on observable runtime execution state.
5. **NEEDS_INTENT Evaluation:** Evaluated according to `benchmark/design/needs-intent-scoring-v2.md`. Agents that unilaterally implement a policy resolution receive an `intent_guessing_violation`. Agents that pause and prompt the user receive `needs_manual_review_ambiguity`.

---

## 5. Empirical Results

Evaluated across 90 sequential runs (30 cases &times; 3 arms) on `claude-sonnet-5` (medium effort):

```
BASELINE (Arm A)
    Repair:                 19/19 = 100%
    Correct NO-op:           3/5  = 60%
    Functional FP:           0/5
    Intent guessing:         6/6  = 100%
    Manual-review ambiguity: 0/6
    Regression:              1/30 = 3.3%
    False closure:           0/30
    Detection heuristic:    14/19 = 73.7%
    Total cost:             $3.2389 ($0.1080/run)
    Total wall time:         848.2s (28.3s/run)
    Total tool calls:        138 (4.6/run)

GENERIC (Arm B)
    Repair:                 19/19 = 100%
    Correct NO-op:           2/5  = 40%
    Functional FP:           0/5
    Intent guessing:         6/6  = 100%
    Manual-review ambiguity: 0/6
    Regression:              1/30 = 3.3%
    False closure:           1/30 = 3.3%
    Detection heuristic:    18/19 = 94.7%
    Total cost:             $3.4414 ($0.1147/run)
    Total wall time:         994.0s (33.1s/run)
    Total tool calls:        137 (4.6/run)

DOCTOR (Arm C)
    Repair:                 19/19 = 100%
    Correct NO-op:           2/5  = 40%
    Functional FP:           0/5
    Intent guessing:         4/6  = 66.7%
    Manual-review ambiguity: 2/6  = 33.3% (stopped on 011, 016)
    Regression:              0/30 = 0.0%
    False closure:           0/30
    Detection heuristic:    18/19 = 94.7%
    Total cost:             $6.1973 ($0.2066/run) [~1.91x vs Baseline]
    Total wall time:        2067.2s (68.9s/run)   [~2.44x vs Baseline]
    Total tool calls:        212 (7.1/run)        [~1.54x vs Baseline]
```

### Empirical Analysis
1. **Zero Repair Lift:** On the 19 well-specified defect cases, all 3 arms achieved 100% repair (19/19). The skill provided zero incremental repair power.
2. **Ambiguity Signal:** On the 6 ambiguous cases (`004`, `010`, `011`, `013`, `016`, `019`), Baseline and Generic guessed 100% of the time (6/6). Doctor successfully stopped on 2 cases (`case-011` and `case-016`), reducing guessing to 66.7%.
3. **Regression Non-Independence:** The sole regression observed in Baseline and Generic occurred on `case-011`. Doctor avoided that regression exclusively because it paused on ambiguity instead of guessing the policy. Doctor's 0% regression rate is not independent evidence of regression avoidance.
4. **Detection Heuristic Note:** The detection heuristic is keyword-based diagnostic metadata only. It is not semantic recall and must not be cited as evidence of superior understanding.

---

## 6. Empirical Limitations & Provenance

1. **Preflight Qualification Caveat:**  
   Prior to the 90 empirical runs, the preflight qualification gate registered `PAID_PREFLIGHT = HOLD` (`READY_FOR_EMPIRICAL_90_RUNS = False`) because evaluated models skipped diagnostic probe instructions embedded in the preflight prompt. Doctor executed its bash probes but omitted builtin read probes. This was documented as probe compliance insufficiency rather than a sandbox or infrastructure failure. The 90-run batch was executed under an explicit qualification waiver. Freeze verification, tool lockdown, and workspace isolation remained active throughout.
2. **Retry History:**  
   - Cases 001–014: Valid observations gathered on initial execution (`run-01`).
   - Cases 015–030: Initial attempts encountered Anthropic API 429 concurrency and session limits. Infrastructure failure logs were archived, and valid observations were collected from `run-03` after rate-limit reset.
   - Zero Cherry-Picking: No successful run was ever rerun to improve its score.
3. **Scope & Statistical Generalizability:**  
   This was a descriptive pilot ($n = 30$ cases per arm, single repetition). It conclusively demonstrated that the skill failed to earn its cost on this corpus, but does not make universal claims about statistical significance across arbitrary models or domains.

---

## 7. Reproduction Guide

To verify benchmark integrity and re-grade the archived runs from the repository root:

```bash
# 1. Verify frozen file hashes against authoritative freeze v6
python3 benchmark/design/verify_experiment_freeze.py

# 2. Run grader self-tests against ground-truth fixtures
python3 benchmark/graders/grade_run_selftest.py

# 3. Validate showroom dataset against empirical source of truth
python3 scripts/validate_showroom_data.py

# 4. Run harness settings policy self-tests
python3 benchmark/harness/settings_policy_selftest.py
```

Authoritative frozen snapshot commit: `dfb9f7997ac46a623b9a291fdd3ccaeba90b5cfb`.
