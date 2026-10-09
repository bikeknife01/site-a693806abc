#!/usr/bin/env python3
"""Ingest and interpret one local combat-report video with a single path argument."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import combat_report_extractor as extractor
import combat_report_interpreter as interpreter
import combat_empirical_analyzer as empirical


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:64] or "video"


def output_directory(repository_root: Path, video: Path, source_hash: str, capture_date: date) -> Path:
    return (
        repository_root / "Game_Details" / "Resources" / "_snapshots"
        / capture_date.isoformat() / "analysis"
        / f"combat-report-{safe_slug(video.stem)}-{source_hash[:8]}" / "extractor-run"
    )


def retained_ocr_matches(path: Path, source_hash: str) -> bool:
    if not path.is_file():
        return False
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (manifest.get("source") or {}).get("sha256") == source_hash


def find_retained_ocr(repository_root: Path, source_hash: str) -> Path | None:
    snapshots_root = repository_root / "Game_Details" / "Resources" / "_snapshots"
    if not snapshots_root.is_dir():
        return None
    matches = [
        path for path in snapshots_root.rglob("ocr_frames.json")
        if "analysis" in path.parts and retained_ocr_matches(path, source_hash)
    ]
    return max(matches, key=lambda path: (path.stat().st_mtime_ns, str(path))) if matches else None


def ingest(
    video: Path, repository_root: Path, capture_date: date, *, experiment: str | None = None,
    variant: str | None = None, question: str | None = None,
) -> dict[str, Path]:
    video = video.expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"Video does not exist or is not a file: {video}")

    source_hash = extractor.sha256_file(video)
    output = output_directory(repository_root, video, source_hash, capture_date)
    ocr_path = output / "ocr_frames.json"
    retained = find_retained_ocr(repository_root, source_hash)
    if retained is not None:
        output, ocr_path = retained.parent, retained
    else:
        output.mkdir(parents=True, exist_ok=True)

    if retained_ocr_matches(ocr_path, source_hash):
        print(f"Reusing retained OCR for this exact video: {ocr_path}", flush=True)
    else:
        if (output / "frames").exists():
            retry_suffix = datetime.now().strftime("retry-%H%M%S")
            output = output.parent / retry_suffix
            output.mkdir(parents=True, exist_ok=True)
            ocr_path = output / "ocr_frames.json"
            print(f"Incomplete prior run found; writing a recoverable retry to: {output}", flush=True)
        ocr_path = extractor.ocr_video(video, output, interval=1.5, min_sharpness=45.0)

    report_path, extractor_insights = extractor.write_report(ocr_path, output, repository_root)
    interpreted = interpreter.interpret_paths(
        report_path,
        output,
        repository_root / "data" / "combat_report_rules.json",
        repository_root / "data" / "combat_report_observations.json",
        repository_root,
    )
    measurement = empirical.build_measurement(
        json.loads(interpreted["enriched"].read_text(encoding="utf-8")),
        json.loads((repository_root / "data" / "combat_trial_definitions.json").read_text(encoding="utf-8")),
        experiment_id=experiment, variant=variant, question=question,
    )
    measurement_json = output / "combat-measurements.json"
    measurement_markdown = output / "combat-measurements.md"
    empirical.write_json(measurement_json, measurement)
    measurement_markdown.write_text(empirical.render_measurement(measurement), encoding="utf-8")
    return {
        "output": output,
        "ocr": ocr_path,
        "report": report_path,
        "extractor_insights": extractor_insights,
        "measurement": measurement_json,
        "measurement_markdown": measurement_markdown,
        **interpreted,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Path to a local combat-report recording")
    parser.add_argument("--experiment", help="Optional local experiment group identifier")
    parser.add_argument("--variant", help="Optional baseline/swap or other variant label")
    parser.add_argument("--question", help="Optional hypothesis not otherwise visible in the recording")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repository_root_from_script()
    try:
        paths = ingest(
            args.video, root, date.today(), experiment=args.experiment,
            variant=args.variant, question=args.question,
        )
    except (FileNotFoundError, RuntimeError) as error:
        raise SystemExit(str(error)) from error

    analysis = json.loads(paths["analysis"].read_text(encoding="utf-8"))
    candidates = json.loads(paths["candidates"].read_text(encoding="utf-8"))
    coverage = analysis["coverage"]
    print("\nCombat report ingestion complete.")
    print(f"Output folder: {paths['output']}")
    print(f"Review first: {paths['markdown']}")
    print(f"Empirical measurements: {paths['measurement_markdown']}")
    print(f"Parsed actions: {coverage.get('action_count', 0)}")
    print(f"Rejected actions: {coverage.get('rejected_action_count', 0)}")
    print(f"Established links: {analysis['insights']['established_link_count']}")
    print(f"Review candidates: {len(candidates['candidates'])}")
    measurement = json.loads(paths["measurement"].read_text(encoding="utf-8"))
    print(f"Configured RNG subjects measured: {len(measurement['trials'])}")
    for warning in coverage.get("warnings", []):
        print(f"Coverage warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
