#!/usr/bin/env python3
"""Validate heuristic-eval evolution event JSONL logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVENT_TYPES = {
    "case_added",
    "case_marked_needs_revision",
    "case_promoted",
    "case_retired",
    "case_revised",
    "experiment_promoted",
    "experiment_retired",
    "experiment_started",
    "failure_pattern_added",
    "human_signal_captured",
    "profile_adapter_updated",
    "rubric_revised",
}

EVIDENCE_KINDS = {
    "coverage_gap",
    "cross_project_reuse",
    "eval_failure",
    "human_review",
    "human_signal",
    "legacy_assertion",
    "module_ref",
    "repeated_regression",
}


def present(value: Any) -> bool:
    return value is not None and value != "" and value != []


def validate_event(event: dict[str, Any], path: Path, line_number: int, errors: list[str]) -> None:
    for field in ("event_id", "timestamp", "event_type", "actor"):
        if not present(event.get(field)):
            errors.append(f"{path}:{line_number}: missing {field}")

    event_type = event.get("event_type")
    if present(event_type) and event_type not in EVENT_TYPES:
        errors.append(f"{path}:{line_number}: invalid event_type: {event_type}")

    decision = event.get("decision")
    if not isinstance(decision, dict):
        errors.append(f"{path}:{line_number}: missing decision object")
    elif not present(decision.get("reason")):
        errors.append(f"{path}:{line_number}: missing decision.reason")

    evidence = event.get("evidence")
    if not isinstance(evidence, dict):
        errors.append(f"{path}:{line_number}: missing evidence object")
    else:
        kind = evidence.get("kind")
        if not present(kind):
            errors.append(f"{path}:{line_number}: missing evidence.kind")
        elif kind not in EVIDENCE_KINDS:
            errors.append(f"{path}:{line_number}: invalid evidence.kind: {kind}")
        if not present(evidence.get("summary")):
            errors.append(f"{path}:{line_number}: missing evidence.summary")

    if event_type == "profile_adapter_updated":
        if not present(event.get("profile_ref")):
            errors.append(f"{path}:{line_number}: profile_adapter_updated missing profile_ref")
        if not present(event.get("adapter_ref")):
            errors.append(f"{path}:{line_number}: profile_adapter_updated missing adapter_ref")
        if isinstance(evidence, dict) and evidence.get("kind") != "module_ref":
            errors.append(f"{path}:{line_number}: profile_adapter_updated requires evidence.kind module_ref")


def eval_dataset_root_for_log(path: Path) -> Path | None:
    resolved = path.resolve()
    for parent in resolved.parents:
        if parent.name == "eval_datasets":
            return parent
    return None


def resolve_ref_path(ref: Any, event_log_path: Path) -> Path | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    target = Path(ref).expanduser()
    if target.is_absolute():
        return target
    eval_root = eval_dataset_root_for_log(event_log_path)
    if eval_root is not None and ref.startswith("eval_datasets/"):
        return eval_root.parent / target
    if eval_root is not None and ref.startswith(("profiles/", "adapters/", "canonical/", "runs/", "experiments/")):
        return eval_root / target
    if not target.is_absolute():
        target = Path.cwd() / target
    return target


def validate_profile_adapter_ref_paths(
    event: dict[str, Any],
    path: Path,
    line_number: int,
    errors: list[str],
) -> None:
    if event.get("event_type") != "profile_adapter_updated":
        return
    for field in ("profile_ref", "adapter_ref"):
        target = resolve_ref_path(event.get(field), path)
        if target is not None and not target.exists():
            errors.append(f"{path}:{line_number}: {field} does not exist: {event.get(field)}")


def validate_event_log(path: Path, check_paths: bool) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [f"{path}: events file not found"]

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"{path}:{line_number}: invalid JSONL: {error}")
            continue
        if not isinstance(event, dict):
            errors.append(f"{path}:{line_number}: event must be a JSON object")
            continue

        event_id = event.get("event_id")
        if isinstance(event_id, str) and event_id:
            if event_id in seen_ids:
                errors.append(f"{path}:{line_number}: duplicate event_id: {event_id}")
            seen_ids.add(event_id)

        validate_event(event, path, line_number, errors)

        dataset_path = event.get("dataset_path")
        if check_paths and present(dataset_path):
            target = resolve_ref_path(str(dataset_path), path)
            if not target.exists():
                errors.append(f"{path}:{line_number}: dataset_path does not exist: {dataset_path}")
        if check_paths:
            validate_profile_adapter_ref_paths(event, path, line_number, errors)

    if not seen_ids and not errors:
        errors.append(f"{path}: no events found")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("--skip-path-check", action="store_true")
    args = parser.parse_args()

    errors = validate_event_log(args.events, not args.skip_path_check)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"Validated {len(args.events.read_text(encoding='utf-8').splitlines())} evolution events")


if __name__ == "__main__":
    main()
