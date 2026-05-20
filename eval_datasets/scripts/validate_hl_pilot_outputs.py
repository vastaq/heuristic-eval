#!/usr/bin/env python3
"""Validate HL pilot review batches, candidate slices, and event logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"{label} {path}: invalid JSON: {error}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} {path}: top-level JSON must be an object")
        return None
    return payload


def validate_review_batch(path: Path, errors: list[str]) -> None:
    payload = load_json(path, "review batch", errors)
    if payload is None:
        return
    if not payload.get("source_dataset"):
        errors.append(f"{path}: missing source_dataset")
    if not isinstance(payload.get("records"), list):
        errors.append(f"{path}: records must be a list")


def validate_candidate_slice(path: Path, errors: list[str]) -> None:
    payload = load_json(path, "candidate slice", errors)
    if payload is None:
        return
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append(f"{path}: records must be a non-empty list")
        return
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}: records[{index}] must be an object")
            continue
        for field in ("id", "input", "generic_dimension"):
            if not record.get(field):
                errors.append(f"{path}: records[{index}] missing {field}")
        if not (record.get("source_path") or record.get("source_id")):
            errors.append(f"{path}: records[{index}] missing source_path or source_id")


def validate_events(path: Path, check_paths: bool, errors: list[str]) -> None:
    base = Path.cwd()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"{path}: events file not found")
        return
    for index, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"{path}:{index}: invalid JSONL: {error}")
            continue
        if not event.get("event_id"):
            errors.append(f"{path}:{index}: missing event_id")
        if not event.get("event_type"):
            errors.append(f"{path}:{index}: missing event_type")
        if not isinstance(event.get("decision"), dict):
            errors.append(f"{path}:{index}: missing decision object")
        if not isinstance(event.get("evidence"), dict):
            errors.append(f"{path}:{index}: missing evidence object")
        dataset_path = event.get("dataset_path")
        if check_paths and dataset_path:
            target = Path(dataset_path)
            if not target.is_absolute():
                target = base / target
            if not target.exists():
                errors.append(f"{path}:{index}: dataset_path does not exist: {dataset_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-batch", action="append", type=Path, default=[])
    parser.add_argument("--candidate-slice", action="append", type=Path, default=[])
    parser.add_argument("--events", type=Path)
    parser.add_argument("--skip-event-path-check", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.review_batch:
        validate_review_batch(path, errors)
    for path in args.candidate_slice:
        validate_candidate_slice(path, errors)
    if args.events:
        validate_events(args.events, not args.skip_event_path_check, errors)

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("HL pilot outputs validated")


if __name__ == "__main__":
    main()
