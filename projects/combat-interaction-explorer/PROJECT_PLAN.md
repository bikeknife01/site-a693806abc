# Combat Interaction Explorer

## Project description

Build an explainable, round-by-round interaction viewer for Dragonfire combat. The first version models declared mechanics—timing, targeting, conditions, statuses, stacks, lanes and action order—without pretending to calculate exact final damage where formulas or server modifiers remain unknown.

## Primary user questions

- What triggers at the start of combat and each round?
- Which enemy or ally is targeted, and why?
- Which statuses are active, stacked, consumed or expired?
- Does a Star/Habit gate or troop-capacity condition apply?
- How do First-Strike, Slow, Stun, Stagger, Overwhelm, Taunt and Confusion affect the sequence?
- What changes in the second ten-round combat cycle after a Stalemate?

## Initial scope

- Three allied and three enemy dragons.
- Left Flank, Vanguard and Right Flank.
- Shared troop type per formation.
- Dragon level, Star Rank and Habit levels.
- PvP, defender-clearing and POI/siege contexts.
- One ten-round cycle, followed by an optional second-cycle reset view.
- Deterministic explanation plus probability branches for chance-based effects.
- Commanders excluded from calculations until live.

## Non-goals for MVP

- Claiming exact battle outcomes or damage totals without a validated formula.
- Live automation or interaction with the game.
- Hidden server modifiers.
- Commander assignment or talent simulation.
- Monte Carlo win-rate claims before observed combat validation exists.

## Existing related files and data

- `data/dragons/*.json`
- `data/effects.json`
- `data/game_mechanics.json`
- `data/dragon_application_knowledge.json`
- `RECOMMENDATION_HANDOFF.md`
- `Game_Details/Resources/dragonAbilitiesTable_merged.*.pb`
- `Game_Details/Resources/dragonAbilityConditionsTable_merged.*.pb`
- `Game_Details/Resources/dragonEffectGroupsTable_merged.*.pb`
- `Game_Details/Resources/dragonEffectsTable_merged.*.pb`
- `Game_Details/Resources/dragonTargeterTable_merged.*.pb`
- `Game_Details/Resources/DragonTargetPrioritizersTable.*.pb`
- `Game_Details/Resources/CombatVariablesTable.*.pb`
- `Game_Details/Resources/TroopEffectivenessTable.*.pb`

## Proposed project files

```text
projects/combat-interaction-explorer/
  PROJECT_PLAN.md
  src/
    engine/
      schedule.*
      targeting.*
      conditions.*
      statuses.*
      action-order.*
      cycle.*
    ui/
    explanations/
  tests/
    fixtures/
    observed-battles/
  public/
  README.md
```

## Core model

The engine should represent combat as an event stream, not a single score:

```text
combat_start
round_start(n)
pre_action_order_effects
ordered_actor_turns
  command/habit/basic attack
  reactive effects
  status/stack updates
round_end(n)
combat_cycle_end
stalemate_or_resolution
```

Each event records source, target candidates, chosen target, selection reason, condition result, effect, duration, confidence and citation.

## Work plan

### Phase C1 — Mechanics graph

- [x] CIE-011 Convert commands, habits, effects, conditions and targeters into normalized graph nodes.
- [x] CIE-012 Normalize exact round schedules and start-of-combat/start-of-round timing.
- [ ] CIE-013 Normalize lane scopes, adjacency, same-lane behavior and priority/fallback rules.
- [x] CIE-014 Model verified Star/level eligibility and retain Habit investment as profile context pending numeric-formula validation.
- [ ] CIE-015 Model shared troop affinity and troop-counter context separately.

### Phase C2 — Status and targeting engine

- [x] CIE-021 Implement status instances, stacks, caps, duration and expiry.
- [ ] CIE-022 Implement target candidate filtering and priority selection.
- [ ] CIE-023 Implement Taunt and Confusion redirection.
- [ ] CIE-024 Implement Stun, Stagger and Overwhelm action suppression.
- [ ] CIE-025 Implement First-Strike, normal Initiative and Slow ordering.
- [ ] CIE-026 Implement Cleanse, Recovery modifiers and named-stack producer/consumer relationships.

### Phase C3 — Timeline engine

- [x] CIE-031 Generate one ten-round event timeline.
- [x] CIE-032 Represent chance effects as branches or expected possibilities, never silently as guaranteed.
- [x] CIE-033 Show unresolved ordering explicitly when the client text does not establish it.
- [ ] CIE-034 Add optional second-cycle view and document what persists across Stalemate.
- [x] CIE-035 Add an “assumptions used” panel.

### Phase C4 — User interface

- [x] CIE-041 Formation editor with lanes, shared troop type, levels and Stars plus shared-profile Habit context.
- [x] CIE-042 Round scrubber and expandable event timeline.
- [x] CIE-043 Formation-state view showing active effects and stacks at each step.
- [ ] CIE-044 Filters for allied, enemy, damage, control, recovery and targeting events.
- [x] CIE-045 Deep links to Encyclopedia records.
- [ ] CIE-046 Export a compact scenario/result JSON for Counter Picking and bug reports.

### Phase C5 — Validation

- [ ] CIE-051 Unit-test lane matching, targeting fallback and adjacency.
- [ ] CIE-052 Unit-test round schedules and duration boundaries.
- [ ] CIE-053 Unit-test status caps, Cleanse and suppression.
- [ ] CIE-054 Create fixtures from screenshot-confirmed dragon kits.
- [ ] CIE-055 Compare at least five timelines against observed battles/logs or recorded combat.
- [x] CIE-056 Mark unsupported damage calculations rather than fabricating totals.

### Phase C6 — Portfolio integration

- [x] CIE-061 Add the shared tool switcher and player-tools landing-page link.
- [x] CIE-062 Accept dragon/formation deep links from the Encyclopedia and Counter Picking Assistant.
- [x] CIE-063 Export a scenario deep link that Counter Picking can inspect or refine.
- [x] CIE-064 Preserve evidence links from every timeline event back to the Encyclopedia.

## MVP acceptance criteria

- A user can define two legal 3-dragon formations and inspect rounds 1–10.
- Every event explains its trigger, selected target and source evidence.
- Lane, priority and fallback behavior follows repository mechanics rules.
- Chance effects are visibly probabilistic.
- The tool works without Commanders and hides staged Commander effects by default.
- Unknown ordering or numeric interpretation is visible to the user.

## Later extensions

- Observed-result calibration and optional damage ranges.
- Monte Carlo probability exploration after formulas are validated.
- Import/export with Counter Picking.
- PvE defender templates from map encounter data.
- Commander layer only after live behavior is documented.

## Implementation status — 2026-09-16

Selected as the next player-facing tool after the Encyclopedia/Atlas vertical slice.
Implementation begins with a dependency-free formation editor and deterministic
round-schedule timeline consuming the existing normalized combat dataset. Status and
targeting state transitions will be added incrementally and remain visibly unknown
where source data does not establish ordering or numeric behavior. The current slice
now resolves lane-aware candidate pools, distinguishes resolved targets from choices
requiring unavailable priority stats, evaluates Star clauses, and exposes status
operations with a conservative state projection. Deterministic applications with one
unambiguous target group receive duration, expiry and stack handling; probability
effects remain branches, contradictory normalized operations remain ambiguous, and
prior-round Stun/Stagger/Overwhelm state is flagged without silently deleting events.
