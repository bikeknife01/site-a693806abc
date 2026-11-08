# 06 — Offline analysis and event reconstruction

Python 3.12+ tooling reads only the local observation store. Use Polars or Pandas for tabular exploration, PyArrow for Parquet exports, SQLite for lineage queries, and Jupyter for reviewable experiments. Streamlit is optional after the core analysis is reproducible from scripts. Pin package versions and record input hashes.

## Memory observation analysis

Join observations to experiment phase annotations by monotonic time within the same generation. Produce per-candidate read success, changed-byte count, digest transition, entropy, update cadence, lifetime and gap rate. Compare idle and combat windows of equal duration; compute lagged correlation with independently annotated actions and a shuffled-time control. Search candidate strings/numbers only in preapproved byte windows and record encoding, endianness, range, alignment and number of hypotheses tested. Plot candidate stability across battles, restarts and builds. A correlation plot is exploratory evidence, not a field definition.

## Reconstruction pipeline

1. **Segment:** identify battle boundaries from validated state transitions or, until then, independently annotated phase boundaries. Do not infer a battle ID from proximity alone.
2. **Decode:** apply a versioned parser only to an approved candidate structure. Preserve raw bytes/hash and offsets. Report unknown fields.
3. **Order:** prefer an observed sequence counter; otherwise use acquisition monotonic intervals and label ties/uncertainty. Host polling time is not automatically game event time.
4. **Deduplicate:** distinguish an unchanged record from a new record with identical values using validated slot generation/counter semantics. If unknown, report both candidate interpretations.
5. **Wrap and gaps:** detect ring-buffer wrap only with counter/slot evidence; flag overwritten, inaccessible or missed intervals. Report lower bound of events seen, not an invented total.
6. **Normalize:** map actor, target, ability, damage, healing, shield, status, duration, stacks and critical indicators only when bytes and independent corroboration support each field. Store a separate evidence link per interpreted claim.
7. **Audit:** reparse the same raw input deterministically with parser hash; diff output across parser versions and keep prior interpretations.

## Completeness and confidence

For each battle report `observed_events`, `candidate_slots`, `poll_gaps`, `unreadable_samples`, `estimated_overwrite_risk`, and `independently_observed_reference_events`. Calculate precision/recall only where the independent reference itself is sufficiently complete; otherwise publish coverage bounds and examples. Confidence classes: `raw` (bytes only), `candidate` (repeatable structure), `corroborated` (matched to independent visible outcomes in repeated trials), `accepted` (reviewed stable parser), and `disputed`. A relationship between exposure and outcome remains correlation unless a controlled comparison supports causality.

Validated events can support damage distributions, activation frequency, healing/mitigation, effect duration and timing comparisons by battle/instance. Each aggregate must expose event IDs and a drill-down query to observation IDs and raw byte spans. Publish version and coverage filters with every chart; never merge unlike builds or unknown completeness silently. The existing Dragonfire combat-report OCR and empirical findings remain separate evidence streams and retain their own gates.
