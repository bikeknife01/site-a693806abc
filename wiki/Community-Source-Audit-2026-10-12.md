# Dragonfire community-source audit — 2026-10-12

This audit compares Dragonfire Sim and Dragonfire Hub with the repository's canonical dragon records, installed-client extraction, and current client screenshots. It records what was accepted, rejected, or retained only as a simulator hypothesis.

The user directed that claims matching across both sites be treated as trusted and verified when they were not contradicted by the supplied client evidence. Such claims are labeled **cross-site verified**. This is deliberately distinct from **screenshot audited** and yields to newer direct client evidence.

## Sources and reproducibility

- Dragonfire Sim: <https://dragonfiresim.com/>, including `/combat-mechanics`, `/guides/tier-list`, `/guides/best-formations`, and `/guides/best-troops`.
- Dragonfire Sim application bundle: `assets/index-KcG_IEUf.js`, SHA-256 `113f13ce26156b28aa4c13c3eac739d8f88605e9b2943a357ab3277a8774fa53`.
- Dragonfire Hub: <https://dragonfire-hub.com/> and its guide/data views.
- Dragonfire Hub data bundle: `_next/static/chunks/1e2b4fc53b91f6fb.js`, SHA-256 `affc7c2355379a761b95769cfffe44344a4d6d1f4ca0e76629b54ec8b38a3b53`.
- Current client screenshots: local, ignored evidence under `Game_Details/Resources/_snapshots/2026-10-12-client-verification/`.

No emulator, account, or client-build metadata was requested or retained for this verification set. The screenshots are used only for the facts visibly established in them.

## Current screenshot ledger

| Evidence | SHA-256 | Result |
| --- | --- | --- |
| `bevlorin_basics.jpg` | `8403aaba6234d5128db26400b356fd529cb7c3b13c46034ba69354928732d576` | Identity and affinities corroborated; displayed stats are account progression. |
| `bevlorin_command.jpg` | `92de93e52fae5598ee40f0da15cc157a96f835d601ca8c7d20e0f3ea9455a4e6` | Existing Command record confirmed. |
| `bevlorin_vanguard.jpg` | `511030ffa0099cab00d10cf074b74754893cc71ba124d4c5456836b626d24c17` | Existing Vanguard record confirmed. |
| `malachite_basics.jpg` | `1cf9cdb70bfea400d2137ca5984a6099ab3cae59b9910bb20cfef826a3ac6f6e` | Identity and affinities corroborated. |
| `malachite_wardens_rally.jpg` | `a561560e1bd6d581c67953fd9a97c68b25ff8d2b929280a422234d2347ef62ff` | Corrected Warden's Rally; older tracked detail images showed Dawnseeker wording. |
| `moondancer_basics.jpg` | `dc8083bc179032d9acf3a0a25572e1bdfd415953beb7a0a147e474abcc48e4cf` | Level 1 values contradict the simulator's alleged base values; installed curves remain primary. |
| `moondancer_command.jpg` | `8720edcf1db2149aa7f5d25416a9c2f714b579ccf7271859fb5fe481ee708d2e` | Rising Tide mitigation corrected to -2.5% per stack. |
| `moondancer_habit1_new_moon.jpg` | `3c0ea4277e705ff5b7b75d37e5f647378069e9f8a09a1110d1c32cf79e99e0cd` | Existing New Moon upgrade track confirmed. |
| `moondancer_habit3_full_moon.jpg` | `4d74905771f81c640ccf04cfcb82a47f9f287f860d0631ccfe683dd9b14f0a6c` | Existing Full Moon upgrade track confirmed. |
| `sunfyre_basics.jpg` | `e98297ba394b36d340fd5aa1f4a0092c8b912a42de6671e8ae7ae57493ff8b62` | Spearmen and Cavalry affinities confirmed; displayed stats excluded as account progression. |
| `tairax_basics.jpg` | `707b7ac458f288995f09f5ca0e142ce504f9c18af73bfc0b6f01d3ed97f71c93` | Cavalry, Shieldbearers, and Siege affinities confirmed; simulator Archer claim rejected. |
| `venator_basics.jpg` | `14d75b511d626b2033a7fbb27a809fc49d5cfb1aced9780d041b0bc5ed96f58a` | Identity and affinities corroborated. |
| `venator_command_skill_feral_strike.jpg` | `57a33e94af6764bba90e42dc19d1262aa617bf576257aa5ea9ee6bf1158fdd92` | Corrected Feral Strike to +20% hits, rounds 4/6/8, and 40% at 6+ Stars. |

## Accepted changes

- Corrected Malachite, Venator, and Moondancer canonical mechanics from current screenshots.
- Added complete Meleys and Smoketail canonical records because both sites agree on their Commands, Vanguards, five Habits, and all upgrade tracks, and the installed client corroborates their structure and terminology.
- Recorded the exact 100-level Dragon Growth Heirloom curve published identically by both sites.
- Recorded the user's direct current-client confirmation of Dragon Army I–IV: five levels each, granting 50, 100, 200, and 250 additional troops per level respectively.
- Preserved simulator constants, the published 427,500-battle tier benchmark, and suggested formations in `data/community_simulation_reference.json` for reproducibility and sensitivity testing—not as canonical live results.

## Conflicts and resolutions

| Subject | Conflict | Resolution |
| --- | --- | --- |
| Dragon base stats | Simulator card values do not consistently match current Level 1 screenshots or installed curves. | Installed per-level curves are primary; Basics screenshots are player snapshots unless explicitly Level 1. |
| Tairax affinity | Dragonfire Sim identifies Archers; Hub and current screenshot identify Cavalry, Shieldbearers, and Siege. | Screenshot/Hub values retained; simulator claim rejected. |
| Venator | Simulator data contains stale hit values or scheduling. | Current screenshot retained: +20%, rounds 4/6/8, 40% at 6+ Stars. |
| Moondancer | Simulator uses -2% Rising Tide mitigation. | Current screenshot and Hub establish -2.5%; screenshot value retained. |
| Simplified star bonuses | Site shorthand does not reproduce every installed high-star scalar. | Installed `star_scalars` remain primary. |
| Ten-round simulation | Simulator ends after one ten-round horizon. | Live combat can enter Stalemate and repeat ten-round cycles; model output is an opening-cycle benchmark. |

## Deliberately not promoted

The simulator's hidden combat constants—damage coefficient, mitigation constant, generic Basic Attack rate, fallback Evade/Protect/Reflect rates, Siege penalty, targeting fallbacks, and similar conventions—are not established live rules. They are stored with green/yellow/red review status only so the repository can reproduce or challenge the public model. Its tier scores and formations are candidate-generation evidence, not predicted winners.

No battle reports were supplied, so this audit does not calibrate those assumptions against controlled outcomes. No Meleys, Smoketail, or Heirloom screenshots were supplied; their accepted data therefore remains explicitly cross-site verified rather than screenshot audited.

## Implementation tracking

- [x] Preserve and hash the supplied screenshot evidence without creating a separate local manifest.
- [x] Correct screenshot-conflicted canonical dragon records and wiki pages.
- [x] Add complete, provenance-labeled Meleys and Smoketail records.
- [x] Add evidence-model support for cross-site verification.
- [x] Add Dragon Army and Dragon Growth progression data.
- [x] Preserve simulator assumptions, benchmarks, formations, and conflicts separately from canonical mechanics.
- [x] Regenerate installed-client and encyclopedia outputs.
- [x] Run schema, encyclopedia, simulator, and recommendation tests.
