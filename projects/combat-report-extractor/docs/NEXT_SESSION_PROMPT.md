# Prompt for a New Codex Session

Copy the text below into a new session opened at `D:\repos\Dragonfire`.

---

Implement the Dragonfire Combat Analyst system described by the repository design
package. Start by reading these files completely:

1. `AGENTS.md`
2. `projects/combat-report-extractor/docs/COMBAT_ANALYST_SPEC.md`
3. `projects/combat-report-extractor/docs/BUILD_PLAN.md`
4. `projects/combat-report-extractor/docs/REPOSITORY_LAYOUT.md`
5. `projects/combat-report-extractor/README.md`
6. `projects/combat-report-extractor/combat_report_extractor.py`
7. `projects/combat-report-extractor/tests/test_extractor.py`

Then inspect `git status --short` and preserve any unrelated work. Implement the plan
end to end in its phased order, using the specification as the acceptance contract.
Create the schemas, canonical seed data, validator, deterministic interpreter, candidate
review workflow, tests, Combat Analyst agent Markdown, wiki guidance, and README/AGENTS
integration described there.

Important constraints:

- Keep the current extractor backward compatible with `combat-report.json` schema
  `1.0.0`; do not refactor OCR unless a tested compatibility need requires it.
- The analyst must operate only on local files. Do not launch MuMu, connect ADB, inspect
  the game process, capture traffic, use instrumentation, or upload recordings/frames.
- Preserve exact OCR/report wording and original action records. Add annotations rather
  than rewriting evidence.
- Keep observed, derived, inferred, and unknown claims distinct.
- Treat timing correlation as correlation, not causation.
- Never auto-promote `rule-candidates.json` into canonical rules.
- Validate canonical names against `data/dragons/*.json`; preserve all supporting and
  contradicting observation references.
- Committed observations must not contain account identifiers, absolute local paths,
  raw recordings, or unreviewed claims presented as established.
- The Strategist must not consume draft/disputed rules or local report results. Any
  Strategist-relevant finding uses the explicit review gate in the plan.
- Render JSON and Markdown from the same deterministic analysis model and include input
  and rule hashes in generated outputs.
- Do not make tests depend on ignored snapshots or network access.

Use the narrowest relevant tests after each phase and finish with:

```powershell
python -m unittest discover -s projects/combat-report-extractor/tests -v
python projects/combat-report-extractor/validate_combat_report_rules.py
git status --short
```

If the ignored local report still exists at
`Game_Details/Resources/_snapshots/2026-10-08/analysis/combat-report-video-3/extractor-run/combat-report.json`,
use it only for Phase 5 calibration after the synthetic test suite passes. Do not make
the implementation depend on that file and do not commit its raw contents. A valid
calibration result may remain unresolved; do not force an accepted combat mapping.

Make coherent commits following the recommended sequence in `BUILD_PLAN.md`. Before
each commit, confirm staged files contain no ignored/local capture material. At the end,
report the implemented phases, tests run, any evidence judgments that remain pending,
and the commit hashes.

---

