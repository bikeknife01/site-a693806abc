# Game of Thrones: Dragonfire knowledge base

This repository contains an AI-oriented reference for dragon army formation recommendations.

## Contents

- [`wiki/`](wiki/) — human-readable mechanics and dragon reference pages.
- [`data/`](data/) — normalized JSON suitable for retrieval and programmatic reasoning.
- [`data/dragon_application_knowledge.json`](data/dragon_application_knowledge.json) — the canonical installed-client roster, level curves, Star scalars, ability templates, and evidence status for 37 production-named dragons.
- [`wiki/Online-Sources.md`](wiki/Online-Sources.md) — dated official/community source audit and unresolved public rules.
- [`projects/game-data-encyclopedia/`](projects/game-data-encyclopedia/) — searchable static encyclopedia implementation for dragons, abilities, effects/statuses, evidence, and progression gates.
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
