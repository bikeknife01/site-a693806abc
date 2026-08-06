# Game of Thrones: Dragonfire knowledge base

This repository contains an AI-oriented reference for dragon army formation recommendations.

## Contents

- [`wiki/`](wiki/) — human-readable mechanics and dragon reference pages.
- [`data/`](data/) — normalized JSON suitable for retrieval and programmatic reasoning.
- [`data/live_updates.json`](data/live_updates.json) — official additions awaiting full screenshot extraction.
- [`wiki/Online-Sources.md`](wiki/Online-Sources.md) — dated official/community source audit and unresolved public rules.
- [`review/`](review/) — extraction questions that require human confirmation.
- [`Dragon_Specs/`](Dragon_Specs/) and [`Game_Details/`](Game_Details/) — source screenshots.

## Data policy

- In-game names and ability text are transcribed exactly as displayed.
- The newest available screenshot is authoritative when sources conflict.
- Ambiguous text is flagged for review rather than silently inferred.
- Player-progression values shown on `*_basics` screenshots (Strength, Intelligence,
  Instinct, Initiative, Stamina, level, XP, and current army size) are not treated as
  general dragon characteristics and are excluded from recommendation logic.
- Full Habit upgrade tracks shown in the star-rank screenshots are durable ability
  definitions and are retained.
- Official web guides may supplement system-level rules. Incomplete official dragon
  profiles are tracked separately and never silently promoted to screenshot-complete records.

## Formation model

A formation has three positions: `left_flank`, `vanguard`, and `right_flank`.
Each position contains one dragon, while one troop-type choice applies to the complete
three-dragon formation. Vanguard abilities apply only when their dragon occupies the
vanguard unless their text says otherwise. Opposing lanes align by matching position
name rather than mirroring: left targets left, vanguard targets vanguard, and right
targets right for default and same-lane attacks unless explicit targeting or another
mechanic redirects them.
See [`wiki/Game-Mechanics.md`](wiki/Game-Mechanics.md) for the source-audited system rules.
