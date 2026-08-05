# Vermax

Warrior Epic · Cavalry and Shieldbearer affinity. Physical attacker that reacts to enemy Fire damage and builds support stacks for Tactical allies.

**Command — Spreading Blaze:** hits the same-lane enemy after Basic Attacks and can stack a Tactical-Damage buff on an ally, with extra attempts against Fire-damage enemies.

**Vanguard — Warrior's Zeal:** +16% Physical Damage Dealt; the Left Flank ally gains +20 Instinct and Initiative.

Constraints: Rallying Flame caps at 4 self stacks and Spreading Blaze at 10 ally stacks. Trial by Flame scales mitigation at the 75%, 50%, and 25% troop-capacity thresholds.

Exact data: [JSON](../../data/dragons/vermax.json).

## Recommendation-critical source coverage

- **Command — Spreading Blaze:** After each Basic Attack: deal Physical Damage to 1 Enemy in the same lane (Damage Rate: +50%). 20% chance to grant 1 stack of Spreading Blaze (max 10 stacks) to 1 Ally that deals Tactical Damage until the end of combat; repeat this chance for each Enemy that deals Fire Damage.
- **Vanguard — Warrior's Zeal:** At Level 16+ and deployed in the Vanguard, increase Physical Damage Dealt by +16%. Increase Instinct and Initiative by +20 of the Ally deployed in the Left Flank.
- **2 Stars — Trial by Flame:** Start of Each Round: Reduce the Fire Damage Received of all allies below 75% troop capacity by -5% until the end of the round. This effect is doubled (-10%) for targets below 50% troop capacity, and tripled (-15%) for targets below 25% troop capacity.
- **4 Stars — Reactive Instincts:** Start of Combat: Increase Instinct by +18% and Initiative by +9% of the Ally with the highest Instinct until the end of combat. Both effects are enhanced by Strength.
- **6 Stars — Rallying Flame:** Start of Combat: 50% chance to grant yourself 1 stack of Rallying Flame (Max 4 Stacks) until the end of combat. Repeat this chance for each enemy that deals Fire Damage. Each stack of Rallying Flame increases your Physical Damage Dealt by +5%. Start of Combat: 50% chance to grant 1 stack of Spreading Blaze (Max 10 Stacks) to 1 Ally that deals Tactical Damage until the end of combat. Repeat this chance for each enemy that deals Fire Damage. Each stack of Spreading Blaze increases the target's Tactical Damage Dealt by +2.5% until the end of combat.
- **8 Stars — Dragon's Valor:** Start of Combat: Reduce your Damage Received by -5% and increase your Strength by +8.5% until the end of combat.
- **10 Stars — Unyielding Resolve:** Start of Combat: 20% chance to grant yourself Advantage (+15%) for 2 round(s). This chance is increased by 1.5x (30%) if you are afflicted with Weakened, and if successful removes the Weakened effect.
