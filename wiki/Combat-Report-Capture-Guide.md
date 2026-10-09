# Combat report capture guide

Use this guide to collect reports that help the Combat Analyst distinguish visible facts
from possible ability mappings. You do not need many formations at once. A controlled
one-dragon swap is usually more useful than several unrelated battles.

## The simplest useful experiment

Capture a pair of PvE battles:

1. **Baseline:** use the normal three-dragon formation.
2. **One-dragon swap:** replace only the dragon whose contribution you want to test.

Keep everything else as similar as practical:

- the same PvE enemy, stage, and difficulty;
- the same two unchanged dragons and their lanes;
- the same shared troop type;
- the same Vanguard assignment unless the swapped dragon makes that impossible;
- the same dragon levels, Star ranks, and Habit levels; and
- the same game/client version.

This is a controlled comparison. If a result disappears when one dragon is removed, the
change makes that dragon a stronger candidate source, but it does not prove causality.
Random activation chances, target eligibility, early defeat, and incomplete report text
remain alternative explanations.

## Best comparison patterns

Collect these in order of usefulness:

1. **Remove the suspected source.** Repeat the same PvE battle without the dragon thought
   to produce the result.
2. **Add the suspected source.** Compare an otherwise stable formation before and after
   adding that dragon.
3. **Swap one competing source.** When two dragons could explain a result, remove one
   while retaining the other.
4. **Repeat the same pair.** Chance-based Habits need several observations. Repetition in
   one formation measures recurrence but does not count as formation independence.
5. **Change the enemy deliberately.** Do this only when testing target conditions such as
   breed, lane, troop type, status, or damage type. Record exactly what changed.

Avoid changing several dragons, troop type, lane order, and enemy at the same time. Such
reports remain useful as observations, but they rarely exclude competing explanations.

## What PvE evidence can establish

PvE reports are well suited to:

- confirming exact report wording;
- connecting a named ability and result shown on the same card;
- observing effect names, targets, rounds, and ownership;
- comparing whether a result recurs after one controlled dragon swap; and
- testing scheduled or target-dependent behavior against a repeatable enemy.

PvE evidence alone should not be generalized into PvP balance, player availability,
universal damage values, or behavior against a materially different enemy. Record the
stage and difficulty so the scope remains clear.

## Optional context note

Do not manually transcribe information that is clearly visible in the recording. The
video is the primary evidence for formations, lanes, troop type, report wording, and any
progression details it shows. The extractor or reviewer should recover those facts from
the retained evidence instead of asking you to enter them twice.

A short local note is optional and useful only for context the video does not establish,
such as the intended comparison or a setup difference that is not visible:

```markdown
# Optional capture context

- Comparison group: experiment-name
- Variant: baseline | swap
- Deliberate change being tested: replaced Dragon A with Dragon B
- Relevant context not visible in the video: none | ...
```

You can omit this file entirely when descriptive paired folder names make the experiment
clear. Never include account identifiers. If a note exists, it remains local unless a
reviewer extracts a minimal, non-account-specific observation into canonical data.

## Record the report

1. Open the detailed combat report at **Troop Formation**.
2. Start recording before scrolling.
3. Show the formation and any visible progression information needed for the comparison.
4. Expand one section at a time.
5. Cover Preparations, every available round, and Stalemate/outcome sections in order.
6. Hold each action card fully visible and stationary for at least two seconds.
7. Avoid leaving the first or last text line clipped by the screen edge.
8. Do not open overlays while recording.
9. Stop only after the final relevant card is visible.

A slow, complete recording is more valuable than a fast recording of several battles.
Revisiting a card while scrolling is safe: the extractor collapses the same semantic
card within a round. Do not rush past it to avoid duplication. For attacks, keep the
card still until the complete damage and remaining-troops sentence is visible; a named
attack without that sentence can be retained, but its damage cannot be added to the
visible parsed total.

## Store and process the run

Use a dated, descriptive, ignored folder. Give paired runs matching names:

```text
Game_Details/Resources/_snapshots/YYYY-MM-DD/analysis/
  pve-stage-name-baseline/
  pve-stage-name-swap-dragon-name/
```

The easiest path performs extraction and interpretation together:

```powershell
.\ingest-combat-report.ps1 'C:\path\to\report.mp4'
```

The command prints its dated ignored output folder. For manual control over the output
name or sampling interval, run the two underlying commands instead:

```powershell
python projects/combat-report-extractor/combat_report_extractor.py extract `
  --video 'C:\path\to\report.mp4' `
  --output 'Game_Details\Resources\_snapshots\YYYY-MM-DD\analysis\run-name'

python projects/combat-report-extractor/combat_report_interpreter.py interpret `
  --report 'Game_Details\Resources\_snapshots\YYYY-MM-DD\analysis\run-name\combat-report.json' `
  --output 'Game_Details\Resources\_snapshots\YYYY-MM-DD\analysis\run-name'
```

Preserve the video, OCR evidence, parsed report, generated analysis, candidate queue, and
cited frames together in that ignored folder. Preserve an optional context note there
only when it records something the video does not show.

## Review checklist

Before asking for a rule update, confirm:

- the coverage warnings and rejected actions were reviewed;
- the cited cards are fully visible in their retained frames;
- exact OCR/report wording has not been silently corrected;
- the baseline and swap differ only in variables visible in the recordings or called out
  in the optional context note;
- competing active abilities visible in the reports are accounted for;
- repeated occurrences are not presented as distinct reports or formations; and
- missing report text is not treated as proof that a chance-based effect failed.

Then ask the Combat Analyst to compare the paired runs, inspect the cited frames, and
identify observations that are safe to curate. It is acceptable—and often correct—for
the result to remain an unresolved candidate.

## Sustainable collection plan

Do not wait until every experiment is complete. Work in small batches:

1. Choose one unresolved effect or result phrase.
2. Record one baseline and one single-dragon swap.
3. Process and review that pair.
4. Use the remaining ambiguity to choose the next swap.
5. Repeat only until the evidence resolves the question or shows that another variable
   must be controlled.

This approach lets the evidence base improve incrementally without requiring a large
capture campaign up front.
