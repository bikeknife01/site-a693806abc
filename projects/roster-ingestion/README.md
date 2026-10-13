# Player roster ingestion

This project converts either a Dragonfire Formation Forge JSON export or a
reviewed screenshot transcription into the same evidence-aware player-roster
snapshot. It then emits a compact profile validated against the deterministic
recommendation planner.

## Normal user workflow

The normal interaction is agent-operated. The user supplies either:

- the path to a Formation Forge JSON export; or
- the path to a screenshot folder, plus a profile alias and capture date when
  they cannot be inferred safely.

The agent inspects the source, runs the appropriate ingestion path, reviews the
generated audit, and reports conflicts or uncertain readings in conversation.
The agent also asks once for the highest unlocked **Dragon's Army** Stronghold
skill and its current level. If the user does not know, the workflow records an
explicit assumed zero bonus instead of leaving an ambiguous unknown.
The user is not expected to run terminal commands or edit transcription JSON.
Commands in this document are implementation and operator references for the
agent, or an optional fallback for users who explicitly want direct CLI access.

The workflow is local-only. Player aliases, screenshots, raw exports, and
generated roster snapshots belong under the ignored `dragon_stars/` tree and
must not be committed.

## Output layout

Use an ISO date so captures sort unambiguously:

```text
dragon_stars/<profile-id>/<YYYY-MM-DD>/
  screenshots/                 # original screenshot evidence, when applicable
  source/
    <original input>.json      # immutable copy made by the CLI
  roster.json                  # evidence-rich archival snapshot
  planner-profile.json         # written only when recommendation-critical data validates
  planner-profile.blocked.txt  # written instead when planner output is unsafe
  ingestion-report.md          # human review report
```

The CLI refuses to overwrite an existing artifact by default. Use
`--overwrite` only when intentionally regenerating a disposable test output;
create a new dated snapshot for new player evidence.

## Shared contract

`roster.json` uses `dragonfire.player-roster.v1` and contains:

- stable canonical dragon slugs;
- player-specific ownership, search inclusion, level, Stars, Power, troop
  capacity, and Habit levels;
- account-level Dragon's Army progression and its derived capacity bonus;
- per-field evidence and review state;
- roster completeness;
- hashes for every input;
- the canonical encyclopedia schema, client versions, source manifest, and
  dataset hash used for identity and enrichment;
- validation warnings and conflicts.

Unknown values are `null`. Zero is used only when zero is meaningful: a Habit
level of `0` explicitly means unavailable or locked. Power and troop capacity
must be positive when known.

Fixed dragon facts—including breed, rarity, troop affinities, abilities,
roles, and mechanics—are not copied into the player roster. Consumers join
them from the recorded canonical dataset. Fixed troop affinities are therefore
identical for both ingestion paths. Scenario-level selectable troops are a
recommendation request input and are not part of the roster schema.

### Dragon's Army capacity

The profile stores one account-level `stronghold.dragons_army` record. The
skill increments are 50, 100, 200, and 250 troops per dragon per level for
Dragon's Army I-IV. Each skill has five levels, and selecting a later skill
means every preceding skill is complete at level 5. The importer records the
current skill's own contribution separately from the cumulative result.

For example, Dragon's Army III level 2 means 250 from I, 500 from II, and 400
from two levels of III: **1,150 additional troops per dragon**, or **3,450**
for a three-dragon formation. Dragon's Army IV level 5 contributes 1,250 from
that skill alone and produces a cumulative 3,000 per dragon after prerequisites.
Derived totals are validated and cannot be supplied independently.

The agent passes a known answer with `--dragons-army-skill` and
`--dragons-army-level`. Omitting both records skill `none`, level `0`, bonus
`0`, provenance `assumed`, and basis `ingestion_default`.

## Path 1: Formation Forge export

Export the roster from Dragonfire Formation Forge and give its path to the
agent. The agent runs the equivalent of:

```powershell
node projects/roster-ingestion/roster.mjs ingest-site `
  --input dragon_stars/structured_rosters/owlgun-roster_10-11-26.json `
  --profile-id owlgun `
  --observed-at 2026-10-11 `
  --dragons-army-skill III `
  --dragons-army-level 2 `
  --output-dir dragon_stars/owlgun/2026-10-11
```

The importer fingerprints the supported export shape and performs this audit:

| Export field | Result |
|---|---|
| `name` | Resolves to the canonical repository slug. |
| `active` | By default maps to both ownership and search inclusion. |
| `reignLevel` | Becomes `level`. |
| `starRank` | Becomes `stars`. |
| `habitLevels` | Maps displayed positions to canonical Habit client keys. |
| zero Power/capacity | Becomes unknown (`null`). |
| rarity/breed/affinity | Validated against canonical data, then omitted. |
| role/damage type/tags | Treated as source-specific classifications and omitted. |
| notes | Preserved only in the raw source copy. |

If the source's `active` switch means only optimizer inclusion while every
exported row is owned, add `--active-means include`. That sets every exported
row to owned and uses `active` only for `include_in_search`. The selected
semantics are recorded in field evidence.

## Path 2: screenshots

Screenshot reading is deliberately assisted rather than silently autonomous.
An agent or reviewer reads the images and creates a transcription JSON; the
CLI hashes the original images, resolves identity, checks the transcription,
and produces the same `roster.json` contract as the site importer.

The transcription format is defined by
`schemas/screenshot-transcription.schema.json`. A minimal example is:

```json
{
  "schema_version": "dragonfire.screenshot-transcription.v1",
  "profile_id": "owlgun",
  "observed_at": "2026-10-11T21:00:00-07:00",
  "roster_preflight": {
    "completeness": "complete",
    "expected_visible_dragons": 36
  },
  "stronghold": {
    "dragons_army": {
      "current_skill": "III",
      "current_level": 2
    }
  },
  "sources": [
    {
      "id": "overview-01",
      "path": "screenshots/overview-01.png",
      "kind": "overview"
    }
  ],
  "observations": [
    {
      "dragon": "Syrax",
      "source_id": "overview-01",
      "fields": {
        "level": {
          "value": 50,
          "confidence": "confirmed",
          "review_status": "confirmed"
        },
        "displayed_stars": {
          "value": { "color": "red", "count": 3 },
          "confidence": "confirmed",
          "review_status": "confirmed"
        }
      }
    }
  ]
}
```

Paths are resolved relative to the transcription JSON. An optional crop uses
pixel coordinates:

```json
"crop": { "x": 1300, "y": 450, "width": 420, "height": 240 }
```

Supported review states are `machine_read`, `confirmed`, `corrected`,
`conflicting`, and `unreadable`. Supported confidence values are `low`,
`medium`, `high`, and `confirmed`. Unreadable values remain `null`.

After reading and recording the screenshots, the agent runs the equivalent of:

```powershell
node projects/roster-ingestion/roster.mjs ingest-screenshots `
  --input dragon_stars/owlgun/2026-10-11/transcription.json `
  --output-dir dragon_stars/owlgun/2026-10-11
```

Overview screenshots normally establish identity, level, and displayed Stars.
Detailed panels can establish Power, troop capacity, and Habit levels. Red and
yellow Stars are preserved exactly; numeric Star Rank is a separately recorded
derived value. Conflicting observations set the field to unknown and block the
planner profile until the transcription is explicitly corrected.
The Dragon's Army answer may be recorded in the transcription or supplied as
the two CLI options; explicit CLI values take precedence. If neither exists,
the same assumed-zero rule used for site exports applies.

## Review and validation

Inspect `ingestion-report.md` before using the profile. It lists:

- normalized and expected roster counts;
- errors, warnings, and conflicts;
- fixed-field drift in site exports;
- zero-as-unknown conversions;
- locked Habit corrections;
- duplicate screenshot coverage;
- fields still needing human review;
- per-dragon progression coverage;
- Dragon's Army source, current tier/level, per-dragon bonus, and three-dragon
  formation bonus.

The agent can revalidate a saved snapshot against current canonical knowledge
with:

```powershell
node projects/roster-ingestion/roster.mjs validate `
  --input dragon_stars/owlgun/2026-10-11/roster.json `
  --report dragon_stars/owlgun/2026-10-11/revalidated-report.md
```

A changed canonical dataset hash is a warning: player observations are still
preserved, but enrichment should be regenerated. Unknown identities, invalid
ranges, displayed-Star disagreements, locked active Habits, broken evidence
references, source hash mismatches, and unresolved critical conflicts fail
closed.

`planner-profile.json` is emitted only after local validation and a dry run
through the recommendation planner's input validator. It intentionally omits
unknown Habit levels and unknown Power.

## Snapshot deltas

Never overwrite a historical player snapshot. The agent compares two dates
with:

```powershell
node projects/roster-ingestion/roster.mjs diff `
  --before dragon_stars/owlgun/2026-10-11/roster.json `
  --after dragon_stars/owlgun/2026-11-03/roster.json `
  --output-dir dragon_stars/owlgun/2026-11-03/diff-from-2026-10-11
```

This writes `roster-diff.json` and `roster-diff.md`. Decreases in level, Stars,
Power, capacity, Habit levels, or Dragon's Army bonuses are review flags rather than automatic errors
because seasonal resets, stale screenshots, and transcription mistakes are all
possible.

## Formation Forge compatibility export

To create an explicit compatibility export, the agent runs:

```powershell
node projects/roster-ingestion/roster.mjs export-forge `
  --input dragon_stars/owlgun/2026-10-11/roster.json `
  --template dragon_stars/owlgun/2026-10-11/source/owlgun-roster_10-11-26.json `
  --output dragon_stars/owlgun/2026-10-11/formation-forge-import.json
```

Canonical identity, rarity, breed, and troop affinities are joined from the
repository. Player progression comes from the roster snapshot. Unknown values
remain `null`; community notes are not regenerated. `--template` preserves the
site's required custom role and primary-damage classifications from an explicit
original export while still replacing canonical and player fields with the
validated values. Without a template those non-canonical classifications remain
`null` and must be reviewed in the site after import.

## Privacy and evidence boundaries

- Keep all player material under ignored `dragon_stars/` paths.
- Use a non-sensitive profile alias; do not store email addresses, platform
  identifiers, credentials, or account tokens.
- Raw exports and screenshots are player evidence, not shared game facts.
- Community notes remain raw source text and never update canonical mechanics.
- Screenshot absence proves nothing unless the capture is explicitly complete.
- Do not infer player Power, capacity, progression, or ownership from canonical
  game knowledge.

## Tests

```powershell
node --test projects/roster-ingestion/tests/*.test.mjs
```

Fixtures cover Formation Forge input, screenshot evidence, duplicate coverage,
conflicts, invalid progression, deterministic output, planner compatibility,
compatibility export, CLI overwrite protection, and snapshot deltas.

