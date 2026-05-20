#!/usr/bin/env python3
"""Audit canonical role testsets for coverage and concentration issues."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "layer",
    "role",
    "character_context",
    "scene_type",
    "difficulty",
    "input",
    "target_behavior",
    "avoid_behavior",
    "tags",
    "rubric_ref",
    "source_path",
    "review_status",
}
SCENE_THRESHOLD = 0.65
TAG_THRESHOLD = 0.65


def ratio(count: int, total: int) -> str:
    if total == 0:
        return "0/0"
    return f"{count}/{total} ({count / total:.0%})"


def audit(dataset_path: Path) -> int:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    records = dataset.get("records", [])
    warnings: list[str] = []

    print(f"Dataset: {dataset_path}")
    print(f"Project: {dataset.get('project', '')}")
    print(f"Total records: {len(records)}")
    print()

    ids = Counter(record.get("id") for record in records)
    for record_id, count in sorted(ids.items()):
        if record_id and count > 1:
            warnings.append(f"duplicate id: {record_id}")

    for index, record in enumerate(records):
        missing = sorted(field for field in REQUIRED_FIELDS if field not in record)
        if missing:
            warnings.append(f"record {index} missing fields: {', '.join(missing)}")

    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_role[record.get("role", "unknown")].append(record)

    for role in sorted(by_role):
        role_records = by_role[role]
        total = len(role_records)
        layer_counts = Counter(record.get("layer", "") for record in role_records)
        scene_counts = Counter(record.get("scene_type", "") for record in role_records)
        difficulty_counts = Counter(record.get("difficulty", "") for record in role_records)
        tag_counts = Counter(tag for record in role_records for tag in record.get("tags", []))
        status_counts = Counter(record.get("review_status", "") for record in role_records)

        print(f"## {role} ({total} records)")
        print("layers:", dict(sorted(layer_counts.items())))
        print("difficulty:", dict(sorted(difficulty_counts.items())))
        print("statuses:", dict(sorted(status_counts.items())))
        print("top scenes:", scene_counts.most_common(3))
        print("top tags:", tag_counts.most_common(5))
        print()

        if total >= 2 and scene_counts:
            scene, count = scene_counts.most_common(1)[0]
            if count / total > SCENE_THRESHOLD:
                warnings.append(f"{role}: scene '{scene}' appears in {ratio(count, total)}")
        if total >= 2 and tag_counts:
            tag, count = tag_counts.most_common(1)[0]
            if count / total > TAG_THRESHOLD:
                warnings.append(f"{role}: tag '{tag}' appears in {ratio(count, total)}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("No audit warnings.")

    return 1 if warnings else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    status = audit(args.dataset)
    if args.strict and status:
        raise SystemExit(status)


if __name__ == "__main__":
    main()
