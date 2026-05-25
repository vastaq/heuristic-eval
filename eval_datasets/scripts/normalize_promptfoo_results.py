#!/usr/bin/env python3
"""Normalize Promptfoo result JSON or failure summaries into observations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def output_text(result: dict[str, Any]) -> str:
    response = result.get("response")
    if isinstance(response, dict):
        return str(response.get("output", ""))
    return ""


def normalize_promptfoo_result(path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results", {}).get("results", [])
    observations: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        metadata = result.get("metadata") or result.get("testCase", {}).get("metadata") or {}
        vars_block = result.get("vars") or result.get("testCase", {}).get("vars") or {}
        grading = result.get("gradingResult") or {}
        pass_value = bool(result.get("success", grading.get("pass", False)))
        score_value = result.get("score", grading.get("score"))
        reason = str(result.get("failureReason") or grading.get("reason", ""))
        metadata = dict(metadata)
        if "generic_dimension" not in metadata:
            metadata["generic_dimension"] = metadata.get("scene_type") or metadata.get("scene") or "legacy_promptfoo_result"
        observation = {
            "observation_id": f"{path.stem}_{index + 1:04d}",
            "source_path": str(path),
            "source_index": index,
            "evaluator": "promptfoo",
            "record_id": metadata.get("id") or result.get("id", ""),
            "role": metadata.get("role", ""),
            "scene_type": metadata.get("scene_type", ""),
            "input": vars_block.get("question") or vars_block.get("user_input") or vars_block.get("input") or "",
            "output": output_text(result),
            "success": pass_value,
            "score": score_value,
            "reason": reason,
            "prompt_variant": metadata.get("prompt_variant", ""),
            "metadata": metadata,
            "judge": {
                "pass": pass_value,
                "score": score_value,
                "reason": reason,
            },
            "failure_tags": [] if pass_value else failure_tags(reason),
        }
        observations.append(observation)
    return observations


def normalize_failure_summary(path: Path, payload: list[Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        observations.append(
            {
                "observation_id": f"{path.stem}_{index + 1:04d}",
                "source_path": str(path),
                "source_index": index,
                "evaluator": "promptfoo_summary",
                "record_id": item.get("id", ""),
                "role": item.get("role", ""),
                "scene_type": item.get("scene", item.get("scene_type", "")),
                "turn": item.get("turn"),
                "input": item.get("question", item.get("input", "")),
                "output": item.get("output", ""),
                "success": False,
                "score": item.get("score"),
                "reason": str(item.get("reason", "")),
                "prompt_variant": item.get("prompt_variant", ""),
                "metadata": {
                    **item,
                    "generic_dimension": item.get("scene", item.get("scene_type", "legacy_failure_summary")),
                },
                "judge": {
                    "pass": False,
                    "score": item.get("score"),
                    "reason": str(item.get("reason", "")),
                },
                "failure_tags": failure_tags(str(item.get("reason", ""))),
            }
        )
    return observations


def normalize_path(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return normalize_promptfoo_result(path, payload)
    if isinstance(payload, list):
        return normalize_failure_summary(path, payload)
    return []


def summarize(observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_role = Counter(str(item.get("role", "")) for item in observations)
    failures_by_role = Counter(str(item.get("role", "")) for item in observations if not item.get("success"))
    by_scene = Counter(str(item.get("scene_type", "")) for item in observations)
    failures_by_scene = Counter(str(item.get("scene_type", "")) for item in observations if not item.get("success"))
    prompt_variants = Counter(str(item.get("prompt_variant", "")) for item in observations)
    return {
        "total": len(observations),
        "successes": sum(1 for item in observations if item.get("success")),
        "failures": sum(1 for item in observations if not item.get("success")),
        "by_role": dict(by_role),
        "failures_by_role": dict(failures_by_role),
        "by_scene": dict(by_scene),
        "failures_by_scene": dict(failures_by_scene),
        "prompt_variants": dict(prompt_variants),
    }


def failure_tags(reason: str) -> list[str]:
    tags: list[str] = []
    if "心理咨询" in reason or "咨询" in reason:
        tags.append("consulting_or_therapy_tone")
    if "客服" in reason:
        tags.append("customer_service_tone")
    if "追问" in reason:
        tags.append("over_questioning")
    if "没有给出" in reason or "没有直接" in reason or "没有真正" in reason:
        tags.append("missing_requested_output")
    if "MBTI" in reason:
        tags.append("mbti_exposure")
    if "角色" in reason or "感知轴" in reason:
        tags.append("role_axis_issue")
    if "JSON" in reason or "Could not extract" in reason:
        tags.append("judge_parse_noise")
    return tags or ["legacy_failure"]


def normalize(paths: list[Path], output: Path, project: str, run_id: str) -> int:
    observations: list[dict[str, Any]] = []
    for path in paths:
        observations.extend(normalize_path(path))
    payload = {
        "version": "v1",
        "project": project,
        "run_id": run_id or output.parent.name,
        "updated_at": date.today().isoformat(),
        "source_paths": [str(path) for path in paths],
        "summary": summarize(observations),
        "records": observations,
        "observations": observations,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Normalized {len(observations)} observations to {output}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--project", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    raise SystemExit(normalize(args.sources, args.output, args.project, args.run_id))


if __name__ == "__main__":
    main()
