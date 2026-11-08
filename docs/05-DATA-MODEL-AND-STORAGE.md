# 05 — Data model and storage

## Storage layers

Use SQLite (WAL) for sessions, instance/process generations, candidate definitions, observations, normalized events and evidence links. Use JSONL for bounded experiment annotations and portable parser/debug output. Store selected bounded raw byte windows in content-addressed compressed blobs only when necessary; SQLite rows reference hash, offset, length and retention class. Export validated analytical tables to Parquet through an offline batch job. Avoid a continuous process-memory dump. All raw research data lives in ignored local snapshots; only sanitized reviewed findings may enter repository data through the existing separate review gate.

## Core relational contract

| Table | Essential columns |
|---|---|
| `session` | `session_id`, UTC start/end, monotonic epoch, collector/source revision, config hash, experiment ID, status |
| `instance_generation` | `generation_id`, session ID, exact display name, inventory ID/index, VMM PID + creation time + image hash/path, guest Android/ABI, endpoint reference, game package/PID/version, candidate root fingerprint, validation status |
| `candidate` | `candidate_id`, locator specification/version, memory region/range class, discovery evidence, status/confidence, approved max length and interval |
| `observation` | `observation_id`, generation ID, sequence, UTC and monotonic acquisition timestamps, candidate ID, VA/range and mapping generation, requested/received bytes, status/error, blob hash or digest, parser version nullable, validation status, confidence, drop/gap flags |
| `event` | `event_id`, battle ID nullable, proposed sequence/time range, actor/target/ability/type and outcome fields nullable, confidence, parser version, validation status |
| `event_evidence` | event ID, observation ID, byte span, rule/version, interpretation note |
| `health_interval` | generation ID, start/end, attempts/successes/drops, bytes, CPU/memory, queue high-water, latency and frame-time aggregates |

Use UUIDs or collision-resistant IDs and foreign keys. `sequence` is monotonic per generation; a new process/root starts a new generation. Store UTC for cross-machine joins and monotonic time for ordering and latency. An event time is an interval unless a timestamp is actually present in validated data. Preserve unknown as NULL, never zero. Every normalized field may carry its own evidence and confidence; a partially decoded event is allowed, but unsupported fields remain null. Event records are immutable across parser revisions: reparse into a new version and retain lineage.

The proposed event payload contains nullable `battle_id`, `event_sequence`, `event_time_start/end`, `actor_id`, `target_id`, `ability_id`, `event_type`, `damage`, `healing`, `shielding`, `status_applied`, `status_removed`, `duration`, `stack_count`, and `critical_hit`. Each has a field-level `status` (`unknown`, `candidate`, `corroborated`, `accepted`, `disputed`) and evidence reference. `battle_id` may be an experiment-local label until a native identifier is decoded. Numeric values carry unit and signedness; effects carry source text/ID when available. Avoid filling fields from canonical dragon profiles when memory data lacks them.

## Retention and privacy

Suggested starting limits for M2, configurable downward: 4 KiB per read, 1 MiB/s per instance, 256 MiB raw blobs/session, 1 GiB aggregate local research quota, and seven days raw retention. These are *safety caps*, not proven performance budgets. Stop collection before quota exhaustion and write a `BudgetExceeded` interval. Keep summaries and hashes longer only if they contain no sensitive bytes; purge raw blobs via explicit retention jobs with audit entries. Encrypt local research store if host policy requires it, restrict filesystem ACLs, and redact incidental account identifiers/tokens. Do not place raw private memory or traffic in Git.

## Example observation envelope

```json
{"observation_id":"uuid","session_id":"uuid","generation_id":"uuid","seq":42,"host_utc":"2026-10-16T00:00:00Z","monotonic_ns":123456789,"candidate_id":"candidate-v1","mapping_generation":3,"range":{"va":"0x...","length":128},"status":"complete","bytes_read":128,"blob_sha256":"hex","parser_version":null,"confidence":"unclassified","validation_status":"raw"}
```

This is a schema example, not an observed record. Parquet exports include event/evidence keys so every aggregate can be traced to observations and their original acquisition context.
