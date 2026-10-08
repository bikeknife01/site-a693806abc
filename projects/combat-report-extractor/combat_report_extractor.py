#!/usr/bin/env python3
"""Extract visible Dragonfire combat-report actions from a screen recording.

The tool is deliberately UI-only. It decodes a local video, OCRs visible report
cards, classifies blue cards as user actions and red cards as enemy actions, and
retains raw evidence beside every normalized record. It never connects to the
game, emulator, or network.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
SECTION_RE = re.compile(r"^(TROOP\s*FORMATION|PREPARATIONS|ROUND\s*\d+|STALEMATE)$", re.I)
DAMAGE_RE = re.compile(r"Deals?\s*([\d,]+)\s*(Physical|Fire|Tactical|Strategic)\s*Damage", re.I)
LOSSES_RE = re.compile(r"takes?\s*([\d,]+)\s*losses?\s*\(([\d,]+)\s*remaining", re.I)
RECOVERY_RE = re.compile(r"Recovers?\s*([\d,]+)\s*total\s*troops", re.I)
PERCENT_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%\s*([^.;]+)", re.I)


def compact(value: str) -> str:
    value = value.translate(str.maketrans({"（": "(", "）": ")", "［": "[", "］": "]"}))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def clean_text(value: str) -> str:
    value = value.translate(str.maketrans({"（": "(", "）": ")", "［": "[", "］": "]"}))
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\[\s+", "[", value)
    return re.sub(r"\s+\]", "]", value)


def load_vocabulary(repository_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    dragons: dict[str, str] = {}
    abilities: dict[str, str] = {compact("Basic Attack"): "Basic Attack"}
    for path in sorted((repository_root / "data" / "dragons").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name")
        if isinstance(name, str):
            dragons[compact(name)] = name
        for key in ("command", "vanguard"):
            ability_name = (data.get(key) or {}).get("name")
            if isinstance(ability_name, str):
                abilities[compact(ability_name)] = ability_name
        for habit in data.get("habits", []):
            ability_name = habit.get("name")
            if isinstance(ability_name, str):
                abilities[compact(ability_name)] = ability_name
    return dragons, abilities


def canonicalize(value: str | None, vocabulary: dict[str, str]) -> str | None:
    if value is None:
        return None
    key = compact(value)
    if not key:
        return None
    if key in vocabulary:
        return vocabulary[key]
    candidates = difflib.get_close_matches(key, vocabulary, n=1, cutoff=0.82)
    return vocabulary[candidates[0]] if candidates else clean_text(value)


def parse_action_head(text: str) -> dict[str, Any] | None:
    squashed = re.sub(r"\s+", "", clean_text(text))
    patterns = (
        ("attack", re.compile(r"^\[(?P<actor>[^\]]+)\]uses\[(?P<ability>[^\]]+)\]toattack\[(?P<target>[^\]]+)\](?:\((?P<lane>[^)]+)\))?", re.I)),
        ("affect", re.compile(r"^\[(?P<actor>[^\]]+)\]activates\[(?P<ability>[^\]]+)\]affecting\[(?P<target>[^\]]+)\](?:\((?P<lane>[^)]+)\))?", re.I)),
        ("self_effect", re.compile(r"^\[(?P<actor>[^\]]+)\]activates\[(?P<ability>[^\]]+)\]onitself", re.I)),
    )
    for kind, pattern in patterns:
        match = pattern.search(squashed)
        if match:
            result = {"kind": kind, **match.groupdict()}
            if kind == "self_effect":
                result["target"] = result["actor"]
            return result
    recovery = re.search(r"^\[(?P<actor>[^\]]+)\]recovers?([\d,]+)totaltroops", squashed, re.I)
    if recovery:
        return {"kind": "recovery", "actor": recovery.group("actor"), "ability": None,
                "target": recovery.group("actor"), "lane": None,
                "inline_recovery": int(recovery.group(2).replace(",", ""))}
    return None


def line_center(line: dict[str, Any]) -> tuple[float, float]:
    points = line.get("box") or []
    if not points:
        return 0.0, 0.0
    return (sum(float(p[0]) for p in points) / len(points),
            sum(float(p[1]) for p in points) / len(points))


def classify_owner(image: Any, line: dict[str, Any]) -> str:
    """Classify the card beneath a line using the stable blue/red body colors."""
    import numpy as np

    _, center_y = line_center(line)
    height, width = image.shape[:2]
    patch = image[max(0, int(center_y) - 14):min(height, int(center_y) + 15),
                  max(0, int(width * 0.28)):min(width, int(width * 0.82))]
    if patch.size == 0:
        return "unknown"
    blue, _green, red = np.median(patch.reshape(-1, 3), axis=0)
    delta = float(blue) - float(red)
    return "user" if delta >= 10 else "enemy" if delta <= -10 else "unknown"


def detect_active_section(image: Any, lines: list[dict[str, Any]]) -> str | None:
    """Find the sidebar item whose circular marker is blue."""
    import numpy as np

    candidates: list[tuple[float, str]] = []
    height, width = image.shape[:2]
    for line in lines:
        x, y = line_center(line)
        label = re.sub(r"\s+", " ", line["text"]).strip().upper()
        if x > width * 0.22 or not SECTION_RE.match(label):
            continue
        patch = image[max(0, int(y) - 28):min(height, int(y) + 29),
                      max(0, int(width * 0.013)):min(width, int(width * 0.042))]
        if patch.size:
            blue, _green, red = np.mean(patch.reshape(-1, 3), axis=0)
            candidates.append((float(blue) - float(red), re.sub(r"ROUND\s*", "ROUND ", label)))
    if not candidates:
        return None
    score, label = max(candidates)
    return label if score >= 18 else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as error:
        raise RuntimeError("FFmpeg was not found. Install requirements.txt or put ffmpeg on PATH.") from error


def extract_frames(video: Path, frame_dir: Path, interval: float) -> list[Path]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = frame_dir / "frame-%06d.jpg"
    subprocess.run([resolve_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(video),
                    "-vf", f"fps=1/{interval}", "-q:v", "2", str(pattern)], check=True)
    return sorted(frame_dir.glob("frame-*.jpg"))


def ocr_video(video: Path, output: Path, interval: float, min_sharpness: float) -> Path:
    try:
        import cv2
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as error:
        raise RuntimeError("Video OCR dependencies are missing. Install requirements.txt.") from error

    frames = extract_frames(video, output / "frames", interval)
    engine = RapidOCR()
    evidence_frames: list[dict[str, Any]] = []
    skipped_blurry = 0
    for index, path in enumerate(frames):
        image = cv2.imread(str(path))
        if image is None:
            continue
        sharpness = float(cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        if sharpness < min_sharpness:
            skipped_blurry += 1
            continue
        result, _elapsed = engine(image)
        lines: list[dict[str, Any]] = []
        for box, text, confidence in result or []:
            record = {"text": clean_text(text), "confidence": round(float(confidence), 6),
                      "box": [[round(float(x), 2), round(float(y), 2)] for x, y in box]}
            record["ownership"] = classify_owner(image, record)
            lines.append(record)
        evidence_frames.append({"frame": path.name, "timestamp_seconds": round(index * interval, 3),
                                "sharpness": round(sharpness, 3),
                                "active_section": detect_active_section(image, lines), "lines": lines})
        if (index + 1) % 10 == 0 or index + 1 == len(frames):
            print(f"OCR frames: {index + 1}/{len(frames)}", flush=True)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source": {"path": str(video.resolve()), "sha256": sha256_file(video),
                   "captured_at_utc": datetime.now(timezone.utc).isoformat()},
        "sampling": {"interval_seconds": interval, "min_sharpness": min_sharpness,
                     "decoded_frames": len(frames), "ocr_frames": len(evidence_frames),
                     "skipped_blurry_frames": skipped_blurry},
        "ownership_rule": {"blue": "user", "red": "enemy", "authority": "user-supplied"},
        "frames": evidence_frames,
    }
    path = output / "ocr_frames.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def attach_details(lines: list[dict[str, Any]], index: int, owner: str) -> list[dict[str, Any]]:
    _, head_y = line_center(lines[index])
    details: list[dict[str, Any]] = []
    for candidate in lines[index + 1:]:
        x, y = line_center(candidate)
        if y <= head_y or y - head_y > 115:
            continue
        if x < 500:
            continue
        if parse_action_head(candidate["text"]):
            break
        if candidate.get("ownership", "unknown") not in (owner, "unknown"):
            continue
        details.append(candidate)
    return details


def parse_ocr_manifest(manifest: dict[str, Any], repository_root: Path) -> dict[str, Any]:
    dragons, abilities = load_vocabulary(repository_root)
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for frame in manifest.get("frames", []):
        section = frame.get("active_section")
        round_match = re.match(r"ROUND\s*(\d+)", section or "", re.I)
        round_number = int(round_match.group(1)) if round_match else None
        lines = sorted(frame.get("lines", []), key=lambda line: line_center(line)[1])
        for index, line in enumerate(lines):
            x, _y = line_center(line)
            if x < 500:
                continue
            parsed = parse_action_head(line["text"])
            if not parsed:
                continue
            owner = line.get("ownership", "unknown")
            details = attach_details(lines, index, owner)
            detail_text = " ".join(item["text"] for item in details)
            damage, losses, recovery = DAMAGE_RE.search(detail_text), LOSSES_RE.search(detail_text), RECOVERY_RE.search(detail_text)
            modifiers = [{"percent": float(percent), "description": description.strip()}
                         for percent, description in PERCENT_RE.findall(detail_text)]
            record = {
                "round": round_number, "section": section, "owner": owner, "kind": parsed["kind"],
                "actor": canonicalize(parsed.get("actor"), dragons),
                "ability": canonicalize(parsed.get("ability"), abilities),
                "target": canonicalize(parsed.get("target"), dragons),
                "target_lane": clean_text(parsed["lane"]) if parsed.get("lane") else None,
                "damage": ({"amount": int(damage.group(1).replace(",", "")),
                            "type": damage.group(2).title()} if damage else None),
                "losses": int(losses.group(1).replace(",", "")) if losses else None,
                "remaining": int(losses.group(2).replace(",", "")) if losses else None,
                "recovery": parsed.get("inline_recovery") or (int(recovery.group(1).replace(",", "")) if recovery else None),
                "modifiers": modifiers,
                "evidence": {"timestamp_seconds": frame.get("timestamp_seconds"), "frame": frame.get("frame"),
                             "ocr_confidence": round(sum(float(item.get("confidence", 0)) for item in [line, *details]) / max(1, len(details) + 1), 6),
                             "head_text": line["text"], "detail_text": detail_text},
            }
            if owner == "unknown" or round_number is None:
                rejected.append({"reason": "missing ownership or round", "record": record})
            else:
                records.append(record)

    # Neighboring sampled frames intentionally overlap. Collapse the same semantic card
    # within an eight-second window even when OCR varies in punctuation or modifier text.
    clustered: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in sorted(records, key=lambda item: item["evidence"]["timestamp_seconds"]):
        key = (
            record["round"], record["owner"], record["kind"],
            compact(record.get("actor") or ""), compact(record.get("ability") or ""),
            compact(record.get("target") or ""), (record.get("damage") or {}).get("amount"),
            record.get("losses"), record.get("remaining"), record.get("recovery"),
        )
        timestamp = record["evidence"]["timestamp_seconds"]
        matches = clustered[key]
        nearby_index = next(
            (index for index, previous in enumerate(matches)
             if abs(timestamp - previous["evidence"]["timestamp_seconds"]) <= 8),
            None,
        )
        if nearby_index is None:
            matches.append(record)
        else:
            previous = matches[nearby_index]
            previous_score = (len(previous["evidence"]["detail_text"]), previous["evidence"]["ocr_confidence"])
            record_score = (len(record["evidence"]["detail_text"]), record["evidence"]["ocr_confidence"])
            if record_score > previous_score:
                matches[nearby_index] = record
    actions = [record for matches in clustered.values() for record in matches]

    # A clipped attack head may have no damage sentence while a neighboring frame has
    # the complete card. Prefer the complete record without hiding genuinely incomplete
    # attacks that have no matching evidence.
    complete_attack_keys = {
        (action["round"], action["owner"], compact(action.get("actor") or ""),
         compact(action.get("ability") or ""), compact(action.get("target") or ""))
        for action in actions if action["kind"] == "attack" and action.get("damage")
    }
    actions = [
        action for action in actions
        if not (
            action["kind"] == "attack" and action.get("damage") is None
            and (action["round"], action["owner"], compact(action.get("actor") or ""),
                 compact(action.get("ability") or ""), compact(action.get("target") or ""))
            in complete_attack_keys
        )
    ]
    actions.sort(key=lambda item: (item["round"], item["evidence"]["timestamp_seconds"], item["owner"]))
    rounds = sorted({record["round"] for record in actions if record["round"] is not None})
    warnings: list[str] = []
    stalemate_visible = any(
        frame.get("active_section") == "STALEMATE" for frame in manifest.get("frames", [])
    )
    expected_last_round = 10 if stalemate_visible else max(rounds, default=0)
    missing_rounds = sorted(set(range(1, expected_last_round + 1)) - set(rounds))
    if missing_rounds:
        warnings.append(f"No parsed visible actions for rounds: {', '.join(map(str, missing_rounds))}.")
    partial = sum(1 for action in actions if action["kind"] == "attack" and action["damage"] is None)
    if partial:
        warnings.append(f"{partial} parsed attack action(s) lack a readable damage sentence.")
    if rejected:
        warnings.append(f"{len(rejected)} action-like OCR record(s) were rejected for missing ownership or round context.")
    actor_owners: dict[str, set[str]] = defaultdict(set)
    for action in actions:
        if action.get("actor"):
            actor_owners[action["actor"]].add(action["owner"])
    contradictions = sorted(actor for actor, owners in actor_owners.items() if len(owners) > 1)
    if contradictions:
        warnings.append(
            "Actor ownership is inconsistent and requires frame review: "
            + ", ".join(contradictions)
            + "."
        )
    return {"schema_version": SCHEMA_VERSION, "source": manifest.get("source"),
            "ownership_rule": manifest.get("ownership_rule"),
            "coverage": {"rounds_with_actions": rounds, "action_count": len(actions),
                         "rejected_action_count": len(rejected), "warnings": warnings},
            "actions": actions, "rejected_actions": rejected}


def aggregate_insights(report: dict[str, Any]) -> dict[str, Any]:
    by_owner: dict[str, dict[str, Any]] = {}
    for owner in ("user", "enemy"):
        actions = [action for action in report["actions"] if action["owner"] == owner]
        damage_actions = [action for action in actions if action.get("damage")]
        by_actor: dict[str, int] = defaultdict(int)
        by_ability: dict[str, int] = defaultdict(int)
        target_damage: dict[str, int] = defaultdict(int)
        damage_types: Counter[str] = Counter()
        for action in damage_actions:
            amount = action["damage"]["amount"]
            by_actor[action["actor"] or "Unknown"] += amount
            by_ability[action["ability"] or "Unknown"] += amount
            target_damage[action["target"] or "Unknown"] += amount
            damage_types[action["damage"]["type"]] += amount
        by_owner[owner] = {
            "parsed_actions": len(actions), "damage_actions": len(damage_actions),
            "visible_damage_total": sum(action["damage"]["amount"] for action in damage_actions),
            "visible_recovery_total": sum(action.get("recovery") or 0 for action in actions),
            "damage_by_actor": dict(sorted(by_actor.items(), key=lambda item: (-item[1], item[0]))),
            "damage_by_ability": dict(sorted(by_ability.items(), key=lambda item: (-item[1], item[0]))),
            "damage_by_target": dict(sorted(target_damage.items(), key=lambda item: (-item[1], item[0]))),
            "damage_by_type": dict(sorted(damage_types.items())),
        }
    return {"by_owner": by_owner}


def render_insights(report: dict[str, Any]) -> str:
    insights = report.get("insights") or aggregate_insights(report)
    lines = ["# Combat report extraction insights", "",
             "> These totals include only successfully parsed text visible in sampled video frames.",
             "> They are not server totals and must not be treated as complete when coverage warnings remain.",
             "", "## Coverage", "", f"- Parsed actions: {report['coverage']['action_count']}",
             f"- Rounds with parsed actions: {', '.join(map(str, report['coverage']['rounds_with_actions'])) or 'none'}"]
    lines.extend(f"- Warning: {warning}" for warning in report["coverage"]["warnings"])
    user_values, enemy_values = insights["by_owner"]["user"], insights["by_owner"]["enemy"]
    lines.extend(["", "## Derived visible-value observations", ""])
    if enemy_values["visible_damage_total"]:
        ratio = user_values["visible_damage_total"] / enemy_values["visible_damage_total"]
        lines.append(
            f"- Parsed blue damage is {ratio:.2f}× parsed red damage "
            f"({user_values['visible_damage_total']:,} vs. {enemy_values['visible_damage_total']:,})."
        )
    for _owner, label, values in (("user", "Blue", user_values), ("enemy", "Red", enemy_values)):
        total = values["visible_damage_total"]
        if total and values["damage_by_actor"]:
            actor, amount = next(iter(values["damage_by_actor"].items()))
            lines.append(f"- {label}'s leading visible damage contributor is {actor}: {amount:,} ({amount / total:.1%}).")
        if total and values["damage_by_ability"]:
            ability, amount = next(iter(values["damage_by_ability"].items()))
            lines.append(f"- {label}'s leading visible damage ability is {ability}: {amount:,} ({amount / total:.1%}).")
        if total and values["damage_by_target"]:
            target, amount = next(iter(values["damage_by_target"].items()))
            lines.append(f"- {label}'s most-damaged visible target is {target}: {amount:,} ({amount / total:.1%}).")
        if values["visible_recovery_total"]:
            lines.append(f"- {label} has {values['visible_recovery_total']:,} parsed visible recovery.")
    for owner, label in (("user", "User / blue"), ("enemy", "Enemy / red")):
        values = insights["by_owner"][owner]
        lines.extend(["", f"## {label}", "", f"- Parsed actions: {values['parsed_actions']}",
                      f"- Visible damage total: {values['visible_damage_total']:,}",
                      f"- Visible recovery total: {values['visible_recovery_total']:,}", "", "### Damage by actor", ""])
        lines.extend(f"- {name}: {amount:,}" for name, amount in values["damage_by_actor"].items())
        lines.extend(["", "### Damage by ability", ""])
        lines.extend(f"- {name}: {amount:,}" for name, amount in values["damage_by_ability"].items())
        lines.extend(["", "### Damage received by target", ""])
        lines.extend(f"- {name}: {amount:,}" for name, amount in values["damage_by_target"].items())
    lines.extend(["", "## Auditable action ledger", ""])
    for action in report["actions"]:
        amount = f"; {action['damage']['amount']:,} {action['damage']['type']} damage" if action.get("damage") else ""
        remaining = f"; {action['remaining']:,} remaining" if action.get("remaining") is not None else ""
        lines.append(f"- R{action['round']} {action['owner']}: {action['actor']} — {action['ability'] or action['kind']} → "
                     f"{action['target'] or 'n/a'}{amount}{remaining} (frame `{action['evidence']['frame']}`, "
                     f"{action['evidence']['timestamp_seconds']:.1f}s)")
    return "\n".join(lines) + "\n"


def write_report(ocr_path: Path, output: Path, repository_root: Path) -> tuple[Path, Path]:
    report = parse_ocr_manifest(json.loads(ocr_path.read_text(encoding="utf-8")), repository_root)
    report["insights"] = aggregate_insights(report)
    output.mkdir(parents=True, exist_ok=True)
    report_path, insights_path = output / "combat-report.json", output / "insights.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    insights_path.write_text(render_insights(report), encoding="utf-8")
    return report_path, insights_path


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=repository_root_from_script())
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract", help="Decode, OCR, parse, and analyze a local video")
    extract.add_argument("--video", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)
    extract.add_argument("--interval", type=float, default=1.5)
    extract.add_argument("--min-sharpness", type=float, default=45.0)
    parse = subparsers.add_parser("parse", help="Parse a retained ocr_frames.json manifest")
    parse.add_argument("--ocr", type=Path, required=True)
    parse.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository_root = args.repository_root.resolve()
    if args.command == "extract":
        if args.interval <= 0:
            raise SystemExit("--interval must be greater than zero")
        args.output.mkdir(parents=True, exist_ok=True)
        ocr_path = ocr_video(args.video.resolve(), args.output.resolve(), args.interval, args.min_sharpness)
        report_path, insights_path = write_report(ocr_path, args.output.resolve(), repository_root)
    else:
        ocr_path = args.ocr.resolve()
        report_path, insights_path = write_report(ocr_path, args.output.resolve(), repository_root)
    print(f"OCR evidence: {ocr_path}")
    print(f"Combat report: {report_path}")
    print(f"Insights: {insights_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

