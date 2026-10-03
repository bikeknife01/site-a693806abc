# Strategist simulator

Read-only mechanics-constrained comparison for one or two strawman enemy formations.
It combines the Counter Assistant's threat, synergy, lane, troop, reliability, and
timing analysis without claiming hidden damage totals or win rates.

Dragon order is always Left Flank, Vanguard, Right Flank. Every formation uses one
shared troop type. Supply one to eight plausible candidate formations:

```powershell
node projects/strategist-simulator/simulate.mjs `
  --strawman "Velar,Vhagar,Moondancer|Shieldbearers" `
  --candidate "Malachite,Seasmoke,Kalspire|Cavalry" `
  --candidate "Tessarion,Malachite,Feskar|Cavalry" `
  --level 50 --stars 6 --habit-level 5 --pretty
```

Add a second `--strawman` to compare candidate robustness across two likely opponents.
The JSON result reports direct, conditional, and uncovered threats for each matchup plus
minimum/mean coverage across both strawmen. Its diagnostic score is only a search aid;
the Strategist must still inspect exact ability evidence and explain disagreements.

Run tests with:

```powershell
node --test projects/strategist-simulator/tests/simulator.test.mjs
```
