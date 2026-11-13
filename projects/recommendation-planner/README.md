# Deterministic recommendation planner

The planner exhaustively evaluates every legal owned trio, all six lane orders, and every available shared troop. It always evaluates each legal expert/common formation in its declared lane order and troop. Those formations carry a disclosed expert recommendation prior but remain subject to normal legality and evidence gates.

It applies each dragon's own level, Star Rank, Habit levels, optional visible Power, and the account-level Dragon's Army capacity upgrade. The result contains the mandatory candidate ledger, a Pareto frontier, deterministic finalists, timing windows, an explicitly limited capacity proxy, and source locators. It does not estimate win rates or invent undocumented combat formulas.

Commanders are not yet inputs to the planner. Their talents, trait synergies, assignments and possible Army Size bonuses are not scored or included in capacity; they can change the practical comparison between formations. Reports disclose this limitation. See the Encyclopedia Commander guide for the official system description and separately labeled installed-client talent text.

The objective-fit axis uses only documented active mechanics. Damage and amplification
components are de-duplicated and use stated magnitudes, target scope, conditions, and
known proc reliability as an ordinal comparison—not a damage simulation. Producer/payoff
chains and scheduled pressure remain separate evidence for high-damage
requests; documented Recovery, Protect, Resistance, mitigation, damage, and timing for
damage-and-survivability requests; active Recovery, Protect, Resistance, Evade, Cleanse,
mitigation, reliability, target coverage, and negative side effects for troop-preservation
requests; exact normalized threat coverage and troop matchup for
counters; and explicit Siege specialization for POI requests. It remains a comparison
axis rather than a universal strength score.

## Run

```powershell
node projects/recommendation-planner/recommend.mjs --input scenario.json --output recommendation.json --pretty
```

The CLI deliberately accepts saved files only. This avoids PowerShell quoting failures,
keeps roster transcription auditable, and ensures the input and output can be retained
together.

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
candidate includes its per-dragon level curve, recorded Star scalar, Dragon's Army
addition, and capacity proxy. The Star scalar is disclosed but never applied because the
installed data does not establish a complete final-stat formula. The proxy is therefore
the raw level curve plus Dragon's Army. For `highest_tile`, total capacity is the primary
documented comparison after hard troop safety. For `troop_preservation`, the weakest
dragon's capacity floor prevents a mechanically elegant but severely under-leveled lane;
documented preservation tier then ranks before total capacity and exact preservation
score. Capacity remains reported for other objectives but does not silently become a
universal score. Preservation component weights are an ordinal planner policy for
comparing documented mechanics; they are not a casualty formula or estimates of saved
troops.

Expert formations are loaded from `data/common_formations.json`. A baseline is reported as `evaluated`, `illegal`, or `inapplicable`, with reasons. Applicability never removes a legal ordinary-combat baseline from the ledger. For endgame portfolios with unknown or partial Power, a complete legal expert portfolio is the conservative default; the strongest mechanics-ranked portfolio remains an explicit alternative.

`competitive_context` accepts `auto`, `endgame`, or `unrestricted`. `auto` resolves to
endgame when at least nine owned dragons are Level 45+ and Rank 6+. In endgame ordinary
combat, Rare dragons are retained for audit but are not strategically qualified unless
they are Thunderstrike or Shadowrend. Siege objectives/troops are scoped exceptions. A
caller may explicitly set `allow_unproven_rare: true`; this is always disclosed.

## Non-overlapping formation portfolios

An unqualified request for any number of formations means a simultaneous,
non-overlapping portfolio. Set `formation_count` and retain the default
`reuse_policy: disjoint_armies`. Use `allow_reuse` only when the user explicitly requests
independent alternatives.

```json
{
  "request_mode": "formation_portfolio",
  "formation_count": 3,
  "reuse_policy": "disjoint_armies",
  "objective": "troop_preservation",
  "roster_preflight": {
    "completeness": "complete",
    "expected_visible_dragons": 9
  },
  "stronghold": {
    "dragons_army": {"current_skill": "III", "current_level": 2}
  },
  "roster": [
    {"dragon": "Velar", "level": 50, "stars": 6, "habit_levels": {}},
    {"dragon": "Vhagar", "level": 50, "stars": 6, "habit_levels": {}},
    {"dragon": "Moondancer", "level": 50, "stars": 6, "habit_levels": {}},
    {"dragon": "Vermithor", "level": 48, "stars": 6, "habit_levels": {}},
    {"dragon": "Rhysarion", "level": 48, "stars": 6, "habit_levels": {}},
    {"dragon": "Tessarion", "level": 47, "stars": 6, "habit_levels": {}},
    {"dragon": "Malachite", "level": 45, "stars": 6, "habit_levels": {}},
    {"dragon": "Seasmoke", "level": 44, "stars": 6, "habit_levels": {}},
    {"dragon": "Kalspire", "level": 43, "stars": 6, "habit_levels": {}}
  ]
}
```

A three-formation disjoint request needs at least nine owned dragons. Screenshot inputs must first pass through
`projects/roster-ingestion/roster.mjs`, and `expected_visible_dragons` must match the
emitted planner profile. The portfolio planner ranks the best troop/lane candidate for
every legal trio, then globally minimizes total candidate-rank cost while enforcing the
reuse policy. It does not select one army and remove its dragons before planning the next,
and it does not restrict allocation to a truncated Pareto list.

Run and retain a deterministic report:

```powershell
node projects/recommendation-planner/recommend.mjs --input portfolio.json --format json --output portfolio-result.json --pretty
node projects/recommendation-planner/recommend.mjs --input portfolio.json --format markdown --output portfolio-report.md
```

Portfolio Markdown is generated from the validated structured result. It includes the
candidate IDs and ranks, allocation attestation, preservation evidence, capacity basis,
risks, evidence locators, common-baseline dispositions, and strongest alternative
portfolio. Do not replace its table with a hand-authored reconstruction.

When ordered subsets of the portfolio have different jobs or eligibility rules, add
`portfolio_groups`. Group counts must sum to `formation_count`. The planner searches each
group under its own objective, applies its constraints before ranking, applies any
explicit rarity preference lexicographically, and then allocates all group slots jointly
under the disjoint-army rule. Rarity preferences record the caller's stated priority;
they are not a universal rarity score.

```json
{
  "request_mode": "formation_portfolio",
  "formation_count": 4,
  "reuse_policy": "disjoint_armies",
  "objective": "highest_tile",
  "portfolio_groups": [
    {
      "id": "primary",
      "label": "Primary tile armies",
      "count": 2,
      "objective": "highest_tile"
    },
    {
      "id": "secondary",
      "label": "Secondary tile armies",
      "count": 2,
      "objective": "highest_tile",
      "constraints": {
        "minimum_dragon_level": 16,
        "minimum_positive_affinities": 2
      },
      "preferences": {
        "affinity_policy": "perfect_unless_explicit_synergy",
        "rarity_order": ["Legendary", "Rare", "Epic"]
      }
    }
  ]
}
```

All recommendation modes apply `perfect_unless_explicit_synergy` by default: target 3/3
positive affinity for the shared troop and admit a lower-affinity candidate only when its
documented explicit-synergy advantage over the highest-synergy eligible 3/3 candidate
with the same competitive qualification is greater than the missing-affinity count.
For grouped requests the comparator is drawn from the same hard-constraint-eligible
group pool, before trio deduplication. It is a candidate-level comparator and does not
attest that the comparator could replace that formation while preserving every other
selected army. When no eligible 3/3 candidate exists in that pool, lower-affinity
candidates remain eligible and the report explicitly says no perfect comparator was
available; it does not claim a synergy override.
Supported group constraints are `minimum_dragon_level` (1–50, applied to every dragon)
and `minimum_positive_affinities` (0–3, counted against the formation's one shared troop
type). `preferences.rarity_order` may contain each of `Rare`, `Epic`, and `Legendary` at
most once. A group may state the default explicitly with
`preferences.affinity_policy: perfect_unless_explicit_synergy`; use a hard
`minimum_positive_affinities: 3` only when no exception is allowed. Grouped portfolios
currently require `reuse_policy: disjoint_armies`. The
structured result includes each slot's group-local candidate rank and a constraint
attestation; output validation fails if any selected formation violates its group.
Group ranks and allocation cost refer to the complete ranked group pool before
competitive or expert filtering. At endgame with incomparable Power, a complete legal,
group-compatible expert portfolio is the conservative default; the mechanics-ranked
portfolio remains the alternative if different.

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

Planner output separates `validation` from `strategic_qualification`. `validation.valid`
checks structure, roster completeness, evidence presence, and non-overlap; it is not an
attestation that the result is a strategically credible endgame recommendation. A caller
must present no definitive recommendation unless both `validation.valid` and
`strategic_qualification.qualified` are true. The Markdown renderer includes the selected formation,
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

