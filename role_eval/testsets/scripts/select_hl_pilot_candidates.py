#!/usr/bin/env python3
"""Select a small traceable review batch for role-eval HL pilots."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_STATUSES = ["candidate"]
CORE_SCENE_TYPES = {
    "low_energy_no_advice",
    "ordinary_frustration",
    "small_joy_shared",
    "one_small_step",
    "direct_choice",
    "message_reply",
    "brief_identity",
    "not_professional",
    "no_prompt_or_system_talk",
    "emotion_to_practical",
    "constraint_respected",
    "no_restart",
    "anti_action_markers",
    "plain_language",
    "anti_generic_comfort",
    "safe_refusal_soft_redirect",
}
TRACE_FIELDS = [
    "id",
    "description",
    "layer",
    "role",
    "character_context",
    "scene_type",
    "difficulty",
    "input",
    "input_var",
    "vars",
    "target_behavior",
    "avoid_behavior",
    "tags",
    "rubric_ref",
    "source_path",
    "source_index",
    "source_id",
    "source",
    "review_status",
    "conversation_id",
    "turn",
    "expected_length",
    "risk_level",
    "revision",
    "updated_at",
    "notes",
    "legacy_asserts",
]


def record_score(record: dict[str, Any]) -> int:
    score = 0
    if record.get("target_behavior"):
        score += 2
    if record.get("avoid_behavior"):
        score += 2
    if record.get("conversation_id"):
        score += 2
    if record.get("scene_type") in CORE_SCENE_TYPES:
        score += 2
    if record.get("legacy_asserts"):
        score += 1
    if record.get("source_path"):
        score += 1
    return score


def selected_fields(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record[field] for field in TRACE_FIELDS if field in record}


def select_records(
    records: list[dict[str, Any]],
    roles: list[str],
    statuses: list[str],
    layers: list[str],
    scene_types: list[str],
    max_records: int,
) -> list[dict[str, Any]]:
    role_set = set(roles)
    status_set = set(statuses)
    layer_set = set(layers)
    scene_set = set(scene_types)
    role_order = {role: index for index, role in enumerate(roles)}

    filtered = []
    for record in records:
        if role_set and record.get("role") not in role_set:
            continue
        if status_set and record.get("review_status", "candidate") not in status_set:
            continue
        if layer_set and record.get("layer") not in layer_set:
            continue
        if scene_set and record.get("scene_type") not in scene_set:
            continue
        filtered.append(record)

    filtered.sort(
        key=lambda record: (
            -record_score(record),
            role_order.get(str(record.get("role", "")), len(role_order)),
            str(record.get("id", "")),
        )
    )
    if not roles:
        return [selected_fields(record) for record in filtered[:max_records]]

    by_role = {role: [] for role in roles}
    for record in filtered:
        role = record.get("role")
        if role in by_role:
            by_role[role].append(record)

    balanced: list[dict[str, Any]] = []
    while len(balanced) < max_records:
        added = False
        for role in roles:
            if by_role[role]:
                balanced.append(by_role[role].pop(0))
                added = True
                if len(balanced) == max_records:
                    break
        if not added:
            break
    return [selected_fields(record) for record in balanced]


def build_payload(
    dataset_path: Path,
    records: list[dict[str, Any]],
    roles: list[str],
    statuses: list[str],
    layers: list[str],
    scene_types: list[str],
    max_records: int,
) -> dict[str, Any]:
    return {
        "generated_at": date.today().isoformat(),
        "source_dataset": str(dataset_path),
        "selection": {
            "roles": roles,
            "statuses": statuses,
            "layers": layers,
            "scene_types": scene_types,
            "max_records": max_records,
            "strategy": "score by traceability, core scene relevance, and multi-turn signal",
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--role", action="append", dest="roles", default=[])
    parser.add_argument("--include-status", action="append", dest="statuses")
    parser.add_argument("--layer", action="append", dest="layers", default=[])
    parser.add_argument("--scene-type", action="append", dest="scene_types", default=[])
    parser.add_argument("--max-records", type=int, default=20)
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    records = select_records(
        dataset.get("records", []),
        args.roles,
        args.statuses or DEFAULT_STATUSES,
        args.layers,
        args.scene_types,
        args.max_records,
    )
    payload = build_payload(
        args.dataset,
        records,
        args.roles,
        args.statuses or DEFAULT_STATUSES,
        args.layers,
        args.scene_types,
        args.max_records,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
