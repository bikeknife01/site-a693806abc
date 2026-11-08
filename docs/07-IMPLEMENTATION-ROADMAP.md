# 07 — Implementation roadmap

Each milestone is a stop/go gate; failure does not automatically trigger a more invasive technique. Outputs are local and ignored until reviewed. A separate coding agent should implement milestones in order and consult the detailed contracts in [03](03-SYSTEM-ARCHITECTURE.md), [05](05-DATA-MODEL-AND-STORAGE.md), and [08](08-VALIDATION-AND-TEST-PLAN.md).

| Milestone | Prerequisites and tasks | Output and acceptance | Failure, risk, next dependency |
|---|---|---|---|
| **M0 reference audit** | Pin source/license; review host rights, RAM inference, page walk, bounds, lifecycle, concurrency; inventory local MuMu. | This audit and defect ledger; environment facts marked observed/unverified. | Unpinned source or unsupported claims fail M0. M1 uses chosen fork. |
| **M1 read-only access** | Exact `TrikePistol` binding; fork source; remove all write API/code/rights, add checked reads/errors, RAII and cancellation; create CMake/MSVC x64 build. | Unique target and reproducible ≤4 KiB non-sensitive read, verified across repeated reads; stale read rejected after restart; no write rights in handle. | NO GO on ambiguous mapping, access denied without acceptable privilege, bad translation, or protection requiring evasion. M2 requires M1. |
| **M2 repeatable observations** | M1; versioned config; bounded selected-range sampler, raw recorder and provenance. | At least three repeatable timed sessions with exact status, sequence, bytes/hash, mapping generation and no unexplained loss. | Partial reads, unbounded memory/disk, or missing lineage fail. M3 needs raw data. |
| **M3 controlled discovery** | M2; phase ledger, idle controls, bounded region comparisons and candidate registry. | At least one candidate with repeatable activity correlation and explicit competing hypotheses, or a documented negative result. | No discriminative data or too-short lifetime is a valid NO GO for event extraction. M4 requires validated candidate. |
| **M4 event parser** | Corroborated structure and independent visible references. | Deterministic versioned parser, raw span links, null unknowns, duplicate/gap accounting, repeated-trial agreement. | Confounded semantics, unacceptable false positives or no boundary evidence fail. M5 needs a stable target. |
| **M5 continuous acquisition** | M4; per-instance worker, bounded queue/storage, metrics, shutdown/recovery. | 24-hour single-instance soak within measured budgets, explicit drops, no stale-sample acceptance, graceful drain. | Frame-time degradation, resource growth or silent gaps fail. M6 depends on stability. |
| **M6 multiple instances** | M5; dynamic inventory and exact PID binding; independent workers. | 1/2/4/8-instance staged benchmark where available, no cross-instance reads, independent failure/restart; unsupported scale levels explicitly recorded. | PID ambiguity or resource overload blocks the corresponding scale level. M7 may proceed on supported levels. |
| **M7 analysis tools** | M4 validated events and M5 durable store. | Reproducible Python reports with observation drill-down, coverage and version filters; Parquet export tested. | Unsupported fields/aggregates fail review. M8 needs report quality. |
| **M8 hardening** | M5–M7; fault injection, update drift, retention, documentation. | 72-hour soak at supported scale, leak/error budget met, clean recovery and reproducible build; signed-off maintenance guide. | Regression or unknown update behavior returns to M1/M3 gate. |

## Implementation order within M1

1. Vendor pinned source under a third-party directory with MIT notice and a patch log; do not copy the ignored clone into Git accidentally.
2. Delete `write<T>`, `writeBytes`, `writeBytes_`, `physWr_`, `hostWr_` and `WriteProcessMemory`; open exact PID with query/read rights only. Static source scan and a Windows handle-rights test gate this change.
3. Add `IHostMemoryReader` and a fake implementation; test translation, bank bounds, partial reads and stale generation without MuMu.
4. Add explicit CLI-instance binding and process creation-time checks. Disallow name/biggest-RAM auto-attach.
5. Build a one-shot diagnostic executable with a fixed tiny read cap, no persistence of arbitrary bytes, and a machine-readable test report. Only then run live M1 on `TrikePistol`.

No production service, automatic battle control, or canonical Dragonfire data edits are part of this planning phase.
