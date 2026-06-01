#!/usr/bin/env python3
"""Create minimal profile and adapter notes for a new eval shape."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "eval_datasets"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def title_from_id(identifier: str) -> str:
    return identifier.replace("_", " ").replace("-", " ").title()


def validate_identifier(identifier: str, label: str) -> str:
    if not ID_PATTERN.fullmatch(identifier):
        raise SystemExit(f"{label} must match {ID_PATTERN.pattern}: {identifier}")
    return identifier


def write_if_missing(path: Path, text: str, force: bool) -> str:
    if path.exists() and not force:
        return "kept"
    path.parent.mkdir(parents=True, exist_ok=True)
    action = "updated" if path.exists() else "created"
    path.write_text(text, encoding="utf-8")
    return action


def profile_note(profile_id: str, domain: str) -> str:
    title = title_from_id(profile_id)
    return f"""# {title} Profile

This profile covers {domain}.

## Domain Purpose

Define what this eval domain is trying to keep inside an acceptable experience
band.

## Domain Boundary

State what belongs in this profile and what should become a different profile.
Do not reuse conversation-role fields unless they naturally describe this
domain.

## Minimum Artifact Shape

Describe the smallest record, run, or observation shape an agent can use without
inventing private project assumptions.

## Required Fields

- `id`
- `input_or_task`
- `expected_behavior`
- `quality_signals`
- `source_ref`
- `review_status`

## List Fields

- `expected_behavior`
- `quality_signals`
- `tags`

## Optional Fields And Local Extensions

List project-local metadata here. Keep private artifacts in ignored run or
experiment directories.

## Taxonomy Or Coverage Dimensions

Name the buckets that prevent the eval from rewarding only one output shape.

## Quality Signals And Rubric Vocabulary

Separate final quality evidence from structural diagnostics. Treat local checks
as diagnostic until human review, judge replay, or stronger evidence supports
them.

## Acceptable Band, Stop Rule, And Bloat Guardrail

Define when the system is good enough, when to `accept_variance`, and when to
`stop_tuning` instead of adding prompt or policy constraints.

## When Run Intake Is Enough

Use `eval_datasets/runs/<adapter>/<run_id>/` when the project already has
outputs, review notes, or diagnostics and does not need reusable canonical
records yet.

## When Canonical Records Are Needed

Create canonical candidates only for repeated, judgeable regressions that need
replay, comparison, or gate protection.
"""


def adapter_note(adapter_id: str, evaluator: str, profile_id: str) -> str:
    title = title_from_id(adapter_id)
    return f"""# {title} Adapter

This adapter note maps {evaluator} evidence into the `{profile_id}` profile.

## Evaluator Or Runner Shape

Describe the external files, result format, and runner assumptions. Keep this
adapter specific to the evaluator shape rather than changing the shared
framework.

## Source Files

- raw evaluator output
- normalized observations
- human review or LLM review
- structural diagnostics

## Import Assumptions

State which fields can be trusted, which are optional, and which should remain
raw evidence.

## Export Assumptions

State whether this adapter exports runnable evaluator files. If it does not,
say so explicitly.

## Result Normalization

Define how pass/fail, scores, reasons, outputs, and case identifiers become
observations.

## Structural Diagnostics

Treat lexical, shape, keyword, or local rule checks as diagnostics unless they
are supported by human review, judge replay, or project evidence.

## Human Signals

Write human judgments to `human_signals.jsonl` and preserve original wording.
Signals can reinterpret metrics, block misleading optimization, or set a next
target.

## Run Intake Outputs

Use `eval_datasets/runs/{adapter_id}/<run_id>/` for `manifest.json`,
`observations.json`, `human_signals.jsonl`, `decision.json`, and summaries.

## Blocked Actions

- automatic accepted status from one run
- prompt mutation before evidence classification
- canonical promotion before replay, audit, or human review
- treating structural diagnostics as final quality
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create minimal profile and adapter README files.")
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--adapter-id", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--evaluator", required=True)
    parser.add_argument("--output-root", default=str(ROOT))
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile_id = validate_identifier(args.profile_id, "profile-id")
    adapter_id = validate_identifier(args.adapter_id, "adapter-id")
    output_root = Path(args.output_root)
    profile_path = output_root / "profiles" / profile_id / "README.md"
    adapter_path = output_root / "adapters" / adapter_id / "README.md"
    profile_action = write_if_missing(profile_path, profile_note(profile_id, args.domain), args.force)
    adapter_action = write_if_missing(adapter_path, adapter_note(adapter_id, args.evaluator, profile_id), args.force)
    profile_label = "kept existing" if profile_action == "kept" else profile_action
    adapter_label = "kept existing" if adapter_action == "kept" else adapter_action
    print(f"{profile_label} profile note: {profile_path}")
    print(f"{adapter_label} adapter note: {adapter_path}")
    print(
        "draft scaffold, not calibrated: edit generated notes with domain-specific "
        "boundaries, fields, rubric vocabulary, and adapter mapping; then run "
        "validate_run_intake.py --validate-module-notes before using them as learning evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
