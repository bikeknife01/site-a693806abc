# Recommendation handoff

This handoff describes the screenshot-audited dragon records in `data/dragons/`. Screenshots remain the sole authority for game facts. A recommendation agent should use this catalog for discovery, then cite the exact JSON fields that support each formation choice.

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
  Epic than Rare, but rarity is not absolute. Rare/blue dragons can have exceptional
  output or uniquely valuable mechanics; Thunderstrike is a confirmed example.
- Habit skill level is separate from Star Rank. Breedmarks and rarity-matched Rare,
  Epic, or Legendary Cores raise each Habit from Level 1 through Level 5. Use the
  matching `upgrade_levels` value when known. Treat investment as secondary but
  meaningful: chance-based Habits may need levels before they are reliable, while
  some Habits are strategically valuable at Level 1.

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
| Moondancer | Physical damage, Rising Tide stacks, Sentinel synergy, Bleed | Sentinel ally dealing Tactical Damage or Recovery; Advantage | Damage Dealt and stat debuffs | Rising Tide max 8; thresholds at 4 and 6 stacks; Siege negative |
| Nyrena | Enemy stat/Physical suppression, Fire/Tactical damage, siege/defense support | Burn extends Physical suppression; adjacent Fire ally | Reduces Physical Damage Dealt and late-round allied Physical Damage Received | Round 6+ defense and After Combat Tile Damage; Shieldbearer/Siege affinities |
| Rhysarion | Hybrid damage, Recovery, control payoff | Any Control effect; damage-focused Right Flank | Opening all-combatant Damage Dealt reduction | Ebbing Fury also reduces allies; scheduled rounds matter |
| Seasmoke | Enemy buff removal, Fire/Physical damage, Panic payoff, Recovery suppression | Panic; adjacent Fire allies | Cleanses enemy Positive effects; Infectious Wrath reduces Recovery Received | Infectious Wrath max 3 and follows successful enemy Cleanse; Siege negative |
| Shadowrend | Physical damage, Panic, late-round allied offense, hybrid Round-9 burst | Left Flank benefiting from Instinct/Initiative | — | Major team buffs occur rounds 7-10; Shieldbearer/Siege affinities |
| Shadowsong | Fire/Burn, Panic payoff, Vulnerable | Panic; high-Strength Right Flank | Vulnerable and opening stat/damage-received debuffs | Command rounds 2/5/8; second 10-Star hit must target a different enemy |
| Sheepstealer | Prey, Fire stacks, Recovery suppression, PvE, Evade/Cleanse | Enemy Recovery feeds targeting and payoff | Prey and Wary Beast suppress Recovery | Legendary; Stolen Flock max 10; some bonus text is PvE-only |
| Shimmer | Tactical damage, Recovery, ally buffs, First-Strike | Resistance doubles Recovery; Fire Left Flank | Self/team mitigation | Highest-Strength targeting; Cavalry/Siege affinities |
| Solstryker | Hybrid Basic-Attack damage, Strength erosion, Overwhelm | Vulnerable doubles even-round Tactical damage | Up to 10 Strength-reduction stacks; Overwhelm | Odd/even behavior differs; Archer affinity |
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
| Vesper | Tactical damage, Slow, mitigation/Resistance, Confusion | Instinct-oriented allies | Slow and late-round Confusion | Confusion only rounds 6-10; Shieldbearer affinity; Siege negative |
| Vhagar | Physical damage, broad Taunt, mitigation/Recovery, Bulwark | Burn doubles Taunt chance; Tactical Left Flank | Taunt, Weakened, large opening mitigation | Bulwark max 5 and third-stack trigger; 10-Star Habit is `Skyward Titan` |
| Zivern | Tactical damage/vulnerability, Panic, enemy stat reduction, Overwhelm, team mitigation | Vulnerable doubles Overwhelm chance; Tactical Left Flank | Reduces Strength/Instinct and allied non-Basic Physical/Tactical damage received | Exact scheduled rounds and adjacency scopes; Archer/Siege affinities |

## Limitations and resolved confirmations

There are no unresolved dragon review items. User confirmation established Dawnseeker's 10-Star Habit as `First Light`, Malachite's Command as `Warden's Rally`, Sheepstealer as Legendary, Vermax as Epic, and Vhagar's 10-Star Habit as `Skyward Titan`.

`data/live_updates.json` contains three dragons without screenshot-complete records:
the official `Shadow of the Greens` additions Starshower and Vermithor, plus Meleys,
which is present in installed-client data but whose current availability was not
established. The installed tables add rarity, affinity, Vanguard text, ability names,
targeting, schedules, and some explicit Star gates. Most numeric values, Habit upgrade
tracks, and current screenshot verification remain missing, so use these dragons only
for conditional strategy and disclose the missing evidence. Their named effects Solar
Flare, Protect, Laceration, and Reflect are defined in `data/effects.json`.

Some Habit description text shows rounded values while the five-column table shows more precision (for example `-7%` in prose and `-7.5%` at level 1). Records preserve the displayed prose and all five table values; recommendations needing an upgrade value should cite `upgrade_levels`.

Player-specific Basics values are intentionally excluded. This repository does not establish live balance changes, hidden formulas, proc ordering beyond displayed wording, or mechanics absent from the supplied screenshots.

System-level official rules and source freshness are documented in
`data/game_mechanics.json` and `wiki/Online-Sources.md`. Account-level Reign Level,
Stronghold, Heirloom, Realm, and Campaign Stage modifiers can change battle outcomes;
request them when a close comparison cannot be resolved from dragon kits and Stars.

## Recommendation evidence rules

- Cite the relevant dragon file and fields, for example: `data/dragons/antares.json → command.verbatim[2]`, `vanguard.verbatim`, or `habits[0].upgrade_levels["5"]`.
- State whether a claim is transcribed or derived. Roles, scenario bias, synergies, counters, and preferred position are derived; timings, values, targets, affinities, and effect text are transcribed.
- Never infer an unstated lane, target count, duration, stack cap, cleanse scope, Basic Attack interaction, status interaction, or damage type.
- For default and “same lane” targeting, map Left Flank to enemy Left Flank, Vanguard
  to enemy Vanguard, and Right Flank to enemy Right Flank. Never mirror Left and Right;
  apply explicit targeting or redirection mechanics when stated.
- Check `review` before using a fact. If a recommendation depends on an unresolved item, disclose it and offer an alternative that does not depend on it.
- Compare Vanguard effects across the whole proposed trio. Do not place every dragon in Vanguard merely because its individual record says that position is useful.
- Cite all three dragons' positive/negative affinity fields when choosing the one shared
  formation troop type, and separately cite `data/game_mechanics.json` when using troop
  matchup advantage.
- Check `data/live_updates.json` when a named dragon has no record under `data/dragons/`.
  Use only explicitly recorded official-profile or installed-client evidence. Never
  infer missing Star gates, values, upgrade tracks, release status, or availability.
- For POI assaults, distinguish the combat formation that clears Defenders from the
  Siege formation that reduces Durability.
