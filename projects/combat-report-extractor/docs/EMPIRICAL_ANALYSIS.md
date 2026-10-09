# Combat empirical analysis workflow

This layer turns interpreted local reports into scoped measurements that can eventually
inform formation recommendations. It does not replace canonical dragon wording and does
not treat correlation as causation.

## One recording

```powershell
.\ingest-combat-report.ps1 'C:\path\to\report.mp4' `
  -Experiment 'stable-experiment-id' `
  -Variant 'baseline' `
  -Question 'The uncertainty this recording tests'
```

The command extracts and interprets the report, then writes
`combat-measurements.json` and `combat-measurements.md` beside the existing ignored
outputs. The measurement contains scheduled, observable, and unknown RNG opportunities;
activations grouped by source event; advertised chance when canonical; effect exposure
windows and inferred persistent stacks; and damage/Recovery samples annotated with
active exposures.

An observable rate is a complete per-report denominator only when coverage is clean and
every scheduled opportunity has positive evidence that the source actor was active.
Missing report text is not a failed activation.

## Repeated experiment

Use the same experiment ID for comparable repeats and stable variant labels:

```powershell
python projects/combat-report-extractor/combat_empirical_analyzer.py aggregate `
  --measurement '<run-one>\combat-measurements.json' `
  --measurement '<run-two>\combat-measurements.json' `
  --experiment 'stable-experiment-id' `
  --output '<ignored-experiment-folder>'
```

The deterministic outputs preserve report hashes, variants, observed numerators and
denominators, unknown opportunities, and a 95% Wilson interval. The interval measures
sampling uncertainty only; it does not repair coverage or confounding.

## Additive or diminishing effects

An outcome during an exposure is an exposure-correlated sample. Estimate an effect only
from like-for-like baseline and changed variants that account for progression, troop
type and surviving count, enemy, target, lane, round, overlapping effects, coverage,
and sample size. Otherwise retain the sample without stating an isolated contribution.

## Review and curation

```powershell
python projects/combat-report-extractor/combat_empirical_analyzer.py propose `
  --aggregate '<ignored-experiment-folder>\combat-experiment.json' `
  --trial '<trial-id>' `
  --output '<ignored-review-folder>\empirical-finding-proposal.json'
```

The proposal is always draft and excluded from recommendations. Reviewed trial
definitions live in `data/combat_trial_definitions.json`; explicitly curated aggregates
live in `data/combat_empirical_findings.json`. A finding may be recommendation-eligible
only when accepted, corroborated, scoped, linked to reviewed observations, and approved
through the Strategist gate.

## Strategist handoff

```powershell
python projects/combat-report-extractor/combat_empirical_analyzer.py handoff `
  --finding '<accepted-finding-id>' `
  --target-file 'data/recommendation_rules.json' `
  --test-command 'python -m unittest discover -s projects/combat-report-extractor/tests -v' `
  --confirm-reviewed-finding `
  --output '<ignored-review-folder>\strategist-handoff.json'
```

The handoff is a proposal and performs no automatic Strategist or recommendation-data
edits. The Strategist reads only canonical findings already marked accepted,
corroborated, recommendation-eligible, and approved.
