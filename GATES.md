# Distillation evasion harness — GATES
Pre-registered before any run (global rule 8). The register is PROTOCOL.md (charter 3.1). This file
records the frozen version and its commit hash; a change to any threshold is a sign-off gate.

| Version | Frozen on | Commit | Signed off by |
|---|---|---|---|
| v1.0 | 2026-11-10 | 3df33c3 | Glen (chat, "accept all recommendations") |
| v2.0 (PROTOCOL_v2.md; supersedes v1.0) | 2026-11-11 | 7fd6ee4 | Glen (chat, "proceed with your recommendations") |

Too-good stop rule (charter 3.8): pause if any AUC ≥ 0.95, any result ≥ 0.05 AUC over its
pass threshold, any detector at exactly 0% or 100% across an entire sweep, or any student score
above the teacher's.

Amendments after freeze are recorded in PROTOCOL.md §10 (A1 to A6 as of 2026-11-11), each with its approving decision; the frozen v1.0 text is otherwise unchanged. A5 and A6 each fix a decision rule before the run it governs.

2026-11-11, decision 32: PROTOCOL v1.0 is superseded by PROTOCOL_v2.md, frozen at 7fd6ee4. v1.0's thresholds and results stand as recorded; v2.0 registers new predictions P1 to P6 before any run under it.

2026-11-12, decision 44: amendment B6 (PROTOCOL_v2.md §10) registers predictions P25 to P36 before any revision analysis runs. Thresholds of v2.0 are unchanged; held-out and sensitivity thresholds are reported beside them, not substituted.
2026-11-12, decision 46: amendment B7 (PROTOCOL_v2.md §10) registers predictions P37 to P42 before any second-round analysis runs. Registered thresholds unchanged; recalibrated thresholds reported beside them.
2026-11-12, decision 47: amendment B8 (P43 to P50) registered before any adversary-pass analysis runs.
2026-11-12, decision 48: amendment B9 (P51) registered before running.
2026-11-13, decision 49: amendment B10 (P52) registered before running.
2026-11-13, decision 50: amendment B11 (P53, P54) registered before running.
2026-11-13, decision 51: amendment B12 (P55, P56) registered before any statistic was computed on the ServeGen traces.
2026-11-13, decision 53: amendment B13 (P57, P58) registered before running.
2026-11-13, decision 54: amendment B14 (P59 to P63) registered before running.
2026-11-13, decision 56: amendment B15 (P64, P65) registered before running.
