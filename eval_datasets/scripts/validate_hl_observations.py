#!/usr/bin/env python3
"""Validate HL replay observation files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = ("version", "run_id", "records")
REQUIRED_RECORD_FIELDS = ("record_id", "input", "output", "judge", "metadata", "failure_tags")


def present(value: Any) -> bool:
    return value is not None and value != ""


def validate_payload(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if not present(payload.get(field)):
            errors.append(f"{path}: missing {field}")

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append(f"{path}: records must be a non-empty list")
        return errors

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}: records[{index}] must be an object")
            continue
        for field in REQUIRED_RECORD_FIELDS:
            if field not in record or not present(record.get(field)):
                errors.append(f"{path}: missing records[{index}].{field}")
        if "judge" in record and not isinstance(record["judge"], dict):
            errors.append(f"{path}: records[{index}].judge must be an object")
        if "metadata" in record and not isinstance(record["metadata"], dict):
            errors.append(f"{path}: records[{index}].metadata must be an object")
        if "failure_tags" in record and not isinstance(record["failure_tags"], list):
            errors.append(f"{path}: records[{index}].failure_tags must be a list")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"{args.path}: invalid JSON: {error}")
    else:
        if not isinstance(payload, dict):
            errors.append(f"{args.path}: top-level JSON must be an object")
        else:
            errors.extend(validate_payload(payload, args.path))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"Validated {len(payload['records'])} observations")


if __name__ == "__main__":
    main()
