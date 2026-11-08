# 09 — Open questions and assumptions

| ID | Unknown / hypothesis | Smallest resolving experiment | Consequence if false |
|---|---|---|---|
| Q1 | Does MuMu 6.8.5.0 keep guest RAM in CLI-reported `MuMuNxDevice.exe` PID's readable address space? | M1 read-only exact-PID attach, inspect bounded host regions and known guest module bytes. | NO GO for this backend. |
| Q2 | Does upstream IA-32e root/bank inference work with this Hyper-V-enabled Android 15 instance? | One capped discovery with logs and independent known-byte cross-check. | Rework provider or NO GO; no broad blind scans. |
| Q3 | Can one discovered root be tied uniquely to package/PID 6238 (transient) rather than another guest process? | Compare module inventory, mapping fingerprint, process lifecycle and read-only Android metadata across restart. | No accepted samples until binding is unique. |
| Q4 | Does least-privilege query/read access work without elevation/debug privilege? | Exact-PID open on local host, first unprivileged then documented elevation only if needed. | Operational restriction or NO GO; do not silently request write rights. |
| Q5 | Are useful battle events retained in accessible memory, and for how long? | M3 bounded idle/combat/report windows with timestamped independent annotations. | Stop event-extraction work; retain negative result. |
| Q6 | Are candidate structures stable across battles, restarts and app versions? | Three battles, app/VM restart, then new-build rerun with structural locator. | Version-specific experimental parser only; no continuous claim. |
| Q7 | Can event order, duplicates and completeness be established? | Deliberate repeated visible actions, varying poll interval, gap/wrap tests. | Report partial observations and coverage bounds, not totals. |
| Q8 | Is `MuMuNxDevice.exe` one-to-one with each instance at 2/4/8 scale? | Start only additional authorized research instances; compare CLI PID, creation time, command line and handles. | Revise identity resolver; never choose by RAM size. |
| Q9 | Can polling meet frame-time and CPU budgets? | Matched baseline/active benchmark in [08](08-VALIDATION-AND-TEST-PLAN.md). | Reduce scope/frequency or NO GO for continuous mode. |
| Q10 | Can host-side observation be detected by client/emulator safeguards? | No reliable proof of nondetection is planned or claimed; observe only ordinary stability and errors. | Record residual uncertainty; never add concealment or bypass. |

Assumptions for design, not established facts: current MuMu CLI remains available; instance names are user-controlled safety labels; Android process ABI may differ from guest ABI list; the memory provider may require a new acquisition generation on every restart; and useful combat data may be absent. The current GO/NO-GO state is in [MASTER-PLAN](MASTER-PLAN.md).
