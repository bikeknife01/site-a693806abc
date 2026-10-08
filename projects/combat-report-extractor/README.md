# Combat report video extractor

This local-only tool converts a Dragonfire combat-report screen recording into retained
OCR evidence, a normalized action ledger, and a deterministic Markdown insight report.
It does not connect to MuMu, ADB, the game process, or the network.

## Combat Analyst

The deterministic interpretation layer maps accepted, evidence-backed rules to
separately reported effects without changing the extractor or source actions. Its design
and implementation contracts are:

- [`docs/COMBAT_ANALYST_SPEC.md`](docs/COMBAT_ANALYST_SPEC.md) — behavior, evidence,
  schemas, rule lifecycle, and acceptance contract;
- [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md) — phased end-to-end implementation plan;
- [`docs/REPOSITORY_LAYOUT.md`](docs/REPOSITORY_LAYOUT.md) — anticipated paths and
  ownership boundaries; and
- [`docs/NEXT_SESSION_PROMPT.md`](docs/NEXT_SESSION_PROMPT.md) — ready-to-copy build
  prompt for a fresh session.

The interpreter accepts extractor schema `1.0.0` and uses only local files. Validate the
canonical stores, then interpret a retained report:

```powershell
python projects/combat-report-extractor/validate_combat_report_rules.py
python projects/combat-report-extractor/combat_report_interpreter.py interpret `
  --report '<run>\combat-report.json' `
  --output '<run>'
```

Optional `--rules`, `--observations`, and `--repository-root` arguments support reviewed
fixtures or another checkout. The command writes:

- `enriched-combat-report.json`: preserved source report, stable event IDs, annotations,
  links, ambiguities, unmatched events, coverage, hashes, and derived insights;
- `combat-analysis.json`: compact deterministic timeline and analysis model;
- `combat-insights.md`: the same model rendered for people; and
- `rule-candidates.json`: a conservative local review queue, never canonical knowledge.

JSON and Markdown are generated from one model and contain no volatile timestamp. See
[`docs/CANDIDATE_REVIEW.md`](docs/CANDIDATE_REVIEW.md) before proposing a draft. The
human evidence guide is
[`wiki/Combat-Report-Interpretation.md`](../../wiki/Combat-Report-Interpretation.md), and
the dedicated workflow agent is
[`dragonfire-combat-analyst.agent.md`](../../.github/agents/dragonfire-combat-analyst.agent.md).
Recommendation-relevant findings must use the proposal-only gate in
[`docs/STRATEGIST_HANDOFF.md`](docs/STRATEGIST_HANDOFF.md); the Strategist never consumes
local reports or draft/disputed rules directly.

The ownership convention is explicit and user-supplied:

- blue card backgrounds and blue dragon names are the user's side;
- red card backgrounds and red dragon names are the enemy side.

The extractor samples video frames, rejects blurred transition frames, identifies the
active round from the blue sidebar marker, classifies action-card ownership from the card
background, OCRs visible text, normalizes known dragon and ability names against
`data/dragons/*.json`, deduplicates overlapping frames, and aggregates only successfully
parsed visible values. Raw OCR text, confidence, timestamp, and frame filename remain on
every action for audit.

## Install

Use Python 3.11 or 3.12 in a local virtual environment:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r projects/combat-report-extractor/requirements.txt
```

The dependencies install a private FFmpeg decoder and a local ONNX OCR model. No video
or frame is uploaded. Virtual environments, decoder binaries, raw recordings, frames,
and generated runs must remain untracked.

## Extract a video

From the repository root:

```powershell
& .\.venv\Scripts\python.exe projects/combat-report-extractor/combat_report_extractor.py extract `
  --video 'C:\path\to\combat-report.mp4' `
  --output 'Game_Details\Resources\_snapshots\YYYY-MM-DD\analysis\combat-report-name' `
  --interval 1.5
```

Outputs:

- `frames/`: sampled evidence frames;
- `ocr_frames.json`: raw OCR, bounding boxes, confidence, ownership classification,
  active section, source hash, and sampling metadata;
- `combat-report.json`: normalized, deduplicated action ledger plus rejected records and
  coverage warnings;
- `insights.md`: visible damage/recovery aggregates and an auditable action ledger.

The default 1.5-second interval is appropriate for a slow continuous scroll. Use `1.0`
when the report scrolls quickly and `2.0` only for a deliberately paused recording.
Never call the aggregates complete when `coverage.warnings` is non-empty. They summarize
visible sampled UI text, not the encrypted server payload.

## Reparse retained OCR

Parser improvements do not require rerunning OCR:

```powershell
python projects/combat-report-extractor/combat_report_extractor.py parse `
  --ocr '<run>\ocr_frames.json' `
  --output '<run>'
```

## Recording guidance

For controlled PvE comparisons, single-dragon swaps, capture-note templates, naming, and
an incremental collection plan, use the
[`Combat Report Capture Guide`](../../wiki/Combat-Report-Capture-Guide.md).

For the most complete result:

1. Open the detailed report and begin at Troop Formation.
2. Expand one section at a time.
3. Scroll slowly enough that every action card is fully stationary for at least two
   seconds; avoid stopping with a text line clipped at the top or bottom.
4. Cover Preparations, every round, and Stalemate/outcome sections in order.
5. Do not open overlays during the recording.

## Validation and tests

```powershell
python -m unittest discover -s projects/combat-report-extractor/tests -v
```

Review `combat-report.json` before using an insight. Unsupported or ambiguous sentence
shapes stay in raw OCR evidence or `rejected_actions`; do not manually promote them
without checking the cited frame.

Lines stating that a dragon “is under the effect of” something are retained in raw OCR
but are not promoted to actions. They describe a visible state snapshot and do not prove
that the affected dragon performed or originated the effect.

