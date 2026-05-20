#!/usr/bin/env python3
"""Validate HL dataset candidate unit files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_UNIT_FIELDS = (
    "unit_id",
    "version",
    "trigger",
    "diagnosis",
    "dataset_intent",
    "candidate_destination",
    "reward_expectation",
    "replay_requirements",
    "records",
)
REQUIRED_RECORD_FIELDS = (
    "id",
    "layer",
    "role",
    "scene_type",
    "difficulty",
    "input",
    "target_behavior",
    "avoid_behavior",
    "tags",
    "rubric_ref",
    "source_path",
    "review_status",
)


def present(value: Any) -> bool:
    return value is not None and value != "" and value != []


def unit_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.glob("*.json") if candidate.is_file())


def validate_unit(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_UNIT_FIELDS:
        if not present(payload.get(field)):
            errors.append(f"{path}: missing {field}")

    trigger = payload.get("trigger")
    if not isinstance(trigger, dict):
        errors.append(f"{path}: trigger must be an object")
    else:
        for field in ("type", "summary"):
            if not present(trigger.get(field)):
                errors.append(f"{path}: missing trigger.{field}")

    for field in ("candidate_destination", "reward_expectation", "replay_requirements"):
        if field in payload and not isinstance(payload[field], list):
            errors.append(f"{path}: {field} must be a list")

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append(f"{path}: records must be a non-empty list")
        return errors
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}: records[{index}] must be an object")
            continue
        for field in REQUIRED_RECORD_FIELDS:
            if not present(record.get(field)):
                errors.append(f"{path}: missing records[{index}].{field}")
        for field in ("target_behavior", "avoid_behavior", "tags"):
            if field in record and not isinstance(record[field], list):
                errors.append(f"{path}: records[{index}].{field} must be a list")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    paths = unit_paths(args.path)
    if not paths:
        errors.append(f"{args.path}: no dataset candidate unit JSON files found")
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path}: invalid JSON: {error}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{path}: top-level JSON must be an object")
            continue
        errors.extend(validate_unit(payload, path))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"Validated {len(paths)} dataset candidate units")


if __name__ == "__main__":
    main()
