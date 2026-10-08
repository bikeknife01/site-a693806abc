# Combat rule candidate review

An ordinary `interpret` run writes `rule-candidates.json` beside the enriched report.
This file is a local review queue, not canonical knowledge. Counts distinguish
occurrences, distinct report IDs, and distinct formation signatures. Listed source
events are alternatives active in the bounded timing window; their presence is not a
causal attribution.

The queue also contains `formation_contexts` and `canonical_source_clues`. These map
displayed abilities from both sides to exact commands, Vanguard abilities, and Habits in
`data/dragons/*.json`. PvE actor labels can be role labels: for example, a uniquely owned
Command can identify the canonical dragon even when the card header does not name it.
Related Habit wording that explicitly extends the displayed Command is included. These
are deterministic source clues, not automatically accepted rules.

Before proposing a rule, inspect every cited retained frame, preserve exact report
wording, identify coverage warnings, compare the clue against every compatible user and
enemy formation ability, and seek a distinct report or formation when the same card is
not explicit. Missing text is not proof that a chance-based trigger failed. Candidate
generation therefore proposes only `timing_correlation` or `unresolved` relationships.

To turn one selected queue item into a caller-chosen draft file:

```powershell
python projects/combat-report-extractor/combat_report_interpreter.py propose `
  --candidates '<run>\rule-candidates.json' `
  --candidate 'candidate.0123456789abcdef' `
  --output '<review-folder>\candidate-proposal.json'
```

The command writes a fragment with `status: draft`, review placeholders, limitations,
and observation templates. It never edits `data/combat_report_rules.json` or
`data/combat_report_observations.json`. A reviewer must separately curate portable
observations, validate canonical dragon/ability names, add negative-match tests, and
explicitly stage any canonical change.
