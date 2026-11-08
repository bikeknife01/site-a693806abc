# 08 — Validation and test plan

## Test matrix

| Level | Cases | Gate |
|---|---|---|
| Static/build | C++20/MSVC x64, CMake, warning-as-error targeted modules, no `WriteProcessMemory`/write-right tokens in compiled acquisition source, MIT notice and pinned hash | Build and read-only policy pass |
| Unit (mock provider) | Exact-length reads, null/zero/overflow ranges, cross-page reads, partial failure with untouched caller output, big-page translation, bank holes, stale root, 32/64-bit pointers, cache invalidation, cancellation, typed errors | Deterministic pass; sanitizers/fuzz corpus for malformed ELF/page tables |
| Identity/integration | Duplicate/missing display name, index reuse, PID reuse with new creation time, changed command line, wrong package, ambiguous module, app restart, VM restart, update | No cross-instance or stale read accepted |
| Storage/parser | Interrupted writes, duplicate sequence, hash mismatch, quota reached, schema migration, parser rerun and lineage drill-down | Recoverable store; every event field links to bytes or is null |
| Load/fault | 1, 2, 4, 8 supported instances; page failure, VMM exit, ADB unavailable, queue saturation, disk full, slow writer, cancellation | Independent worker failure, explicit drops, bounded resource use |
| Combat validation | Three or more controlled battles plus idle controls, independent event annotations, duplicate/ring tests, app and VM restart, new build | Confidence and completeness report; no unsupported field claimed |

## Measurement protocol

Capture baseline without collector, then collector with an idle configured worker, then active sampling under the same game activity and graphics settings. At each 1/2/4/8-instance level (only with authorized research instances), record p50/p95/p99 read latency, reads/s, bytes/s, guest translation time, host CPU, collector private bytes, handle count, queue depth/drops, disk write rate, emulator frame-time distribution and app stability. Run at least 30 minutes per stage for initial budget setting and 24 hours for M5 soak; M8 requires 72 hours. Repeat after app and MuMu updates. Use OS performance counters/ETW and MuMu's own observable metrics where available; label measurement source. Do not invent throughput or assert no detection.

Initial **acceptance targets to validate**, not measured results: zero cross-instance reads and zero silent drops; 100% rejection of tested stale generations; no monotonic unbounded growth of handles/private bytes; p95 sampling latency below half the configured interval; queue stays under 80% capacity in steady state; frame-time p95 increase under 5% relative to matched baseline; CPU and bytes/s within user-configured per-instance limits. If baseline noise obscures 5%, report confidence interval and defer the performance gate. Recovery target: worker resumes within 60 seconds after a normal restart, with the gap explicitly recorded. Targets may be revised only with measured evidence and a documented reason.

Fault injection must never patch the game or VMM. Use mocks for corrupt tables, partial reads and PID reuse; use ordinary `TrikePistol` lifecycle events for live restart tests. A protection or access failure is a test result, not a reason to bypass it. Preserve benchmark config, source hashes, raw metrics and plots locally; publish only sanitized aggregate results.
