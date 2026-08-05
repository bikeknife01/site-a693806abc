# Game mechanics

## Formation

An army contains three dragons and configurable troops. The positions are Left Flank,
Vanguard, and Right Flank. A dragon's named Vanguard ability applies when it is level
16+ and deployed in the Vanguard, according to the individual ability text.

The Army Builder can save custom formations and swap configurations even if a dragon
is assigned to another army or has depleted health or stamina. The official launch
announcement says an account can field up to five dragon-led armies simultaneously;
this does not change the three-dragon limit within one formation.

## Troop advantage

`Cavalry → Shieldbearers → Archers → Spearmen → Cavalry`

An advantaged troop deals more damage and takes less damage. A disadvantaged troop
deals less and takes more. Siege is weak to all combat troop types but deals massive
damage to POI Durability.

Affinity is independent of troop-type advantage. Positive affinity boosts dragon
stats and Siege damage, Neutral has no effect, and Negative reduces stats and Siege
damage output.

Troops are generic while trained and stored; their type is selected when assigned to
an army. When a dragon runs out of troops, it retreats to its Stronghold or current
garrison. Exact affinity and advantage multipliers are not publicly documented.

## Damage

| Damage | Enhanced by | Mitigated by |
|---|---|---|
| Physical Damage | Strength | Instinct |
| Tactical Damage | Instinct | Intelligence |
| Fire Damage | Intelligence | Initiative |

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
- **Reign Level** resets each Reign. It increases maximum army size and the dragon's
  Strength, Instinct, Intelligence, and Initiative.
- **Rarity** affects Hatchery drop rate and maximum combat power, but no public numeric
  rarity multiplier is available.
- **Habit upgrades** use Breedmarks and Rarity Cores and persist between Reigns.
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
Recovery modifier order, or battle tiebreak rules. Preserve exact ability wording and
do not infer these mechanics. See [Online-Sources.md](Online-Sources.md) for the dated
source audit.
