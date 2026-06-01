#!/usr/bin/env python3
"""Validate minimal heuristic-learning action guards for a run decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_evolution_events import validate_event_log
from validate_hl_learning_state import validate_state


PROMPT_MUTATION_MARKERS = (
    "prompt",
    "policy",
    "instruction",
    "system message",
    "system_prompt",
    "策略",
    "提示词",
    "系统提示",
    "指令",
)

MUTATION_VERBS = (
    "add",
    "change",
    "edit",
    "mutate",
    "patch",
    "revise",
    "rewrite",
    "tune",
    "update",
    "补",
    "加",
    "改",
    "调整",
    "添加",
    "改写",
    "修改",
    "优化",
    "重写",
)

PROMPT_MUTATION_DECISIONS = {
    "compact_prompt_candidate",
    "controlled_prompt_experiment",
    "prompt_mutation",
    "prompt_tuning",
    "revise_prompt_boundary",
    "revise_prompt_or_policy",
}

MUTATION_GUARD_PHRASES = (
    "before any prompt mutation",
    "before prompt mutation",
    "block prompt mutation",
    "blocked prompt mutation",
    "not a prompt",
    "stop tuning",
    "不是 prompt",
    "不改 prompt",
    "不修改 prompt",
    "不要修改 prompt",
    "先不改 prompt",
    "先不要修改 prompt",
    "停止调 prompt",
)

LOCAL_RULE_PATTERNS = (
    "case-specific rule",
    "case_specific_rule",
    "case specific rule",
    "failed case",
    "for case ",
    "if rule",
    "if/when",
    "narrow rule",
    "one-off rule",
    "一条规则",
    "单条规则",
    "局部规则",
    "失败用例",
    "针对用例",
)

UNSAFE_PROMPT_SHORTCUTS = {
    "add_case_specific_if_rule",
    "auto_mutate_prompt",
    "continue_prompt_tuning_for_narrow_failures",
    "mutate_prompt_from_legacy_import_only",
    "prompt_patch_without_replay",
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

COMPRESSION_OUTCOMES = {
    "accept_direction",
    "accept_variance",
    "blocked_prompt_mutation",
    "case_revision",
    "create_candidate_cases",
    "downgrade_metric_to_diagnostic",
    "failure_pattern_candidate",
    "judge_noise",
    "revise_rubric",
    "revise_variable_injection",
    "rubric_revision",
    "revise_or_supplement_eval_first",
    "stop_tuning",
    "inspect_before_prompt_tuning",
}

EVAL_REVISION_DECISIONS = {
    "revise_or_supplement_eval_first",
}

INSPECTION_DECISIONS = {
    "inspect_before_prompt_tuning",
}

DATASET_GENERATION_DECISIONS = {
    "create_dataset_candidate_unit",
    "dataset_generation",
    "generate_dataset_candidate",
}
PROMPT_SUPPORTING_REWARD_DECISIONS = {
    "compress_candidate",
    "keep_experiment",
}

PROMPT_MUTATION_SIGNAL_OUTCOMES = PROMPT_MUTATION_DECISIONS | {
    "controlled_prompt_experiment",
}


def load_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing {label}: {path.name}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def load_human_signals(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append("missing human_signals.jsonl")
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"human_signals.jsonl line {line_number} is not valid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"human_signals.jsonl line {line_number} must be a JSON object")
            continue
        records.append(value)
    return records


def list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def text_suggests_prompt_mutation(text: str) -> bool:
    lowered = text.lower().replace("-", "_")
    if any(phrase in lowered for phrase in MUTATION_GUARD_PHRASES):
        return False
    if any(phrase in lowered for phrase in LOCAL_RULE_PATTERNS):
        return any(verb in lowered for verb in MUTATION_VERBS)
    has_marker = any(marker in lowered for marker in PROMPT_MUTATION_MARKERS)
    has_mutation_verb = any(verb in lowered for verb in MUTATION_VERBS)
    return has_marker and has_mutation_verb


def decision_suggests_prompt_mutation(decision: dict[str, Any]) -> bool:
    decision_type = decision.get("decision_type")
    if isinstance(decision_type, str) and decision_type in PROMPT_MUTATION_DECISIONS:
        return True
    text_parts: list[str] = []
    text_parts.extend(list_strings(decision.get("next_actions")))
    text_parts.extend(list_strings(decision.get("allowed_actions")))
    return any(text_suggests_prompt_mutation(part) for part in text_parts)


def validate_signal_refs(decision: dict[str, Any], signal_count: int, errors: list[str]) -> None:
    refs = decision.get("human_signal_refs")
    if not isinstance(refs, list):
        errors.append("human_signal_refs must be a list")
        return
    for ref in refs:
        if not isinstance(ref, str) or not ref.startswith("human_signals.jsonl#"):
            errors.append(f"human_signal_refs contains invalid ref: {ref}")
            continue
        line = ref.rsplit("#", 1)[-1]
        if not line.isdigit() or not (1 <= int(line) <= signal_count):
            errors.append(f"human_signal_refs points outside human_signals.jsonl: {ref}")


def referenced_signal_records(decision: dict[str, Any], signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ref in decision.get("human_signal_refs", []):
        if not isinstance(ref, str) or not ref.startswith("human_signals.jsonl#"):
            continue
        line = ref.rsplit("#", 1)[-1]
        if not line.isdigit():
            continue
        line_number = int(line)
        if 1 <= line_number <= len(signals):
            records.append(signals[line_number - 1])
    return records


def human_signal_supports_decision(signal: dict[str, Any], decision_type: str) -> bool:
    outcome = signal.get("suggested_outcome")
    if not isinstance(outcome, str) or not outcome.strip():
        return False
    if decision_type in PROMPT_MUTATION_DECISIONS:
        return outcome in PROMPT_MUTATION_SIGNAL_OUTCOMES
    if decision_type == "accept_direction":
        return outcome in {"accept_direction", "accepted_direction"}
    return outcome == decision_type


def validate_allowed_blocked_action_conflicts(decision: dict[str, Any], errors: list[str]) -> None:
    allowed_actions = set(list_strings(decision.get("allowed_actions")))
    blocked_actions = set(list_strings(decision.get("blocked_actions")))
    overlap = sorted(action for action in allowed_actions & blocked_actions if action.strip())
    if overlap:
        errors.append(f"allowed_actions and blocked_actions overlap: {', '.join(overlap)}")


def validate_manifest_decision_consistency(
    manifest: dict[str, Any], decision: dict[str, Any], errors: list[str]
) -> None:
    for key in ("run_id", "profile", "adapter"):
        if manifest.get(key) != decision.get(key):
            errors.append(f"manifest.{key} and decision.{key} must match")


def validate_human_signal_records(signals: list[dict[str, Any]], errors: list[str]) -> None:
    for index, signal in enumerate(signals, start=1):
        for key in ("signal_type", "raw_signal", "suggested_outcome"):
            value = signal.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"human_signals[{index}].{key} must be a non-empty string")
        for key in ("candidate_failure_tags", "blocked_actions"):
            if key in signal and not isinstance(signal[key], list):
                errors.append(f"human_signals[{index}].{key} must be a list")
        if "needs_review" in signal and not isinstance(signal["needs_review"], bool):
            errors.append(f"human_signals[{index}].needs_review must be a boolean")
        source_type = signal.get("source_type")
        if source_type is not None and not isinstance(source_type, str):
            errors.append(f"human_signals[{index}].source_type must be a string")
        if signal.get("needs_review") is False:
            if not isinstance(source_type, str) or not source_type.strip():
                errors.append(f"human_signals[{index}].source_type is required when needs_review=false")
            elif source_type == "agent_inference":
                errors.append(
                    f"human_signals[{index}].source_type cannot be agent_inference when needs_review=false"
                )


def validate_reviewed_blocking_signals_carried(
    decision: dict[str, Any], signals: list[dict[str, Any]], errors: list[str]
) -> None:
    decision_blocked_actions = set(list_strings(decision.get("blocked_actions")))
    for signal in signals:
        if signal.get("needs_review") is not False:
            continue
        for action in list_strings(signal.get("blocked_actions")):
            stripped_action = action.strip()
            if stripped_action and stripped_action not in decision_blocked_actions:
                errors.append(
                    "decision.blocked_actions must include reviewed human signal blocked_action: "
                    f"{stripped_action}"
                )


def validate_signal_supports_decision(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    expected_decision_type: str,
) -> None:
    records = referenced_signal_records(decision, signals)
    supporting_records = [
        record for record in records if human_signal_supports_decision(record, expected_decision_type)
    ]
    if records and not supporting_records:
        errors.append(f"human_signal_refs does not support decision_type {expected_decision_type}")
    elif supporting_records and not any(record.get("needs_review") is False for record in supporting_records):
        errors.append(
            f"human_signal_refs contains unreviewed support for decision_type {expected_decision_type}"
        )


def has_valid_signal_refs(
    decision: dict[str, Any], signals: list[dict[str, Any]], errors: list[str], prefix: str
) -> bool:
    refs = decision.get("human_signal_refs")
    if not isinstance(refs, list) or not refs:
        errors.append(f"{prefix} requires human_signal_refs")
        return False
    before = len(errors)
    validate_signal_refs(decision, len(signals), errors)
    return len(errors) == before


def validate_prompt_mutation_controls(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    base_dir: Path,
    context: dict[str, Any] | None = None,
) -> None:
    if has_valid_signal_refs(decision, signals, errors, "prompt mutation"):
        decision_type = decision.get("decision_type")
        expected_decision_type = decision_type if isinstance(decision_type, str) else "prompt_mutation"
        validate_signal_supports_decision(decision, signals, errors, expected_decision_type)

    gate = decision.get("prompt_bloat_gate")
    if not isinstance(gate, dict) or gate.get("checked") is not True:
        errors.append("prompt mutation requires prompt_bloat_gate.checked=true")
        gate = {}
    else:
        validate_traction_audit_gate(gate, errors, base_dir)

    replay_targets = list_strings(decision.get("replay_targets"))
    if not replay_targets or all(target.strip().lower().startswith("none") for target in replay_targets):
        errors.append("prompt mutation requires replay_targets")

    blocked_actions = set(list_strings(decision.get("blocked_actions")))
    if blocked_actions.isdisjoint(UNSAFE_PROMPT_SHORTCUTS):
        errors.append("prompt mutation requires blocked unsafe prompt shortcuts")
    validate_learning_state_carryover_if_ref_present(
        decision,
        errors,
        base_dir,
        target_fields=("replay_targets",),
        context=context,
    )


def resolve_ref(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def validate_traction_audit_gate(gate: dict[str, Any], errors: list[str], base_dir: Path) -> None:
    if not non_empty_string(gate.get("repeated_failure_basis")):
        errors.append("prompt_bloat_gate requires repeated_failure_basis")

    if not list_strings(gate.get("non_prompt_alternatives_considered")):
        errors.append("prompt_bloat_gate requires non_prompt_alternatives_considered")

    ordinary_risk = gate.get("ordinary_interaction_risk")
    if not non_empty_string(ordinary_risk):
        errors.append("prompt_bloat_gate requires ordinary_interaction_risk")
    elif ordinary_risk.strip().lower() in {"high", "severe"}:
        errors.append("prompt_bloat_gate ordinary_interaction_risk must not be high")

    if not non_empty_string(gate.get("removal_condition")):
        errors.append("prompt_bloat_gate requires removal_condition")

    audit_ref = gate.get("traction_audit_ref")
    not_needed_reason = gate.get("traction_audit_not_needed_reason")
    if isinstance(audit_ref, str) and audit_ref.strip():
        audit_path = resolve_ref(audit_ref.strip(), base_dir)
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"traction audit ref is not readable: {audit_ref}: {exc}")
            return
        except json.JSONDecodeError as exc:
            errors.append(f"traction audit ref is not valid JSON: {audit_ref}: {exc}")
            return
        if not isinstance(audit, dict):
            errors.append(f"traction audit ref must point to a JSON object: {audit_ref}")
            return
        recommended_next_action = audit.get("recommended_next_action")
        if recommended_next_action == "revise_or_supplement_eval_first":
            errors.append("traction audit recommends revising eval before prompt mutation")
        if recommended_next_action == "inspect_before_prompt_tuning":
            errors.append("traction audit requires inspect_before_prompt_tuning before prompt mutation")
        return

    if not isinstance(not_needed_reason, str) or not not_needed_reason.strip():
        errors.append("prompt mutation requires traction_audit_ref or traction_audit_not_needed_reason")


def validate_traction_audit_decision_ref(
    decision: dict[str, Any],
    errors: list[str],
    base_dir: Path,
    expected_next_action: str,
) -> None:
    audit_ref = decision.get("traction_audit_ref")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        errors.append(f"{expected_next_action} requires traction_audit_ref")
        return
    audit_path = resolve_ref(audit_ref.strip(), base_dir)
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"traction audit ref is not readable: {audit_ref}: {exc}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"traction audit ref is not valid JSON: {audit_ref}: {exc}")
        return
    if not isinstance(audit, dict):
        errors.append(f"traction audit ref must point to a JSON object: {audit_ref}")
        return
    if audit.get("recommended_next_action") != expected_next_action:
        errors.append(
            "traction audit recommended_next_action does not support "
            f"{expected_next_action}"
        )


def target_is_placeholder(target: str) -> bool:
    normalized = " ".join(target.strip().lower().replace("_", " ").split())
    if normalized in PLACEHOLDER_TARGETS:
        return True
    return normalized.startswith(("later:", "todo:", "tbd:"))


def validate_target_specificity(
    decision_type: str,
    field: str,
    targets: list[str],
    errors: list[str],
) -> None:
    for target in targets:
        if target_is_placeholder(target):
            errors.append(f"{decision_type} {field} contains placeholder target: {target}")


def validate_inspection_controls(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    base_dir: Path,
    context: dict[str, Any] | None = None,
) -> None:
    decision_type = decision.get("decision_type")
    if not isinstance(decision_type, str):
        return

    if has_valid_signal_refs(decision, signals, errors, decision_type):
        validate_signal_supports_decision(decision, signals, errors, decision_type)

    validate_traction_audit_decision_ref(decision, errors, base_dir, decision_type)

    next_review_targets = list_strings(decision.get("next_review_targets"))
    replay_targets = list_strings(decision.get("replay_targets"))
    if not next_review_targets and not replay_targets:
        errors.append(f"{decision_type} requires next_review_targets or replay_targets")
    validate_target_specificity(decision_type, "next_review_targets", next_review_targets, errors)
    validate_target_specificity(decision_type, "replay_targets", replay_targets, errors)
    validate_learning_state_carryover_if_ref_present(
        decision,
        errors,
        base_dir,
        target_fields=("next_review_targets", "replay_targets"),
        context=context,
    )

    blocked_actions = set(list_strings(decision.get("blocked_actions")))
    if blocked_actions.isdisjoint(UNSAFE_PROMPT_SHORTCUTS):
        errors.append(f"{decision_type} requires blocked unsafe prompt shortcuts")


def validate_eval_revision_controls(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    base_dir: Path,
    context: dict[str, Any] | None = None,
) -> None:
    decision_type = decision.get("decision_type")
    if not isinstance(decision_type, str):
        return

    if has_valid_signal_refs(decision, signals, errors, decision_type):
        validate_signal_supports_decision(decision, signals, errors, decision_type)

    validate_traction_audit_decision_ref(decision, errors, base_dir, decision_type)

    eval_revision_targets = list_strings(decision.get("eval_revision_targets"))
    replay_targets = list_strings(decision.get("replay_targets"))
    if not eval_revision_targets and not replay_targets:
        errors.append(f"{decision_type} requires eval_revision_targets or replay_targets")
    validate_target_specificity(decision_type, "eval_revision_targets", eval_revision_targets, errors)
    validate_target_specificity(decision_type, "replay_targets", replay_targets, errors)
    validate_learning_state_carryover_if_ref_present(
        decision,
        errors,
        base_dir,
        target_fields=("eval_revision_targets", "replay_targets"),
        context=context,
    )

    blocked_actions = set(list_strings(decision.get("blocked_actions")))
    if blocked_actions.isdisjoint(UNSAFE_PROMPT_SHORTCUTS):
        errors.append(f"{decision_type} requires blocked unsafe prompt shortcuts")


def validate_compression_controls(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    base_dir: Path,
    context: dict[str, Any] | None = None,
) -> None:
    state_ref = decision.get("learning_state_ref")
    if not isinstance(state_ref, str) or not state_ref.strip():
        errors.append("compression decision requires learning_state_ref")
        return

    decision_type = decision.get("decision_type")
    if has_valid_signal_refs(decision, signals, errors, "compression decision"):
        expected_decision_type = decision_type if isinstance(decision_type, str) else "compression"
        validate_signal_supports_decision(decision, signals, errors, expected_decision_type)

    state_path = resolve_ref(state_ref.strip(), base_dir)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"learning state ref is not readable: {state_ref}: {exc}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"learning state ref is not valid JSON: {state_ref}: {exc}")
        return
    if not isinstance(state, dict):
        errors.append(f"learning state ref must point to a JSON object: {state_ref}")
        return
    for error in validate_state(state, state_path):
        errors.append(f"learning state invalid: {error}")
    validate_learning_state_context(state, context, errors)

    last_outcome = state.get("last_primary_outcome")
    if isinstance(decision_type, str) and isinstance(last_outcome, str) and last_outcome != decision_type:
        errors.append(
            f"learning state last_primary_outcome does not match decision_type: {last_outcome} != {decision_type}"
        )
    state_blocked_actions = set(list_strings(state.get("blocked_actions")))
    decision_blocked_actions = set(list_strings(decision.get("blocked_actions")))
    missing_blocked_actions = sorted(decision_blocked_actions - state_blocked_actions)
    if missing_blocked_actions:
        errors.append(
            "learning state missing decision blocked_actions: "
            f"{', '.join(missing_blocked_actions)}"
        )

    if decision.get("decision_type") == "failure_pattern_candidate":
        pattern_refs = list_strings(decision.get("failure_pattern_refs"))
        deferred_reason = decision.get("failure_pattern_deferred_reason")
        if not pattern_refs and (not isinstance(deferred_reason, str) or not deferred_reason.strip()):
            errors.append(
                "failure_pattern_candidate requires failure_pattern_refs or failure_pattern_deferred_reason"
            )

    decision_type_for_event = decision_type if isinstance(decision_type, str) else None
    validate_event_refs(
        decision,
        errors,
        base_dir,
        decision_type_for_event,
        require_decision_context=True,
    )


def validate_learning_state_carryover(
    decision: dict[str, Any],
    state: dict[str, Any],
    errors: list[str],
    target_fields: tuple[str, ...],
) -> None:
    state_blocked_actions = set(list_strings(state.get("blocked_actions")))
    decision_blocked_actions = set(list_strings(decision.get("blocked_actions")))
    missing_blocked_actions = sorted(state_blocked_actions - decision_blocked_actions)
    if missing_blocked_actions:
        errors.append(
            "decision.blocked_actions must include learning_state.blocked_actions: "
            f"{', '.join(missing_blocked_actions)}"
        )

    state_targets = {
        target
        for target in list_strings(state.get("next_replay_targets"))
        if target.strip() and target.strip() != "none:stop_tuning"
    }
    if not state_targets or not target_fields:
        return

    decision_targets: set[str] = set()
    for field in target_fields:
        decision_targets.update(list_strings(decision.get(field)))
    missing_targets = sorted(state_targets - decision_targets)
    if missing_targets:
        if len(target_fields) == 1:
            field_label = target_fields[0]
        else:
            field_label = "/".join(target_fields)
        errors.append(
            f"decision.{field_label} must include learning_state.next_replay_targets: "
            f"{', '.join(missing_targets)}"
        )


def validate_learning_state_context(
    state: dict[str, Any],
    context: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if context is None:
        return
    for field in ("project", "profile", "adapter", "run_id"):
        state_value = state.get(field)
        context_value = context.get(field)
        if (
            isinstance(state_value, str)
            and state_value.strip()
            and isinstance(context_value, str)
            and context_value.strip()
            and state_value.strip() != context_value.strip()
        ):
            errors.append(f"learning_state_ref {field} does not match manifest.{field}")


def validate_learning_state_carryover_if_ref_present(
    decision: dict[str, Any],
    errors: list[str],
    base_dir: Path,
    target_fields: tuple[str, ...],
    context: dict[str, Any] | None = None,
) -> None:
    state_ref = decision.get("learning_state_ref")
    if not isinstance(state_ref, str) or not state_ref.strip():
        return
    state_path = resolve_ref(state_ref.strip(), base_dir)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"learning state ref is not readable: {state_ref}: {exc}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"learning state ref is not valid JSON: {state_ref}: {exc}")
        return
    if not isinstance(state, dict):
        errors.append(f"learning state ref must point to a JSON object: {state_ref}")
        return
    for error in validate_state(state, state_path):
        errors.append(f"learning state invalid: {error}")
    validate_learning_state_context(state, context, errors)
    validate_learning_state_carryover(decision, state, errors, target_fields)


def validate_optional_learning_state_ref(
    decision: dict[str, Any],
    errors: list[str],
    action_label: str,
    base_dir: Path,
    target_fields: tuple[str, ...] = (),
    context: dict[str, Any] | None = None,
) -> None:
    state_ref = decision.get("learning_state_ref")
    state_not_needed_reason = decision.get("learning_state_not_needed_reason")
    if not isinstance(state_ref, str) or not state_ref.strip():
        if not isinstance(state_not_needed_reason, str) or not state_not_needed_reason.strip():
            errors.append(f"{action_label} requires learning_state_ref or learning_state_not_needed_reason")
        return

    state_path = resolve_ref(state_ref.strip(), base_dir)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"learning state ref is not readable: {state_ref}: {exc}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"learning state ref is not valid JSON: {state_ref}: {exc}")
        return
    if not isinstance(state, dict):
        errors.append(f"learning state ref must point to a JSON object: {state_ref}")
        return
    for error in validate_state(state, state_path):
        errors.append(f"learning state invalid: {error}")
    validate_learning_state_context(state, context, errors)
    validate_learning_state_carryover(decision, state, errors, target_fields)


def dataset_generation_requested(decision: dict[str, Any]) -> bool:
    decision_type = decision.get("decision_type")
    if isinstance(decision_type, str) and decision_type in DATASET_GENERATION_DECISIONS:
        return True
    dataset_generation = decision.get("dataset_generation")
    return isinstance(dataset_generation, dict) and dataset_generation.get("needed") is True


def validate_dataset_generation_controls(
    decision: dict[str, Any],
    signals: list[dict[str, Any]],
    errors: list[str],
    base_dir: Path,
    context: dict[str, Any] | None = None,
) -> None:
    decision_type = decision.get("decision_type")
    expected_decision_type = (
        decision_type
        if isinstance(decision_type, str) and decision_type in DATASET_GENERATION_DECISIONS
        else "create_dataset_candidate_unit"
    )
    if has_valid_signal_refs(decision, signals, errors, "dataset candidate generation"):
        validate_signal_supports_decision(decision, signals, errors, expected_decision_type)

    replay_targets = list_strings(decision.get("replay_targets"))
    if not replay_targets or all(target.strip().lower().startswith("none") for target in replay_targets):
        errors.append("dataset candidate generation requires replay_targets")

    validate_optional_learning_state_ref(
        decision,
        errors,
        "dataset candidate generation",
        base_dir,
        target_fields=("replay_targets",),
        context=context,
    )


def route_observation_path_for_decision(decision: dict[str, Any], base_dir: Path) -> tuple[str, Path] | None:
    route_ref = decision.get("observation_route_ref")
    if not isinstance(route_ref, str) or not route_ref.strip():
        return None
    route_path = resolve_ref(route_ref.strip(), base_dir)
    try:
        route = json.loads(route_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(route, dict):
        return None
    observation_ref = route.get("observation_path")
    if not isinstance(observation_ref, str) or not observation_ref.strip():
        return None
    observation_ref_text = observation_ref.strip()
    return observation_ref_text, resolve_ref(observation_ref_text, route_path.parent)


def validate_reward_assessment_refs(
    decision: dict[str, Any],
    errors: list[str],
    base_dir: Path,
    route_observation_path: tuple[str, Path] | None = None,
) -> None:
    refs = decision.get("reward_assessment_refs")
    if refs is None:
        return
    if not isinstance(refs, list):
        errors.append("reward_assessment_refs must be a list")
        return
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"reward_assessment_refs contains invalid ref: {ref}")
            continue
        reward_path = resolve_ref(ref.strip(), base_dir)
        try:
            reward = json.loads(reward_path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"reward_assessment_refs ref is not readable: {ref}: {exc}")
            continue
        except json.JSONDecodeError as exc:
            errors.append(f"reward_assessment_refs ref is not valid JSON: {ref}: {exc}")
            continue
        if not isinstance(reward, dict):
            errors.append(f"reward_assessment_refs ref must point to a JSON object: {ref}")
            continue

        decision_run_id = decision.get("run_id")
        reward_run_id = reward.get("observation_run_id")
        if isinstance(decision_run_id, str) and decision_run_id.strip():
            if not isinstance(reward_run_id, str) or not reward_run_id.strip():
                errors.append(
                    f"reward_assessment_refs missing observation_run_id for decision.run_id: {ref}"
                )
            elif decision_run_id.strip() != reward_run_id.strip():
                errors.append(f"reward_assessment_refs observation_run_id does not match decision.run_id: {ref}")
        reward_observation_path = reward.get("observation_path")
        if route_observation_path is not None and isinstance(reward_observation_path, str) and reward_observation_path.strip():
            route_observation_ref, route_observation_resolved = route_observation_path
            reward_observation_ref = reward_observation_path.strip()
            reward_observation_resolved = resolve_ref(reward_observation_ref, reward_path.parent)
            if (
                reward_observation_ref != route_observation_ref
                and reward_observation_resolved != route_observation_resolved
            ):
                errors.append(
                    "reward_assessment_refs observation_path does not match "
                    f"observation_route_ref observation_path: {ref}"
                )

        if reward.get("decision") == "not_assessed":
            errors.append(f"reward_assessment_refs points to not_assessed reward: {ref}")
        if reward.get("assessment_level") != "judged_replay":
            errors.append(f"reward_assessment_refs requires judged_replay: {ref}")

        hard_gates = reward.get("hard_gates")
        if not isinstance(hard_gates, dict):
            errors.append(f"reward_assessment_refs missing hard_gates: {ref}")
            continue
        for gate in ("has_real_model_output", "has_real_judge_score"):
            if hard_gates.get(gate) is not True:
                errors.append(f"reward_assessment_refs requires {gate}=true: {ref}")
        reward_decision = reward.get("decision")
        if (
            decision_suggests_prompt_mutation(decision)
            and reward_decision not in PROMPT_SUPPORTING_REWARD_DECISIONS
        ):
            errors.append(f"reward_assessment_refs decision does not support prompt mutation: {ref}")


def record_ids_from_observation(observation: dict[str, Any]) -> set[str]:
    records = observation.get("records")
    if not isinstance(records, list):
        return set()
    record_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        record_id = record.get("record_id")
        if isinstance(record_id, str) and record_id.strip():
            record_ids.add(record_id.strip())
    return record_ids


def observation_records_missing_stable_ids(observation: dict[str, Any]) -> bool:
    records = observation.get("records")
    if not isinstance(records, list) or not records:
        return False
    for record in records:
        if not isinstance(record, dict):
            continue
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            return True
    return False


def validate_route_candidate_evidence_refs(
    route: dict[str, Any],
    observation_ref: str,
    observation: dict[str, Any] | None,
    errors: list[str],
) -> None:
    candidates = route.get("outcome_candidates")
    if not isinstance(candidates, list):
        errors.append("observation_route_ref outcome_candidates must be a list")
        return

    known_record_ids = record_ids_from_observation(observation) if observation is not None else set()
    missing_stable_ids = (
        observation_records_missing_stable_ids(observation) if observation is not None else False
    )
    reported_missing_stable_ids = False
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            errors.append(f"observation_route_ref outcome_candidates[{index}] must be an object")
            continue
        outcome = candidate.get("outcome")
        evidence_refs = list_strings(candidate.get("evidence_refs"))
        if outcome != "stop_tuning" and not evidence_refs:
            errors.append(f"observation_route_ref outcome_candidates[{index}] requires evidence_refs")
        if evidence_refs and missing_stable_ids and not reported_missing_stable_ids:
            errors.append(
                "observation_route_ref observation_path records require stable record_id for evidence_refs"
            )
            reported_missing_stable_ids = True
        for evidence_ref in evidence_refs:
            if "#" not in evidence_ref:
                errors.append(f"observation_route_ref evidence_ref is invalid: {evidence_ref}")
                continue
            path_text, record_id = evidence_ref.rsplit("#", 1)
            if path_text != observation_ref:
                errors.append(f"observation_route_ref evidence_ref path does not match observation_path: {evidence_ref}")
            if not record_id:
                errors.append(f"observation_route_ref evidence_ref is invalid: {evidence_ref}")
            elif known_record_ids and record_id not in known_record_ids:
                errors.append(f"observation_route_ref evidence_ref points to missing record: {evidence_ref}")


def validate_context_field_match(
    actual: dict[str, Any],
    expected: dict[str, Any],
    field: str,
    actual_label: str,
    expected_label: str,
    errors: list[str],
) -> None:
    actual_value = actual.get(field)
    expected_value = expected.get(field)
    if (
        not (isinstance(actual_value, str) and actual_value.strip())
        and isinstance(expected_value, str)
        and expected_value.strip()
    ):
        errors.append(f"{actual_label} requires {field} when {expected_label}.{field} is set")
        return
    if (
        isinstance(actual_value, str)
        and actual_value.strip()
        and isinstance(expected_value, str)
        and expected_value.strip()
        and actual_value.strip() != expected_value.strip()
    ):
        errors.append(f"{actual_label} {field} does not match {expected_label}.{field}")


def validate_observation_route_ref(decision: dict[str, Any], errors: list[str], base_dir: Path) -> None:
    route_ref = decision.get("observation_route_ref")
    if route_ref is None:
        return
    if not isinstance(route_ref, str) or not route_ref.strip():
        errors.append("observation_route_ref must be a non-empty string")
        return

    route_path = resolve_ref(route_ref.strip(), base_dir)
    try:
        route = json.loads(route_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"observation_route_ref is not readable: {route_ref}: {exc}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"observation_route_ref is not valid JSON: {route_ref}: {exc}")
        return
    if not isinstance(route, dict):
        errors.append(f"observation_route_ref must point to a JSON object: {route_ref}")
        return

    observation_ref = route.get("observation_path")
    observation: dict[str, Any] | None = None
    if not isinstance(observation_ref, str) or not observation_ref.strip():
        errors.append("observation_route_ref requires observation_path")
    else:
        observation_path = resolve_ref(observation_ref.strip(), route_path.parent)
        try:
            loaded_observation = json.loads(observation_path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"observation_route_ref observation_path is not readable: {observation_ref}: {exc}")
        except json.JSONDecodeError as exc:
            errors.append(f"observation_route_ref observation_path is not valid JSON: {observation_ref}: {exc}")
        else:
            if not isinstance(loaded_observation, dict):
                errors.append(f"observation_route_ref observation_path must point to a JSON object: {observation_ref}")
            else:
                observation = loaded_observation
    observation_ref_text = observation_ref.strip() if isinstance(observation_ref, str) else ""
    if observation_ref_text:
        validate_route_candidate_evidence_refs(route, observation_ref_text, observation, errors)

    decision_run_id = decision.get("run_id")
    route_run_id = route.get("run_id")
    if (
        isinstance(decision_run_id, str)
        and decision_run_id.strip()
        and isinstance(route_run_id, str)
        and route_run_id.strip()
        and decision_run_id != route_run_id
    ):
        errors.append("observation_route_ref run_id does not match decision.run_id")
    for field in ("profile", "adapter"):
        validate_context_field_match(route, decision, field, "observation_route_ref", "decision", errors)
    if observation is not None:
        observation_run_id = observation.get("run_id")
        if (
            isinstance(route_run_id, str)
            and route_run_id.strip()
            and isinstance(observation_run_id, str)
            and observation_run_id.strip()
            and observation_run_id != route_run_id
        ):
            errors.append("observation_route_ref observation_path run_id does not match route.run_id")
        for field in ("profile", "adapter"):
            validate_context_field_match(
                observation,
                decision,
                field,
                "observation_route_ref observation_path",
                "decision",
                errors,
            )
            validate_context_field_match(
                observation,
                route,
                field,
                "observation_route_ref observation_path",
                "route",
                errors,
            )

    route_blocked_actions = set(list_strings(route.get("blocked_actions")))
    decision_blocked_actions = set(list_strings(decision.get("blocked_actions")))
    for action in sorted(route_blocked_actions - decision_blocked_actions):
        errors.append(f"decision.blocked_actions must include observation route blocked_action: {action}")

    route_outcomes = set()
    primary_outcome = route.get("primary_outcome")
    if isinstance(primary_outcome, str) and primary_outcome.strip():
        route_outcomes.add(primary_outcome.strip())
    candidates = route.get("outcome_candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            outcome = candidate.get("outcome")
            if isinstance(outcome, str) and outcome.strip():
                route_outcomes.add(outcome.strip())

    decision_type = decision.get("decision_type")
    if isinstance(decision_type, str) and decision_type.strip():
        if route_outcomes and decision_type not in route_outcomes and decision_type != "needs_decision":
            errors.append(f"observation_route_ref does not support decision_type {decision_type}")

    if decision_suggests_prompt_mutation(decision) and route.get("prompt_mutation_allowed") is not True:
        errors.append("observation_route_ref blocks prompt mutation")


def validate_existing_route_not_ignored(decision: dict[str, Any], errors: list[str], base_dir: Path) -> None:
    route_ref = decision.get("observation_route_ref")
    if isinstance(route_ref, str) and route_ref.strip():
        return
    if not (base_dir / "route.json").is_file():
        return
    if decision_suggests_prompt_mutation(decision):
        errors.append("prompt mutation requires observation_route_ref when route.json exists")
    if dataset_generation_requested(decision):
        errors.append("dataset candidate generation requires observation_route_ref when route.json exists")


def event_supports_decision(event: dict[str, Any], expected_decision_type: str) -> bool:
    event_decision = event.get("decision")
    if not isinstance(event_decision, dict):
        return False
    expected_values = {expected_decision_type}
    if expected_decision_type == "accept_direction":
        expected_values.add("accepted_direction")
    return any(event_decision.get(key) in expected_values for key in ("to", "outcome", "decision_type"))


def event_context_errors(
    event: dict[str, Any],
    decision: dict[str, Any],
    ref: str,
    require_decision_context: bool = False,
) -> list[str]:
    errors: list[str] = []
    event_decision = event.get("decision")
    expected_run_id = decision.get("run_id")
    if isinstance(expected_run_id, str) and expected_run_id.strip():
        event_run_ids = []
        if isinstance(event.get("run_id"), str):
            event_run_ids.append(event["run_id"])
        if isinstance(event_decision, dict) and isinstance(event_decision.get("run_id"), str):
            event_run_ids.append(event_decision["run_id"])

        for run_id in event_run_ids:
            if run_id.strip() and run_id.strip() != expected_run_id:
                errors.append(f"event_refs run_id does not match decision.run_id: {ref}")
                break
        if require_decision_context and not event_run_ids:
            errors.append(f"event_refs missing run_id for decision context: {ref}")

    expected_decision_id = decision.get("decision_id")
    event_decision_ids = []
    if isinstance(event.get("decision_id"), str):
        event_decision_ids.append(event["decision_id"])
    if isinstance(event_decision, dict) and isinstance(event_decision.get("decision_id"), str):
        event_decision_ids.append(event_decision["decision_id"])
    if isinstance(expected_decision_id, str) and expected_decision_id.strip():
        if require_decision_context and not event_decision_ids:
            errors.append(f"event_refs missing decision_id for decision context: {ref}")
        for decision_id in event_decision_ids:
            if decision_id.strip() and decision_id.strip() != expected_decision_id:
                errors.append(f"event_refs decision_id does not match decision.decision_id: {ref}")
                break

    expected_signal_refs = set(list_strings(decision.get("human_signal_refs")))
    event_signal_ref_lists = []
    if isinstance(event.get("human_signal_refs"), list):
        event_signal_ref_lists.append(set(list_strings(event["human_signal_refs"])))
    if isinstance(event_decision, dict) and isinstance(event_decision.get("human_signal_refs"), list):
        event_signal_ref_lists.append(set(list_strings(event_decision["human_signal_refs"])))
    if require_decision_context and expected_signal_refs and not event_signal_ref_lists:
        errors.append(f"event_refs missing human_signal_refs for decision context: {ref}")
    for signal_refs in event_signal_ref_lists:
        if signal_refs != expected_signal_refs:
            errors.append(f"event_refs human_signal_refs do not match decision.human_signal_refs: {ref}")
            break
    return errors


def validate_event_refs(
    decision: dict[str, Any],
    errors: list[str],
    base_dir: Path,
    expected_decision_type: str | None = None,
    require_decision_context: bool = False,
) -> None:
    refs = decision.get("event_refs")
    if not isinstance(refs, list) or not refs:
        errors.append("compression decision requires event_refs")
        return

    for ref in refs:
        if not isinstance(ref, str) or "#" not in ref:
            errors.append(f"event_refs contains invalid ref: {ref}")
            continue
        path_text, event_id = ref.rsplit("#", 1)
        if not path_text or not event_id:
            errors.append(f"event_refs contains invalid ref: {ref}")
            continue
        event_path = resolve_ref(path_text, base_dir)
        event_errors = validate_event_log(event_path, check_paths=False)
        for error in event_errors:
            errors.append(f"event ref invalid: {error}")
        if event_errors:
            continue
        matched_event = None
        for line in event_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if isinstance(event, dict) and event.get("event_id") == event_id:
                matched_event = event
                break
        if matched_event is None:
            errors.append(f"event_refs points to missing event_id: {ref}")
        elif expected_decision_type and not event_supports_decision(matched_event, expected_decision_type):
            errors.append(f"event_refs does not support decision_type {expected_decision_type}: {ref}")
        elif matched_event is not None:
            errors.extend(
                event_context_errors(
                    matched_event,
                    decision,
                    ref,
                    require_decision_context=require_decision_context,
                )
            )


def validate_acceptance_controls(
    decision: dict[str, Any], signals: list[dict[str, Any]], errors: list[str], base_dir: Path
) -> None:
    decision_type = decision.get("decision_type")
    expected_decision_type = decision_type if isinstance(decision_type, str) else "accept_direction"
    if has_valid_signal_refs(decision, signals, errors, "accepted direction"):
        validate_signal_supports_decision(decision, signals, errors, expected_decision_type)
    refs = decision.get("event_refs")
    if not isinstance(refs, list) or not refs:
        errors.append("accepted direction requires event_refs")
    else:
        validate_event_refs(
            decision,
            errors,
            base_dir,
            expected_decision_type,
            require_decision_context=True,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that prompt/policy mutation decisions have the minimal HL guardrails."
    )
    parser.add_argument("run_dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []
    run_dir = args.run_dir
    if not run_dir.exists() or not run_dir.is_dir():
        errors.append(f"run directory does not exist: {run_dir}")
    manifest = load_json(run_dir / "manifest.json", errors, "manifest")
    decision = load_json(run_dir / "decision.json", errors, "decision")
    human_signals = load_human_signals(run_dir / "human_signals.jsonl", errors)

    if manifest and decision:
        validate_manifest_decision_consistency(manifest, decision, errors)
    validate_human_signal_records(human_signals, errors)
    if decision:
        validate_allowed_blocked_action_conflicts(decision, errors)
        validate_reviewed_blocking_signals_carried(decision, human_signals, errors)
        validate_reward_assessment_refs(
            decision,
            errors,
            run_dir,
            route_observation_path=route_observation_path_for_decision(decision, run_dir),
        )
        validate_observation_route_ref(decision, errors, run_dir)
        validate_existing_route_not_ignored(decision, errors, run_dir)
    context = manifest if manifest else None
    if decision and decision_suggests_prompt_mutation(decision):
        validate_prompt_mutation_controls(decision, human_signals, errors, run_dir, context)
    if decision and dataset_generation_requested(decision):
        validate_dataset_generation_controls(decision, human_signals, errors, run_dir, context)
    if decision.get("decision_type") in EVAL_REVISION_DECISIONS:
        validate_eval_revision_controls(decision, human_signals, errors, run_dir, context)
    if decision.get("decision_type") in INSPECTION_DECISIONS:
        validate_inspection_controls(decision, human_signals, errors, run_dir, context)
    if decision.get("decision_type") in COMPRESSION_OUTCOMES:
        validate_compression_controls(decision, human_signals, errors, run_dir, context)
    if decision.get("accepted_direction") is True:
        validate_acceptance_controls(decision, human_signals, errors, run_dir)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"learning action plan valid: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
