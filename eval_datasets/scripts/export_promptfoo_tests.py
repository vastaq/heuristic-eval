#!/usr/bin/env python3
"""Export canonical role testsets to promptfoo YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from yaml_bridge import dump_yaml


DEFAULT_STATUSES = {"accepted"}


def build_default_rubric(record: dict[str, Any]) -> str:
    target = "\n".join(f"- {item}" for item in record.get("target_behavior", []))
    avoid = "\n".join(f"- {item}" for item in record.get("avoid_behavior", []))
    return (
        "The output should satisfy these target behaviors:\n"
        f"{target or '- Respond naturally and preserve the target role.'}\n\n"
        "Fail or lower confidence if it shows these avoid behaviors:\n"
        f"{avoid or '- Ignore the user or lose the target role.'}"
    )


def record_to_promptfoo(record: dict[str, Any]) -> dict[str, Any]:
    vars_block: dict[str, Any] = dict(record.get("vars") or {})
    input_var = record.get("input_var") or "question"
    vars_block[input_var] = record["input"]
    if record.get("character_context"):
        vars_block["character_context"] = record["character_context"]

    metadata_keys = [
        "id",
        "layer",
        "role",
        "scene_type",
        "difficulty",
        "source_path",
        "source_id",
        "source_index",
        "review_status",
        "risk_level",
        "expected_length",
        "tags",
    ]
    metadata = {key: record[key] for key in metadata_keys if key in record}
    if "conversation_id" in record:
        metadata["conversationId"] = record["conversation_id"]
    if "turn" in record:
        metadata["turn"] = record["turn"]

    assertions = record.get("legacy_asserts")
    if not assertions:
        assertions = [{"type": "llm-rubric", "value": build_default_rubric(record)}]

    test = {
        "vars": vars_block,
        "metadata": metadata,
        "assert": assertions,
    }
    if record.get("description"):
        test["description"] = record["description"]
    return test


def export_dataset(dataset_path: Path, output_path: Path, statuses: set[str]) -> int:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    records = [
        record
        for record in dataset.get("records", [])
        if record.get("review_status", "candidate") in statuses
    ]
    tests = [record_to_promptfoo(record) for record in records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_yaml(tests), encoding="utf-8")
    print(f"Exported {len(tests)} tests to {output_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--include-status",
        action="append",
        dest="statuses",
        help="Review status to include. Defaults to accepted. Repeatable.",
    )
    args = parser.parse_args()
    statuses = set(args.statuses or DEFAULT_STATUSES)
    raise SystemExit(export_dataset(args.dataset, args.output, statuses))


if __name__ == "__main__":
    main()
