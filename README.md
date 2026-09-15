# Interaction Doctor Benchmark


[English](README.md) | [한국어](README.ko.md)
> **STATUS NOTICE: SKILL DISCONTINUED &bull; BENCHMARK RETAINED**  
> Interaction Doctor was an experimental coding-agent skill designed to audit and repair interaction ownership, gesture conflicts, and UI lifecycle behaviors.  
> In an empirical, 30-case, 90-run controlled benchmark against `claude-sonnet-5`, the skill **did not improve repair success over the baseline model** (19/19 in all arms) and imposed **~1.91&times; token cost** and **~2.44&times; execution latency**.  
> The skill has therefore been **discontinued as a product**.  
> This repository is retained as an open benchmark, evaluation harness, and engineering postmortem.

---

## Benchmark Showroom

An interactive research dossier and postmortem showroom is published on GitHub Pages:

👉 **[https://saramjh.github.io/interaction-doctor/](https://saramjh.github.io/interaction-doctor/)**

- **Executive Report (`index.html`):** Narrative breakdown of empirical results, resource overhead, and why three productization mitigation attempts failed.
- **Case Explorer (`cases.html`):** Interactive matrix of all 30 benchmark cases, filterable by outcome, difficulty, and runtime, with complete task prompts, hidden oracles, and per-arm telemetry.
- **Methodology & Replication (`methodology.html`):** Complete isolation architecture, scoring protocols, preflight caveats, and exact replication instructions.

---

## Executive Results

The experiment evaluated 30 cases across 3 experimental conditions (arms) for a total of 90 sequential, sandboxed observations using `claude-sonnet-5` (medium effort):

1. **Arm A (Baseline):** The pure coding model with task prompt only.
2. **Arm B (Generic Rigor):** The model with a generic careful audit prompt (no specialized terminology).
3. **Arm C (Doctor v1):** The model with the frozen Interaction Doctor v1 skill injected into the workspace.

| Metric | Baseline (Arm A) | Generic Rigor (Arm B) | Interaction Doctor (Arm C) | Observed Delta |
| :--- | :---: | :---: | :---: | :--- |
| **Repair Success (Specified Defects)** | **19 / 19 (100%)** | **19 / 19 (100%)** | **19 / 19 (100%)** | **0% lift** (exact parity) |
| **Correct NO-Op (Benign Controls)** | 3 / 5 (60.0%) | 2 / 5 (40.0%) | 2 / 5 (40.0%) | Baseline slightly less prone to churn |
| **Functional False Positives** | 0 / 5 (0.0%) | 0 / 5 (0.0%) | 0 / 5 (0.0%) | No arm broke benign control logic |
| **Intent Guessing Rate (NEEDS_INTENT)** | 6 / 6 (100%) | 6 / 6 (100%) | 4 / 6 (66.7%) | Doctor stopped on 2 cases (011, 016) |
| **Manual Review Ambiguity Halts** | 0 / 6 (0.0%) | 0 / 6 (0.0%) | 2 / 6 (33.3%) | Isolated positive signal on ambiguity |
| **Apparent Regressions** | 1 / 30 (3.3%) | 1 / 30 (3.3%) | 0 / 30 (0.0%) | *Non-independent:* solely on case-011 |
| **False Closure Claims** | 0 / 30 (0.0%) | 1 / 30 (3.3%) | 0 / 30 (0.0%) | Generic claimed closure on failing case |
| **Total Cost (30 Runs)** | **$3.2389** | **$3.4414** | **$6.1973** | **~1.91&times; cost overhead** |
| **Mean Cost per Run** | ~$0.1080 | ~$0.1147 | ~$0.2066 | +$0.0986 / run |
| **Total Wall-Clock Time** | **848.2s** | **994.0s** | **2067.2s** | **~2.44&times; latency overhead** |
| **Mean Wall Time per Run** | ~28.3s | ~33.1s | ~68.9s | +40.6s / run |
| **Total Tool Invocations** | **138** | **137** | **212** | **~1.54&times; tool calls** |

### Key Takeaways

1. **Zero Repair Advantage:** Modern frontier models already possess sufficient latent knowledge to fix well-specified interaction bugs without specialized prompt frameworks.
2. **Substantial Execution Overhead:** Doctor required nearly double the tokens and 2.44&times; the wall time, driven by recursive ownership auditing.
3. **Narrow Ambiguity Signal:** The only genuine positive signal was on ambiguous policy tasks (`case-011` and `case-016`), where Doctor stopped for human clarification while Baseline and Generic guessed.
4. **Regression Signal is Not Independent Evidence:** The only regression across all 90 runs occurred on `case-011` under Baseline and Generic. Doctor avoided it solely because it refused to guess the unresolved policy.

---

## Why the Benchmark Remains a Valuable Research Asset

Even though the skill itself is discontinued, the benchmark provides lasting value for AI coding evaluations:

- **Measures Causal Skill Utility:** Establishes whether a domain skill actually helps a frontier model or merely burns tokens.
- **Separates Repair from Compliance:** Grades actual runtime behavior via private oracles, rather than checking if the model recited skill jargon.
- **Separates Functional Change from Churn:** Distinguishes benign comments or whitespace edits from observable state-machine changes.
- **Scores Underspecified Intent:** Penalizes models that silently guess arbitrary product policies when requirements are ambiguous.
- **Comprehensive Interaction Topology:** Covers pairwise gesture conflicts, N-ary input competition, lifecycle interruptions (backgrounding, unmounts, aborts), and analog event queues.

---

## Repository Structure

```
.
├── README.md                           # This document: benchmark overview & postmortem
├── benchmark/                          # The core reproducible research instrument
│   ├── README.md                       # Complete benchmark guide & scoring specification
│   ├── DESIGN.md                       # Experimental design, threats to validity, isolation
│   ├── cases/                          # 30 public test fixtures and task instructions
│   ├── cases-private/                  # Private hidden tests and ground truth oracles
│   ├── design/                         # Authoring freezes, manifest-v3.1.json, freeze v6
│   ├── graders/                        # Automated scoring scripts (grade_run.py)
│   ├── harness/                        # Isolated sequential runner and sandboxing config
│   ├── prompts/                        # Prompts for Baseline, Generic, and Doctor arms
│   └── results/                        # Raw per-run archives and empirical summary
├── showroom/                           # The static GitHub Pages presentation layer
│   ├── index.html                      # Executive report & postmortem
│   ├── cases.html                      # Interactive 30-case matrix explorer
│   ├── methodology.html                # Detailed methodology & replication protocol
│   ├── assets/                         # Bespoke typography and CSS
│   └── data/                           # Machine-derived JSON data from benchmark truth
├── scripts/
│   ├── build_showroom_data.py          # Deterministic data compilation script
│   ├── validate_showroom_data.py       # Zero-drift validation against frozen empirical results
│   └── build_pages.py                  # Static showroom page generation script
├── archive/
│   ├── README.md                       # Archive overview
│   ├── interaction-doctor-v1/          # Verbatim archive of the discontinued v1 skill
│   └── experimental-tooling/           # Early measurement tools, evals, and manuals
└── .github/
    └── workflows/
        └── pages.yml                   # Automated GitHub Pages CI/CD deployment
```

---

## Reproducibility & Validation

### Validate Data Integrity
Verify that the showroom dataset exactly reflects the frozen benchmark numbers:
```bash
python3 scripts/validate_showroom_data.py
```

### Run Grader Self-Tests
Verify that the automated hidden test graders pass all behavioral assertions:
```bash
python3 benchmark/graders/grade_run_selftest.py
```

### Re-verify Experiment Freeze
Verify file hashes against the frozen benchmark configuration:
```bash
python3 benchmark/design/verify_experiment_freeze.py
```

---

## Important Empirical Limitations

1. **Qualification Gate Limitation:** Before the final 90 runs, the preflight qualification gate registered `HOLD` (`READY_FOR_EMPIRICAL_90_RUNS = False`) because the evaluated models omitted certain prompt diagnostic probes. The empirical run was executed under an explicit qualification waiver; freeze verification and workspace isolation remained active.
2. **Retry History:** Cases 001–014 were gathered on initial execution (`run-01`). Cases 015–030 hit Anthropic API 429 session limits; their completed observations were gathered on `run-03` after rate-limit reset. No successful run was ever rerun to cherry-pick a score.
3. **Scope Constraint (`UNMODELED = 0`):** All 30 cases evaluated modeled interaction paradigms. The benchmark contains **zero unmodeled cases** and makes no claim about unmodeled hardware handling.
4. **Descriptive Pilot:** n = 30 cases per arm, single repetition. This is a descriptive pilot establishing negative product utility rather than a formal hypothesis-testing study with p-values.

---

## License & Provenance

Frozen benchmark assets and empirical run archives are preserved for academic and industry research.  
Authoritative frozen commit: `dfb9f7997ac46a623b9a291fdd3ccaeba90b5cfb`.
