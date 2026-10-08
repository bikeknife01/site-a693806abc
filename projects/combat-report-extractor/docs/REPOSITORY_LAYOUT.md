# Dragonfire Combat Analyst — Anticipated Repository Layout

The Combat Analyst is an extension of `projects/combat-report-extractor`, not a separate
capture system. Paths marked **existing** are already present. Paths marked **planned**
are implementation targets; this document does not imply they exist yet.

```text
D:/repos/Dragonfire/
├── .github/
│   └── agents/
│       ├── dragonfire-strategist.agent.md                 # existing
│       └── dragonfire-combat-analyst.agent.md             # planned
├── data/
│   ├── dragons/                                           # existing canonical kits
│   ├── effects.json                                       # existing shared effects
│   ├── game_mechanics.json                                # existing shared mechanics
│   ├── combat_report_rules.json                           # planned canonical rules
│   └── combat_report_observations.json                    # planned curated evidence
├── wiki/
│   └── Combat-Report-Interpretation.md                    # planned human guide
├── projects/
│   └── combat-report-extractor/
│       ├── README.md                                      # existing entry point
│       ├── requirements.txt                               # existing dependencies
│       ├── combat_report_extractor.py                     # existing OCR/parser
│       ├── combat_report_interpreter.py                   # planned enrichment CLI
│       ├── validate_combat_report_rules.py                # planned data validator
│       ├── docs/
│       │   ├── COMBAT_ANALYST_SPEC.md                     # this design contract
│       │   ├── BUILD_PLAN.md                              # phased implementation
│       │   ├── REPOSITORY_LAYOUT.md                       # this file
│       │   └── NEXT_SESSION_PROMPT.md                     # implementation handoff
│       ├── schemas/
│       │   ├── combat-report-rules.schema.json            # planned
│       │   ├── combat-report-observations.schema.json     # planned
│       │   └── enriched-combat-report.schema.json         # planned
│       └── tests/
│           ├── fixtures/
│           │   ├── ocr_frames.json                        # existing
│           │   ├── combat_report_v1.json                  # planned boundary fixture
│           │   ├── interpreter_synthetic.json             # planned match fixture
│           │   ├── rules_valid.json                       # planned
│           │   ├── observations_valid.json                # planned
│           │   └── invalid/                               # planned negative cases
│           ├── test_extractor.py                          # existing
│           ├── test_rule_validation.py                    # planned
│           └── test_interpreter.py                        # planned
└── Game_Details/
    └── Resources/
        └── _snapshots/
            └── YYYY-MM-DD/
                └── analysis/
                    └── combat-report-name/                # ignored local run
                        ├── frames/
                        ├── ocr_frames.json
                        ├── combat-report.json
                        ├── insights.md
                        ├── enriched-combat-report.json    # planned generated output
                        ├── combat-analysis.json            # planned generated output
                        ├── combat-insights.md              # planned generated output
                        └── rule-candidates.json            # planned local review queue
```

## Placement rationale

### `.github/agents/`

Agent Markdown belongs beside the existing Strategist agent. It contains operating
instructions, evidence discipline, and response behavior—not canonical combat mappings.

### `data/`

Accepted rules and curated observations are shared repository knowledge and may later
serve more than one tool. Keeping them in `data/` makes them visible to validators,
documentation, and future consumers. The two stores remain separate so a rule can be
re-evaluated without erasing the evidence that supported or contradicted it.

### `projects/combat-report-extractor/`

The interpreter consumes the extractor's normalized output, shares its language and
tests, and is operated as part of the same workflow. Keeping both CLIs here avoids a
premature package split while preserving a clean responsibility boundary.

### `projects/combat-report-extractor/schemas/`

These schemas define project-specific contracts and sit with the code that validates
them. If they later become cross-project contracts, they can move to
`projects/shared-data-foundation/schemas/` through an explicit migration.

### `wiki/`

The wiki is the human-readable companion. It summarizes accepted knowledge and open
questions but is not the source of truth for matching behavior.

### ignored `_snapshots/`

Raw recordings, frames, OCR, enriched reports, and candidate queues stay local because
they can be large, account-adjacent, and machine-specific. Code and tests must not rely
on these paths. Only deliberately curated observation excerpts enter `data/`.

## Naming rules

- Python modules and JSON filenames use `snake_case` where repository conventions do.
- JSON Schema files use kebab-case to match existing project schema conventions.
- Rule IDs use `rule.<source>.<result>.vN`.
- Observation IDs use `observation.<report>.<sequence>`.
- Generated local filenames are stable and contain no execution timestamp; the parent
  run folder carries capture identity.
- Avoid a generic `rules.md` or agent-embedded mapping table that could diverge from
  `data/combat_report_rules.json`.

## Dependency boundary

The initial interpreter should use the Python standard library plus the smallest
available JSON Schema validator already justified by repository dependencies. If a new
runtime dependency is required, add it to `requirements.txt`, pin it appropriately, and
document why. Interpretation tests must not load OCR, FFmpeg, ONNX, MuMu, ADB, or the
network.

