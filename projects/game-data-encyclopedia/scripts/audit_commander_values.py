#!/usr/bin/env python3
"""Extract a traceable, static Commander progression inventory from a local capture.

Numeric protobuf field paths and source progression references are retained: this is
not a decoder of combat behavior or evidence of server activation.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Game_Details/Resources"))
from _pbdump import dump_file  # noqa: E402

TABLES = ("commanderTalentTable_merged", "dragonAbilitiesTable_merged", "dragonEffectGroupsTable_merged", "dragonEffectsTable_merged", "dragonProgressionWithSourceTable_merged", "progressionTable_merged")


def refs(value, path=""):
    if isinstance(value, dict):
        if isinstance(value.get("2"), str) and isinstance(value.get("1"), dict) and "_fixed64_int" in value["1"]:
            yield path, value["2"]
        else:
            for key, child in value.items():
                yield from refs(child, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, child in enumerate(value, 1):
            yield from refs(child, f"{path}[{index}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resources", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.resources)
    tables, hashes = {}, {}
    for name in TABLES:
        paths = list(root.rglob(name + ".*.pb"))
        if len(paths) != 1:
            raise ValueError(f"Expected exactly one {name}, found {len(paths)}")
        path = paths[0]
        hashes[name] = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        rows = dump_file(str(path))["1"]
        if name == "progressionTable_merged":
            tables[name] = {r["2"].get("1", {}).get("2"): r["2"] for r in rows if isinstance(r.get("2"), dict) and isinstance(r["2"].get("1"), dict)}
        else:
            tables[name] = {r["1"]["2"]: r["2"] for r in rows if isinstance(r.get("1"), dict) and isinstance(r["1"].get("2"), str)}

    reference = json.loads((ROOT / "data/commanders.json").read_text(encoding="utf-8"))
    all_rows = {key: (table, value) for table, rows in tables.items() for key, value in rows.items() if key}
    result = {"snapshot_date": "2026-11-13", "client_version": "26.10.58019 / 345", "source_hashes": hashes, "talents": []}
    for commander in reference["commanders"]:
        for talent in commander["talents"]:
            matches = [(key, row) for key, row in tables[TABLES[0]].items() if row.get("2") == talent["client_key"]]
            if len(matches) != 1:
                raise ValueError(f"Talent lookup is ambiguous: {talent['client_key']}")
            talent_key, row = matches[0]
            root_ability = row["5"]["2"]
            token = root_ability.removeprefix("ability_talent_").removesuffix("_01")
            # Include reactive sub-abilities referenced in localization or named for the same talent.
            pending = [talent_key] + [key for key in tables[TABLES[1]] if key.startswith(f"ability_talent_{token}_")]
            seen, edges, tracks = set(), [], {}
            while pending:
                key = pending.pop()
                if key in seen or key not in all_rows:
                    continue
                seen.add(key)
                table, value = all_rows[key]
                if table == "progressionTable_merged":
                    entry = value.get("1000", {}).get("1002", {}).get("2", [])
                    entry = entry if isinstance(entry, list) else [entry]
                    if entry and all(isinstance(x, dict) and "_fixed64_double" in x for x in entry):
                        tracks[key] = [x["_fixed64_double"] for x in entry]
                for field, target in refs(value):
                    if target in all_rows:
                        edges.append({"from": key, "field": field, "to": target})
                        pending.append(target)
            result["talents"].append({"commander": commander["name"], "talent": talent["name"], "client_key": talent_key, "ability": root_ability, "edges": sorted(edges, key=lambda x: (x["from"], x["field"], x["to"])), "tracks": dict(sorted(tracks.items()))})
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['talents'])} talents, {sum(len(t['tracks']) for t in result['talents'])} linked tracks")


if __name__ == "__main__":
    main()
