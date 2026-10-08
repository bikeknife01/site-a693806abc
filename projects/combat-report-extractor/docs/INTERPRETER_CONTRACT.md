# Combat Analyst deterministic boundary

The interpreter accepts extractor reports with schema version `1.0.0`. It never
changes an input action. Each enriched event contains the original action under
`source_action` and receives an ID constructed as:

```text
event.<first 16 hex characters of SHA-256(canonical input report)>.<zero-based position, six digits>.<first 12 hex characters of SHA-256(canonical action)>
```

Canonical JSON uses UTF-8, sorted object keys, compact separators, and preserves list
order. Generated lists are ordered by input position, then stable rule or candidate ID.
No generated file contains a run timestamp. Consequently, identical reports, rules,
and observations produce byte-identical outputs.

The fixture `tests/fixtures/combat_report_v1.json` locks the existing extractor
boundary. `tests/fixtures/interpreter_synthetic.json` deliberately includes source
activations, separately reported results, an ambiguous result, and an unmatched result.
It is synthetic evidence and does not establish a game mechanic.

Recordings, extracted frames, OCR manifests, and generated runs remain excluded by the
repository ignore rules. Test fixtures contain only synthetic or already-minimized
extractor data.
