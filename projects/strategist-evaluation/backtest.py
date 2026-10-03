from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
DEFAULT_CASES = PROJECT / "backtest_cases.json"
LANES = ("left_flank", "vanguard", "right_flank")
LANE_LABELS = {
    "Left Flank": "left_flank",
    "Vanguard": "vanguard",
    "Right Flank": "right_flank",
}
BLIND_PREFIX = (
    "Blind evaluation: do not read or search projects/strategist-evaluation, its "
    "benchmarks, backtest cases, prior runs, or expected-answer files. Use the canonical "
    "Dragonfire sources named in your agent instructions. Do not edit files.\n\n"
)


def load_cases(path: Path = DEFAULT_CASES) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_cases(payload: dict[str, Any], ids: list[str] | None) -> list[dict[str, Any]]:
    cases = payload["cases"]
    if not ids:
        return cases
    wanted = set(ids)
    selected = [case for case in cases if case["id"] in wanted]
    missing = wanted - {case["id"] for case in selected}
    if missing:
        raise ValueError(f"Unknown case id(s): {', '.join(sorted(missing))}")
    return selected


def parse_formation(response: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {"troop_type": None, **{lane: None for lane in LANES}}
    plain_response = response.replace("**", "")
    troop = re.search(
        r"Formation\s+troop\s+type:\s*([A-Za-z]+)", plain_response, flags=re.IGNORECASE
    )
    if not troop:
        troop = re.search(r"Best-supported\s+counter:\s*([A-Za-z]+)\b", plain_response, flags=re.IGNORECASE)
    if troop:
        result["troop_type"] = troop.group(1).strip()
    for line in response.splitlines():
        match = re.match(
            r"^\|\s*(Left Flank|Vanguard|Right Flank)\s*\|\s*\**\s*([^|*]+?)\s*\**\s*\|",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        canonical_label = next(label for label in LANE_LABELS if label.lower() == match.group(1).lower())
        lane = LANE_LABELS[canonical_label]
        if result[lane] is None:
            result[lane] = match.group(2).strip()
    return result


def pattern_present(pattern: str, response: str) -> bool:
    return re.search(pattern, response, flags=re.IGNORECASE | re.DOTALL) is not None


def evaluate_check(check: dict[str, Any], response: str) -> dict[str, Any]:
    all_results = {pattern: pattern_present(pattern, response) for pattern in check.get("all_patterns", [])}
    any_patterns = check.get("any_patterns", [])
    any_results = {pattern: pattern_present(pattern, response) for pattern in any_patterns}
    none_results = {pattern: not pattern_present(pattern, response) for pattern in check.get("none_patterns", [])}
    passed = all(all_results.values()) and (not any_patterns or any(any_results.values())) and all(none_results.values())
    return {
        "id": check["id"],
        "label": check["label"],
        "critical": check.get("critical", False),
        "passed": passed,
        "all_patterns": all_results,
        "any_patterns": any_results,
        "none_patterns": none_results,
    }


def grade_case(case: dict[str, Any], response: str) -> dict[str, Any]:
    parsed = parse_formation(response)
    expected = case.get("expected_formation")
    formation_checks: dict[str, bool] = {}
    if expected:
        formation_checks = {
            field: (parsed.get(field) or "").casefold() == expected[field].casefold()
            for field in ("troop_type", *LANES)
        }
    reasoning = [evaluate_check(check, response) for check in case["reasoning_checks"]]
    critical_reasoning = [item for item in reasoning if item["critical"]]
    exact_match = bool(expected) and all(formation_checks.values())
    reasoning_pass = all(item["passed"] for item in critical_reasoning)
    passed = reasoning_pass and (not expected or exact_match)
    return {
        "id": case["id"],
        "kind": case["kind"],
        "benchmark_id": case["benchmark_id"],
        "parsed_formation": parsed,
        "expected_formation": expected,
        "formation_checks": formation_checks,
        "exact_formation_match": exact_match if expected else None,
        "reasoning_checks": reasoning,
        "critical_reasoning_pass": reasoning_pass,
        "passed": passed,
    }


def grade_run(cases: list[dict[str, Any]], response_dir: Path) -> dict[str, Any]:
    results = []
    missing = []
    for case in cases:
        path = response_dir / f"{case['id']}.md"
        if not path.exists():
            missing.append(case["id"])
            continue
        results.append(grade_case(case, path.read_text(encoding="utf-8")))
    benchmarks = [item for item in results if item["kind"] == "benchmark"]
    holdouts = [item for item in results if item["kind"] == "holdout"]
    exact_matches = sum(item["exact_formation_match"] is True for item in benchmarks)
    resolved_response_dir = response_dir.resolve()
    try:
        report_response_dir = resolved_response_dir.relative_to(ROOT).as_posix()
    except ValueError:
        report_response_dir = str(resolved_response_dir)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "response_dir": report_response_dir,
        "summary": {
            "cases_graded": len(results),
            "cases_missing": len(missing),
            "benchmark_exact_matches": exact_matches,
            "benchmark_total": len(benchmarks),
            "critical_reasoning_passes": sum(item["critical_reasoning_pass"] for item in results),
            "holdout_passes": sum(item["passed"] for item in holdouts),
            "holdout_total": len(holdouts),
            "overall_pass": not missing and all(item["passed"] for item in results),
        },
        "missing": missing,
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Dragonfire Strategist backtest",
        "",
        f"- Benchmark formation matches: {summary['benchmark_exact_matches']}/{summary['benchmark_total']}",
        f"- Expert-rationale passes: {summary['critical_reasoning_passes']}/{summary['cases_graded']}",
        f"- Holdout passes: {summary['holdout_passes']}/{summary['holdout_total']}",
        f"- Missing responses: {summary['cases_missing']}",
        f"- Overall: {'PASS' if summary['overall_pass'] else 'REVIEW REQUIRED'}",
        "",
        "| Case | Formation | Expert rationale | Result |",
        "|---|---:|---:|---:|",
    ]
    for item in report["results"]:
        formation = "n/a" if item["exact_formation_match"] is None else ("match" if item["exact_formation_match"] else "mismatch")
        reasoning = "pass" if item["critical_reasoning_pass"] else "fail"
        lines.append(f"| `{item['id']}` | {formation} | {reasoning} | {'PASS' if item['passed'] else 'FAIL'} |")
    for item in report["results"]:
        lines.extend(["", f"## {item['id']}", ""])
        if item["expected_formation"]:
            lines.append(f"Parsed formation: `{json.dumps(item['parsed_formation'], ensure_ascii=False)}`")
            lines.append("")
        for check in item["reasoning_checks"]:
            marker = "x" if check["passed"] else " "
            critical = " (critical)" if check["critical"] else ""
            lines.append(f"- [{marker}] {check['label']}{critical}")
    if report["missing"]:
        lines.extend(["", "## Missing responses", "", *[f"- `{case_id}.md`" for case_id in report["missing"]]])
    return "\n".join(lines) + "\n"


def generate_with_copilot(cases: list[dict[str, Any]], output_dir: Path, agent: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "agent_definition_sha256": hashlib.sha256(
            (ROOT / ".github" / "agents" / f"{agent}.agent.md").read_bytes()
        ).hexdigest(),
        "cases": [],
    }
    for case in cases:
        prompt = BLIND_PREFIX + case["prompt"]
        response_path = output_dir / f"{case['id']}.md"
        if response_path.exists():
            response = response_path.read_text(encoding="utf-8")
        else:
            command = [
                "copilot", "-C", str(ROOT), "--agent", agent, "--no-color", "--no-ask-user",
                "--allow-tool=read", "--allow-tool=search", "--allow-tool=web",
                "--allow-tool=shell(node projects/strategist-simulator/simulate.mjs:*)",
                "-s", "-p", prompt,
            ]
            completed = subprocess.run(
                command,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"Copilot failed for {case['id']}: {completed.stderr.strip()}")
            response = completed.stdout
            response_path.write_text(response, encoding="utf-8")
        manifest["cases"].append({
            "id": case["id"],
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        })
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and grade blind Dragonfire Strategist backtests.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--case", action="append", dest="case_ids", help="Run only this case id; repeatable.")
    parser.add_argument("--list-prompts", action="store_true")
    parser.add_argument("--generate-with-copilot", type=Path, metavar="OUTPUT_DIR")
    parser.add_argument("--responses", type=Path, help="Directory containing <case-id>.md responses.")
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-markdown", type=Path)
    args = parser.parse_args()

    payload = load_cases(args.cases)
    cases = selected_cases(payload, args.case_ids)
    if args.list_prompts:
        for case in cases:
            print(f"[{case['id']}]\n{BLIND_PREFIX}{case['prompt']}\n")
    if args.generate_with_copilot:
        print("NOTICE: this sends prompt-selected repository content to the configured GitHub Copilot service.", file=sys.stderr)
        generate_with_copilot(cases, args.generate_with_copilot, payload["agent"])
    response_dir = args.responses or args.generate_with_copilot
    if response_dir:
        report = grade_run(cases, response_dir)
        markdown = render_markdown(report)
        print(markdown, end="")
        if args.report_json:
            args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.report_markdown:
            args.report_markdown.write_text(markdown, encoding="utf-8")
        return 0 if report["summary"]["overall_pass"] else 1
    if not args.list_prompts:
        parser.error("choose --list-prompts, --generate-with-copilot, or --responses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
