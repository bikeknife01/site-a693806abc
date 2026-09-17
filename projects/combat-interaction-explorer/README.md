# Combat Interaction Explorer

Dependency-free static combat timing explorer. The first slice supports two three-dragon
formations, fixed lanes, level/Star/Vanguard eligibility, shared troop context, stable
scenario URLs, a ten-round schedule, lane-aware target candidates, conservative status
state/expiry projections, probability branches, instant Recovery interactions that stay
out of persistent status state, and links to Encyclopedia evidence.

It deliberately does not claim exact damage, action order, target selection, chance
outcomes or status state before those mechanics are implemented and validated.

## Build and test

```powershell
python projects/combat-interaction-explorer/scripts/build.py
node --test projects/combat-interaction-explorer/tests/engine.test.mjs
```

The build consumes the generated normalized dataset at
`projects/game-data-encyclopedia/public/data/encyclopedia.json` and writes `dist/`.
