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
