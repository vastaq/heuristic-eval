#!/usr/bin/env python3
"""Bootstrap heuristic learning state from legacy eval assets.

This script discovers old tests, exports, run results, and summaries, then
writes a traceable import manifest plus a conservative learning-state scaffold.
It does not promote records, mutate prompts, or mark anything accepted.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


TEST_NAMES = ("test", "tests", "canonical", "dataset", "datasets")
RESULT_NAMES = ("result", "results", "full", "full30", "retest", "run", "runs")
SUMMARY_NAMES = ("summary", "audit", "failure", "failures", "review", "notes")


def has_token(path: Path, tokens: tuple[str, ...]) -> bool:
    haystack = " ".join(part.lower() for part in path.parts)
    return any(token in haystack for token in tokens)


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in {".yaml", ".yml"}:
        return "legacy_export_yaml"
    if suffix == ".md" and has_token(path, SUMMARY_NAMES):
        return "legacy_summary"
    if suffix in {".json", ".jsonl"} and has_token(path, RESULT_NAMES):
        return "legacy_eval_result"
    if suffix == ".json" and has_token(path, TEST_NAMES):
        return "legacy_canonical_json"
    if suffix == ".md" and any(token in name for token in SUMMARY_NAMES):
        return "legacy_summary"
    return "legacy_other"


def discover(roots: list[Path]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for root in roots:
        root = root.resolve()
        candidates = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        for path in candidates:
            if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
                continue
            kind = classify(path)
            if kind == "legacy_other":
                continue
            assets.append(
                {
                    "path": str(path),
                    "root": str(root),
                    "kind": kind,
                    "action": default_action(kind),
                }
            )
    return assets


def default_action(kind: str) -> str:
    return {
        "legacy_canonical_json": "convert_to_candidate_records",
        "legacy_export_yaml": "preserve_as_seed_or_export_view",
        "legacy_eval_result": "normalize_to_run_observations",
        "legacy_summary": "compress_to_failure_pattern_state_or_event",
    }.get(kind, "needs_human_review")


def learning_state(assets: list[dict[str, Any]], project: str) -> dict[str, Any]:
    counts = Counter(asset["kind"] for asset in assets)
    return {
        "system_id": "heuristic_eval_dataset_system",
        "version": "v1",
        "updated_at": date.today().isoformat(),
        "active_loop": "legacy_import_bootstrap",
        "core_dimensions": [],
        "memory_layers": {
            "legacy_manifest": "manifest.json",
            "run_intake": "eval_datasets/runs/",
            "seeds": "eval_datasets/seeds/",
            "events": "eval_datasets/evolution/events.jsonl",
        },
        "known_failure_patterns": [],
        "open_gaps": [
            "Review legacy assets before promotion.",
            "Normalize evaluator results into observations.",
            "Compress repeated failures into candidate failure patterns.",
        ],
        "reward_weights": {
            "user_facing_relevance": 0.2,
            "diagnostic_clarity": 0.2,
            "cross_project_generality": 0.15,
            "replay_stability": 0.15,
            "noise_reduction": 0.15,
            "compression_value": 0.15,
        },
        "allowed_actions": [
            "convert_to_candidate_records",
            "normalize_to_run_observations",
            "create_failure_pattern_candidate",
            "revise_rubric",
            "accept_variance",
            "create_targeted_replay",
        ],
        "blocked_actions": [
            "promote_to_accepted_without_review",
            "mutate_prompt_from_legacy_import_only",
            "add_release_gate_from_legacy_import_only",
        ],
        "next_replay_targets": next_targets(counts),
        "last_primary_outcome": "legacy_import",
        "acceptable_band": {},
        "prompt_or_policy_complexity": {},
        "metadata": {
            "project": project,
            "asset_counts": dict(counts),
        },
    }


def next_targets(counts: Counter[str]) -> list[str]:
    targets = []
    if counts["legacy_eval_result"]:
        targets.append("Normalize legacy eval results into observations.")
    if counts["legacy_canonical_json"] or counts["legacy_export_yaml"]:
        targets.append("Review imported tests as candidate records only.")
    if counts["legacy_summary"]:
        targets.append("Compress summaries into candidate failure patterns or stop_tuning decisions.")
    return targets or ["Review discovered legacy assets."]


def write_outputs(assets: list[dict[str, Any]], output_dir: Path, project: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter(asset["kind"] for asset in assets)
    manifest = {
        "version": "v1",
        "project": project,
        "import_type": "legacy_learning_bootstrap",
        "updated_at": date.today().isoformat(),
        "rules": {
            "legacy_import_is_not_accepted": True,
            "legacy_import_is_not_prompt_mutation": True,
            "legacy_import_is_not_gate_promotion": True,
        },
        "asset_counts": dict(counts),
        "assets": assets,
    }
    decision = {
        "version": "v1",
        "primary_outcome": "needs_human_review",
        "allowed_next_steps": [
            "normalize_results",
            "review_candidate_records",
            "create_failure_pattern_candidates",
            "targeted_replay",
        ],
        "blocked_next_steps": [
            "auto_accept_records",
            "auto_mutate_prompt",
            "auto_promote_gate",
        ],
    }
    summary = [
        "# Legacy Learning Bootstrap",
        "",
        f"Project: `{project}`",
        "",
        "## Asset Counts",
        "",
    ]
    for kind, count in sorted(counts.items()):
        summary.append(f"- `{kind}`: {count}")
    summary.extend(
        [
            "",
            "## Import Boundary",
            "",
            "- Legacy import does not imply accepted records.",
            "- Legacy import does not imply prompt mutation.",
            "- Legacy import does not imply gate promotion.",
            "- Next steps should review, normalize, replay, or compress evidence.",
        ]
    )

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "learning_state.v1.json").write_text(
        json.dumps(learning_state(assets, project), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--project", default="legacy_import")
    args = parser.parse_args()

    assets = discover(args.roots)
    write_outputs(assets, args.output_dir, args.project)
    print(f"Discovered {len(assets)} legacy assets.")
    print(f"Wrote bootstrap artifacts to {args.output_dir}.")


if __name__ == "__main__":
    main()
