# Shop and Currency Evaluator

## Project description

Build a spender-oriented evaluator for shops, chests, guarantees and event currencies. The tool should answer which purchase path most efficiently achieves a chosen gameplay objective while acknowledging server-only prices, rotating availability, random outcomes and the user's tolerance for variance.

## Primary user questions

- What is the least expensive path to unlock or reach a target Star Rank?
- Is a guaranteed relic offer better than chest pulls at my current pity state?
- What is the expected, conservative and worst-case cost?
- Which bundle contents have meaningful gameplay value for me?
- Should I buy now or preserve currency for a later shop stage/banner?
- How much duplicate or unwanted value is embedded in an offer?

## Player-profile decisions

- Optimize for spender value, not “never spend premium currency.”
- Support target completion, speed and certainty as selectable priorities.
- Building-time skips have zero value by default because the user autocompletes construction.
- Cosmetic value defaults to zero but can be user-adjusted.
- Energy/stamina, keys, relics, shards, cores, upgrade materials and premium currency can have account-specific values.
- Commanders and Commander shards remain staged and excluded unless they become live.

## Existing related files and tables

- `Game_Details/Resources/ShopTable.*.pb`
- `Game_Details/Resources/ShopSlotTable.*.pb`
- `Game_Details/Resources/ShopBonusTable.*.pb`
- `Game_Details/Resources/itemTable_merged.*.pb`
- `Game_Details/Resources/GachaChestTable_1.*.pb`
- `Game_Details/Resources/GachaChestTypeTable.*.pb`
- `Game_Details/Resources/GachaPityTable.*.pb`
- `Game_Details/Resources/GachaPullOptions.*.pb`
- `Game_Details/Resources/OfferControl.*.pb`
- Activity, progression, localization and currency-related tables in the same resource directory.
- Snapshot semantic diffs showing staged Charlie shop slots.

## Proposed project files

```text
projects/shop-currency-evaluator/
  PROJECT_PLAN.md
  src/
    economy/
      catalog.*
      currencies.*
      offers.*
      gacha.*
      pity.*
      valuation.*
      goal-search.*
    ui/
  tests/
    offer-fixtures/
  local-data/                # ignored; user-entered prices/history
  README.md
```

## Core concepts

### Objective-first evaluation

Examples:

- Unlock Meleys.
- Reach Smoketail 6 Stars.
- Acquire a specified number of relics.
- Maximize useful dragon progression within a dollar or premium-currency budget.
- Compare direct guarantee, banner pulls and mixed bundle paths.

### Valuation modes

- **Goal completion:** minimum expected cost to reach the target.
- **Certainty:** favor guarantees and conservative outcomes.
- **Expected value:** value probability-weighted contents.
- **Marginal account value:** reduce value for already-complete or unwanted items.
- **Spend ceiling:** best path that does not exceed a hard budget.

### Missing live data

When price, stock, odds or availability is server-only, the UI must request manual entry or screenshot transcription. Client presence alone must not be presented as a purchasable live offer.

## Work plan

### Phase S1 — Economy graph audit

- [ ] SCE-011 Resolve Shop → Slot → Stock/Offer → Item → Quantity relationships.
- [ ] SCE-012 Resolve currencies, costs, limits and reset/stage conditions.
- [ ] SCE-013 Resolve chest reward pools, pull options and pity rules.
- [ ] SCE-014 Mark server-only or unresolved price/odds fields.
- [ ] SCE-015 Mark staged future shops separately from live shops.

### Phase S2 — Player valuation profile

- [ ] SCE-021 Define owned dragons, Stars, pity and inventory inputs.
- [ ] SCE-022 Define target dragon/Star/material goals.
- [ ] SCE-023 Define real-money and premium-currency budgets.
- [ ] SCE-024 Default construction-time items to zero value.
- [ ] SCE-025 Support custom values for cosmetics, stamina and surplus materials.
- [ ] SCE-026 Keep purchase history local and ignored by Git.

### Phase S3 — Offer calculator

- [ ] SCE-031 Calculate deterministic bundle contents and unit costs.
- [ ] SCE-032 Calculate expected, conservative and guarantee-path chest outcomes.
- [ ] SCE-033 Model current pity state and pity resets.
- [ ] SCE-034 Model quantity limits and prerequisite offers.
- [ ] SCE-035 Discount duplicate/unusable contents using account profile.
- [ ] SCE-036 Show assumptions and unresolved inputs.

### Phase S4 — Goal-path optimizer

- [ ] SCE-041 Search combinations of live offers and pulls to reach a target.
- [ ] SCE-042 Produce cheapest expected, cheapest guaranteed and lowest-variance paths.
- [ ] SCE-043 Respect hard budget and stock constraints.
- [ ] SCE-044 Compare “buy now” with known later stage/banner inventory without claiming staged availability.
- [ ] SCE-045 Explain the marginal contribution of each purchase.

### Phase S5 — UI and capture workflow

- [ ] SCE-051 Catalog view by live/staged/expired/unknown status.
- [ ] SCE-052 Manual price, odds and current-pity entry.
- [ ] SCE-053 Goal builder and scenario comparison.
- [ ] SCE-054 Currency conversion/value breakdown.
- [ ] SCE-055 Deep links to dragons, items and effects in Encyclopedia.
- [ ] SCE-056 Export/import a sanitized local scenario without account identifiers.

### Phase S6 — Validation

- [ ] SCE-061 Reproduce at least five visible shop offers exactly.
- [ ] SCE-062 Test pity boundary immediately before and after guarantee.
- [ ] SCE-063 Test duplicate and already-maxed item valuation.
- [ ] SCE-064 Test hard budget and stock limits.
- [ ] SCE-065 Verify staged Charlie slots never appear as live without evidence.

## MVP acceptance criteria

- A user can enter a target, current progress, pity, offer prices and budget.
- The tool compares direct offers and chest paths using expected and guaranteed cases.
- Construction-time items contribute zero value by default.
- Server-only values are visibly manual inputs.
- Staged shops are never represented as live inventory.
- Every recommendation shows cost, assumptions, useful contents and wasted/duplicate contents.

## Later extensions

- Screenshot-assisted offer transcription.
- Historical price and banner comparison.
- Alert when a newly copied client snapshot changes an offer or pity rule.
- Optional portfolio budgeting across several desired dragons.
