# Sheepstealer

Hunter Legendary · Positive affinities: Cavalry and Archers · No displayed negative affinity

Sheepstealer is a Prey-focused Fire attacker and Recovery suppressor. **Wild Hunt** marks a Prey, prioritizing enemies that recently received Recovery; Prey reduces Recovery Received by 30%. Its scheduled Fire attack prioritizes Prey and doubles against it. At 10 Stars it damages the Prey and recovers itself each round, tripling both effects when the Prey received Recovery in the prior round.

**Vanguard — Hunter's Cunning:** at level 16+, +20% Recovery Received and +25 Intelligence; the Right Flank ally gains +10% Physical Damage Dealt. Cavalry or Archers are source-supported troop choices.

Constraints and synergies: several Habits key off the Prey's troop capacity or Recovery. Stolen Flock has a 10-stack cap and includes a PvE-only Fire bonus for Food Tiles and Beast Encounters. Baited Kill supplies Vulnerable and conditional self-Cleanse; Wary Beast supplies conditional Evade and team Recovery suppression.

Exact wording and all five Habit levels: [JSON](../../data/dragons/sheepstealer.json).

## Recommendation-critical source coverage

- **Command — Wild Hunt:** Each Round: if no enemy is marked as your Prey, 40% chance to mark 1 Enemy in any lane as your Prey for 3 rounds, prioritizing enemies that received Recovery within the last round. Prey reduces Recovery Received by -30%. Rounds 1, 4, 7, 10: Deal Fire Damage to 1 Enemy in any lane, prioritizing Prey (+100%, doubled to +200% against Prey). At 10 Stars: each round, damage Prey with Fire and recover yourself; both triple if Prey received Recovery within the last round.
- **Vanguard — Hunter's Cunning:** At Level 16+ and deployed in the Vanguard Increase your Recovery Received by +20% and Intelligence by +25. Increase Physical Damage Dealt by +10% of the Ally deployed in the Right Flank.
- **2 Stars — Stolen Flock:** Start of Combat: Increase your Fire Damage Dealt by +10% when battling non-player armies at Food Tiles and when battling Encounters against Beasts until the end of combat. Each Round: 50% chance to gain 1 stack of Stolen Flock (Max 10 Stacks). When your Prey receives Recovery: Gain 1 stack of Stolen Flock (Max 10 Stacks). Each stack of Stolen Flock increases your Fire Damage Dealt by +3% until the end of combat.
- **4 Stars — Dragon's Cunning:** Start of Combat: Increase your Intelligence by +16% and reduce Instinct by -12% (enhanced by Initiative) of 2 Enemies within adjacency. Each effect lasts until the end of combat.
- **6 Stars — Baited Kill:** Each Round: 25% chance to afflict your Prey with Vulnerable (+20%). This chance is doubled (50%) if the target received Recovery within the last 1 round. Each Round: If your Prey is above 50% Troop Capacity, 50% chance to Cleanse yourself of 1 Negative effect applied by an enemy that reduces your Damage Dealt.
- **8 Stars — Wary Beast:** At the Start of Each Round: If your Prey is above 50% Troop Capacity, gain Evade until the end of the round. Start of Combat: Reduce the Recovery Received by -10% of 3 Enemies in any lane until the end of combat.
- **10 Stars — Savage Claim:** Wild Hunt gains: Each Round: If you have a Prey, deal Fire Damage to them (Damage Rate: +24%) and apply Recovery to yourself (Recovery Rate: +10%, enhanced by Intelligence). If your Prey received Recovery within the last round, triple the Damage (+72%) and Recovery (+30%).
