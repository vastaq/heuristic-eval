#!/usr/bin/env python3
"""Import promptfoo test YAML into a canonical seed JSON file."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from yaml_bridge import parse_yaml


INPUT_KEYS = ("question", "user_input", "input", "message")


def input_key(vars_block: dict[str, Any]) -> str:
    for key in INPUT_KEYS:
        if isinstance(vars_block.get(key), str):
            return key
    return "question"


def first_input(vars_block: dict[str, Any]) -> str:
    for key in ("question", "user_input", "input", "message"):
        value = vars_block.get(key)
        if isinstance(value, str):
            return value
    return ""


def target_behavior(assertions: list[dict[str, Any]]) -> list[str]:
    for assertion in assertions:
        if assertion.get("type") == "llm-rubric" and assertion.get("value"):
            return [str(assertion["value"])]
    return ["Imported legacy test; review target behavior before accepting."]


def records_from_promptfoo(source_path: Path, role: str) -> list[dict[str, Any]]:
    parsed = parse_yaml(source_path.read_text(encoding="utf-8"))
    if parsed is None:
        return []
    if not isinstance(parsed, list):
        raise ValueError("Expected promptfoo tests YAML to be a list.")

    records: list[dict[str, Any]] = []
    conversation_turns: dict[str, int] = {}
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        vars_block = item.get("vars") or {}
        metadata = item.get("metadata") or {}
        assertions = item.get("assert") or []
        if not isinstance(assertions, list):
            assertions = []

        record_role = metadata.get("role") or role
        record_id = metadata.get("id") or f"{record_role}_legacy_{index + 1:03d}"
        selected_input_key = input_key(vars_block)
        conversation_id = metadata.get("conversationId") or metadata.get("conversation_id")
        record = {
            "id": record_id,
            "layer": metadata.get("layer", "core_smoke"),
            "role": record_role,
            "character_context": vars_block.get("character_context", ""),
            "scene_type": metadata.get("scene_type", "legacy_import"),
            "difficulty": metadata.get("difficulty", "medium"),
            "input": first_input(vars_block),
            "input_var": selected_input_key,
            "vars": vars_block,
            "target_behavior": target_behavior(assertions),
            "avoid_behavior": [
                "Imported legacy test; review avoid behavior before accepting."
            ],
            "tags": metadata.get("tags", []),
            "rubric_ref": metadata.get("rubric_ref", "legacy_import"),
            "source_path": str(source_path),
            "source_index": index,
            "source_id": metadata.get("id", ""),
            "source": "legacy_import",
            "review_status": "candidate",
            "revision": 1,
            "legacy_asserts": assertions,
        }
        if conversation_id:
            record["conversation_id"] = conversation_id
        if metadata.get("turn"):
            record["turn"] = metadata["turn"]
        elif conversation_id:
            conversation_turns[conversation_id] = conversation_turns.get(conversation_id, 0) + 1
            record["turn"] = conversation_turns[conversation_id]
        records.append(record)
    return records


def import_tests(source_path: Path, output_path: Path, project: str, role: str) -> int:
    records = records_from_promptfoo(source_path, role)

    payload = {
        "version": "v1",
        "project": project,
        "dataset_type": "character_prompt_eval_seed",
        "source_paths": [str(source_path)],
        "updated_at": date.today().isoformat(),
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(records)} tests to {output_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--role", required=True)
    args = parser.parse_args()
    raise SystemExit(import_tests(args.source, args.output, args.project, args.role))


if __name__ == "__main__":
    main()
