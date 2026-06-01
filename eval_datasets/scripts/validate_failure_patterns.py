#!/usr/bin/env python3
"""Validate heuristic eval failure pattern JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = ("id", "scope", "failure_modes")
OWNER_FIELDS = ("profile", "domain", "role")
REQUIRED_MODE_FIELDS = ("id", "description", "signals", "evidence")
REQUIRED_EVIDENCE_FIELDS = ("kind", "summary")


def json_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.glob("*.json") if candidate.is_file())


def require_non_empty(value: Any) -> bool:
    return value is not None and value != "" and value != []


def validate_payload(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if not require_non_empty(payload.get(field)):
            errors.append(f"{path}: missing {field}")
    if not any(require_non_empty(payload.get(field)) for field in OWNER_FIELDS):
        errors.append(f"{path}: missing one of {', '.join(OWNER_FIELDS)}")

    modes = payload.get("failure_modes")
    if not isinstance(modes, list) or not modes:
        errors.append(f"{path}: failure_modes must be a non-empty list")
        return errors

    for index, mode in enumerate(modes):
        if not isinstance(mode, dict):
            errors.append(f"{path}: failure_modes[{index}] must be an object")
            continue
        for field in REQUIRED_MODE_FIELDS:
            if not require_non_empty(mode.get(field)):
                errors.append(f"{path}: missing failure_modes[{index}].{field}")
        if "signals" in mode and not isinstance(mode["signals"], list):
            errors.append(f"{path}: failure_modes[{index}].signals must be a list")
        if "evidence" in mode and not isinstance(mode["evidence"], list):
            errors.append(f"{path}: failure_modes[{index}].evidence must be a list")
        elif isinstance(mode.get("evidence"), list):
            for evidence_index, evidence in enumerate(mode["evidence"]):
                if not isinstance(evidence, dict):
                    errors.append(
                        f"{path}: failure_modes[{index}].evidence[{evidence_index}] must be an object"
                    )
                    continue
                for field in REQUIRED_EVIDENCE_FIELDS:
                    if not require_non_empty(evidence.get(field)):
                        errors.append(
                            f"{path}: missing failure_modes[{index}].evidence[{evidence_index}].{field}"
                        )
    return errors


def validate_path(path: Path) -> int:
    paths = json_paths(path)
    errors: list[str] = []
    for json_path in paths:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{json_path}: invalid JSON: {error}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{json_path}: top-level JSON must be an object")
            continue
        errors.extend(validate_payload(payload, json_path))

    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"Validated {len(paths)} failure pattern files")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    raise SystemExit(validate_path(args.path))


if __name__ == "__main__":
    main()
