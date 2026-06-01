#!/usr/bin/env python3
"""Score an HL mutation from replay observations."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REWARD_WEIGHTS = {
    "user_facing_relevance": 0.2,
    "diagnostic_clarity": 0.25,
    "cross_project_generality": 0.15,
    "replay_stability": 0.2,
    "noise_reduction": 0.1,
    "compression_value": 0.1,
}


def load_observations(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path}: records must be a non-empty list")
    return payload


def clamp_score(value: float) -> int:
    return max(0, min(4, round(value)))


def judge_stats(records: list[dict[str, Any]]) -> tuple[float, float]:
    judged = [
        record.get("judge")
        for record in records
        if isinstance(record.get("judge"), dict) and record["judge"].get("score") is not None
    ]
    if not judged:
        return 0.0, 0.0
    scores = [float(judge.get("score") or 0) for judge in judged]
    pass_rate = sum(1 for judge in judged if judge.get("pass") is True) / len(judged)
    return sum(scores) / len(scores), pass_rate


def metadata_values(records: list[dict[str, Any]], key: str) -> set[str]:
    values = set()
    for record in records:
        metadata = record.get("metadata")
        if isinstance(metadata, dict) and metadata.get(key):
            values.add(str(metadata[key]))
    return values


def failure_tags(records: list[dict[str, Any]]) -> set[str]:
    tags = set()
    for record in records:
        raw_tags = record.get("failure_tags")
        if isinstance(raw_tags, list):
            tags.update(str(tag) for tag in raw_tags if tag)
    return tags


def risk_flags(records: list[dict[str, Any]]) -> list[str]:
    flags: set[str] = set()
    risky_tags = failure_tags(records)
    if {"stiff_response", "mechanical_tone", "unnatural_tone"} & risky_tags:
        flags.add("naturalness_low")
    if {"prompt_bloat_risk", "prompt_patch_pressure"} & risky_tags:
        flags.add("prompt_bloat_risk")
    if {"case_by_case_overfit", "overfit_risk"} & risky_tags:
        flags.add("overfit_risk")

    for record in records:
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            continue
        naturalness = str(metadata.get("naturalness", "")).strip().lower()
        if naturalness in {"low", "poor", "bad", "stiff", "mechanical"}:
            flags.add("naturalness_low")
        bloat_risk = str(metadata.get("prompt_bloat_risk", "")).strip().lower()
        if bloat_risk in {"high", "medium_high", "severe"}:
            flags.add("prompt_bloat_risk")
        regression_risk = str(metadata.get("regression_risk", "")).strip().lower()
        if regression_risk in {"high", "medium_high", "severe"}:
            flags.add("regression_risk_high")
    return sorted(flags)


def has_real_model_output(observations: dict[str, Any], records: list[dict[str, Any]]) -> bool:
    if observations.get("dry_run") is True:
        return False
    for record in records:
        if record.get("dry_run") is True:
            return False
        output = record.get("output")
        if not isinstance(output, str) or not output.strip() or output.strip() == "[DRY RUN]":
            return False
    return True


def has_real_judge_score(records: list[dict[str, Any]]) -> bool:
    for record in records:
        judge = record.get("judge")
        if not isinstance(judge, dict):
            return False
        score = judge.get("score")
        if not isinstance(score, (int, float)):
            return False
        if judge.get("pass") not in {True, False}:
            return False
    return True


def assessment_level(hard_gates: dict[str, bool]) -> str:
    if not hard_gates["has_real_model_output"]:
        return "dry_run"
    if not hard_gates["has_real_judge_score"]:
        return "unjudged_replay"
    return "judged_replay"


def score_records(records: list[dict[str, Any]], generality_key: str) -> dict[str, int]:
    avg_score, pass_rate = judge_stats(records)
    tags = failure_tags(records)
    dimensions = metadata_values(records, "generic_dimension")
    generality_values = metadata_values(records, generality_key)

    return {
        "user_facing_relevance": clamp_score(avg_score * 4 if avg_score else 1),
        "diagnostic_clarity": clamp_score(2 + min(len(tags), 2)),
        "cross_project_generality": clamp_score(1 + min(len(generality_values) - 1, 3)),
        "replay_stability": clamp_score(pass_rate * 4 if avg_score else 1),
        "noise_reduction": clamp_score(2 + min(len(tags), 2)),
        "compression_value": clamp_score(1 + min(len(dimensions), 3)),
    }


def weighted_total(scores: dict[str, int]) -> float:
    return round(sum(scores[key] * REWARD_WEIGHTS[key] for key in REWARD_WEIGHTS), 3)


def decide(total: float, hard_gates: dict[str, bool], level: str) -> str:
    if level != "judged_replay":
        return "not_assessed"
    if not hard_gates["has_replay"]:
        return "needs_revision"
    if not hard_gates.get("risk_signals_clear", True):
        return "needs_revision"
    if total >= 3.2 and hard_gates["has_source_trace"]:
        return "compress_candidate"
    if total >= 2.4:
        return "keep_experiment"
    if total >= 1.5:
        return "needs_revision"
    return "retire_or_noop"


def build_assessment(
    observations: dict[str, Any],
    observation_path: Path,
    mutation_id: str,
    generality_key: str,
) -> dict[str, Any]:
    records = observations["records"]
    scores = score_records(records, generality_key)
    risks = risk_flags(records)
    hard_gates = {
        "has_replay": len(records) > 0,
        "has_source_trace": all(record.get("record_id") for record in records),
        "has_judge_or_dry_run": all(isinstance(record.get("judge"), dict) for record in records),
        "has_real_model_output": has_real_model_output(observations, records),
        "has_real_judge_score": has_real_judge_score(records),
        "risk_signals_clear": not risks,
    }
    level = assessment_level(hard_gates)
    total = weighted_total(scores)
    return {
        "version": "v1",
        "mutation_id": mutation_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "observation_path": str(observation_path),
        "observation_run_id": observations.get("run_id"),
        "generality_key": generality_key,
        "scores": scores,
        "weights": REWARD_WEIGHTS,
        "weighted_total": total,
        "risk_flags": risks,
        "hard_gates": hard_gates,
        "assessment_level": level,
        "decision": decide(total, hard_gates, level),
        "notes": "Conservative automatic score; use human review before promotion.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mutation-id", default="hl_mutation")
    parser.add_argument(
        "--generality-key",
        default="role",
        help="Metadata key used for cross-project generality scoring. Defaults to role for conversation evals.",
    )
    args = parser.parse_args()

    try:
        observations = load_observations(args.observations)
        assessment = build_assessment(
            observations,
            args.observations,
            args.mutation_id,
            args.generality_key,
        )
    except (json.JSONDecodeError, ValueError) as error:
        print(error)
        raise SystemExit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(assessment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote reward assessment to {args.output}")


if __name__ == "__main__":
    main()
