#!/usr/bin/env python3
"""Audit whether a dataset is safe to use as prompt-tuning pressure."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yaml_bridge import parse_yaml


SHAPE_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "action_step": [
        re.compile(pattern, re.I)
        for pattern in [
            r"\b(give|offer|suggest|provide|include|choose|pick|name|answer) (at most )?(one|a|an)\b",
            r"\b(one|a) (tiny|small|safe|simple|concrete|practical|calm|next) (step|action|activity|thing|way|cue|count)\b",
            r"\bnext (action|step)\b",
            r"\bconcrete (step|action|activity|suggestion|way)\b",
            r"\bright away\b",
            r"\bbreath(s|ing)?\b",
            r"\bpractical\b",
            r"\bactivity\b",
        ]
    ],
    "exact_shape": [
        re.compile(pattern, re.I)
        for pattern in [
            r"\bexact(ly)?\b",
            r"\bone (line|sentence|phrase|word|thing|count)\b",
            r"\bshort\b",
            r"\bno extra\b",
            r"\bavoid extra\b",
            r"\banswer directly\b",
            r"\bfollow-up question(s)?\b",
            r"\blist(s|ing)?\b",
        ]
    ],
    "presence": [
        re.compile(pattern, re.I)
        for pattern in [
            r"\bpresence\b",
            r"\bvalidate|validation|acknowledge|notice\b",
            r"\bfeeling|sad|sadness|angry|anger|mad|disappointment\b",
            r"\brespect\b",
            r"\bcompanionship|stay with|sit with|quiet\b",
            r"\bshame|safe|gentle|warm\b",
            r"\bnot want|does not want|don't want\b",
        ]
    ],
    "identity_boundary": [
        re.compile(pattern, re.I)
        for pattern in [
            r"\bidentity|doctor|teacher|ai|assistant|product\b",
            r"\bwho are you\b",
            r"\bboundar(y|ies)\b",
        ]
    ],
    "anti_action": [
        re.compile(pattern, re.I)
        for pattern in [
            r"\bno (advice|action|fix|fixing|technique|practice)\b",
            r"\bwithout (adding|a|any) (new )?(calming|practical|action|fix|technique)\b",
            r"\bdo not (add|offer|suggest|push|require)\b",
            r"\bavoid (adding|pushing|extra advice|extra)\b",
            r"\bat most one\b",
            r"\bquiet companionship can pass\b",
            r"\beven without a concrete action\b",
        ]
    ],
}

WARN_THRESHOLDS = {
    "dominant_shape": 0.65,
    "action_step": 0.55,
    "exact_shape": 0.35,
    "presence_min": 0.25,
    "anti_action_min": 0.15,
}


def load_dataset(path: Path) -> tuple[list[dict[str, Any]], str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("records"), list):
            return parsed["records"], "canonical_json"
        if isinstance(parsed, list):
            return parsed, "json_list"
        raise ValueError(f"Unsupported JSON dataset shape in {path}")

    parsed = parse_yaml(text)
    if isinstance(parsed, list):
        return parsed, "promptfoo_yaml"
    if isinstance(parsed, dict) and isinstance(parsed.get("tests"), list):
        return parsed["tests"], "promptfoo_yaml"
    raise ValueError(f"Unsupported YAML dataset shape in {path}")


def record_id(record: dict[str, Any], index: int) -> str:
    metadata = record.get("metadata")
    if isinstance(metadata, dict) and metadata.get("id"):
        return str(metadata["id"])
    if record.get("id"):
        return str(record["id"])
    return f"record_{index:03d}"


def collect_text(record: dict[str, Any]) -> str:
    parts: list[str] = []

    for key in ("input", "target_behavior", "avoid_behavior", "rubric", "rubric_ref"):
        value = record.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)

    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        for key in ("scene_type", "eval_bucket", "expected_length"):
            if metadata.get(key):
                parts.append(str(metadata[key]))
        tags = metadata.get("tags")
        if isinstance(tags, list):
            parts.extend(str(tag) for tag in tags)

    tags = record.get("tags")
    if isinstance(tags, list):
        parts.extend(str(tag) for tag in tags)

    assertions = record.get("assert", record.get("assertions", []))
    if isinstance(assertions, list):
        for assertion in assertions:
            if isinstance(assertion, dict):
                value = assertion.get("value")
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, dict):
                    parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))

    return "\n".join(parts)


def classify(text: str) -> list[str]:
    shapes = []
    for shape, patterns in SHAPE_PATTERNS.items():
        if any(pattern.search(text) for pattern in patterns):
            shapes.append(shape)
    return shapes or ["unclassified"]


def ratio(count: int, total: int) -> float:
    return count / total if total else 0.0


def audit(path: Path) -> dict[str, Any]:
    records, dataset_type = load_dataset(path)
    shape_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    row_outputs: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        text = collect_text(record)
        shapes = classify(text)
        shape_counts.update(shapes)

        metadata = record.get("metadata")
        if isinstance(metadata, dict) and metadata.get("eval_bucket"):
            bucket_counts[str(metadata["eval_bucket"])] += 1

        row_outputs.append(
            {
                "id": record_id(record, index),
                "shapes": shapes,
                "rubric_excerpt": " ".join(text.split())[:240],
            }
        )

    total = len(row_outputs)
    warnings: list[dict[str, Any]] = []
    classified_counts = {shape: shape_counts.get(shape, 0) for shape in SHAPE_PATTERNS}

    if total:
        top_shape, top_count = shape_counts.most_common(1)[0]
        action_count = shape_counts.get("action_step", 0)
        presence_count = shape_counts.get("presence", 0)
        anti_count = shape_counts.get("anti_action", 0)
        has_counterpressure = (
            ratio(presence_count, total) >= WARN_THRESHOLDS["presence_min"]
            and ratio(anti_count, total) >= WARN_THRESHOLDS["anti_action_min"]
        )
        if top_shape != "unclassified" and ratio(top_count, total) > WARN_THRESHOLDS["dominant_shape"]:
            severity = "medium" if has_counterpressure else "high"
            warnings.append(
                {
                    "code": "dominant_shape",
                    "message": f"{top_shape} appears in {top_count}/{total} records.",
                    "severity": severity,
                }
            )

        if ratio(action_count, total) > WARN_THRESHOLDS["action_step"]:
            severity = "medium" if has_counterpressure else "high"
            warnings.append(
                {
                    "code": "action_step_pressure",
                    "message": f"Action-step language appears in {action_count}/{total} records.",
                    "severity": severity,
                }
            )

        exact_count = shape_counts.get("exact_shape", 0)
        if ratio(exact_count, total) > WARN_THRESHOLDS["exact_shape"]:
            warnings.append(
                {
                    "code": "exact_shape_pressure",
                    "message": f"Exact-response-shape language appears in {exact_count}/{total} records.",
                    "severity": "medium",
                }
            )

        if ratio(presence_count, total) < WARN_THRESHOLDS["presence_min"]:
            warnings.append(
                {
                    "code": "presence_coverage_gap",
                    "message": f"Presence/restraint language appears in only {presence_count}/{total} records.",
                    "severity": "medium",
                }
            )

        if ratio(anti_count, total) < WARN_THRESHOLDS["anti_action_min"]:
            warnings.append(
                {
                    "code": "anti_action_coverage_gap",
                    "message": f"Anti-action counterpressure appears in only {anti_count}/{total} records.",
                    "severity": "high",
                }
            )

    if any(warning["severity"] == "high" for warning in warnings):
        next_action = "revise_or_supplement_eval_first"
    elif warnings:
        next_action = "inspect_before_prompt_tuning"
    else:
        next_action = "prompt_tuning_allowed_with_bloat_gate"

    return {
        "version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(path),
        "dataset_type": dataset_type,
        "total_records": total,
        "shape_counts": dict(sorted(classified_counts.items())),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "thresholds": WARN_THRESHOLDS,
        "warnings": warnings,
        "recommended_next_action": next_action,
        "records": row_outputs,
    }


def write_markdown(audit_result: dict[str, Any], path: Path) -> None:
    total = audit_result["total_records"]
    lines = [
        "# Dataset Traction Audit",
        "",
        f"Dataset: `{audit_result['dataset_path']}`",
        f"Total records: `{total}`",
        f"Recommended next action: `{audit_result['recommended_next_action']}`",
        "",
        "## Shape Counts",
        "",
        "| Shape | Count | Share |",
        "| --- | ---: | ---: |",
    ]
    for shape, count in audit_result["shape_counts"].items():
        share = f"{ratio(int(count), total):.0%}" if total else "0%"
        lines.append(f"| `{shape}` | {count} | {share} |")

    if audit_result["bucket_counts"]:
        lines.extend(["", "## Eval Buckets", "", "| Bucket | Count |", "| --- | ---: |"])
        for bucket, count in audit_result["bucket_counts"].items():
            lines.append(f"| `{bucket}` | {count} |")

    lines.extend(["", "## Warnings", ""])
    if audit_result["warnings"]:
        for warning in audit_result["warnings"]:
            lines.append(
                f"- `{warning['severity']}` `{warning['code']}`: {warning['message']}"
            )
    else:
        lines.append("No traction warnings.")

    lines.extend(
        [
            "",
            "## Use",
            "",
            "Use this audit before prompt tuning. If the audit recommends eval revision,",
            "treat prompt pass rate as a biased signal until the dataset has countercases",
            "for the role behaviors it wants to preserve.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    result = audit(args.dataset)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if args.markdown:
        write_markdown(result, args.markdown)


if __name__ == "__main__":
    main()
