# Game mechanics

## Formation

An army contains three dragons and one configurable troop type shared across the
entire formation. The three dragons cannot each select a different troop type. The
positions are Left Flank, Vanguard, and Right Flank. A dragon's named Vanguard ability
applies when it is level 16+ and deployed in the Vanguard, according to the individual
ability text.

Opposing lanes align by matching position names rather than as a mirrored board:
Left Flank faces Left Flank, Vanguard faces Vanguard, and Right Flank faces Right
Flank. Default Basic Attacks and abilities that target an enemy in the “same lane” use
this alignment. Explicit targeting or redirection mechanics such as `any lane`, lane
priorities, adjacency, Taunt, or Confusion can select a different target. This mapping
is confirmed by a current in-game damage report showing a Right Flank dragon's Basic
Attack hit the enemy Right Flank; equivalent published official wording has not been
found.

The Army Builder can save custom formations and swap configurations even if a dragon
is assigned to another army or has depleted health or stamina. The official launch
announcement says an account can field up to five dragon-led armies simultaneously;
this does not change the three-dragon limit within one formation.

## Troop advantage

`Cavalry → Shieldbearers → Archers → Spearmen → Cavalry`

An advantaged troop deals more damage and takes less damage. A disadvantaged troop
deals less and takes more. Siege is weak to all combat troop types but deals massive
damage to POI Durability.

Affinity is independent of troop-type advantage. Positive affinity boosts the matching
dragon's combat stats, increasing its stat-dependent damage and ability effectiveness,
and also boosts Siege damage. Neutral has no effect, while Negative reduces combat
stats and Siege damage output.

If all three dragons have Positive affinity for the formation's shared troop type, the
formation is **affinity-perfect**: it receives the greatest affinity-derived combat-stat
and damage benefit available to that fixed trio. Troop-type advantage is a separate
matchup bonus: the advantaged army deals more damage to the weak troop type and takes
less damage from it.

Affinity-perfect does not automatically mean best overall. A trio with less affinity
overlap may still outperform it through stronger Commands, Habits, Vanguard effects,
control, Recovery, mitigation, timing, or a better troop counter against the specific
enemy. Use affinity-perfect coverage as a strong damage baseline and tiebreaker, then
optimize the whole formation and matchup.

Troops are generic while trained and stored; one type is selected when the formation
is assigned troops. Choose that single type by weighing the affinities of all three
dragons and the opposing army's troop type. When a dragon runs out of troops, it
retreats to its Stronghold or current garrison. Exact affinity and advantage
multipliers are not publicly documented.

## Damage

| Damage | Enhanced by | Mitigated by |
|---|---|---|
| Physical Damage | Strength | Instinct |
| Tactical Damage | Instinct | Intelligence |
| Fire Damage | Intelligence | Initiative |

## Automated combat and Stalemate

When an army enters a tile containing an enemy army, the armies fight. Combat plays
out automatically: the player does not activate abilities, choose targets, or make
other decisions during the rounds.

If both armies are still fighting after Round 10, combat enters a Stalemate, also
described as a regrouping phase, for 60 seconds. During this window, a player may
recall the army. It returns to the tile it occupied immediately before entering the
contested tile. If neither army is defeated, retreats, or is recalled before the
Stalemate ends, another 10-round automated combat cycle begins. Combat and Stalemate
cycles continue until one army is defeated or retreats/is recalled.

Formation analysis should therefore distinguish early and sustained plans. Opening
effects and Rounds 1-10 determine whether an army can win before the first Stalemate;
mitigation, Recovery, control, and recurring or late schedules determine performance
in later cycles. Most PvP fights include one Stalemate, while some include two. This is
a common observed horizon rather than a cycle limit. There are no manual mid-combat
tactics to recommend.

## Breed roles

| Breed | Role | Strategic identity |
|---|---|---|
| Champion | Suppressor | Protectors that reduce threats and strengthen allies |
| Hunter | Debuffer | Intelligence-based Fire attackers and defense disruptors |
| Sentinel | Buffer | Instinct-based Tactical support, healing, and control |
| Warrior | Enhancer | Strength-based frontline offense amplifiers |

## Recommendation constraint

The Strength, Intelligence, Instinct, Initiative, Stamina, level, XP, current Star
Rank, and army-size values visible on a dragon's Basics screenshot reflect player
progress. They must not be used as general evidence that one dragon is intrinsically
stronger than another.

## Progression and account modifiers

- **Star Rank** persists between Reigns, increases dragon stats, and unlocks Habits.
- **Displayed Stars** are yellow through Rank 5. After that, one red star means Rank 6,
  two red stars means Rank 7, continuing through five red stars at Rank 10. Normalize
  the display to numeric rank before checking Habit unlocks.
- **Reign Level** resets each Reign. It increases maximum army size and the dragon's
  Strength, Instinct, Intelligence, and Initiative.
- **Rarity** is a tendency, not a strict ranking. Legendary kits tend to have more
  advanced and stronger elements than Epic, followed by Rare, but actual abilities,
  unlocks, synergy, and matchup remain decisive. Rare/blue dragons can be exceptional;
  Thunderstrike is a known example. No public numeric rarity multiplier is available.
- **Habit skill level** runs from 1 through 5 and is separate from Star Rank. Breedmarks
  and rarity-matched Rare, Epic, or Legendary Cores upgrade Habits permanently. The
  five values under `upgrade_levels` are these skill levels.
- **Habit investment** is secondary but meaningful. Some Habits are valuable at Level
  1, while chance-based Habits may require levels before they can reliably anchor a
  strategy. Use the known level to refine effectiveness, not as the sole reason to
  select or reject a dragon.
- **Stronghold upgrades** reset with each campaign and can change troop offense/defense,
  PvE damage, Siege damage, dragon stats, breed damage, army size, and reinforcement.
- **Heirloom ranks** persist. Most Heirloom effects require sufficient seasonal House
  Level to activate; Mastery is permanently active regardless of House Level.
- **Campaign Stage and Realm modifiers** can temporarily change rules or costs.

These systems mean that Star ranks alone do not fully explain battle outcomes. Ask for
Reign Level and relevant account or stage modifiers when comparing close matchups.

## PvE and Points of Interest

Every tile has Defenders and Durability. Defenders must be defeated before Siege
damage can reduce Durability, and the tile is conquered at zero Durability. Official
guidance therefore separates combat formations from Siege formations: clear the
Defenders first, then use Siege troops against the structure.

Encounters use Resolve, do not require tile connection, and do not grant ownership.
Some require multiple armies. Wild Dragons are a primary Breedmark source; the
official guide says each breed has a weakness to another breed but does not publish
the mapping.

## Public-rule limits

No reviewed official source publishes the exact combat formula, complete proc order,
formal adjacency geometry, universal status stacking rules, Cleanse selection order,
Recovery modifier order, or battle tiebreak rules. Matching named positions for
same-lane targeting are established by current in-game evidence, but preserve exact
ability wording and do not infer other geometry. See
[Online-Sources.md](Online-Sources.md) for the dated source audit.
