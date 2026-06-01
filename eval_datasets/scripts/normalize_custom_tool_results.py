#!/usr/bin/env python3
"""Normalize custom tool-runner trace JSON into HL observations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def tool_steps(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def judge_block(trace: dict[str, Any]) -> dict[str, Any]:
    judge = trace.get("judge")
    if isinstance(judge, dict):
        return dict(judge)
    success = trace.get("success")
    return {
        "pass": success if success in {True, False} else False,
        "score": trace.get("score"),
        "reason": str(trace.get("reason", "")),
    }


def normalize_trace(path: Path, trace: dict[str, Any], index: int) -> dict[str, Any]:
    record_id = str(trace.get("record_id") or trace.get("id") or f"tool_trace_{index + 1:04d}")
    user_task = str(trace.get("user_task") or trace.get("input") or trace.get("task") or "")
    final_outcome = str(trace.get("final_outcome") or trace.get("output") or "")
    judge = judge_block(trace)
    failure_tags = list_strings(trace.get("failure_tags"))
    metadata = trace.get("metadata") if isinstance(trace.get("metadata"), dict) else {}
    metadata = dict(metadata)
    metadata.setdefault("generic_dimension", trace.get("failure_type") or "tool_use_trace")
    return {
        "observation_id": f"{path.stem}_{index + 1:04d}",
        "source_path": str(path),
        "source_index": index,
        "evaluator": "custom_tool_runner",
        "record_id": record_id,
        "trace_id": str(trace.get("trace_id") or record_id),
        "user_task": user_task,
        "tool_steps": tool_steps(trace.get("tool_steps") or trace.get("tool_calls")),
        "final_outcome": final_outcome,
        "input": user_task,
        "output": final_outcome,
        "success": judge.get("pass"),
        "score": judge.get("score"),
        "reason": str(trace.get("reason") or judge.get("reason") or ""),
        "failure_type": str(trace.get("failure_type") or ""),
        "metadata": metadata,
        "judge": judge,
        "failure_tags": failure_tags,
    }


def traces_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        traces = payload.get("traces") or payload.get("records") or payload.get("results")
    else:
        traces = payload
    if not isinstance(traces, list):
        return []
    return [trace for trace in traces if isinstance(trace, dict)]


def normalize_paths(paths: list[Path]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for index, trace in enumerate(traces_from_payload(payload)):
            observations.append(normalize_trace(path, trace, index))
    return observations


def summarize(observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_failure_type = Counter(str(item.get("failure_type", "")) for item in observations)
    return {
        "total": len(observations),
        "successes": sum(1 for item in observations if item.get("judge", {}).get("pass") is True),
        "failures": sum(1 for item in observations if item.get("judge", {}).get("pass") is False),
        "by_failure_type": dict(by_failure_type),
    }


def normalize(
    sources: list[Path],
    output: Path,
    *,
    project: str,
    run_id: str,
    profile: str,
    adapter: str,
) -> int:
    observations = normalize_paths(sources)
    payload = {
        "version": "v1",
        "project": project,
        "run_id": run_id or output.parent.name,
        "profile": profile,
        "adapter": adapter,
        "updated_at": date.today().isoformat(),
        "source_paths": [str(path) for path in sources],
        "summary": summarize(observations),
        "records": observations,
        "observations": observations,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Normalized {len(observations)} custom tool observations to {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--project", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--profile", default="tool_use_eval")
    parser.add_argument("--adapter", default="custom_tool_runner")
    args = parser.parse_args()
    try:
        return normalize(
            args.sources,
            args.output,
            project=args.project,
            run_id=args.run_id,
            profile=args.profile,
            adapter=args.adapter,
        )
    except json.JSONDecodeError as error:
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
