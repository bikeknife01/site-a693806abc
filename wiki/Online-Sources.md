# Online source audit

Last reviewed: 2026-08-31

This page records public sources checked for game rules and live additions. It is a
source-quality ledger, not a claim that every public strategy opinion is correct.
Exact dragon ability screenshots in this repository remain authoritative for the
audited dragon records.

## Installed-client source reviewed

The locally installed application data under `Game_Details/Resources/` and its
structured extraction under `Game_Details/Resources/_extracted/` were reviewed on
2026-08-31. This is first-party implementation evidence, but it is not a clean list of
released content: the tables also contain WIP dragons, test/balance dragons, NPCs, and
unresolved localization keys. Presence in the client therefore does not establish
release status or player availability.

The useful joined sources are `clean_dragons.csv`, `clean_dragon_habits.csv`,
`dragonCommandsTable_merged.1787687230.json`,
`dragonAffinityTable_merged.1787687230.json`, and `locale_enUS.json`. For all 34
screenshot-audited dragons, the extraction matched breed, Vanguard name, all five
Habit names, and positive/negative troop affinities. It also established a separate
Rare/Epic/Legendary `rarity_tier` for each dragon without replacing screenshot labels
such as Juvenile, Adult, or Elder.

Starshower and Vermithor are complete enough in the client to fill their Vanguard
names/text and several nonnumeric details previously absent from their official
profiles. Meleys is also present with identity, Legendary rarity, Warrior breed,
affinities, Vanguard, Command/Habit names, schedules, targeting, Laceration, and
Reflect behavior. The extraction does not expose resolved Habit upgrade tracks, and
many detailed descriptions retain progression placeholders, so these three remain in
`data/live_updates.json` rather than becoming screenshot-complete dragon records.

`WildDragonTable.1786045129.json` joined to Node Finder strings in `locale_enUS.json`
also resolves the PvE breed weaknesses: Champion Wild Dragons are weak to Warriors,
Sentinels to Hunters, Hunters to Champions, and Warriors to Sentinels. This mapping is
specific to Wild Dragon encounters and is not evidence of a universal PvP breed cycle.

## Source priority

1. Current in-game text and screenshots.
2. Official WB Games support guides and official Dragonfire news/profile pages.
3. Repeated, reproducible player observations with enough battle context.
4. Fan databases and guides for discovery or strategic hypotheses.
5. Tier lists, unsourced summaries, and search snippets only as leads.

When sources conflict, prefer the newest direct evidence and record the conflict rather
than merging incompatible claims.

## Official sources reviewed

| Source | Coverage | Result |
| --- | --- | --- |
| [Official site](https://gotdragonfire.com/) | Current portal and official channel links | No detailed mechanics on the landing page. Links to official news, support, Discord, and social channels. |
| [Official guide hub and glossary](https://news.gotdragonfire.com/dragonfire-guide-hub-glossary/) | Core terminology and guide index | Confirmed troops retreat at zero, Reign/Campaign terminology, map terminology, and progression currencies. |
| [A Guide to Dragons](https://hbogamessupport.wbgames.com/hc/en-us/articles/46520226701459-A-Guide-to-Dragons) | Dragon progression, abilities, troops, breeds | Added Star Rank stat growth, Reign Level stat/army growth, Command activation guidance, troop advantage outcomes, and formation-preset behavior. |
| [The Map of Westeros](https://hbogamessupport.wbgames.com/hc/en-us/articles/46843383089555-The-Map-of-Westeros) | PvE/PvP map, Defenders, Durability, encounters, POIs | Added Defender-before-Durability sequencing, Siege role, garrison behavior, encounter rules, and Wild Dragon breed-weakness caveat. |
| [Stronghold Guide](https://hbogamessupport.wbgames.com/hc/en-us/articles/46842392115987-Stronghold-Guide) | Seasonal upgrades, armies, rarity, barracks | Added generic troop assignment, rarity impact, and account/season modifiers that can make equal dragon formations perform differently. |
| [A Guide to Campaigns](https://hbogamessupport.wbgames.com/hc/en-us/articles/46838575242643-A-Guide-to-Campaigns) | Reigns, stages, resets, durable progress | Added the eight-week Reign model, stage modifiers, reset/durable distinctions, and known campaign names. |
| [Heirloom Guide](https://news.gotdragonfire.com/a-guide-to-upgrades-heirlooms/) | Persistent account upgrades | Added permanent Heirloom ranks, seasonal House Level activation, Amplifiers, and always-active Mastery. |
| [Worldwide release announcement](https://news.gotdragonfire.com/game-of-thrones-dragonfire-is-now-available/) | High-level game model | Confirmed up to five simultaneous dragon-led armies and seasonal Reigns with permanent dragon growth. |
| [World Health dev log](https://news.gotdragonfire.com/dev-log-1/) | World transitions and matchmaking direction | Confirmed Alliances survive transitions while Worlds/Factions may change. Matchmaking statements are dated plans, not combat rules. |
| [Starshower profile](https://news.gotdragonfire.com/starshower-the-wishkeeper/) | New official dragon | Added an incomplete live record and Solar Flare. Exact values and Vanguard text remain unavailable. |
| [Vermithor profile](https://news.gotdragonfire.com/vermithor-the-bronze-fury/) | New official dragon | Added an incomplete live record and Protect. Exact values and Vanguard text remain unavailable. |

No official patch-note archive, combat formula, universal proc order, or published
errata list was found during this audit. Official profile prose can omit values and
Vanguard text, so it must not silently replace complete in-game records.

## Community sources reviewed

| Source | Assessment | Use |
| --- | --- | --- |
| [Dragonfire Hub](https://dragonfire-hub.com/) | Active fan database and lineup builder. Its public guide largely mirrors the in-game effect glossary; detailed blog analysis is commonly Patreon-gated. | Useful for discovery, filtering, and candidate combinations. Verify mechanics against official or in-game text. |
| [Dragonfire Hub guide](https://dragonfire-hub.com/guide) | Repeats damage types, status definitions, and named stack mechanics. | Corroboration only; it did not resolve combat formulas, proc order, adjacency, or Cleanse priority. |
| [Game of Thrones Dragonfire Wiki tier list](https://www.gameofthronesdragonfire.wiki/tier-list) | Launch-stage, explicitly confidence-weighted, but stale enough to mark dragons with complete repository data as pending. | Do not import rankings. Its advice to avoid spreading rare resources is a strategic opinion, not a combat rule. |
| Reddit communities `r/GOTDragonfire` and `r/GOT_DragonFire` | Search surfaced formation posts that primarily link to videos; accessible post text did not provide auditable mechanics. | Leads for testing and meta discussion, not rule authority. |
| RTS Mobile formation videos surfaced through web search | Potential player-tested strategy, but no battle reports or transcripts were available in the inspected results. | Do not encode claims without reproducible matchup context. |

## Still unknown

- Exact damage, affinity, troop-advantage, rarity, and stat-scaling formulas.
- Complete round/action/proc resolution order and battle tiebreak rules.
- Formal geometry for `within adjacency` beyond individual ability text. Current
    in-game damage-report evidence establishes matching named positions for `same lane`,
    but equivalent published official wording has not been found.
- Universal stacking, control-conflict, Cleanse-priority, and Recovery-order rules.
- Full in-game records for Starshower, Vermithor, and Meleys, especially exact values,
  Habit upgrade tracks, current screenshot verification, and Meleys availability.

## User-confirmed in-game clarifications

The following mechanics were confirmed from current gameplay on 2026-08-05 and are
treated as direct observations pending equivalent published official wording:

- Combat starts when an army enters an enemy-occupied tile and resolves automatically
    without player choices during the rounds.
- An unresolved fight enters a 60-second Stalemate/regrouping phase after each
    10-round combat cycle; recall during that phase returns the army to its previous
    tile. If neither army is defeated or leaves, another 10-round cycle begins. The
    cycle repeats until defeat or retreat/recall.
- Most observed PvP fights include one Stalemate and sometimes two. This observation
    describes a common planning horizon, not a maximum number of cycles.
- Opposing lanes align by matching position names for default Basic Attacks and
    `same lane` targeting: Left Flank to Left Flank, Vanguard to Vanguard, and Right
    Flank to Right Flank. Explicit targeting and redirection mechanics can override
    that alignment. A supplied damage report shows a Right Flank Basic Attack hitting
    the enemy Right Flank.
- Stars, rarity, and Habit skill level are distinct progression/selection dimensions.
    Higher Stars do not automatically identify the strongest dragon. Legendary kits tend
    to be more advanced than Epic and Rare, but lower-rarity dragons can be uniquely or
    exceptionally effective.
- Habits have skill levels 1-5 and use Breedmarks plus rarity-matched Rare, Epic, or
    Legendary Cores. Investment changes displayed Habit values and can be especially
    important for activation reliability.

These gaps should be answered with current in-game screenshots or controlled battle
tests. Until then, recommendations must state assumptions and avoid false precision.
