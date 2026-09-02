---
name: add-dragon
description: Add a screenshot-complete Game of Thrones: Dragonfire dragon to the repository when the user supplies the dragon's name and screenshot-folder path. Extract the Basics, Command, Vanguard, and five Habits; update canonical JSON, wiki documentation, the recommendation handoff, and any applicable shared or live-update records; preserve exact in-game wording and flag uncertainty instead of guessing.
---
# Add a Screenshot-Complete Dragon

Add one new dragon to the Dragonfire knowledge base from current in-game screenshots.

The user supplies:

- **Dragon name**
- **Screenshot folder path**

Example:

> Add Vermithor from `D:\repos\Dragonfire\Dragon_Specs\Vermithor`

## Source authority

Treat screenshots in the supplied folder as authoritative for exact dragon data.

Do not use fan sites or prior summaries to fill missing screenshot text. Official sources may explain shared systems but must not override newer in-game wording.

Preserve capitalization, terminology, percentages, durations, targets, conditions, exclusions, priorities, and round schedules exactly in JSON `verbatim` fields.

Never guess cropped, unclear, contradictory, or missing text. Record the uncertainty in the dragon JSON `review` array.

## Required screenshot coverage

Inspect images by their displayed content rather than relying only on filenames.

Confirm coverage for:

- Basics/details panel
- Complete Command, including continuation panels
- Vanguard ability
- 2-Star Habit
- 4-Star Habit
- 6-Star Habit
- 8-Star Habit
- 10-Star Habit
- All five displayed upgrade-level values for every Habit

If required coverage is missing, report the missing panels and do not represent the dragon as screenshot-complete.

## Repository preparation

Before editing:

1. Read `.github\copilot-instructions.md`.
2. Read `RECOMMENDATION_HANDOFF.md`, especially its schema and evidence rules.
3. Read `data\game_mechanics.json` and `data\effects.json`.
4. Inspect at least two comparable records under `data\dragons\`.
5. Inspect their matching pages under `wiki\dragons\`.
6. Check `data\live_updates.json` for an incomplete entry matching the dragon.
7. Check `wiki\Online-Sources.md` for prior official-source coverage.
8. Check the worktree and preserve unrelated user changes.

## Screenshot extraction

### Basics

Transcribe:

- Exact dragon name
- Breed
- Displayed rarity/classification label
- Positive troop affinities
- Negative troop affinities

Do not treat player-specific Basics values as stable dragon traits. Exclude:

- Strength
- Instinct
- Intelligence
- Initiative
- Stamina
- Current level
- XP
- Reign Level
- Current Star Rank
- Current army size

Use `excluded_progression_snapshot` consistently with existing records.

Do not silently convert labels such as `Elder`, `Adult`, or `Juvenile` into rarity tiers. Record only the label actually established by the screenshot or explicit authoritative evidence.

### Command

Capture:

- Exact name
- Exact displayed type, such as `Active` or `Attack Modifier`
- Complete wording across every continuation panel
- Base behavior
- Star-gated additions
- Timing
- Chances
- Targets and scopes
- Priorities
- Durations
- Damage or Recovery rates
- Conditions
- Stack caps
- Basic Attack exclusions

Use a string when the existing convention supports one coherent clause. Use an ordered string array when multiple clauses or continuation panels are clearer.

Do not infer proc order, targeting, adjacency, stacking, or interaction rules not stated in the screenshots.

### Vanguard

Capture:

- Exact name
- Unlock level
- Complete verbatim wording
- Self effects
- Directional Left Flank or Right Flank effects

Preserve directional wording exactly.

### Habits

Create exactly five Habits ordered by these unlocks:

1. 2 Stars
2. 4 Stars
3. 6 Stars
4. 8 Stars
5. 10 Stars

For each Habit capture:

- `star_unlock`
- Exact name
- Complete `verbatim` text
- Upgrade values for Levels 1–5
- Optional `value_unit`
- Optional normalized tags when consistent with existing records

Habit skill Levels 1–5 are not Star ranks. Map the five displayed columns to keys `"1"` through `"5"`.

Use scalar upgrade values when one value changes. Use objects with concise `snake_case` keys when multiple values change.

Keep signs meaningful:

- Increases are positive
- Reductions are negative where established by existing conventions
- Chances and rates remain numeric percentages without `%` symbols

## Canonical dragon JSON

Create:

`data\dragons\<lowercase-name>.json`

Follow the established shape:

- `name`
- `breed`
- `rarity_label`
- `troop_affinities`
- `excluded_progression_snapshot`
- `command`
- `vanguard`
- `habits`
- `derived`
- `review`

Use optional `structured`, tags, or derived fields only when supported and useful. Follow vocabulary already used by neighboring records.

Derived analysis may include:

- Roles
- Preferred troop candidates
- Troops to avoid
- Explicit synergy inputs
- Explicit synergy outputs
- Formation needs
- Conditional position preference
- Scenario bias
- Concise strategic notes

Derived fields must remain distinguishable from transcribed facts. Do not invent undocumented mechanics to make the derived analysis appear complete.

A Vanguard ability does not automatically make Vanguard the dragon’s best formation position. If adding `preferred_position`, treat it as derived and conditional.

Set `review` to an empty array only when all recommendation-critical evidence is clear. Otherwise record precise, actionable review items.

## Dragon wiki page

Create:

`wiki\dragons\<ExactName>.md`

Follow existing pages:

1. Dragon name heading
2. Breed, displayed rarity/classification, and affinities
3. Concise role and synergy explanation
4. Material constraints, conditions, stack caps, or exclusions
5. Link to the canonical JSON
6. `Recommendation-critical source coverage`
7. Command summary
8. Vanguard summary
9. All five Habits in Star-unlock order

The wiki is a readable companion. Keep exact values and critical conditions, but make JSON the canonical detailed record.

Do not introduce mechanics absent from the screenshots.

## Recommendation handoff

Update `RECOMMENDATION_HANDOFF.md`.

Add the dragon alphabetically to the compact dragon catalog with:

- Supported roles
- Explicit synergies or required inputs
- Supported counters or pressure
- Important constraints

Update limitations or confirmations when the new evidence resolves or creates a material repository issue.

Do not duplicate the full ability record in the handoff.

## Conditional shared-file updates

### Effects

Update `data\effects.json` only when the screenshots establish a genuinely new named effect that strategists must understand across recommendations.

Preserve exact supported behavior and scope. Do not generalize a dragon-specific mechanic beyond its displayed wording.

### Game mechanics

Update `data\game_mechanics.json` and `wiki\Game-Mechanics.md` only when the screenshots establish a shared system rule rather than a dragon-specific ability.

### Live updates

If the dragon exists in `data\live_updates.json`, remove or retire that incomplete entry only after the screenshot-complete JSON is finished.

Keep valid official-source history where appropriate.

### Source audit

Update `wiki\Online-Sources.md` when:

- The dragon previously had an official profile tracked there
- Screenshot evidence resolves a documented gap
- Screenshot and official wording conflict
- Source status or freshness materially changes

Never silently resolve a source conflict.

### README and agent customization

Do not update `README.md` merely for another dragon unless repository structure or policy changes.

Do not duplicate dragon mechanics in `.github\agents\` or `.github\copilot-instructions.md`. The strategist reads canonical data and the handoff.

## Consistency review

Before validation, confirm:

- The dragon name is consistent across screenshots, JSON, wiki, and handoff.
- All screenshots were inspected.
- Every Command continuation panel is represented.
- Exactly five Habits exist.
- Habit unlocks are exactly `2`, `4`, `6`, `8`, and `10`.
- Every Habit has upgrade keys `"1"` through `"5"`.
- Verbatim fields preserve in-game wording.
- Player-specific Basics values are not used as stable characteristics.
- Star Rank and Habit skill level are not conflated.
- Affinities match the Basics screenshot.
- Damage types, scopes, priorities, exclusions, schedules, and stack caps are retained.
- Derived strategy is supported by explicit mechanics.
- Wiki and handoff claims agree with canonical JSON.
- Any uncertainty appears in `review`.
- A completed dragon is removed from incomplete live-update tracking when applicable.

## Validation

Parse every changed JSON file using existing system tooling.

On Windows PowerShell, a suitable check is:

`Get-ChildItem data\*.json, data\dragons\*.json | ForEach-Object { Get-Content -Raw $_.FullName | ConvertFrom-Json | Out-Null }`

Then run:

`git diff --check`

Inspect the final diff for accidental changes, malformed Markdown, inconsistent naming, omitted screenshot clauses, and unrelated modifications.

Do not declare completion if JSON parsing fails, `git diff --check` reports errors, required screenshot coverage is missing, or recommendation-critical ambiguity was silently guessed.

## Completion response

Report:

- Dragon added
- Screenshot folder used
- Files created or updated
- Any unresolved review items
- Any conditional shared-data changes
- Validation result