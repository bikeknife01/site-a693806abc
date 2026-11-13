# Online source audit

Last reviewed: 2026-10-12

This page records public sources checked for game rules and live additions. It is a
source-quality ledger, not a claim that every public strategy opinion is correct.
Exact dragon ability screenshots in this repository remain authoritative for the
audited dragon records. Matching Dragonfire Hub and Dragonfire Sim claims accepted
under the user's 2026-10-12 direction are labeled cross-site verified rather than
screenshot audited and yield to contradictory current-client evidence.

## Installed-client source reviewed

The 2026-10-01 local snapshot of client `26.9.56700` (`versionCode` 326) and its
structured analysis under `Game_Details/Resources/_snapshots/2026-10-01/` were
reviewed against the 2026-09-16 client `26.9.56160`. This is first-party implementation
evidence, but it is not a clean list of
released content: the tables also contain WIP dragons, test/balance dragons, NPCs, and
unresolved localization keys. Presence in the client therefore does not establish
release status or player availability.

The canonical application index is regenerated from the captured versioned dragon,
Command, Habit, progression, base-localization, and delta-localization resources. Its
metadata records the exact source filenames and build. Unchanged logical resources in
the newer snapshot remain continuing installed evidence; they are not discarded merely
because the resource diff did not flag them. For all 36
screenshot-audited dragons, the extraction matched breed, Vanguard name, all five
Habit names, and positive/negative troop affinities. It also established a separate
Rare/Epic/Legendary `rarity_tier` for each dragon without replacing screenshot labels
such as Juvenile, Adult, or Elder.

Starshower's and Vermithor's client templates supplied their structure but retained
unresolved progression references. Current in-game screenshots now establish both
dragons' exact Commands, Vanguards, affinities, five Habit texts, and all Habit upgrade
tracks. Meleys is also present with identity,
Legendary rarity, Warrior breed,
affinities, Vanguard, Command/Habit names, schedules, targeting, Laceration, and
Reflect behavior. Smoketail is now a production-named Epic Hunter with six complete
ability slots, and Ember Snare explicitly names Burn. Meleys and Smoketail were
user-confirmed as Season 3 available dragons on 2026-10-01. Their complete records are
now cross-site verified because Dragonfire Hub and Dragonfire Sim publish matching
Commands, Vanguards, five Habits, and upgrade tracks; the installed client corroborates
their structure and terminology. Meleys has since been screenshot audited; see the
2026-11-05 update below. Their provenance and usage rules are retained in
`data/installed_evidence.json` and `wiki/Community-Source-Audit-2026-10-12.md`.

`WildDragonTable.1786045129.json` joined to Node Finder strings in `locale_enUS.json`
also resolves the PvE breed weaknesses: Champion Wild Dragons are weak to Warriors,
Sentinels to Hunters, Hunters to Champions, and Warriors to Sentinels. This mapping is
specific to Wild Dragon encounters and is not evidence of a universal PvP breed cycle.

## Source priority

1. Current in-game text and screenshots.
2. Official WB Games support guides and official Dragonfire news/profile pages.
3. Explicitly reviewed matching Dragonfire Hub and Dragonfire Sim claims that do not
   conflict with current client evidence, labeled cross-site verified.
4. Repeated, reproducible player observations with enough battle context.
5. Fan databases and guides for discovery or strategic hypotheses.
6. Tier lists, unsourced summaries, and search snippets only as leads.

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
| [Starshower profile](https://news.gotdragonfire.com/starshower-the-wishkeeper/) | Official dragon profile | Previously supplied an incomplete record and Solar Flare; current in-game screenshots now supersede its missing exact values and Vanguard text. |
| [Vermithor profile](https://news.gotdragonfire.com/vermithor-the-bronze-fury/) | Official dragon profile | Previously supplied an incomplete record and Protect; current in-game screenshots now supersede its missing exact values and Vanguard text. |

No official patch-note archive, combat formula, universal proc order, or published
errata list was found during this audit. Official profile prose can omit values and
Vanguard text, so it must not silently replace complete in-game records.

## Community sources reviewed

| Source | Assessment | Use |
| --- | --- | --- |
| [Dragonfire Hub](https://dragonfire-hub.com/) | Active fan database and lineup builder with structured dragon, progression, and effect data. | Matching Meleys, Smoketail, and Dragon Growth values were cross-site verified; conflicts still yield to client evidence. |
| [Dragonfire Hub guide](https://dragonfire-hub.com/guide) | Repeats damage types, status definitions, and named stack mechanics. | Corroboration; it did not resolve combat formulas, proc order, adjacency, or Cleanse priority. |
| [Dragonfire Sim](https://dragonfiresim.com/) | Public Monte Carlo simulator with dragon cards, Guides, and exposed implementation constants. | Full Meleys/Smoketail and Dragon Growth data agreed with Hub. Simulator constants, tier output, and formations are retained separately as model benchmarks, not live formulas. |
| [Dragonfire Sim combat mechanics](https://dragonfiresim.com/combat-mechanics) | Documents the site's combat model and assumptions. | Useful for reproducibility and empirical-test design; unverified constants are not promoted to canonical mechanics. |
| [Dragonfire Sim tier list](https://dragonfiresim.com/guides/tier-list) | 427,500 simulated battles at 10 Stars, Level 50, Habit Rank 5. | Aggregate candidate-discovery benchmark only; scenario and simulator assumptions prevent treating percentages as live win rates. |
| [Dragonfire Sim formations and troops](https://dragonfiresim.com/guides/best-formations) | Publishes candidate trios and shared troop choices. | Candidate generation only; the repository planner must re-evaluate them against the user's roster, progression, matchup, and legal common baselines. |
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

## Meleys screenshot update — 2026-11-05

Supplied screenshots now establish Meleys's ability texts and five upgrade tracks; the
Legendary tier remains installed-client evidence. Royal Rend shows four Vulnerable
stacks, +5% Damage Received per stack, and +12.5% Physical Damage Received in the
otherwise branch. The earlier cross-site canonical transcription omitted the stack
count and recorded +7%; its source cannot override these screenshots. The previous
wiki summaries of Brisk Might and The Red Queen also mischaracterized their effects.
The otherwise chance and its precise condition remain unspecified by the panel.

## Smoketail screenshot update — 2026-11-05

Supplied screenshots establish Smoketail's Command, Vanguard, affinity, five Habit
texts, and displayed upgrade tracks. The Epic tier remains installed-client evidence.
Unraveled's screenshot supplies a separate Champion track (-10.5%, -13%, -15%,
-18%, -21%) that the prior canonical record omitted. Ashen Phantom and Unraveled
show reductions with negative signs, correcting the prior positive-sign transcription.
The screenshot shows level 5 for the unlocked Habits and level 1 for the locked
10-Star Habit; these are Habit levels, not Star ranks.
