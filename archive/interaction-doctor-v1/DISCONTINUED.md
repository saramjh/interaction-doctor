# Product Discontinuation Notice: Interaction Doctor v1

**Notice Date:** September 2026  
**Status:** DISCONTINUED / DEPRECATED  

The Interaction Doctor v1 skill preserved in this directory is no longer actively maintained or recommended for production use.

In a 30-case, 90-run empirical controlled benchmark on `claude-sonnet-5`:
- Repair success on defective fixtures: 19/19 (100%) on Baseline vs 19/19 (100%) on Doctor (0% lift).
- Execution cost: $6.20 (Doctor) vs $3.24 (Baseline) (~1.91x cost).
- Wall-clock time: 2067s (Doctor) vs 848s (Baseline) (~2.44x latency).
- Ambiguity handling: Doctor correctly halted on 2/6 cases (011, 016) while baseline guessed on 6/6, but this isolated capability did not justify the heavy cost and latency overhead.

This skill is retained for archival provenance and benchmark reproducibility.
For the active benchmark and evaluation corpus, see `benchmark/` and `showroom/`.
