# Game of Thrones: Dragonfire knowledge base

This repository contains an AI-oriented reference for dragon army formation recommendations.

## Contents

- [`wiki/`](wiki/) — human-readable mechanics and dragon reference pages.
- [`data/`](data/) — normalized JSON suitable for retrieval and programmatic reasoning.
- [`data/recommendation_rules.json`](data/recommendation_rules.json) — machine-checkable formation constraints, decision flow, comparison axes, and benchmark anti-overfitting rules.
- [`data/common_formations.json`](data/common_formations.json) — user-confirmed common formations that must be considered as equal-footing recommendation baselines when applicable.
- [`data/dragon_application_knowledge.json`](data/dragon_application_knowledge.json) — the canonical installed-client roster, level curves, Star scalars, ability templates, and evidence status for 38 production-named dragons.
- [`data/installed_evidence.json`](data/installed_evidence.json) — dated installed-client observations and lifecycle classifications that must not be mistaken for live or screenshot-audited behavior.
- [`wiki/client-updates/`](wiki/client-updates/) — durable summaries of local installed-client comparisons; raw snapshots remain ignored.
- [`wiki/Online-Sources.md`](wiki/Online-Sources.md) — dated official/community source audit and unresolved public rules.
- [`projects/game-data-encyclopedia/`](projects/game-data-encyclopedia/) — searchable static encyclopedia implementation for dragons, abilities, effects/statuses, evidence, and progression gates.
- [`projects/recommendation-planner/`](projects/recommendation-planner/) — deterministic mixed-progression formation search, mandatory common-baseline ledger, Pareto comparison, timing analysis, and evidence trace; it also supports consolidated, validated multi-matchup reports with explicit roster scope and dragon-reuse policy.
- [`projects/combat-report-extractor/`](projects/combat-report-extractor/) — local-only combat-report video OCR, blue/red ownership classification, auditable action normalization, deduplication, and visible-value insight reports.
- [`review/`](review/) — extraction questions that require human confirmation.
- [`Dragon_Specs/`](Dragon_Specs/) and [`Game_Details/`](Game_Details/) — source screenshots.

## Data policy

- In-game names and ability text are transcribed exactly as displayed.
- The newest available screenshot is authoritative when sources conflict.
- Ambiguous text is flagged for review rather than silently inferred.
- Player-progression values shown on `*_basics` screenshots are historical snapshots,
  not cross-player facts. Recommendations instead use the client-derived level curve
  for the reported dragon level, and keep Star Rank separate from level and Habit
  skill levels.
- Full Habit upgrade tracks shown in the star-rank screenshots are durable ability
  definitions and are retained.
- Official web guides may supplement system-level rules. Incomplete official dragon
  profiles are included as client-discovered records and never silently promoted to
  screenshot-complete records.
- Unchanged logical resources in a newer installed snapshot remain continuing client
  evidence; the canonical index records the snapshot/build and source resource versions.

## Formation model

A formation has three positions: `left_flank`, `vanguard`, and `right_flank`.
Each position contains one dragon, while one troop-type choice applies to the complete
three-dragon formation. Vanguard abilities apply only when their dragon occupies the
vanguard unless their text says otherwise. Opposing lanes align by matching position
name rather than mirroring: left targets left, vanguard targets vanguard, and right
targets right for default and same-lane attacks unless explicit targeting or another
mechanic redirects them.
See [`wiki/Game-Mechanics.md`](wiki/Game-Mechanics.md) for the source-audited system rules.

## Game-Data Encyclopedia

Build and test the first static vertical slice with:

```powershell
python projects/game-data-encyclopedia/scripts/build.py
python -m unittest discover -s projects/game-data-encyclopedia/tests -v
```

The deployed artifact is designed for `/encyclopedia/` alongside the existing map.
It reads only compact generated data; ignored local snapshots are not a runtime input.

Regenerate the canonical installed-client index from an explicit dated capture (the
source path is required so the historical working set cannot silently replace newer
evidence):

```powershell
python Game_Details/Resources/_build_dragon_application_knowledge.py `
  --resources Game_Details/Resources/_snapshots/2026-10-01/android_data/com.wb.goog.hotd.socialstrategy/files/Resources `
  --snapshot-manifest Game_Details/Resources/_snapshots/2026-10-01/analysis/snapshot_manifest.json
```

Compare any two captured `Resources` directories and produce logical-resource, row,
localization, and repository-consumer impact reports with:

```powershell
python Game_Details/Resources/analyze_update.py `
  --old <old-Resources-directory> `
  --new <new-Resources-directory> `
  --output Game_Details/Resources/_snapshots/<date> `
  --snapshot-date <YYYY-MM-DD> `
  --old-client-version <version> `
  --new-client-version <version> `
  --old-version-code <code> `
  --new-version-code <code>
```

The impact report routes review work; it never edits canonical data or promotes staged
client content to live behavior.
