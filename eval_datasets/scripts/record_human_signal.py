#!/usr/bin/env python3
"""Append a structured human signal to a run intake directory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise SystemExit(f"expected true or false, got: {value}")


def write_jsonl_line(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def require_non_empty(value: str, label: str) -> None:
    if not value.strip():
        raise SystemExit(f"{label} must be non-empty")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append one human signal JSONL record to a run.")
    parser.add_argument("--run-dir", required=True, help="Directory containing a run intake.")
    parser.add_argument("--signal-type", required=True)
    parser.add_argument("--raw-signal", required=True)
    parser.add_argument("--context-ref", default="")
    parser.add_argument("--classification", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--suggested-outcome", default="needs_review")
    parser.add_argument("--blocked-action", action="append", default=[])
    parser.add_argument("--next-action", default="")
    parser.add_argument("--needs-review", default="true")
    parser.add_argument("--source-type", default="user")
    parser.add_argument("--source-ref", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"run directory does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise SystemExit(f"run-dir is not a directory: {run_dir}")
    for required in ("manifest.json", "decision.json"):
        if not (run_dir / required).exists():
            raise SystemExit(f"run directory must contain {required}: {run_dir}")
    require_non_empty(args.signal_type, "signal-type")
    require_non_empty(args.raw_signal, "raw-signal")
    require_non_empty(args.suggested_outcome, "suggested-outcome")

    payload = {
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "signal_type": args.signal_type,
        "raw_signal": args.raw_signal,
        "context_ref": args.context_ref,
        "candidate_classification": args.classification,
        "candidate_failure_tags": args.tag,
        "suggested_outcome": args.suggested_outcome,
        "blocked_actions": args.blocked_action,
        "next_action": args.next_action,
        "needs_review": parse_bool(args.needs_review),
        "source_type": args.source_type,
        "source_ref": args.source_ref,
    }
    write_jsonl_line(run_dir / "human_signals.jsonl", payload)
    print(f"appended human signal: {run_dir / 'human_signals.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
