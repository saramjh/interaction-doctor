# Interaction Doctor Archive

> **STATUS: DISCONTINUED PRODUCT MATERIALS**  
> This directory contains historical and deprecated product materials from the discontinued **Interaction Doctor** project.  
> These assets are preserved for transparency, provenance, and historical research.

---

## Directory Inventory

### 1. `interaction-doctor-v1/`
The frozen, discontinued v1 skill definition. Contains:
- `SKILL.md`: The agent-facing instruction manual and audit protocol.
- `references/`: The 10 formal model specifications (claims, ownership, runtime modeling, intent & ambiguity, closure contract, adversarial validation, etc.).

> **Benchmark Provenance Note:**  
> The benchmark harness (`benchmark/harness/config.py`) references `.claude/skills/interaction-doctor/` at the repository root to verify frozen file hashes against `benchmark/design/experiment-freeze-v6.json`. That root copy is retained byte-for-byte to maintain exact experimental freeze validity. `archive/interaction-doctor-v1/` serves as the public, browsable archive of the discontinued skill.

### 2. `experimental-tooling/`
Early exploratory tools, manual evaluation runs, and documentation created during the initial development of the Interaction Doctor concept (August–September 2026), prior to the creation of the 30-case benchmark:
- `evals/`: Early manual evaluation runs and test subjects.
- `research/`: Device measurement logs across iOS, Android, macOS, and iPadOS.
- `tools/`: Browser-based verification harnesses for gesture conflict testing.
- `demo/`: Broken demonstration UI pages illustrating interaction bugs.
- `CONFLICTS.md`: Comprehensive audit of gesture and pointer conflicts across mobile platforms.
- `interaction-doctor-ops-manual.md` & `interaction-doctor-execution-playbook.md`: Historical operational playbooks.

---

## Why These Materials Are Archived

During controlled empirical evaluation (30 cases, 90 runs), the Interaction Doctor v1 skill failed to improve repair capability over the baseline model while imposing a ~1.91&times; token cost penalty and ~2.44&times; execution latency. Subsequent attempts to mitigate cost through universal semantic eval gates, self-routing, and native static detectors also failed to establish a viable product path.

As a result, all active product development was terminated, and the repository was transitioned into an open benchmark and research asset.
