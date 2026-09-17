# Counter-Picking Assistant

Dependency-free, evidence-first static matchup planner. Its first slice extracts explicit
enemy damage, harmful-status and Recovery threats, filters to the selected roster, and
returns legal three-dragon formations with lane placement, one shared troop type, exact
counter wording, uncovered-risk disclosure, Encyclopedia links, and Combat Explorer export.

It does not predict wins, invent damage totals, or collapse all contexts into a universal
dragon tier score.

## Build and test

```powershell
python projects/counter-picking-assistant/scripts/build.py
node --test projects/counter-picking-assistant/tests/engine.test.mjs
```
