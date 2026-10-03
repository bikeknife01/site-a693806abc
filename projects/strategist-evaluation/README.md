# Strategist evaluation

This project records reproducible expert-formation benchmarks without turning them
into preferred-line exceptions.

## Baseline

The pre-change Strategist prompt is the Git blob at
`b02c4bc:.github/agents/dragonfire-strategist.agent.md`. For every supplied benchmark,
capture its recommendation from that prompt before evaluating the revised prompt.
Record both outputs verbatim with the same input and repository revision.

## Benchmark record

Store records under `benchmarks/` as JSON matching `benchmark.schema.json`. Unknown
values remain the string `unknown`; do not impute player progression. Each record keeps
the expert line, scenario, candidate roster, baseline output, revised runs, diagnosis,
generalized changes, and at least one holdout or variation. A defensible disagreement
may be retained with an evidence explanation.

Run contract tests with:

```powershell
python -m unittest discover -s projects/strategist-evaluation/tests -v
```

## Blind backtest

`backtest_cases.json` defines three exact-match expert benchmarks and three holdouts.
The grader treats these as separate questions:

1. Did the Strategist choose the expert troop type, trio, and exact lane order?
2. Did it recover the expert rationale, with correct gates and chance/uncertainty
   discipline? A failed expert-rationale check does not by itself prove that a
   different recommendation is mechanically invalid; that disagreement requires
   review of the raw response.
3. Does the same reasoning react correctly when a Star gate or matchup assumption is
   changed?

List the exact blind prompts without contacting an external service:

```powershell
python projects/strategist-evaluation/backtest.py --list-prompts
```

To grade responses captured elsewhere, save one Markdown response per case as
`<case-id>.md`, then run:

```powershell
python projects/strategist-evaluation/backtest.py `
  --responses path/to/responses `
  --report-markdown path/to/report.md `
  --report-json path/to/report.json
```

The script can invoke the installed GitHub Copilot CLI with the repository's
`dragonfire-strategist` custom agent and immediately grade the results:

```powershell
python projects/strategist-evaluation/backtest.py `
  --generate-with-copilot path/to/new-run `
  --report-markdown path/to/new-run/report.md `
  --report-json path/to/new-run/report.json
```

This last mode sends prompt-selected repository content to the configured GitHub
Copilot service. Use it only with explicit authorization. Every prompt tells the agent
not to read `projects/strategist-evaluation`, which prevents the expected formations
and prior answers from contaminating the run. Each generated run records hashes of the
agent definition, prompts, and raw responses.

Exact agreement is deliberately not the only result. A formation match with failed
critical reasoning is a failure; a mismatch with sound reasoning is reported as a
mismatch for expert review rather than silently tuned into an exception.

