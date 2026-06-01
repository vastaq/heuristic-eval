#!/usr/bin/env python3
"""Create or update a compact heuristic-learning state snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REWARD_WEIGHTS = {
    "user_facing_relevance": 0.2,
    "diagnostic_clarity": 0.2,
    "cross_project_generality": 0.15,
    "replay_stability": 0.15,
    "noise_reduction": 0.15,
    "compression_value": 0.15,
}

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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_unique(items: list[str], additions: list[str]) -> list[str]:
    for item in additions:
        if item not in items:
            items.append(item)
    return items


def default_state(active_loop: str) -> dict[str, Any]:
    return {
        "system_id": "heuristic_eval_dataset_system",
        "version": "v1",
        "updated_at": now_utc(),
        "active_loop": active_loop,
        "core_dimensions": [],
        "memory_layers": {
            "runs": "eval_datasets/runs/",
            "experiments": "eval_datasets/experiments/",
            "failure_patterns": "eval_datasets/evolution/failure_patterns/",
            "events": "eval_datasets/evolution/events.jsonl",
        },
        "known_failure_patterns": [],
        "open_gaps": [],
        "reward_weights": dict(DEFAULT_REWARD_WEIGHTS),
        "allowed_actions": [],
        "blocked_actions": [],
        "next_replay_targets": [],
        "evidence_refs": [],
        "last_primary_outcome": "needs_review",
        "acceptable_band": {},
        "prompt_or_policy_complexity": {},
    }


def load_state(path: Path, active_loop: str) -> dict[str, Any]:
    if not path.exists():
        return default_state(active_loop)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"state must be a JSON object: {path}")
    return payload


def string_set(items: list[Any]) -> set[str]:
    return {item for item in items if isinstance(item, str)}


def target_is_placeholder(target: str) -> bool:
    normalized = " ".join(target.strip().lower().replace("_", " ").split())
    if normalized in PLACEHOLDER_TARGETS:
        return True
    return normalized.startswith(("later:", "todo:", "tbd:"))


def require_next_replay_target(primary_outcome: str, next_replay_targets: list[str]) -> None:
    targets = [target.strip() for target in next_replay_targets if target.strip()]
    for target in targets:
        if target_is_placeholder(target):
            raise SystemExit(f"next replay target contains placeholder: {target}")
    if primary_outcome == "stop_tuning":
        if "none:stop_tuning" not in targets:
            raise SystemExit("stop_tuning requires --next-replay-target none:stop_tuning")
        return
    if primary_outcome not in {"needs_review", "legacy_import"} and not targets:
        raise SystemExit(f"primary outcome {primary_outcome} requires --next-replay-target")


def require_scope(primary_outcome: str, state: dict[str, Any], profile: str, adapter: str) -> None:
    if primary_outcome not in SCOPED_PRIMARY_OUTCOMES:
        return
    effective_profile = profile.strip() or str(state.get("profile", "")).strip()
    effective_adapter = adapter.strip() or str(state.get("adapter", "")).strip()
    if not effective_profile or not effective_adapter:
        raise SystemExit(f"primary outcome {primary_outcome} requires --profile and --adapter")


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


def profile_adapter_event_errors(state_path: Path, refs: list[str], profile: str, adapter: str) -> list[str]:
    event_refs = [ref for ref in refs if "events.jsonl#" in ref]
    if not event_refs:
        return ["profile_adapter_update requires profile_adapter_updated event_ref"]
    errors: list[str] = []
    for ref in event_refs:
        event_path = evidence_ref_path(state_path, ref)
        if not event_path.exists():
            errors.append(f"profile_adapter_update event_ref file does not exist: {ref}")
            continue
        status = profile_adapter_event_ref_status(state_path, ref, profile, adapter)
        if status == "missing":
            errors.append(f"profile_adapter_update event_ref not found: {ref}")
        elif status == "mismatch":
            errors.append(
                "profile_adapter_update event_ref does not match profile/adapter scope: "
                f"{ref}"
            )
    return errors


def profile_adapter_update_evidence_errors(
    primary_outcome: str,
    state_path: Path,
    state: dict[str, Any],
    profile: str,
    adapter: str,
    evidence_refs: list[str],
) -> list[str]:
    if primary_outcome != "profile_adapter_update":
        return []
    effective_profile = profile.strip() or str(state.get("profile", "")).strip()
    effective_adapter = adapter.strip() or str(state.get("adapter", "")).strip()
    refs = [
        ref
        for ref in [*state.get("evidence_refs", []), *evidence_refs]
        if isinstance(ref, str) and ref.strip()
    ]
    errors: list[str] = []
    if not any(f"profiles/{effective_profile}/" in ref for ref in refs):
        errors.append("profile_adapter_update requires evidence_refs for profile module")
    elif not has_existing_evidence_path(state_path, refs, f"profiles/{effective_profile}/"):
        errors.append("profile_adapter_update profile module evidence_ref does not exist")
    if not any(f"adapters/{effective_adapter}/" in ref for ref in refs):
        errors.append("profile_adapter_update requires evidence_refs for adapter module")
    elif not has_existing_evidence_path(state_path, refs, f"adapters/{effective_adapter}/"):
        errors.append("profile_adapter_update adapter module evidence_ref does not exist")
    if not any("validate_run_intake" in ref and "passed" in ref for ref in refs):
        errors.append("profile_adapter_update requires validate_run_intake evidence_ref")
    errors.extend(profile_adapter_event_errors(state_path, refs, effective_profile, effective_adapter))
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record one compressed learning outcome in state.")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--active-loop", required=True)
    parser.add_argument("--primary-outcome", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--profile", default="")
    parser.add_argument("--adapter", default="")
    parser.add_argument("--known-failure-pattern", action="append", default=[])
    parser.add_argument("--open-gap", action="append", default=[])
    parser.add_argument("--next-replay-target", action="append", default=[])
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--blocked-action", action="append", default=[])
    parser.add_argument("--allowed-action", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state = load_state(args.state, args.active_loop)
    state.setdefault("system_id", "heuristic_eval_dataset_system")
    state.setdefault("version", "v1")
    state.setdefault("core_dimensions", [])
    state.setdefault("memory_layers", default_state(args.active_loop)["memory_layers"])
    state.setdefault("reward_weights", dict(DEFAULT_REWARD_WEIGHTS))
    state.setdefault("acceptable_band", {})
    state.setdefault("prompt_or_policy_complexity", {})
    for key in (
        "known_failure_patterns",
        "open_gaps",
        "allowed_actions",
        "blocked_actions",
        "next_replay_targets",
        "evidence_refs",
    ):
        state.setdefault(key, [])
        if not isinstance(state[key], list):
            raise SystemExit(f"state.{key} must be a list")

    blocked_actions = string_set(state["blocked_actions"]) | set(args.blocked_action)
    allowed_actions = string_set(state["allowed_actions"]) | set(args.allowed_action)
    if args.primary_outcome in blocked_actions:
        raise SystemExit(f"primary outcome cannot also be blocked: {args.primary_outcome}")
    action_overlap = sorted(allowed_actions & blocked_actions)
    if action_overlap:
        raise SystemExit(f"allowed_actions and blocked_actions overlap: {', '.join(action_overlap)}")
    combined_next_replay_targets = list(state["next_replay_targets"])
    append_unique(combined_next_replay_targets, args.next_replay_target)
    require_next_replay_target(args.primary_outcome, combined_next_replay_targets)
    require_scope(args.primary_outcome, state, args.profile, args.adapter)
    evidence_errors = profile_adapter_update_evidence_errors(
        args.primary_outcome,
        args.state,
        state,
        args.profile,
        args.adapter,
        args.evidence_ref,
    )
    if evidence_errors:
        raise SystemExit("; ".join(evidence_errors))

    state["updated_at"] = now_utc()
    state["active_loop"] = args.active_loop
    state["last_primary_outcome"] = args.primary_outcome
    for key in ("run_id", "project", "profile", "adapter"):
        value = getattr(args, key.replace("-", "_"))
        if value.strip():
            state[key] = value.strip()
    append_unique(state["known_failure_patterns"], args.known_failure_pattern)
    append_unique(state["open_gaps"], args.open_gap)
    state["next_replay_targets"] = combined_next_replay_targets
    append_unique(state["evidence_refs"], args.evidence_ref)
    append_unique(state["blocked_actions"], args.blocked_action)
    append_unique(state["allowed_actions"], args.allowed_action)

    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"recorded learning outcome: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
