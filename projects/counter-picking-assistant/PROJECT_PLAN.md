# Counter-Picking Assistant

## Project description

Build an explainable assistant that recommends dragons, lanes and one shared troop type against a specified enemy formation or PvE defender profile. Recommendations must be based on explicit counters, timing, targeting, status interactions and roster eligibility—not a universal tier score.

## Primary user questions

- Which owned dragons best counter this enemy trio?
- Which lane should each dragon occupy?
- Which shared troop type is best for this matchup?
- What enemy mechanic is each selection answering?
- Which missing Star/Habit breakpoint prevents a counter from working?
- What is the safest alternative if the ideal counter is unavailable?

## Initial scope

- Manual enemy formation entry by dragon, lane, level/Star/Habit when known.
- Optional partial enemy information with confidence degradation.
- Player roster filter.
- PvP, defender-clearing and POI/siege objectives.
- Top recommendations with explanations and alternatives.
- Commanders excluded until live.

## Non-goals

- A single context-free dragon ranking.
- Guaranteed win predictions.
- Recommendations using dragons or Habits the player does not own/unlock unless clearly labeled as aspirational.
- Assigning separate troop types per lane.
- Treating rarity or raw power as a sufficient counter argument.

## Existing related files

- `data/dragons/*.json`
- `data/effects.json`
- `data/game_mechanics.json`
- `data/dragon_application_knowledge.json`
- `RECOMMENDATION_HANDOFF.md`
- Combat Interaction Explorer scenario/result format when implemented.

## Proposed project files

```text
projects/counter-picking-assistant/
  PROJECT_PLAN.md
  src/
    rules/
      threat-extraction.*
      counter-evidence.*
      candidate-generation.*
      formation-search.*
      explanation.*
    ui/
  tests/
    matchup-fixtures/
  README.md
```

## Recommendation model

### Enemy threat extraction

Turn the enemy formation into explicit threats:

- Damage types and round schedules.
- Control, Recovery, Cleanse, mitigation and damage amplification.
- Lane/priority targeting.
- Trait/breed/troop/capacity conditions.
- Named stack engines and producer/payoff chains.
- Opening burst versus late-cycle scaling.

### Counter evidence

Candidate evidence includes:

- Direct text counter, such as anti-Fire or anti-Recovery.
- Action denial or Cleanse relevant to an enemy mechanic.
- Target-priority exploitation.
- Damage type versus enemy mitigation profile.
- Lane protection or redirection.
- Troop affinity and troop-counter cycle.
- Timing alignment: the counter must activate before or during the threat window.

### Search strategy

- Filter illegal/unowned/inactive candidates first.
- Generate legal trios and Vanguard placements.
- Choose one shared troop type.
- Evaluate explicit threat coverage, synergy, timing and exposure.
- Retain several non-dominated options rather than collapsing everything into one opaque score.

## Work plan

### Phase P1 — Threat taxonomy

- [x] CPA-011 Define normalized threat categories with source evidence.
- [x] CPA-012 Extract threats from dragon commands, Habits, Vanguard and troop choice.
- [x] CPA-013 Represent timing, lane and probability.
- [x] CPA-014 Represent missing enemy information and confidence loss.
- [x] CPA-015 Exclude staged Commander effects from live threat extraction.

### Phase P2 — Counter rule library

- [x] CPA-021 Encode direct effect-to-counter relationships.
- [ ] CPA-022 Encode status prevention, suppression, Cleanse and mitigation relationships.
- [x] CPA-023 Encode target-priority and lane exploitation.
- [x] CPA-024 Encode troop affinity and matchup separately.
- [x] CPA-025 Encode producer/payoff synergy requirements.
- [x] CPA-026 Require source citations and explanation templates for every rule.

### Phase P3 — Formation generation

- [x] CPA-031 Import or create a player roster.
- [x] CPA-032 Enforce verified level, Star and Vanguard eligibility; retain Habit levels as context pending numeric-formula validation.
- [x] CPA-033 Generate legal trios, lanes and shared troop types.
- [x] CPA-034 Track threat coverage and new vulnerabilities for each candidate.
- [x] CPA-035 Return best-fit, safer alternative and accessible alternative.

### Phase P4 — Explainability and UI

- [x] CPA-041 Enemy formation/threat editor.
- [x] CPA-042 Recommendation cards with lane and troop placement.
- [x] CPA-043 “Why this works” linked to exact mechanics.
- [x] CPA-044 “What can go wrong” and missing-input section.
- [x] CPA-045 Compare two proposed counters side by side.
- [x] CPA-046 Export formation to Combat Interaction Explorer.

### Phase P5 — Validation

- [x] CPA-051 Build matchup fixtures for Fire, Physical, Tactical, Recovery, control and stack teams.
- [x] CPA-052 Verify recommendation eligibility against Stars/Habits.
- [ ] CPA-053 Review top recommendations for at least ten known matchups.
- [ ] CPA-054 Record observed outcomes without fitting rules to a single anecdote.
- [x] CPA-055 Test partial-information behavior.

### Phase P6 — Portfolio integration

- [x] CPA-061 Add the shared tool switcher and player-tools landing-page link.
- [ ] CPA-062 Import enemy and candidate formations through the Combat Explorer scenario contract.
- [ ] CPA-063 Deep-link every threat and counter explanation to its Encyclopedia evidence.
- [x] CPA-064 Export recommended formations directly into Combat Explorer.

## MVP acceptance criteria

- Given an enemy trio and owned roster, the tool returns legal counter formations.
- Each recommendation identifies the enemy threats it answers.
- Lane and shared troop recommendations follow documented game rules.
- Missing data lowers confidence instead of being silently assumed.
- At least one alternative is offered when the strongest counter is unavailable.
- Results can be inspected in the Combat Interaction Explorer.

## Later extensions

- Screenshot-assisted enemy formation entry.
- Alliance-shared matchup library without sharing private account credentials.
- Encounter/defender imports from the Atlas.
- Observed-match feedback and calibrated confidence.
- Commander counters only after the feature is live and validated.

## Delivery status — 2026-09-17

The working assistant extracts explicit damage, harmful-status and Recovery threats,
filters a selectable live roster, evaluates legal lane permutations, proposes three distinct
formation alternatives, selects one shared troop type, and exports to Combat Explorer.
It now compares documented timing windows, same-lane and priority targeting, directional
Vanguard support, producer/payoff status chains, and saved Habit-level activation rates.
Transparent ranking contributions and Fire/Physical/Tactical/Recovery/control fixtures
cover the expanded engine. Partial-information confidence and side-by-side comparison are
implemented. Observed-match collection is available locally without affecting scores, and
schedule attribution is scoped to individual damage/effect clauses. Ten-match expert review
and real observed outcome collection remain pending because those require actual battle evidence.
