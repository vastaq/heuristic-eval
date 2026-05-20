#!/usr/bin/env python3
"""Validate role-eval heuristic learning state snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = (
    "system_id",
    "version",
    "updated_at",
    "active_loop",
    "core_dimensions",
    "memory_layers",
    "known_failure_patterns",
    "open_gaps",
    "reward_weights",
    "allowed_actions",
    "blocked_actions",
    "next_replay_targets",
)

REQUIRED_REWARD_WEIGHTS = (
    "user_facing_relevance",
    "diagnostic_clarity",
    "cross_project_generality",
    "replay_stability",
    "noise_reduction",
    "compression_value",
)


def require(value: Any) -> bool:
    return value is not None and value != "" and value != []


def validate_state(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in payload:
            errors.append(f"{path}: missing {field}")

    core_dimensions = payload.get("core_dimensions")
    if not isinstance(core_dimensions, list):
        errors.append(f"{path}: core_dimensions must be a list")
    else:
        for index, dimension in enumerate(core_dimensions):
            if not isinstance(dimension, dict):
                errors.append(f"{path}: core_dimensions[{index}] must be an object")
                continue
            for field in ("id", "status", "evidence"):
                if not require(dimension.get(field)):
                    errors.append(f"{path}: core_dimensions[{index}] missing {field}")
            if "evidence" in dimension and not isinstance(dimension["evidence"], list):
                errors.append(f"{path}: core_dimensions[{index}].evidence must be a list")

    reward_weights = payload.get("reward_weights")
    if not isinstance(reward_weights, dict):
        errors.append(f"{path}: reward_weights must be an object")
    else:
        for field in REQUIRED_REWARD_WEIGHTS:
            value = reward_weights.get(field)
            if value is None:
                errors.append(f"{path}: missing reward_weights.{field}")
            elif not isinstance(value, int | float):
                errors.append(f"{path}: reward_weights.{field} must be numeric")

    for field in ("allowed_actions", "blocked_actions", "next_replay_targets", "open_gaps"):
        if field in payload and not isinstance(payload[field], list):
            errors.append(f"{path}: {field} must be a list")

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
            errors.extend(validate_state(payload, args.path))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("HL learning state validated")


if __name__ == "__main__":
    main()
