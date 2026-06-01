#!/usr/bin/env python3
"""Route HL observations into conservative learning-action suggestions."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMPT_BLOCKED_ACTIONS = [
    "mutate_prompt_or_policy",
    "auto_mutate_prompt",
    "add_case_specific_if_rule",
    "continue_prompt_tuning_for_narrow_failures",
    "promote_to_gate",
]

COVERAGE_GAP_TAGS = {
    "coverage_gap",
    "dataset_gap",
    "missing_coverage",
    "missing_scene",
    "taxonomy_gap",
    "thin_coverage",
}

LOW_SEVERITY_TAGS = {
    "acceptable_variance",
    "judge_noise",
    "low_severity",
    "minor_failure",
    "narrow_failure",
}

FAILURE_PATTERN_EXCLUDED_TAGS = COVERAGE_GAP_TAGS | LOW_SEVERITY_TAGS | {
    "prompt_bloat_risk",
    "prompt_patch_pressure",
}

ROLE_SPECIFIC_FAILURE_TAGS = {
    "borrowed_imagery",
    "lore_drift",
    "perception_axis_collapse",
    "prop_stuffing",
    "role_axis_collapse",
    "role_specific_failure",
}


def load_observations(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path}: records must be a non-empty list")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"{path}: records[{index}] must be an object")
    return payload


def record_id(record: dict[str, Any], index: int) -> str:
    value = record.get("record_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"record_{index}"


def tags_for(record: dict[str, Any]) -> list[str]:
    raw_tags = record.get("failure_tags")
    if not isinstance(raw_tags, list):
        return []
    return [str(tag).strip() for tag in raw_tags if str(tag).strip()]


def metadata_for(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def learning_scope_for(record: dict[str, Any], failure_tag: str = "") -> str:
    metadata = metadata_for(record)
    raw_scope = str(
        metadata.get("learning_scope")
        or metadata.get("candidate_classification")
        or metadata.get("scope")
        or ""
    ).strip().lower()
    normalized = raw_scope.replace("-", "_")
    if normalized in {"role", "role_specific", "single_role"}:
        return "role_specific"
    if normalized in {"project", "project_specific", "profile_extension"}:
        return "project_specific"
    if normalized in {"generic", "generic_conversation", "conversation_core", "conversation_core_candidate"}:
        return "generic"
    if failure_tag in ROLE_SPECIFIC_FAILURE_TAGS:
        return "role_specific"
    return "generic"


def scope_key_for(record: dict[str, Any], learning_scope: str) -> str:
    metadata = metadata_for(record)
    if learning_scope == "role_specific":
        role = str(metadata.get("role") or metadata.get("role_id") or metadata.get("character") or "").strip()
        return f"role:{role}" if role else "role:unknown"
    if learning_scope == "project_specific":
        project = str(metadata.get("project") or metadata.get("project_id") or metadata.get("profile") or "").strip()
        return f"project:{project}" if project else "project:unknown"
    return "generic"


def judge_pass(record: dict[str, Any]) -> bool | None:
    judge = record.get("judge")
    if not isinstance(judge, dict):
        return None
    value = judge.get("pass")
    if value in {True, False}:
        return value
    return None


def pass_rate(records: list[dict[str, Any]]) -> float:
    judged = [judge_pass(record) for record in records if judge_pass(record) is not None]
    if not judged:
        return 0.0
    return round(sum(1 for value in judged if value is True) / len(judged), 3)


def failed_records(records: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    failures: list[tuple[int, dict[str, Any]]] = []
    for index, record in enumerate(records):
        if judge_pass(record) is False or tags_for(record):
            failures.append((index, record))
    return failures


def is_low_severity(record: dict[str, Any]) -> bool:
    tags = set(tags_for(record))
    metadata = metadata_for(record)
    severity = str(metadata.get("severity", "")).strip().lower()
    scope = str(metadata.get("scope", "")).strip().lower()
    if severity in {"low", "minor", "trivial"}:
        return True
    if scope in {"narrow", "single_case", "case_specific"}:
        return True
    return bool(tags & LOW_SEVERITY_TAGS)


def portable_ref(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)


def evidence_refs(path_text: str, records: list[tuple[int, dict[str, Any]]]) -> list[str]:
    return [f"{path_text}#{record_id(record, index)}" for index, record in records]


def build_failure_pattern_candidates(
    observation_ref: str, failures: list[tuple[int, dict[str, Any]]], min_repeat: int
) -> list[dict[str, Any]]:
    by_bucket: dict[tuple[str, str, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, record in failures:
        for tag in tags_for(record):
            if tag not in FAILURE_PATTERN_EXCLUDED_TAGS:
                learning_scope = learning_scope_for(record, tag)
                scope_key = scope_key_for(record, learning_scope)
                by_bucket[(tag, learning_scope, scope_key)].append((index, record))

    candidates: list[dict[str, Any]] = []
    for (tag, learning_scope, scope_key), tagged_records in sorted(by_bucket.items()):
        if len(tagged_records) < min_repeat:
            continue
        reason_scope = "generic" if learning_scope == "generic" else learning_scope.replace("_", "-")
        candidates.append(
            {
                "outcome": "failure_pattern_candidate",
                "failure_tag": tag,
                "learning_scope": learning_scope,
                "scope_key": scope_key,
                "record_count": len(tagged_records),
                "evidence_refs": evidence_refs(observation_ref, tagged_records),
                "reason": f"Repeated {reason_scope} failure tag should be compressed before prompt mutation.",
            }
        )
    return candidates


def build_dataset_candidates(
    observation_ref: str, failures: list[tuple[int, dict[str, Any]]]
) -> list[dict[str, Any]]:
    matched = [
        (index, record)
        for index, record in failures
        if set(tags_for(record)) & COVERAGE_GAP_TAGS
    ]
    if not matched:
        return []
    tag_counts = Counter(tag for _, record in matched for tag in tags_for(record) if tag in COVERAGE_GAP_TAGS)
    return [
        {
            "outcome": "create_dataset_candidate_unit",
            "failure_tags": sorted(tag_counts),
            "record_count": len(matched),
            "evidence_refs": evidence_refs(observation_ref, matched),
            "reason": "Coverage or taxonomy gaps should become small candidate units, not prompt rules.",
        }
    ]


def stop_tuning_candidate(
    observation_ref: str,
    records: list[dict[str, Any]],
    failures: list[tuple[int, dict[str, Any]]],
    actual_pass_rate: float,
    acceptable_pass_rate: float,
) -> dict[str, Any] | None:
    if actual_pass_rate < acceptable_pass_rate:
        return None
    if failures and not all(is_low_severity(record) for _, record in failures):
        return None
    return {
        "outcome": "stop_tuning",
        "record_count": len(records),
        "evidence_refs": evidence_refs(observation_ref, failures) if failures else [],
        "reason": "Run is inside the acceptable band and remaining failures are low severity or narrow.",
    }


def choose_primary(candidates: list[dict[str, Any]]) -> str:
    order = [
        "stop_tuning",
        "accept_variance",
        "failure_pattern_candidate",
        "create_dataset_candidate_unit",
        "needs_review",
    ]
    outcomes = [candidate.get("outcome") for candidate in candidates]
    for outcome in order:
        if outcome in outcomes:
            return outcome
    return "needs_review"


def build_route(
    observations: dict[str, Any],
    observation_path: Path,
    output_base_dir: Path,
    acceptable_pass_rate: float,
    min_repeat: int,
) -> dict[str, Any]:
    records = observations["records"]
    failures = failed_records(records)
    actual_pass_rate = pass_rate(records)
    observation_ref = portable_ref(observation_path, output_base_dir)
    candidates: list[dict[str, Any]] = []

    stop_candidate = stop_tuning_candidate(
        observation_ref, records, failures, actual_pass_rate, acceptable_pass_rate
    )
    if stop_candidate:
        candidates.append(stop_candidate)
    candidates.extend(build_failure_pattern_candidates(observation_ref, failures, min_repeat))
    candidates.extend(build_dataset_candidates(observation_ref, failures))
    if not candidates:
        candidates.append(
            {
                "outcome": "needs_review",
                "record_count": len(records),
                "evidence_refs": evidence_refs(observation_ref, failures),
                "reason": "No conservative automatic route matched.",
            }
        )

    primary = choose_primary(candidates)
    next_replay_targets = ["none:stop_tuning"] if primary == "stop_tuning" else [
        f"review:{primary}"
    ]
    route = {
        "version": "v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "observation_path": observation_ref,
        "run_id": observations.get("run_id"),
        "acceptable_pass_rate": acceptable_pass_rate,
        "pass_rate": actual_pass_rate,
        "record_count": len(records),
        "failure_count": len(failures),
        "primary_outcome": primary,
        "outcome_candidates": candidates,
        "prompt_mutation_allowed": False,
        "blocked_actions": PROMPT_BLOCKED_ACTIONS,
        "next_replay_targets": next_replay_targets,
        "notes": "Conservative routing only; use action-plan validation before durable changes.",
    }
    for key in ("profile", "adapter"):
        value = observations.get(key)
        if isinstance(value, str) and value.strip():
            route[key] = value.strip()
    return route


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--acceptable-pass-rate", type=float, default=0.85)
    parser.add_argument("--min-repeat", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        observations = load_observations(args.observations)
        route = build_route(
            observations,
            args.observations,
            args.output.parent,
            args.acceptable_pass_rate,
            args.min_repeat,
        )
    except (json.JSONDecodeError, ValueError) as error:
        print(error)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(route, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote observation route to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
