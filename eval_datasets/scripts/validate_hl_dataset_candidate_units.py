#!/usr/bin/env python3
"""Validate HL dataset candidate unit files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_UNIT_FIELDS = (
    "unit_id",
    "version",
    "trigger",
    "diagnosis",
    "dataset_intent",
    "candidate_destination",
    "reward_expectation",
    "replay_requirements",
    "records",
)
REQUIRED_RECORD_FIELDS = (
    "id",
    "layer",
    "role",
    "scene_type",
    "difficulty",
    "input",
    "target_behavior",
    "avoid_behavior",
    "tags",
    "rubric_ref",
    "source_path",
    "review_status",
)
DEFAULT_LIST_FIELDS = (
    "avoid_behavior",
    "expected_behavior",
    "quality_signals",
    "tags",
    "target_behavior",
)
FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SCAFFOLD_PLACEHOLDER_PHRASES = (
    "Define what this eval domain is trying to keep",
    "State what belongs in this profile",
    "Describe the smallest record, run, or observation shape",
    "List project-local metadata here",
    "Name the buckets that prevent the eval",
)


def present(value: Any) -> bool:
    return value is not None and value != "" and value != []


def unit_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.glob("*.json") if candidate.is_file())


def markdown_section(text: str, heading: str) -> list[str]:
    wanted = heading.strip().lower()
    in_section = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            if in_section:
                break
            if title == wanted:
                in_section = True
            continue
        if in_section:
            lines.append(line)
    return lines


def field_name_from_bullet(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith(("-", "*")):
        return None
    backtick_match = re.search(r"`([^`]+)`", stripped)
    if backtick_match:
        candidate = backtick_match.group(1).strip()
    else:
        candidate = stripped[1:].strip().split(maxsplit=1)[0] if stripped[1:].strip() else ""
        candidate = candidate.rstrip(":,.;")
    if FIELD_NAME_PATTERN.fullmatch(candidate):
        return candidate
    return None


def fields_from_profile_text(text: str, *headings: str) -> tuple[str, ...]:
    section: list[str] = []
    for heading in headings:
        section = markdown_section(text, heading)
        if section:
            break
    fields: list[str] = []
    seen: set[str] = set()
    for line in section:
        field = field_name_from_bullet(line)
        if field and field not in seen:
            fields.append(field)
            seen.add(field)
    return tuple(fields)


def stable_unique(*field_groups: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    fields: list[str] = []
    seen: set[str] = set()
    for group in field_groups:
        for field in group:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return tuple(fields)


def contains_scaffold_placeholder(text: str) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in SCAFFOLD_PLACEHOLDER_PHRASES)


def profile_ref_matches_profile(path: Path, profile: str) -> bool:
    return len(path.parts) >= 3 and path.parts[-3:] == ("profiles", profile, "README.md")


def validate_unit(
    payload: dict[str, Any],
    path: Path,
    profile: str,
    required_record_fields: tuple[str, ...],
    list_fields: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_UNIT_FIELDS:
        if not present(payload.get(field)):
            errors.append(f"{path}: missing {field}")

    payload_profile = payload.get("profile")
    if not present(payload_profile):
        errors.append(f"{path}: missing profile")
    elif payload_profile != profile:
        errors.append(f"{path}: profile mismatch: {payload_profile} != {profile}")

    trigger = payload.get("trigger")
    route_backed = present(payload.get("source_route_ref"))
    trigger_evidence_refs: set[str] = set()
    if not isinstance(trigger, dict):
        errors.append(f"{path}: trigger must be an object")
    else:
        for field in ("type", "summary"):
            if not present(trigger.get(field)):
                errors.append(f"{path}: missing trigger.{field}")
        if route_backed:
            evidence_refs = trigger.get("evidence_refs")
            if not isinstance(evidence_refs, list):
                errors.append(f"{path}: source_route_ref requires trigger.evidence_refs")
            else:
                trigger_evidence_refs = {
                    ref.strip() for ref in evidence_refs if isinstance(ref, str) and ref.strip()
                }
                if not trigger_evidence_refs:
                    errors.append(f"{path}: source_route_ref requires trigger.evidence_refs")

    for field in ("candidate_destination", "reward_expectation", "replay_requirements"):
        if field in payload and not isinstance(payload[field], list):
            errors.append(f"{path}: {field} must be a list")

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append(f"{path}: records must be a non-empty list")
        return errors
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}: records[{index}] must be an object")
            continue
        for field in required_record_fields:
            if not present(record.get(field)):
                errors.append(f"{path}: missing records[{index}].{field}")
        for field in list_fields:
            if field in record and not isinstance(record[field], list):
                errors.append(f"{path}: records[{index}].{field} must be a list")
        if route_backed:
            evidence_ref = record.get("evidence_ref")
            if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                errors.append(f"{path}: missing records[{index}].evidence_ref for route-backed unit")
            elif trigger_evidence_refs and evidence_ref.strip() not in trigger_evidence_refs:
                errors.append(f"{path}: records[{index}].evidence_ref not listed in trigger.evidence_refs")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--profile",
        default="conversation_role",
        help="Profile whose candidate records are being validated.",
    )
    parser.add_argument(
        "--record-field",
        action="append",
        default=[],
        help="Required record field for this profile. Repeat to override conversation-role defaults.",
    )
    parser.add_argument(
        "--profile-ref",
        type=Path,
        default=None,
        help="Profile README whose Required Fields section defines record fields.",
    )
    parser.add_argument(
        "--list-field",
        action="append",
        default=[],
        help="Record field that must be a list when present. Repeat to override defaults.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    profile_record_fields: tuple[str, ...] = ()
    profile_list_fields: tuple[str, ...] = ()
    if args.profile_ref is not None:
        if not profile_ref_matches_profile(args.profile_ref, args.profile):
            errors.append(f"profile_ref must point to profiles/{args.profile}/README.md")
        try:
            profile_text = args.profile_ref.read_text(encoding="utf-8")
            if contains_scaffold_placeholder(profile_text):
                errors.append("profile_ref contains scaffold placeholder text")
            profile_record_fields = fields_from_profile_text(
                profile_text, "Required Fields", "Required Record Fields"
            )
            profile_list_fields = fields_from_profile_text(profile_text, "List Fields", "List Record Fields")
        except OSError as error:
            errors.append(f"profile_ref is not readable: {args.profile_ref}: {error}")
        if not profile_record_fields:
            errors.append("profile_ref does not define required record fields")
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    if profile_record_fields:
        required_record_fields = stable_unique(profile_record_fields, args.record_field)
    elif args.record_field:
        required_record_fields = tuple(args.record_field)
    else:
        if args.profile != "conversation_role":
            print("non-conversation profiles require profile-specific --record-field values")
            raise SystemExit(1)
        required_record_fields = REQUIRED_RECORD_FIELDS
    list_fields = stable_unique(DEFAULT_LIST_FIELDS, profile_list_fields, args.list_field)

    paths = unit_paths(args.path)
    if not paths:
        errors.append(f"{args.path}: no dataset candidate unit JSON files found")
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path}: invalid JSON: {error}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{path}: top-level JSON must be an object")
            continue
        errors.extend(validate_unit(payload, path, args.profile, required_record_fields, list_fields))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"Validated {len(paths)} dataset candidate units")


if __name__ == "__main__":
    main()
