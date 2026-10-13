# Deterministic recommendation planner

The planner exhaustively evaluates every legal owned trio, all six lane orders, and every available shared troop. It always evaluates each legal common formation in its declared lane order and troop, even when that baseline is dominated or becomes the primary recommendation.

It applies each dragon's own level, Star Rank, Habit levels, optional visible Power, and the account-level Dragon's Army capacity upgrade. The result contains the mandatory candidate ledger, a Pareto frontier, deterministic finalists, timing windows, modeled troop capacity, and source locators. It does not estimate win rates or invent undocumented combat formulas.

The objective-fit axis uses only documented active mechanics: damage-bearing abilities,
damage amplification, producer/payoff chains, and scheduled pressure for high-damage
requests; documented Recovery, Protect, Resistance, mitigation, damage, and timing for
damage-and-survivability requests; exact normalized threat coverage and troop matchup for
counters; and explicit Siege specialization for POI requests. It remains a comparison
axis rather than a universal strength score.

## Run

```powershell
node projects/recommendation-planner/recommend.mjs --input scenario.json --output recommendation.json --pretty
```

Read-only agent environments that cannot create a scenario file may pass the same object
directly with `--input-json '<JSON object>'`. Supply exactly one input mode.

Minimal valid input can use a roster array (real recommendations should include every
owned dragon so exhaustive search is meaningful):

```json
{
  "objective": "counter",
  "available_troops": ["Cavalry", "Shieldbearers"],
  "roster": [
    {"dragon": "Malachite", "owned": true, "level": 50, "stars": 6, "power": 128000, "habit_levels": {}},
    {"dragon": "Seasmoke", "owned": true, "level": 47, "stars": 8, "power": 131000, "habit_levels": {}},
    {"dragon": "Kalspire", "owned": true, "level": 45, "stars": 6, "power": 119000, "habit_levels": {}}
  ],
  "enemy": {
    "troop_type": "Shieldbearers",
    "formation": [
      {
        "dragon": "Velar",
        "lane": "Left Flank",
        "level": 50,
        "stars": 6,
        "habit_levels": {}
      }
    ]
  }
}
```

`roster` entries may identify a dragon with `dragon`, `slug`, or `name`. The planner also
accepts the application's exported `profile.dragons` object directly. Level and Stars are
required so that progression is never silently assumed. Habit levels may be omitted and
then remain unknown; `0` explicitly marks a Habit unavailable. `power` is optional and is
used only when every eligible roster dragon has known current Power, so every searched
candidate is comparable; a mixture of known and unknown Power is never treated as zero.

An ingestion profile may include `profile.stronghold.dragons_army`. The planner derives
its per-dragon bonus from `current_skill` (`none`, `I`–`IV`) and `current_level` (0–5),
and rejects a supplied derived total that disagrees with the canonical prerequisite
sequence. If it is absent, capacity uses an explicitly disclosed assumed `+0` bonus. Each
candidate includes its per-dragon level curve, Star scalar, Dragon's Army addition, and
total modeled capacity. For `highest_tile` and `troop_preservation` objectives, capacity
becomes a primary comparison dimension after direct coverage and troop safety; it remains
reported, but does not silently become a universal score for other objectives.

Common formations are loaded from `data/common_formations.json`. A baseline is reported as `evaluated`, `illegal`, or `inapplicable`, with reasons. Applicability never removes a legal ordinary-combat baseline from the ledger.

## Multi-matchup batch input

Use a single batch whenever several enemy formations must be compared. This removes the
ambiguity between three separate recommendations and one global allocation. It also
produces one validated, retained audit artifact instead of asking a parent agent to
reconstruct results from delegated output.

```json
{
  "objective": "counter",
  "available_troops": ["Cavalry", "Shieldbearers", "Spearmen"],
  "roster_preflight": {
    "completeness": "complete",
    "expected_visible_dragons": 3
  },
  "request_mode": "one_per_matchup",
  "reuse_policy": "independent_matchups",
  "roster": [
    {"dragon": "Velar", "level": 50, "stars": 6, "displayed_stars": {"color": "red", "count": 1}, "habit_levels": {}},
    {"dragon": "Vhagar", "level": 50, "stars": 6, "displayed_stars": {"color": "red", "count": 1}, "habit_levels": {}},
    {"dragon": "Moondancer", "level": 50, "stars": 6, "displayed_stars": {"color": "red", "count": 1}, "habit_levels": {}}
  ],
  "scenarios": [
    {"id": "velar-line", "common_formation_id": "velar-vhagar-moondancer-shieldbearers"},
    {"id": "vermithor-line", "common_formation_id": "vermithor-rhysarion-venator-spearmen"},
    {"id": "malachite-line", "common_formation_id": "malachite-seasmoke-kalspire-cavalry-counter"}
  ]
}
```

Each batch scenario may instead supply a normal `enemy` object with a troop type and
explicit three-lane formation. A `common_formation_id` resolves the canonical enemy
formation plus its explicitly labeled reference assumptions; it does not claim that those
assumptions are the opponent's observed account progression.

`request_mode` is `one_per_matchup` (one selected counter for each enemy) or
`top_n_per_matchup` (several Pareto finalists for each enemy). `reuse_policy` is
`independent_matchups` (the normal case: the same owned dragon may appear in different
hypothetical battles) or `disjoint_armies` (one distinct three-dragon army per scenario).
Disjoint allocation currently applies to `one_per_matchup`; the planner searches the
documented Pareto finalists and fails closed if no distinct allocation exists.

`roster_preflight.completeness` must be `complete` only after the source roster has been
fully transcribed. Otherwise use `declared_subset`; the result will state that the search
is exhaustive only within that subset. `expected_visible_dragons`, when supplied, must
equal the number of submitted owned dragons. For screenshot transcription,
`displayed_stars` accepts `{ "color": "yellow"|"red", "count": 1..5 }`; a red star
maps to ranks 6–10 and must agree with `stars`.

Run a batch to JSON or deterministic Markdown:

```powershell
node projects/recommendation-planner/recommend.mjs --input batch.json --format json --output batch-result.json --pretty
node projects/recommendation-planner/recommend.mjs --input batch.json --format markdown --output batch-report.md
```

The batch output contains `validation`. A caller must present no recommendation if
`validation.valid` is not true. The Markdown renderer includes the selected formation,
per-threat direct/probabilistic/partial/none coverage, progression gates, exact-evidence
links in JSON, common-baseline check, alternative and reversal conditions, risks, and the
selection attestation. Keep the output until the caller has verified and delivered it.

Coverage labels are deliberately conservative. `direct` means the documented response
has no identified activation, target, damage-exclusion, prerequisite, or timing limit;
`probabilistic` means the response has an activation chance and no further identified limit; `partial` means a scope,
exclusion, prerequisite, or evidence limit prevents a whole-category claim; `none` means
no documented response was found. Each response includes its exact text, chance, and
qualifiers. The planner applies these same distinctions in its counter-selection
metrics. The report states when available troops are default assumptions and identifies
the common formations' enemy progression as reference assumptions.

