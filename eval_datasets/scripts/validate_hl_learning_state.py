#!/usr/bin/env python3
"""Validate heuristic eval learning state snapshots."""

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
    "last_primary_outcome",
    "acceptable_band",
    "prompt_or_policy_complexity",
)

REQUIRED_REWARD_WEIGHTS = (
    "user_facing_relevance",
    "diagnostic_clarity",
    "cross_project_generality",
    "replay_stability",
    "noise_reduction",
    "compression_value",
)

PLACEHOLDER_TARGETS = {
    "decide later",
    "fix later",
    "later",
    "later:review",
    "review later",
    "tbd",
    "todo",
    "unknown",
}

SCOPED_PRIMARY_OUTCOMES = {
    "create_dataset_candidate_unit",
    "profile_adapter_update",
}


def require(value: Any) -> bool:
    return value is not None and value != "" and value != []


def string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def target_is_placeholder(target: str) -> bool:
    normalized = " ".join(target.strip().lower().replace("_", " ").split())
    if normalized in PLACEHOLDER_TARGETS:
        return True
    return normalized.startswith(("later:", "todo:", "tbd:"))


def eval_dataset_root_for_state(state_path: Path) -> Path:
    resolved = state_path.resolve()
    for parent in resolved.parents:
        if parent.name == "eval_datasets":
            return parent
    return resolved.parent


def workspace_root_for_state(state_path: Path) -> Path:
    eval_root = eval_dataset_root_for_state(state_path)
    if eval_root.name == "eval_datasets":
        return eval_root.parent
    return eval_root


def evidence_ref_path(state_path: Path, ref: str) -> Path:
    raw_path = ref.split("#", 1)[0].strip()
    path = Path(raw_path)
    if path.is_absolute():
        return path
    if raw_path.startswith("eval_datasets/"):
        return workspace_root_for_state(state_path) / path
    if raw_path.startswith(("profiles/", "adapters/")):
        return eval_dataset_root_for_state(state_path) / path
    return state_path.resolve().parent / path


def has_existing_evidence_path(state_path: Path, refs: list[str], needle: str) -> bool:
    return any(evidence_ref_path(state_path, ref).exists() for ref in refs if needle in ref)


def event_id_from_ref(ref: str) -> str:
    if "#" not in ref:
        return ""
    return ref.split("#", 1)[1].strip()


def profile_adapter_event_ref_status(state_path: Path, ref: str, profile: str, adapter: str) -> str:
    event_id = event_id_from_ref(ref)
    if not event_id:
        return "missing"
    event_path = evidence_ref_path(state_path, ref)
    if not event_path.exists():
        return "missing"
    for line in event_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("event_id") != event_id:
            continue
        evidence = event.get("evidence")
        decision = event.get("decision")
        profile_ref = str(event.get("profile_ref", ""))
        adapter_ref = str(event.get("adapter_ref", ""))
        if (
            event.get("event_type") == "profile_adapter_updated"
            and isinstance(evidence, dict)
            and evidence.get("kind") == "module_ref"
            and isinstance(decision, dict)
            and decision.get("to") == "profile_adapter_update"
            and f"profiles/{profile}/" in profile_ref
            and f"adapters/{adapter}/" in adapter_ref
        ):
            return "ok"
        return "mismatch"
    return "missing"


def profile_adapter_event_errors(path: Path, refs: list[str], profile: str, adapter: str) -> list[str]:
    event_refs = [ref for ref in refs if "events.jsonl#" in ref]
    if not event_refs:
        return [f"{path}: profile_adapter_update requires profile_adapter_updated event_ref"]
    errors: list[str] = []
    for ref in event_refs:
        event_path = evidence_ref_path(path, ref)
        if not event_path.exists():
            errors.append(f"{path}: profile_adapter_update event_ref file does not exist: {ref}")
            continue
        status = profile_adapter_event_ref_status(path, ref, profile, adapter)
        if status == "missing":
            errors.append(f"{path}: profile_adapter_update event_ref not found: {ref}")
        elif status == "mismatch":
            errors.append(
                f"{path}: profile_adapter_update event_ref does not match profile/adapter scope: {ref}"
            )
    return errors


def profile_adapter_update_evidence_errors(payload: dict[str, Any], path: Path) -> list[str]:
    if payload.get("last_primary_outcome") != "profile_adapter_update":
        return []
    profile = str(payload.get("profile", "")).strip()
    adapter = str(payload.get("adapter", "")).strip()
    refs = string_items(payload.get("evidence_refs"))
    errors: list[str] = []
    if profile and not any(f"profiles/{profile}/" in ref for ref in refs):
        errors.append(f"{path}: profile_adapter_update requires evidence_refs for profile module")
    elif profile and not has_existing_evidence_path(path, refs, f"profiles/{profile}/"):
        errors.append(f"{path}: profile_adapter_update profile module evidence_ref does not exist")
    if adapter and not any(f"adapters/{adapter}/" in ref for ref in refs):
        errors.append(f"{path}: profile_adapter_update requires evidence_refs for adapter module")
    elif adapter and not has_existing_evidence_path(path, refs, f"adapters/{adapter}/"):
        errors.append(f"{path}: profile_adapter_update adapter module evidence_ref does not exist")
    if not any("validate_run_intake" in ref and "passed" in ref for ref in refs):
        errors.append(f"{path}: profile_adapter_update requires validate_run_intake evidence_ref")
    errors.extend(profile_adapter_event_errors(path, refs, profile, adapter))
    return errors


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

    for field in ("allowed_actions", "blocked_actions", "next_replay_targets", "open_gaps", "evidence_refs"):
        if field in payload and not isinstance(payload[field], list):
            errors.append(f"{path}: {field} must be a list")
    allowed_actions = payload.get("allowed_actions")
    blocked_actions = payload.get("blocked_actions")
    if isinstance(allowed_actions, list) and isinstance(blocked_actions, list):
        blocked_set = {action for action in blocked_actions if isinstance(action, str)}
        for action in sorted({action for action in allowed_actions if isinstance(action, str) and action in blocked_set}):
            errors.append(f"{path}: allowed_actions and blocked_actions overlap: {action}")
    for field in ("acceptable_band", "prompt_or_policy_complexity"):
        if field in payload and not isinstance(payload[field], dict):
            errors.append(f"{path}: {field} must be an object")
    last_primary_outcome = payload.get("last_primary_outcome")
    if "last_primary_outcome" in payload:
        if not isinstance(last_primary_outcome, str) or not require(last_primary_outcome):
            errors.append(f"{path}: last_primary_outcome must be a non-empty string")
        elif isinstance(payload.get("blocked_actions"), list) and last_primary_outcome in payload["blocked_actions"]:
            errors.append(f"{path}: last_primary_outcome repeats blocked action: {last_primary_outcome}")
        elif isinstance(payload.get("next_replay_targets"), list):
            next_replay_targets = string_items(payload.get("next_replay_targets"))
            for target in next_replay_targets:
                if target_is_placeholder(target):
                    errors.append(f"{path}: next_replay_targets contains placeholder target: {target}")
            if last_primary_outcome == "stop_tuning":
                if "none:stop_tuning" not in next_replay_targets:
                    errors.append(f"{path}: stop_tuning requires next_replay_targets to include none:stop_tuning")
            elif last_primary_outcome not in {"needs_review", "legacy_import"} and not next_replay_targets:
                errors.append(
                    f"{path}: next_replay_targets must include a target for "
                    f"last_primary_outcome {last_primary_outcome}"
                )
        if last_primary_outcome in SCOPED_PRIMARY_OUTCOMES and (
            not require(payload.get("profile")) or not require(payload.get("adapter"))
        ):
            errors.append(f"{path}: {last_primary_outcome} requires profile and adapter")
        errors.extend(profile_adapter_update_evidence_errors(payload, path))

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
