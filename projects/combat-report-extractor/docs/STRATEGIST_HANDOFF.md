# Combat Analyst to Strategist review gate

Combat Analyst findings never flow directly into recommendation data. The handoff command
creates a review proposal only when a canonical rule is already `accepted` and
`corroborated`, cites exact compatible dragon ability text, retains limitations and
counterevidence, and an operator explicitly confirms that the finding is a durable
mechanic rather than an account-specific result.

The operator must name the intended receiving files and the tests that would validate a
later, separately reviewed change:

```powershell
python projects/combat-report-extractor/combat_report_interpreter.py handoff `
  --rule 'rule.velar.gales-of-power.first-strike.v1' `
  --target-file 'data/effects.json' `
  --test-command 'python -m unittest discover -s projects/combat-report-extractor/tests -v' `
  --confirm-durable-mechanic `
  --output '<review-folder>\strategist-handoff.json'
```

The output embeds portable reviewed observations and exact canonical ability wording. It
sets `automatic_changes` to false and excludes draft/disputed rules, generated local
report results, account-specific damage, and unreviewed candidates. The command never
edits mechanics, effects, dragon profiles, recommendation rules, or either agent.
