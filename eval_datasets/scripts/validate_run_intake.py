#!/usr/bin/env python3
"""Validate the structural integrity of a run-intake directory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROMPTFOO_SPECIFIC_TERMS = (
    "promptfoo",
    "normalize_promptfoo_results.py",
    "import_promptfoo_tests.py",
    "batch_import_test_yaml.py",
)
PROMPTFOO_SCHEMA_FIELDS = (
    "vars",
    "input_var",
    "legacy_asserts",
    "assert",
)
CONVERSATION_ROLE_SPECIFIC_TERMS = (
    "character_context",
    "target_behavior",
    "avoid_behavior",
    "role_eval",
)
CONVERSATION_ROLE_SCHEMA_FIELDS = (
    "role",
    "scene_type",
)
SCAFFOLD_PLACEHOLDER_PHRASES = (
    "Define what this eval domain is trying to keep",
    "State what belongs in this profile",
    "Describe the smallest record, run, or observation shape",
    "List project-local metadata here",
    "Name the buckets that prevent the eval",
    "Describe the external files, result format, and runner assumptions",
    "State which fields can be trusted",
    "State whether this adapter exports runnable evaluator files",
    "Define how pass/fail, scores, reasons, outputs, and case identifiers become",
)


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


def load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
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


def require_string(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    value = mapping.get(key)
    if not isinstance(value, str):
        errors.append(f"{label}.{key} must be a string")
    elif "path/to" in value:
        errors.append(f"{label}.{key} contains placeholder path: {value}")


def require_list(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    if not isinstance(mapping.get(key), list):
        errors.append(f"{label}.{key} must be a list")


def resolve_ref(path_text: str) -> Path:
    return Path(path_text).expanduser()


def path_contains_module_readme(path: Path, module_dir: str, module_id: str) -> bool:
    parts = path.parts
    expected = (module_dir, module_id, "README.md")
    for index in range(0, len(parts) - len(expected) + 1):
        if parts[index : index + len(expected)] == expected:
            return True
    return False


def eval_datasets_root_for_module(path: Path, module_dir: str, module_id: str) -> Path | None:
    resolved = path.expanduser().resolve()
    parts = resolved.parts
    expected = ("eval_datasets", module_dir, module_id, "README.md")
    for index in range(0, len(parts) - len(expected) + 1):
        if parts[index : index + len(expected)] == expected:
            return Path(*parts[: index + 1])
    return None


def has_markdown_heading(text: str, heading: str) -> bool:
    expected = heading.strip().lower()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip().lower()
        if title == expected:
            return True
    return False


def markdown_section_has_body(text: str, heading: str) -> bool:
    expected = heading.strip().lower()
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            if in_section:
                return False
            if title == expected:
                in_section = True
            continue
        if in_section and stripped:
            return True
    return False


def markdown_section_text(text: str, heading: str) -> str:
    expected = heading.strip().lower()
    in_section = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            if in_section:
                break
            if title == expected:
                in_section = True
            continue
        if in_section:
            lines.append(line)
    return "\n".join(lines)


def contains_markdown_token(text: str, token: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])"
    return re.search(pattern, text.lower()) is not None


def validate_module_note_sections(path: Path, label: str, required_sections: list[str], errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{label} is not readable: {path}: {exc}")
        return
    normalized = text.lower()
    for section in required_sections:
        if not has_markdown_heading(text, section):
            errors.append(f"{label} missing module note section: {section}")
        elif not markdown_section_has_body(text, section):
            errors.append(f"{label} empty module note section: {section}")
    if any(phrase.lower() in normalized for phrase in SCAFFOLD_PLACEHOLDER_PHRASES):
        errors.append(f"{label} contains scaffold placeholder text")


def validate_manifest_decision_consistency(
    manifest: dict[str, Any], decision: dict[str, Any], errors: list[str]
) -> None:
    for key in ("run_id", "profile", "adapter"):
        if manifest.get(key) != decision.get(key):
            errors.append(f"manifest.{key} and decision.{key} must match")


def validate_adapter_boundaries(
    manifest: dict[str, Any], decision: dict[str, Any], validate_adapter_boundaries: bool, errors: list[str]
) -> None:
    if not validate_adapter_boundaries:
        return
    adapter = manifest.get("adapter")
    profile = manifest.get("profile")
    if isinstance(profile, str) and profile != "conversation_role":
        profile_ref = manifest.get("profile_ref")
        if isinstance(profile_ref, str) and profile_ref.strip():
            path = resolve_ref(profile_ref)
            if path.is_file():
                raw_text = path.read_text(encoding="utf-8")
                text = raw_text.lower()
                for term in CONVERSATION_ROLE_SPECIFIC_TERMS:
                    if term.lower() in text:
                        errors.append(
                            "manifest.profile_ref contains conversation-role term outside "
                            f"conversation_role profile: {term}"
                        )
                required_fields_text = markdown_section_text(raw_text, "Required Fields")
                for term in CONVERSATION_ROLE_SCHEMA_FIELDS:
                    if contains_markdown_token(required_fields_text, term):
                        errors.append(
                            "manifest.profile_ref required fields contain conversation-role field outside "
                            f"conversation_role profile: {term}"
                        )
    if not isinstance(adapter, str) or adapter == "promptfoo":
        return
    searchable = json.dumps({"manifest": manifest, "decision": decision}, ensure_ascii=False).lower()
    if any(term in searchable for term in PROMPTFOO_SPECIFIC_TERMS):
        errors.append("non-promptfoo adapter must not reference Promptfoo-specific artifacts")
    adapter_ref = manifest.get("adapter_ref")
    if isinstance(adapter_ref, str) and adapter_ref.strip():
        path = resolve_ref(adapter_ref)
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            for term in PROMPTFOO_SPECIFIC_TERMS:
                if term.lower() in text:
                    errors.append(
                        f"manifest.adapter_ref contains Promptfoo-specific term for non-promptfoo adapter: {term}"
                    )
            for term in PROMPTFOO_SCHEMA_FIELDS:
                if contains_markdown_token(text, term):
                    errors.append(
                        f"manifest.adapter_ref contains Promptfoo schema field for non-promptfoo adapter: {term}"
                    )


def validate_module_refs(
    manifest: dict[str, Any], require_module_refs: bool, validate_module_notes: bool, errors: list[str]
) -> None:
    ref_specs = {
        "profile_ref": (
            "profiles",
            "profile",
            [
                "Domain Purpose",
                "Domain Boundary",
                "Minimum Artifact Shape",
                "Required Fields",
                "Quality Signals And Rubric Vocabulary",
                "Acceptable Band, Stop Rule, And Bloat Guardrail",
                "When Run Intake Is Enough",
            ],
        ),
        "adapter_ref": (
            "adapters",
            "adapter",
            [
                "Source Files",
                "Result Normalization",
                "Structural Diagnostics",
                "Human Signals",
                "Blocked Actions",
            ],
        ),
    }
    module_roots: dict[str, Path] = {}
    for key, (module_dir, id_key, required_sections) in ref_specs.items():
        value = manifest.get(key)
        if not value:
            if require_module_refs:
                errors.append(f"manifest.{key} is required")
            continue
        if not isinstance(value, str):
            errors.append(f"manifest.{key} must be a string")
            continue
        if "path/to" in value:
            errors.append(f"manifest.{key} contains placeholder path: {value}")
            continue
        path = resolve_ref(value)
        if not path.exists():
            errors.append(f"manifest.{key} does not exist: {value}")
            continue
        module_id = manifest.get(id_key)
        if isinstance(module_id, str) and module_id and not path_contains_module_readme(path, module_dir, module_id):
            errors.append(f"manifest.{key} must point to {module_dir}/{module_id}/README.md")
        elif isinstance(module_id, str) and module_id:
            root = eval_datasets_root_for_module(path, module_dir, module_id)
            if root is not None:
                module_roots[key] = root
        if validate_module_notes:
            validate_module_note_sections(path, f"manifest.{key}", required_sections, errors)
    if {"profile_ref", "adapter_ref"} <= module_roots.keys() and module_roots["profile_ref"] != module_roots["adapter_ref"]:
        errors.append("manifest.profile_ref and manifest.adapter_ref must share the same eval_datasets root")


def validate_manifest(
    manifest: dict[str, Any], require_module_refs: bool, validate_module_notes: bool, errors: list[str]
) -> None:
    for key in ("run_id", "project", "profile", "adapter"):
        require_string(manifest, key, "manifest", errors)
    require_string(manifest, "source_artifact_root", "manifest", errors)
    validate_module_refs(manifest, require_module_refs, validate_module_notes, errors)
    source_files = manifest.get("source_files")
    if not isinstance(source_files, dict):
        errors.append("manifest.source_files must be an object")
        return
    for key, value in source_files.items():
        if not isinstance(key, str) or not key:
            errors.append("manifest.source_files keys must be non-empty strings")
        if not isinstance(value, str):
            errors.append(f"manifest.source_files.{key} must be a string")
        elif not value.strip():
            errors.append(f"manifest.source_files.{key} must be a non-empty string")
        elif "path/to" in value:
            errors.append(f"manifest.source_files.{key} contains placeholder path: {value}")


def validate_decision(decision: dict[str, Any], human_signal_count: int, errors: list[str]) -> None:
    for key in ("decision_id", "run_id", "profile", "adapter", "decision_type", "primary_reason"):
        require_string(decision, key, "decision", errors)

    accepted_direction = decision.get("accepted_direction")
    if accepted_direction is not None and not isinstance(accepted_direction, bool):
        errors.append("decision.accepted_direction must be true, false, or null")
    if accepted_direction is True and decision.get("primary_reason") == "Summarize the main evidence in one sentence.":
        errors.append("decision.accepted_direction true requires a non-placeholder primary_reason")

    for key in ("human_signal_refs", "blocked_actions", "next_actions"):
        require_list(decision, key, "decision", errors)
    blocked_action_set: set[str] = set()
    for index, action in enumerate(decision.get("blocked_actions", []), start=1):
        if not isinstance(action, str):
            errors.append(f"decision.blocked_actions[{index}] must be a string")
        elif action.strip():
            blocked_action_set.add(action.strip())
    allowed_actions = decision.get("allowed_actions", [])
    if allowed_actions is not None:
        if not isinstance(allowed_actions, list):
            errors.append("decision.allowed_actions must be a list")
        else:
            for index, action in enumerate(allowed_actions, start=1):
                if not isinstance(action, str):
                    errors.append(f"decision.allowed_actions[{index}] must be a string")
                    continue
                stripped_action = action.strip()
                if stripped_action in blocked_action_set:
                    errors.append(f"decision.allowed_actions repeats blocked action: {stripped_action}")
    valid_next_actions: list[str] = []
    for index, action in enumerate(decision.get("next_actions", []), start=1):
        if not isinstance(action, str):
            errors.append(f"decision.next_actions[{index}] must be a string")
            continue
        stripped_action = action.strip()
        if stripped_action:
            valid_next_actions.append(stripped_action)
        if stripped_action == "state the next smallest useful action":
            errors.append("decision.next_actions contains placeholder: state the next smallest useful action")
        if stripped_action in blocked_action_set:
            errors.append(f"decision.next_actions repeats blocked action: {stripped_action}")
    if isinstance(decision.get("next_actions"), list) and not valid_next_actions:
        errors.append("decision.next_actions must include at least one non-empty action")

    dataset_generation = decision.get("dataset_generation")
    if not isinstance(dataset_generation, dict):
        errors.append("decision.dataset_generation must be an object")
    elif not isinstance(dataset_generation.get("needed"), bool):
        errors.append("decision.dataset_generation.needed must be a boolean")

    for ref in decision.get("human_signal_refs", []):
        if not isinstance(ref, str) or not ref.startswith("human_signals.jsonl#"):
            errors.append(f"decision.human_signal_refs contains invalid ref: {ref}")
            continue
        line_text = ref.rsplit("#", 1)[-1]
        if not line_text.isdigit():
            errors.append(f"decision.human_signal_refs contains invalid line ref: {ref}")
            continue
        line_number = int(line_text)
        if line_number < 1 or line_number > human_signal_count:
            errors.append(f"decision.human_signal_refs points outside human_signals.jsonl: {ref}")


def referenced_human_signal_records(decision: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for ref in decision.get("human_signal_refs", []):
        if not isinstance(ref, str) or not ref.startswith("human_signals.jsonl#"):
            continue
        line_text = ref.rsplit("#", 1)[-1]
        if not line_text.isdigit():
            continue
        line_number = int(line_text)
        if 1 <= line_number <= len(records):
            selected.append(records[line_number - 1])
    return selected


def validate_decision_signal_alignment(
    decision: dict[str, Any], human_signals: list[dict[str, Any]], errors: list[str]
) -> None:
    next_actions = decision.get("next_actions")
    next_action_set = set()
    if isinstance(next_actions, list):
        next_action_set = {action.strip() for action in next_actions if isinstance(action, str)}
    blocked_actions = decision.get("blocked_actions")
    blocked_action_set = set()
    if isinstance(blocked_actions, list):
        blocked_action_set = {action.strip() for action in blocked_actions if isinstance(action, str)}
    for record in referenced_human_signal_records(decision, human_signals):
        next_action = record.get("next_action")
        if (
            isinstance(next_action, str)
            and next_action.strip()
            and isinstance(next_actions, list)
            and next_action.strip() not in next_action_set
        ):
            errors.append(
                "decision.next_actions must include referenced human signal next_action: "
                f"{next_action.strip()}"
            )
        for blocked_action in record.get("blocked_actions", []):
            if (
                isinstance(blocked_action, str)
                and blocked_action.strip()
                and isinstance(blocked_actions, list)
                and blocked_action.strip() not in blocked_action_set
            ):
                errors.append(
                    "decision.blocked_actions must include referenced human signal blocked_action: "
                    f"{blocked_action.strip()}"
                )


def validate_human_signals(records: list[dict[str, Any]], errors: list[str]) -> None:
    for index, record in enumerate(records, start=1):
        for key in ("signal_type", "raw_signal", "suggested_outcome"):
            value = record.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"human_signals[{index}].{key} must be a non-empty string")
        for key in ("candidate_failure_tags", "blocked_actions"):
            require_list(record, key, f"human_signals[{index}]", errors)
        if "needs_review" in record and not isinstance(record["needs_review"], bool):
            errors.append(f"human_signals[{index}].needs_review must be a boolean")
        source_type = record.get("source_type")
        if source_type is not None and not isinstance(source_type, str):
            errors.append(f"human_signals[{index}].source_type must be a string")
        if record.get("needs_review") is False:
            if not isinstance(source_type, str) or not source_type.strip():
                errors.append(f"human_signals[{index}].source_type is required when needs_review=false")
            elif source_type == "agent_inference":
                errors.append(
                    f"human_signals[{index}].source_type cannot be agent_inference when needs_review=false"
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a run-intake directory.")
    parser.add_argument("run_dir")
    parser.add_argument(
        "--require-module-refs",
        action="store_true",
        help="Require manifest.profile_ref and manifest.adapter_ref to point at existing module notes.",
    )
    parser.add_argument(
        "--validate-module-notes",
        action="store_true",
        help="Validate minimum profile/adapter README sections when refs are present.",
    )
    parser.add_argument(
        "--validate-adapter-boundaries",
        action="store_true",
        help="Reject evaluator-specific artifacts that do not belong to the selected adapter.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_dir = Path(args.run_dir)
    errors: list[str] = []
    if not run_dir.exists() or not run_dir.is_dir():
        errors.append(f"run directory does not exist: {run_dir}")
    manifest = load_json(run_dir / "manifest.json", errors, "manifest")
    decision = load_json(run_dir / "decision.json", errors, "decision")
    human_signals = load_jsonl(run_dir / "human_signals.jsonl", errors)

    if manifest:
        validate_manifest(manifest, args.require_module_refs, args.validate_module_notes, errors)
    if decision:
        validate_decision(decision, len(human_signals), errors)
        validate_decision_signal_alignment(decision, human_signals, errors)
    if manifest and decision:
        validate_manifest_decision_consistency(manifest, decision, errors)
        validate_adapter_boundaries(manifest, decision, args.validate_adapter_boundaries, errors)
    validate_human_signals(human_signals, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"run intake valid: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
