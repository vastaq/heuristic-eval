#!/usr/bin/env python3
"""Batch import role-directory test*.yaml files into one canonical dataset."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from import_promptfoo_tests import records_from_promptfoo


def role_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    if len(rel.parts) <= 1:
        return path.stem
    return rel.parts[0]


def stable_prefix(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    raw = "_".join(rel.parts)
    return re.sub(r"[^0-9A-Za-z]+", "_", raw).strip("_").lower()


def discover(root: Path) -> list[Path]:
    files = []
    for path in root.glob("**/test*.yaml"):
        if "node_modules" in path.parts or "role_eval" in path.parts:
            continue
        files.append(path)
    return sorted(files)


def dedupe_ids(records: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for record in records:
        original = record["id"]
        candidate = original
        suffix = 2
        while candidate in seen:
            candidate = f"{original}_{suffix}"
            suffix += 1
        record["id"] = candidate
        seen.add(candidate)


def batch_import(root: Path, output_path: Path, project: str) -> int:
    files = discover(root)
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for path in files:
        role = role_from_path(root, path)
        try:
            imported = records_from_promptfoo(path, role)
        except Exception as exc:  # noqa: BLE001 - import should continue across legacy files.
            skipped.append({"path": str(path.relative_to(root)), "reason": str(exc)})
            continue

        prefix = stable_prefix(root, path)
        for record in imported:
            record["id"] = f"{prefix}_{record['id']}"
            record["source_path"] = str(path.relative_to(root))
            record["source_file"] = str(path.relative_to(root))
            records.append(record)

    dedupe_ids(records)
    payload = {
        "version": "v1",
        "project": project,
        "dataset_type": "character_prompt_eval",
        "source_paths": [str(path.relative_to(root)) for path in files],
        "updated_at": date.today().isoformat(),
        "records": records,
        "skipped": skipped,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovered {len(files)} test YAML files.")
    print(f"Imported {len(records)} records to {output_path}.")
    if skipped:
        print(f"Skipped {len(skipped)} files:")
        for item in skipped:
            print(f"- {item['path']}: {item['reason']}")
    return 0 if not skipped else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project", default="all_existing_roles")
    args = parser.parse_args()
    raise SystemExit(batch_import(args.root.resolve(), args.output, args.project))


if __name__ == "__main__":
    main()
