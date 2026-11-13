# Recommendation handoff

This handoff describes the recommendation data set. Apply the ordered contract in
`data/recommendation_rules.json`, then use `data/dragon_application_knowledge.json` to
discover the complete production-named client roster and obtain level-specific base
stats. Load `data/common_formations.json` for every formation recommendation so the
user-confirmed expert-recommended formations enter the candidate ledger with their
formation-level prior whenever legal for an ordinary combat recommendation.
For reviewed dragons, `data/dragons/<name>.json` remains primary for exact mechanics.
Its optional `evidence` block distinguishes screenshot-audited records from explicitly
approved cross-site verification. Client-only records must be labeled as such and their
evidence limitations disclosed.

Expert formations are positive recommendation priors and comparison baselines, not fixed winners or sacrificial controls.
Recompute them under the player's actual roster, levels, Stars, Habit levels, Power, and
troop availability. Apply the same objective, mechanics, lane, reliability, timing, and
matchup tests used for newly constructed candidates. Applicability tags affect the
comparison but do not remove a legal baseline. Do not exclude or down-rank a common
formation because it is a baseline. When endgame Power is not comparable and a complete
legal expert portfolio exists, use it as the conservative default while preserving the
mechanically ranked portfolio as an alternative. Known comparable Power or material
objective, matchup, progression, or availability evidence may displace that prior.

When shell execution is available and the required progression inputs are known, run
`projects/recommendation-planner/recommend.mjs` using the input contract documented in
`projects/recommendation-planner/README.md`. It deterministically enumerates owned trios,
lane orders, and available shared troop types; retains every legal common baseline;
constructs the required candidate ledger; computes a Pareto frontier; and emits timing,
overlap, progression, tradeoff, and evidence-locator records. Its primary candidate is a
documented lexicographic choice among nondominated results, not a predicted winner. Verify
decisive wording in the cited canonical source and preserve alternatives when unknown
combat formulas could reverse the ordering.

For multiple enemy formations, submit one `scenarios` batch to that planner and retain
its validated JSON or deterministic Markdown report. Explicitly declare whether the
request is one counter per matchup or several finalists per matchup, and whether a dragon
may be reused across hypothetical battles. The batch contract resolves the three common
formations by canonical ID, records roster completeness and screenshot star
normalization, emits a per-threat coverage matrix, progression gates, evidence, common
baseline dispositions, alternatives, reversal conditions, and risks, and fails closed
when a required audit field is absent. Do not reconstruct or summarize a multi-matchup
recommendation from an unverified delegated response.
The batch report distinguishes `direct`, `probabilistic`, `partial`, and `none` coverage
using the ability's chance, target scope, duration, prerequisites, and damage exclusions.
Read the remaining gap beside each enemy source instance. A lineup screenshot establishes
dragon progression but does not establish available shared troop types or actual enemy
progression; identify those as assumptions when the user has not supplied them.

## Required recommendation inputs and level handling

Ask for each candidate dragon's **level**, **Star Rank**, and unlocked Habits' **skill
levels** before making a close power comparison. Read
`level_model.base_stats_by_level.<stat>.values_by_level[level - 1]` from
`data/dragon_application_knowledge.json`; the index is zero-based while the game level
is one-based. These are client-derived base values for Strength, Intelligence, Instinct,
Initiative, and Max Army Size.

- Dragon Level is separate from Star Rank and Habit level. Combat experience and Meat
  raise Dragon Level but never raise Star Rank. Star Rank increases only through the
  dragon-specific Relics obtained from opened Dragon Chests.
- Star Ranks 2, 4, 6, 8, and 10 each unlock one Habit. Unlocking a Habit does not raise
  its skill level; Breedmarks and the Core matching the dragon's Rare, Epic, or
  Legendary rarity raise that Habit separately from Level 1 through Level 5.
- The client provides separate `star_scalars` but does not establish a complete public final-stat formula. Do not manufacture one or apply `base × (1 + scalar)`. The planner's capacity proxy uses the raw level curve plus the confirmed Dragon's Army bonus, discloses the scalar without applying it, and keeps this distinct from an observed in-game capacity.
- Base stats are strategically meaningful: Strength enhances Physical damage and mitigates Physical damage through the defender's Instinct; Instinct enhances Tactical damage and mitigates it through the defender's Intelligence; Intelligence enhances Fire damage and mitigates it through the defender's Initiative. Treat Troop Capacity as the army's practical health pool: higher maximum army size increases staying power before depletion and affects explicit troop-capacity thresholds. For highest-tile or troop-preservation recommendations, compare the candidates' explicitly limited level-curve-plus-Dragon's-Army capacity proxies before preferring a mechanically elegant but materially lower-level formation. Do not describe that proxy as observed or final in-game capacity.
- If levels are unknown, make a kit-and-synergy recommendation only, label it level-agnostic, and say that the choice may change with actual levels and Stars.

The 38 included production-named client rows have screenshot-audited canonical dragon records. WIP, test, NPC, wild, balance-test, and
unresolved rows are deliberately excluded. Meleys and Smoketail are user-confirmed
Season 3 available dragons, and both are screenshot audited.

## Canonical JSON schema

Each `data/dragons/<name>.json` record uses the following keys:

| Key | Meaning |
|---|---|
| `name` | Exact dragon name displayed on the Basics panel. |
| `breed` | Displayed breed: Champion, Hunter, Sentinel, or Warrior. Breed role definitions are in `data/game_mechanics.json`. |
| `rarity_label` | Exact displayed classification or explicitly user-confirmed rarity. Existing values such as Elder, Adult, and Juvenile must not be silently converted to Rare, Epic, or Legendary. Record rarity tier separately when directly established. |
| `rarity_tier` | Installed-client rarity classification: Rare, Epic, or Legendary. This is separate from `rarity_label` and does not replace the displayed age-style label. |
| `troop_affinities.positive` | Troop types shown with positive affinity. These boost dragon stats and Siege damage. |
| `troop_affinities.negative` | Troop types shown with negative affinity. These reduce dragon stats and Siege damage output. An empty array means no negative icon was displayed; it does not prove every unlisted troop is beneficial. |
| `troop_affinities.review_required` | Optional legacy flag indicating uncertainty in affinity extraction. Consult `review` regardless. |
| `excluded_progression_snapshot` | Basics-panel values excluded from cross-dragon recommendations because they reflect the player's current progression rather than stable dragon mechanics. |
| `command.name` | Exact detailed Command title. Check `review` for source conflicts. |
| `command.type` | Displayed type, usually `Active` or `Attack Modifier`. |
| `command.verbatim` | One string or an ordered array combining all Command continuation panels. It preserves timing, targets, damage types, conditions, rates, durations, priority, and star gates. This is the primary recommendation evidence. |
| `command.structured` | Optional normalized tags and synergy inputs/outputs. Useful for retrieval, but never override `verbatim`. |
| `vanguard.name` | Exact Vanguard ability name. |
| `vanguard.unlock_level` | Required dragon level, normally 16. |
| `vanguard.verbatim` | Exact placement requirement, self effect, affected flank, stats, and values. |
| `vanguard.structured` | Optional target/stat normalization. If absent, parse only the explicit `verbatim` wording. |
| `habits` | Exactly five records, unlocked at 2, 4, 6, 8, and 10 Stars. |
| `habits[].star_unlock` | Required Star rank for the Habit. |
| `habits[].name` | Displayed Habit title. Check `review` if a title is cropped. |
| `habits[].verbatim` | Screenshot wording for triggers, targets, exclusions, durations, priorities, stacks, and status behavior. |
| `habits[].upgrade_levels` | All five displayed level columns. Scalar tracks map levels `1`–`5` to values; multi-stat tracks map each level to a named object. |
| `habits[].value_unit` | Optional normalized unit label. |
| `habits[].tags` | Optional normalized retrieval tags. |
| `derived.roles` | Strategic classification supported by Command, Vanguard, or Habit evidence. It is derived, not in-game text. |
| `derived.preferred_position` | Optional suggested slot. Treat as conditional: every Vanguard ability requires Vanguard, but only one formation dragon can occupy that slot. |
| `derived.preferred_troops` | Troop types supported by this dragon's positive affinity. This is candidate evidence for the formation's one shared troop type, not a per-dragon troop assignment. Still test opposing troop matchups. |
| `derived.avoid_troops` | Troops with displayed negative affinity. Absence of this optional key is equivalent to no recorded avoidance beyond `troop_affinities.negative`. |
| `derived.formation_needs` | Optional enabling effects or flank partners inferred directly from explicit mechanics. |
| `derived.scenario_bias` | Optional heuristic scores, not source facts. Do not cite them as mechanics. |
| `derived.notes` | Optional qualified strategic interpretation. |
| `review` | Precise unresolved source conflicts, crops, or missing required facts. A non-empty array must be disclosed in recommendations that depend on the affected fact. |
| `evidence` | Optional provenance block for a reviewed canonical record whose authority is not the default screenshot audit. `cross_site_confirmed` records are usable with source disclosure and yield to contradictory current-client evidence. |

## Client knowledge schema

`data/dragon_application_knowledge.json` is the canonical application-data index:

| Key | Meaning |
|---|---|
| `dragons[].recommendation_status` | `screenshot_audited` and `cross_site_verified` permit use of the matching canonical mechanics record, with provenance disclosure for the latter. `client_discovered` is usable only with the documented caveats. |
| `dragons[].availability_status` | Separates `screenshot_observed`, `campaign_observed`, `user_confirmed_available`, and `installed_unverified`; installed-unverified dragons are conditional only and never default recommendations. |
| `dragons[].level_model.max_level` | Maximum level exposed by the current client row. |
| `level_model.base_stats_by_level` | Exact client curve per stat, ordered levels 1–50. Use the player-reported level. |
| `level_model.star_scalars` | Separate client Star scaling curves. Never treat them as a complete final-stat formula unless that formula is established. |
| `dragons[].troop_affinities` | Installed-client positive, negative, and neutral affinity values joined from the current affinity table. Screenshot-audited affinity fields remain primary when available. |
| `client_ability_slots` | Client command and six ability slots, including the Breed/Vanguard ability in slot 1. `description_template` can contain unresolved progression tokens, so it supplements but never overrides screenshot wording. |
| `recommendation_evidence` | Availability and missing-evidence disclosures required for client-discovered dragons. |

## Mechanics glossary

| Term | Source-supported meaning |
|---|---|
| `Physical Damage` | Enhanced by Strength and mitigated by Instinct. Some clauses explicitly exclude Basic Attacks. |
| `Tactical Damage` | Enhanced by Instinct and mitigated by Intelligence. |
| `Fire Damage` | Enhanced by Intelligence and mitigated by Initiative. |
| `Basic Attack` | The normal attack. Clauses marked “excluding Basic Attacks” apply only to other Physical damage; Attack Modifier Commands trigger from or alter Basic Attacks as stated. |
| `Bleed` | Harmful Physical Damage each round for 2 rounds. |
| `Panic` | Harmful Tactical Damage each round. |
| `Burn` | Harmful Fire Damage each round. |
| `First-Strike` | Acts before all other combatants each round. |
| `Double-Strike` | Grants a second Basic Attack each round. |
| `Recovery` | Restores troops. Distinguish Recovery Dealt, Recovery Received, and Recovery Rate. |
| `Advantage` | Increases Damage Dealt. |
| `Resistance` | Reduces Damage Received. |
| `Slow` | Acts after all other combatants each round. |
| `Weakened` | Reduces Damage Dealt. |
| `Vulnerable` | Increases Damage Received. |
| `Prey` | Reduces Recovery Received by 30% in Sheepstealer's supplied Command panel; shared generic wording outside that panel is less specific. |
| `Evade` | Each incoming damage instance has a chance to be ignored. |
| `Cleanse` | Removes negative effects from an Ally or positive effects from an Enemy, as the ability specifies. |
| `Taunt` | Forces the target's Basic Attack against the taunting dragon. |
| `Stun` | Prevents Commands, Habits, and Basic Attacks on the target's turn. |
| `Overwhelm` | Prevents Active Commands and Habits on the target's turn. |
| `Stagger` | Prevents Attack Modifier Commands and Basic Attacks on the target's turn. |
| `Confusion` | Gives a 50% chance to mistake Allies for Enemies and vice versa when using a Command, Habit, or Basic Attack. |
| `Fire Ward`, `Resilient Bond`, `Rising Tide`, `Mirage`, `Stolen Flock`, `Infectious Wrath`, `Rallying Flame`, `Spreading Blaze`, `Steady Erosion`, `Bulwark` | Named stack mechanics. Their caps, gains, consumers, affected stats, and durations are dragon-specific; cite the relevant Habit or Command rather than generalizing. |

The game's effect menu places Bleed, Panic, and Burn under “Positive Effects,” but all three harm the afflicted target. Use `effect_on_target` from `data/effects.json` and the dragon wording, not the menu heading, when reasoning about benefit or harm.

## Formation interpretation

- A formation has `left_flank`, `vanguard`, and `right_flank`. Opposing lanes align by
  matching name rather than mirroring: Left Flank faces Left Flank, Vanguard faces
  Vanguard, and Right Flank faces Right Flank. “Same lane” and default Basic Attacks
  use that matching position. Explicit scopes and mechanics such as “any lane,” lane
  priorities, adjacency, Taunt, or Confusion can override or redirect the default.
  “Within adjacency” is not interchangeable with “any lane”; preserve the displayed
  scope.
- A formation selects exactly one troop type shared by all three dragons. Do not assign
  troop types independently by lane. Compare the candidate troop type against every
  dragon's affinity and separately against the opposing formation's shared troop type.
- Star displays are yellow through Rank 5. One red star is Rank 6, two red stars is
  Rank 7, and so forth through five red stars at Rank 10. Normalize the display before
  applying `star_unlock` gates.
- Vanguard abilities activate only at the displayed level requirement and only while the dragon is deployed in Vanguard. Compare all three candidate Vanguard effects before assigning the slot; a record's `preferred_position` is not a mandate.
- A Vanguard clause affecting the Left or Right Flank is directional. Do not move the intended recipient to the other flank.
- Round lists are exact schedules. “Each Round,” “Odd-numbered Rounds,” a range such as `Rounds 6-10`, and a list such as `Rounds 1, 4, 6, 9` are distinct.
- Priority wording does not guarantee that the prioritized target exists. Preserve fallback scope such as “in any lane,” “same lane,” or “within adjacency.”
- Positive affinity supplies candidate evidence for the formation's shared troop type;
  negative affinity weighs against that shared choice. A trio may require a compromise
  when their affinities differ. When all three dragons have Positive affinity for the
  shared type, classify the formation as affinity-perfect: this maximizes the
  affinity-derived combat-stat and damage benefit for that fixed trio. Separately
  account for the troop cycle: Cavalry > Shieldbearers > Archers > Spearmen > Cavalry.
  Troop advantage directly improves damage dealt and reduces damage received in that
  matchup. Siege is disadvantaged against all combat troop types and specializes in
  POI Durability damage.
- Treat affinity-perfect coverage as a strong damage baseline and tiebreaker, not an
  absolute formation rule. Explicit Command/Habit/Vanguard synergies, control,
  mitigation, Recovery, timing, enemy troop counters, and scenario objectives may
  outweigh perfect affinity overlap. State the compensating value whenever the
  recommendation gives up an available affinity-perfect option.
- Values in `upgrade_levels` are the five displayed Habit levels, not five Star unlocks. The Habit itself unlocks at `star_unlock`.
- Combat begins when an army enters a tile containing an enemy army and resolves
  automatically without player choices during rounds. If both armies remain after a
  10-round cycle, a 60-second Stalemate/regrouping phase begins. During that window, a
  player may recall the army to the tile it occupied before entering the contested
  tile. If neither army is defeated or leaves, another 10-round cycle begins. Combat
  and Stalemate repeat until one army is defeated or retreats/is recalled.
- Evaluate both opening and sustained performance. Most PvP fights include one
  Stalemate and sometimes two, so compare plans into the second combat cycle and, when
  relevant, the third, while treating neither as a fixed cap or assuming every round
  completes. Do not suggest manual ability activation, targeting, or timing during any
  combat cycle.
- Star Rank controls stat growth and Habit unlocks but is not a direct power ranking.
  Legendary dragons tend to have more advanced/stronger kit elements than Epic, and
  Epic than Rare, but rarity is not absolute. In endgame ordinary combat, Rare dragons
  are strategically gated unless reviewed as exceptions; Thunderstrike and Shadowrend
  are confirmed exceptions, and Siege use is scoped separately. This is not a universal
  strength ranking and may be explicitly overridden with disclosure.
- Habit skill level is separate from Star Rank. Breedmarks and rarity-matched Rare,
  Epic, or Legendary Cores raise each Habit from Level 1 through Level 5. Use the
  matching `upgrade_levels` value when known. Treat investment as secondary but
  meaningful: chance-based Habits may need levels before they are reliable, while
  some Habits are strategically valuable at Level 1.

## Recommendation decision order

Use this order rather than a generic “best dragon” ranking:

1. **Eligibility:** exclude dragons the player does not own, Habits not unlocked at the reported Star Rank, and Vanguard effects unavailable below level 16. Keep client-discovered dragons conditional.
2. **Objective and enemy:** distinguish PvP, defender-clearing, POI Durability/Siege, campaign, and Wild Dragon targets. Apply enemy troop matchup and explicit counters before broad role labels.
3. **Comparable progression:** compare the three candidates' level curves only at their reported level and only with Star Rank called out. A high-level stat advantage is meaningful only for the damage type or mitigation relation the kit actually uses.
4. **Mechanics chain:** prefer explicit producer → payoff chains (for example Burn → a Burn payoff, Bleed → a Bleed payoff, or Tactical damage/Recovery → a named stack) over two dragons merely sharing a broad role. Respect trigger rounds, target scope, duration, stack cap, and chance.
5. **Position:** select one Vanguard by comparing the trio's active Vanguard effects, then put the named Left/Right Flank beneficiary in the correct flank. Do not optimize three individual Vanguard effects simultaneously.
6. **Shared troops:** choose one troop type for all three dragons. Score positive/negative affinity coverage separately from the troop counter cycle and scenario objective; explain any deliberate compromise.
7. **Confidence:** cite the facts used, distinguish transcribed facts from derived judgment, and state the missing input most likely to change the result.

Do not turn level, rarity, affinity, or derived role labels into a universal numeric score. They are decision factors whose value depends on the exact damage type, Star/Habit gate, enemy, timing, and formation context.

## Compact dragon catalog

“Counters/pressure” below is derived only from explicit effects; a dash means no direct counter clause is asserted.

| Dragon | Supported roles | Synergies / inputs | Counters or pressure | Constraints |
|---|---|---|---|---|
| Antares | Fire damage, Vulnerable, Slow payoff, damage amplification | Reliable Slow; Physical Right Flank benefits from Strength/Initiative | Amplifies Fire and non-Basic Physical damage received | 6-Star recurring damage requires Slowed enemies; Archer affinity; Siege negative |
| Arrax | Physical damage, Weakened, team mitigation | Bleed doubles Weakened chance; Tactical Left Flank | Reduces allied Tactical/Fire damage received | Defensive Habit changes with Archer vs Shieldbearer troops |
| Arulix | Overwhelm/Stagger control, anti-damage, stat debuff, effect copying | Allies exposing Weakened/Vulnerable; durable Right Flank | Reduces Fire damage dealers and attacks non-Basic Physical dealers | Control rounds and target priorities are fixed; Cavalry affinity |
| Bevlorin | Hybrid damage, anti-Fire, Recovery, stat support | Long fights; damage-focused Right Flank | Reduces enemy Fire Damage Dealt; Fire Ward | Recovery occurs on odd rounds at 6+ Stars; Spearmen affinity |
| Caraxes | Fire burst, Slow/Burn, First-Strike payoff, finisher | First-Strike | Debuffs non-Basic Physical damage; scales as enemies retreat/lose troops | Command fires only rounds 3/6/9; Spearmen/Cavalry affinities |
| Crimson | Fire damage, Stun, Weakened, low-troop suppression | Taunt doubles Weakened chance; Physical Right Flank | Stun and stat reduction; reduces low-troop Recovery | Capacity thresholds and odd/even schedules; Spearmen/Archers/Siege affinities |
| Daemoros | Physical damage, Burn, Panic, Confusion | Tactical Left Flank from Vanguard | Confusion and adaptive damage-type mitigation | Command only odd rounds; Archer affinity |
| Dawnseeker | Tactical damage, Recovery, Initiative, First-Strike provider | Fire Left Flank; teams needing Recovery/turn order | First-Strike tempo | 10-Star Habit is `First Light`; Spearmen affinity; Siege negative |
| Feskar | Physical suppression, Tactical finisher, Burn payoff, Stagger | Burn; durable Right Flank | Reduces highest-Strength enemy's non-Basic Physical damage; prioritizes Warriors for Stagger | Six-star Fire clause targets Physical dealers; Cavalry affinity; Siege negative |
| Jagadrix | Fire damage, Initiative/Instinct debuff, Panic payoff | Panic; high-Strength Right Flank | Weakened and stat reduction | Same-lane base attacks; later all-enemy payoff only against Tactical dealers |
| Kalspire | Basic-Attack modifier, hybrid damage, Bleed/Panic, stat debuff | Basic Attacks; Right Flank needing mitigation | Reduces enemy Strength/Intelligence; self Stun trades for opening mitigation | Screenshot filenames for Command/Vanguard are swapped, but panel contents are clear |
| Malachite | Tactical damage, Recovery, Advantage, ally stat/turn-order support | Fire Left Flank; adjacent ally for First-/Double-Strike | Temporary ally mitigation | Command confirmed as `Warden's Rally`; Cavalry/Shieldbearer affinities; Siege negative |
| Meleys | Physical damage, Laceration, Initiative pressure, Reflect, Bleed payoff | Bleed; high Initiative; Tactical Left Flank | Targets highest Initiative; Vulnerable/Physical vulnerability; reflects Basic Attacks | Screenshot audited; Royal Rend otherwise chance unspecified; Cavalry/Archer affinities; Siege negative |
| Moondancer | Physical damage, Rising Tide stacks, Sentinel synergy, Bleed | Sentinel ally dealing Tactical Damage or Recovery; Advantage | Damage Dealt and stat debuffs | Rising Tide max 8; thresholds at 4 and 6 stacks; Siege negative |
| Nyrena | Enemy stat/Physical suppression, Fire/Tactical damage, siege/defense support | Burn extends Physical suppression; adjacent Fire ally | Reduces Physical Damage Dealt and late-round allied Physical Damage Received | Round 6+ defense and After Combat Tile Damage; Shieldbearer/Siege affinities |
| Rhysarion | Hybrid damage, Recovery, control payoff | Any Control effect; damage-focused Right Flank | Opening all-combatant Damage Dealt reduction | Ebbing Fury also reduces allies; scheduled rounds matter |
| Seasmoke | Enemy buff removal, Fire/Physical damage, Panic payoff, Recovery suppression | Panic; adjacent Fire allies | Cleanses enemy Positive effects; Infectious Wrath reduces Recovery Received | Infectious Wrath max 3 and follows successful enemy Cleanse; Siege negative |
| Shadowrend | Physical damage, Panic, late-round allied offense, hybrid Round-9 burst | Left Flank benefiting from Instinct/Initiative | — | Major team buffs occur rounds 7-10; Shieldbearer/Siege affinities |
| Shadowsong | Fire/Burn, Panic payoff, Vulnerable | Panic; high-Strength Right Flank | Vulnerable and opening stat/damage-received debuffs | Command rounds 2/5/8; second 10-Star hit must target a different enemy |
| Sheepstealer | Prey, Fire stacks, Recovery suppression, PvE, Evade/Cleanse | Enemy Recovery feeds targeting and payoff | Prey and Wary Beast suppress Recovery | Legendary; Stolen Flock max 10; some bonus text is PvE-only |
| Shimmer | Tactical damage, Recovery, ally buffs, First-Strike | Resistance doubles Recovery; Fire Left Flank | Self/team mitigation | Highest-Strength targeting; Cavalry/Siege affinities |
| Solstryker | Hybrid Basic-Attack damage, Strength erosion, Overwhelm | Vulnerable doubles even-round Tactical damage | Up to 10 Strength-reduction stacks; Overwhelm | Odd/even behavior differs; Archer affinity |
| Smoketail | Fire damage, Burn, Weakened payoff, stat suppression, Champion counter | Reliable Weakened; Right Flank benefiting from Strength/Initiative | Reduces Tactical/Fire output, stats, and raises Fire Damage Received | Screenshot audited; Spearmen affinity; Unraveled scales per Weakened enemy, with a separate Champion track |
| Starshower | Tactical damage, Solar Flare consumption, Cleanse/Evade, enemy stat reduction, ally mitigation | Resistance strengthens 10-Star mitigation; Advantage expands it to all Allies; Tactical Left Flank | Reduces all-enemy Intelligence/Initiative and applies same-lane Tactical vulnerability | Solar Flare consumption is 50% chance; Night Guardian remains chance-based; Tactical Breach table-label conflict is recorded in review |
| Sunfyre | Tactical/Fire damage, Burn, anti-Fire, Cleanse, low-troop defense | Benefits when below 75%/50% troop capacity | Reduces enemy Fire Damage and Intelligence | Several effects depend on first damage received each round and damage type |
| Syrax | Tactical damage, Fire/First-Strike support, Recovery/Cleanse | Fire ally; Slow increases Recovery; Control cleansing | Teamwide stat/Initiative shifts and multi-effect Cleanse | Recovery on rounds 2/5/8; Spearmen/Archers affinities; Siege negative |
| Tairax | Fire/Burn, Stagger, control payoff, Resistance/Evade | Any Control effect; Burn produces Resistance chances | Raises damage received of controlled enemies | Same-lane base clause; exact odd/2-5-8 schedules; no direct negative affinity |
| Tashix | Mirage Fire scaling, Tactical/Initiative debuff, Weakened | Enemy Tactical dealers increase Weakened chance | Reduces Tactical Damage Dealt and enemy stats | Mirage max 10; thresholds at 4 and 7; 7-stack burst once per combat; Siege negative |
| Tessarion | Fire/Physical damage, Fire ally support, mitigation, Panic payoff | Fire ally; Panic extends self mitigation | Reduces enemy Damage Dealt and allied Physical Damage Received | Several odd-round/capacity conditions; Spearmen/Cavalry/Siege affinities |
| Thunderstrike | Physical damage, Bleed, Stagger, Initiative | Advantage doubles Stagger duration | Armor Break raises enemy Physical Damage Received | Command split by odd/even rounds; Cavalry affinity |
| Vaeldra | Taunt, Physical damage, mixed damage amplification | Fire/Physical flank attackers | Taunt; converts already-Taunted enemies to Stagger | Taunt-triggered amplification excludes Basic Attacks for Physical damage |
| Velar | Tactical damage, Advantage, First-Strike/Slow, Recovery/Cleanse | Initiative scaling; teams vulnerable to Bleed/Panic/Burn | Cleanses all allies and applies Slow | Command's Cleanse/Recovery is 10-Star gated; Shieldbearer affinity |
| Venator | Basic-Attack Physical damage, Hunter counter, Double-Strike, Overwhelm | More Basic Attacks/Double-Strike | Prioritizes Hunters and least-troop enemies | Attack Modifier; low-capacity 10-Star trigger; Spearmen/Shieldbearer affinities |
| Vermax | Physical damage, Fire-reactive stacking support, mitigation | Enemy Fire dealers add stack attempts; Tactical ally receives Spreading Blaze | Fire mitigation thresholds | Epic; Rallying Flame max 4, Spreading Blaze max 10 |
| Vermithor | Hybrid Physical/Tactical damage, Protect, self-mitigation, Physical/Fire suppression | Adjacent Ally for Protect; Right Flank Ally when deployed Vanguard | Prioritizes Warriors for Physical suppression and Hunters for Fire suppression; 8-Star mitigation scales with enemy breeds | Noble Sacrifice's Tactical vulnerability falls to 0% only at Habit Level 5; 6-Star Bronze Bulwark materially improves damage and Protect reliability |
| Vesper | Tactical damage, Slow, mitigation/Resistance, Confusion | Instinct-oriented allies | Slow and late-round Confusion | Confusion only rounds 6-10; Shieldbearer affinity; Siege negative |
| Vhagar | Physical damage, broad Taunt, mitigation/Recovery, Bulwark | Burn doubles Taunt chance; Tactical Left Flank | Taunt, Weakened, large opening mitigation | Bulwark max 5 and third-stack trigger; 10-Star Habit is `Skyward Titan` |
| Zivern | Tactical damage/vulnerability, Panic, enemy stat reduction, Overwhelm, team mitigation | Vulnerable doubles Overwhelm chance; Tactical Left Flank | Reduces Strength/Instinct and allied non-Basic Physical/Tactical damage received | Exact scheduled rounds and adjacency scopes; Archer/Siege affinities |

## Limitations and resolved confirmations

Starshower has one documented UI-label conflict: Tactical Breach's sentence says
`Tactical Damage Received`, while its five-column upgrade row says `Damage Dealt`.
The canonical values follow the explicit sentence and installed description, and the
conflict remains in `review`. User confirmation established Dawnseeker's 10-Star Habit
as `First Light`, Malachite's Command as `Warden's Rally`, Sheepstealer as Legendary,
Vermax as Epic, and Vhagar's 10-Star Habit as `Skyward Titan`.

Meleys and Smoketail are user-confirmed available Season 3 dragons with complete
cross-site-verified canonical records. Use them with source disclosure; do not call
them screenshot audited. Starshower and Vermithor are screenshot complete. Their named
effects Solar Flare, Protect, Laceration, Reflect, and Burn are defined in
`data/effects.json`. Consult `data/installed_evidence.json` for lifecycle and evidence
classification before using any installed-only behavior.

Some Habit description text shows rounded values while the five-column table shows more precision (for example `-7%` in prose and `-7.5%` at level 1). Records preserve the displayed prose and all five table values; recommendations needing an upgrade value should cite `upgrade_levels`.

Basics screenshots are historical player snapshots and are not used as cross-player facts. The client level curves replace them for level-aware comparisons. This repository still does not establish live balance changes, the formula combining base values and Star scalars, proc ordering beyond displayed wording, or mechanics absent from the supplied screenshots.

System-level official rules and source freshness are documented in
`data/game_mechanics.json` and `wiki/Online-Sources.md`. Account-level Reign Level,
Stronghold, Heirloom, Realm, and Campaign Stage modifiers can change battle outcomes;
request them when a close comparison cannot be resolved from dragon kits and Stars.

## Recommendation evidence rules

- Compare the proposed leader with every legal entry in
  `data/common_formations.json`. State briefly why each baseline wins, loses, or is
  inapplicable. If a common formation is strongest, return it as the recommendation and
  compare it with the strongest non-baseline challenger.
- Keep `validation.valid` and `strategic_qualification.qualified` distinct. Structural
  validity proves count, non-overlap, roster preflight, IDs, and evidence—not endgame
  strategic credibility.
- Cite the relevant dragon file and fields, for example: `data/dragons/antares.json → command.verbatim[2]`, `vanguard.verbatim`, or `habits[0].upgrade_levels["5"]`. For level-sensitive claims, also cite `data/dragon_application_knowledge.json → dragons[name=Antares].level_model.base_stats_by_level.strength.values_by_level[level - 1]`.
- State whether a claim is transcribed or derived. Roles, scenario bias, synergies, counters, and preferred position are derived; timings, values, targets, affinities, and effect text are transcribed.
- Check `data/installed_evidence.json` before using client-derived changes. Respect its
  `recommendation_use`: `exclude` never affects live recommendations,
  `corroboration_only` cannot create a mechanic absent from explicit wording, and
  `conditional_only` requires an installed-client qualifier and missing-field disclosure.
- Never infer an unstated lane, target count, duration, stack cap, cleanse scope, Basic Attack interaction, status interaction, or damage type.
- For default and “same lane” targeting, map Left Flank to enemy Left Flank, Vanguard
  to enemy Vanguard, and Right Flank to enemy Right Flank. Never mirror Left and Right;
  apply explicit targeting or redirection mechanics when stated.
- Check `review` before using a fact. If a recommendation depends on an unresolved item, disclose it and offer an alternative that does not depend on it.
- Compare Vanguard effects across the whole proposed trio. Do not place every dragon in Vanguard merely because its individual record says that position is useful.
- Cite all three dragons' positive/negative affinity fields when choosing the one shared
  formation troop type, and separately cite `data/game_mechanics.json` when using troop
  matchup advantage.
- Check `data/dragon_application_knowledge.json` when a named dragon has no record
  under `data/dragons/`. Use only explicitly recorded client evidence and disclose
  its `recommendation_evidence` limitations. Never infer missing Star gates, values,
  upgrade tracks, release status, availability, or a final-stat formula.
- For POI assaults, distinguish the combat formation that clears Defenders from the
  Siege formation that reduces Durability.
