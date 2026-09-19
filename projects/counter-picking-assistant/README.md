# Counter-Picking Assistant

Dependency-free, evidence-first static matchup planner. It extracts explicit enemy damage,
harmful-status and Recovery threats, filters to the selected roster, evaluates every legal
three-dragon lane permutation, and returns formations with one shared troop type, exact
counter wording, uncovered-risk disclosure, Encyclopedia links, and Combat Explorer export.
The shared browser-local player profile stores owned dragons, levels, Star Ranks, and
per-Habit levels. Each exported dragon entry also includes its array of verified positive
troop affinities as `preferred_troops`. Verified level/Star gates affect eligibility; saved
Habit levels determine documented chance tracks. Rankings expose their contributions from threat coverage,
reliability, timing, explicit producer/payoff chains, lane fit, control, and troop fit.

The assistant treats same-lane pressure, lane/breed priorities, directional Vanguard support,
Round 1-10 schedules, and status prerequisites as evidence. Unknown proc order, damage
formulas, and adjacency geometry remain unresolved rather than being guessed.

Enemy lanes may be left unknown. The result then reports lower input confidence and scores
only documented threats. Two proposed counters can be compared side by side. Real match
outcomes can be saved and exported from browser-local storage under the observed-match
schema; observation records are deliberately marked `scoring_effect: none` and do not alter
recommendations without a separate reviewed calibration change.

It does not predict wins, invent damage totals, or collapse all contexts into a universal
dragon tier score.

## Build and test

```powershell
python projects/counter-picking-assistant/scripts/build.py
node --test projects/counter-picking-assistant/tests/engine.test.mjs
```
