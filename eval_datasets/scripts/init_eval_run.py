#!/usr/bin/env python3
"""Create a thin run-intake skeleton for a project-local eval loop."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def parse_key_value(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"empty source-file key in: {item}")
        parsed[key] = value.strip()
    return parsed


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create manifest, decision, and human-signal files for a thin eval run."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--profile", default="generative_content")
    parser.add_argument("--adapter", default="batch_story_generation")
    parser.add_argument("--output-dir")
    parser.add_argument("--source-root", default="path/to/project/local/output")
    parser.add_argument("--source-file", action="append", default=[], help="Source reference as KEY=PATH")
    parser.add_argument("--controlled-variable", action="append", default=[])
    parser.add_argument("--content-unit", action="append", default=[])
    parser.add_argument("--case-count", type=int, default=0)
    parser.add_argument("--success-count", type=int, default=0)
    parser.add_argument("--failure-count", type=int, default=0)
    parser.add_argument("--decision-type", default="accept_direction")
    parser.add_argument("--primary-reason", default="Summarize the main evidence in one sentence.")
    parser.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else ROOT / "eval_datasets" / "runs" / args.adapter / args.run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    template_dir = ROOT / "eval_datasets" / "templates" / args.profile
    manifest = load_json(template_dir / "run_manifest.template.json")
    decision = load_json(template_dir / "decision.template.json")

    source_files = manifest.get("source_files", {})
    source_files.update(parse_key_value(args.source_file))

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest.update(
        {
            "run_id": args.run_id,
            "project": args.project,
            "profile": args.profile,
            "adapter": args.adapter,
            "created_at": created_at,
            "source_artifact_root": args.source_root,
            "source_files": source_files,
            "controlled_variables": args.controlled_variable,
            "content_units": args.content_unit,
            "case_count": args.case_count,
            "success_count": args.success_count,
            "failure_count": args.failure_count,
            "notes": args.notes
            or "Keep private data in the project workspace. This manifest only points to it.",
        }
    )

    decision.update(
        {
            "decision_id": f"{args.run_id}_decision",
            "run_id": args.run_id,
            "profile": args.profile,
            "adapter": args.adapter,
            "decision_type": args.decision_type,
            "primary_reason": args.primary_reason,
            "human_signal_refs": [],
            "notes": args.notes,
        }
    )

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "decision.json", decision)
    (output_dir / "human_signals.jsonl").write_text("", encoding="utf-8")

    print(f"created run intake: {output_dir}")
    print(f"- {output_dir / 'manifest.json'}")
    print(f"- {output_dir / 'decision.json'}")
    print(f"- {output_dir / 'human_signals.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
