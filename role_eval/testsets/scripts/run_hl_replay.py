#!/usr/bin/env python3
"""Run a lightweight HL replay and write observation JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from yaml_bridge import parse_yaml


DRY_RUN_OUTPUT = "[DRY RUN]"
THINK_TAG_RE = re.compile(r"<think>[\s\S]*?</think>\s*", re.IGNORECASE)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: YAML must contain an object")
    return payload


def load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"{path}: records must be a list")
    return [record for record in records if isinstance(record, dict)]


def resolve_file_value(value: str, root: Path) -> str:
    path_value = value.removeprefix("file://")
    path = Path(path_value)
    if not path.is_absolute():
        path = root / path
    return path.read_text(encoding="utf-8")


def load_variables(context: dict[str, Any], root: Path) -> dict[str, str]:
    variables: dict[str, str] = {}
    raw_variables = context.get("variables") or {}
    if not isinstance(raw_variables, dict):
        return variables
    for name, spec in raw_variables.items():
        if isinstance(spec, dict) and "file" in spec:
            variables[name] = resolve_file_value(str(spec["file"]), root)
        elif isinstance(spec, dict) and "value" in spec:
            variables[name] = str(spec["value"])
        elif isinstance(spec, str):
            variables[name] = spec
    return variables


def load_record_context(record: dict[str, Any], context: dict[str, Any], root: Path) -> str:
    record_context = context.get("record_context") or {}
    field = "character_context"
    if isinstance(record_context, dict):
        field = str(record_context.get("character_context_field") or field)
    value = record.get(field) or record.get("character_context") or ""
    if isinstance(value, str) and value.startswith("file://"):
        try:
            return resolve_file_value(value, root)
        except FileNotFoundError:
            return value
    return str(value)


def render_template(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def build_messages(record: dict[str, Any], context: dict[str, Any], root: Path) -> list[dict[str, str]]:
    variables = load_variables(context, root)
    variables.update(record.get("vars") or {})
    variables["input"] = record.get("input", "")
    variables["character_context"] = load_record_context(record, context, root)
    prompt = context.get("prompt") or {}
    if not isinstance(prompt, dict):
        prompt = {}
    system_template = str(prompt.get("system_template") or "")
    user_template = str(prompt.get("user_template") or "{{input}}")
    messages: list[dict[str, str]] = []
    system_content = render_template(system_template, variables).strip()
    if system_content:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": render_template(user_template, variables).strip()})
    return messages


def chat_completion(provider: dict[str, Any], messages: list[dict[str, str]]) -> str:
    api_key_env = str(provider.get("api_key_env") or "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable: {api_key_env}")

    base_url = os.environ.get(str(provider.get("base_url_env") or ""), provider.get("base_url"))
    base_url = str(base_url or "https://api.openai.com/v1").rstrip("/")
    endpoint = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
    body = {
        "model": provider.get("model"),
        "messages": messages,
        "temperature": provider.get("temperature", 0.1),
        "max_tokens": provider.get("max_tokens", 1024),
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    context = None
    if provider.get("verify_ssl") is False:
        context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(request, timeout=int(provider.get("timeout", 60)), context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError(f"Model call failed: {error}") from error
    return str(payload["choices"][0]["message"]["content"])


def postprocess_output(output: str) -> str:
    return THINK_TAG_RE.sub("", output).strip()


def build_rubric(record: dict[str, Any]) -> str:
    target = "\n".join(f"- {item}" for item in record.get("target_behavior", []))
    avoid = "\n".join(f"- {item}" for item in record.get("avoid_behavior", []))
    return (
        "Target behavior:\n"
        f"{target or '- Respond naturally and satisfy the user request.'}\n\n"
        "Avoid behavior:\n"
        f"{avoid or '- Ignore the user request or lose the role.'}"
    )


def judge_output(
    record: dict[str, Any],
    output: str,
    provider: dict[str, Any],
    judge_config: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    enabled = bool(judge_config.get("enabled"))
    if not enabled:
        return {"enabled": False}
    if dry_run:
        return {"enabled": True, "pass": None, "score": None, "reason": "dry run"}

    judge_provider = dict(provider)
    judge_provider.update(judge_config.get("provider") or {})
    rubric = build_rubric(record)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict evaluator. Return only JSON with keys "
                "pass, score, and reason."
            ),
        },
        {
            "role": "user",
            "content": f"Rubric:\n{rubric}\n\nModel output:\n{output}",
        },
    ]
    raw = chat_completion(judge_provider, messages)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"enabled": True, "pass": None, "score": None, "reason": raw}
    return {
        "enabled": True,
        "pass": parsed.get("pass"),
        "score": parsed.get("score"),
        "reason": parsed.get("reason"),
    }


def observation_metadata(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "role",
        "project",
        "generic_dimension",
        "scene_type",
        "source_dataset",
        "source_path",
        "review_status",
    )
    return {key: record.get(key) for key in keys if key in record}


def build_observation(
    record: dict[str, Any],
    output: str,
    messages: list[dict[str, str]],
    judge: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    record_id = record.get("id") or record.get("source_record_id")
    return {
        "record_id": record_id,
        "source_record_id": record.get("source_record_id") or record.get("source_id"),
        "input": record.get("input", ""),
        "output": output,
        "judge": judge,
        "metadata": observation_metadata(record),
        "failure_tags": [],
        "dry_run": dry_run,
        "rendered_messages": messages,
    }


def run(config_path: Path, dry_run: bool, input_override: Path | None, output_override: Path | None) -> int:
    root = Path.cwd()
    config = load_yaml(config_path)
    context_path = Path(config["context_path"])
    if not context_path.is_absolute():
        context_path = root / context_path
    context = load_yaml(context_path)
    input_path = input_override or Path(config["input_path"])
    output_path = output_override or Path(config["output_path"])
    if not input_path.is_absolute():
        input_path = root / input_path
    if not output_path.is_absolute():
        output_path = root / output_path

    provider = config.get("provider") or {}
    if not isinstance(provider, dict):
        raise ValueError("provider must be an object")
    if provider.get("type") not in (None, "openai_compatible"):
        raise ValueError("only openai_compatible provider is supported")
    judge_config = config.get("judge") or {"enabled": False}
    if not isinstance(judge_config, dict):
        raise ValueError("judge must be an object")

    observations = []
    for record in load_records(input_path):
        messages = build_messages(record, context, root)
        output = DRY_RUN_OUTPUT if dry_run else postprocess_output(chat_completion(provider, messages))
        judge = judge_output(record, output, provider, judge_config, dry_run)
        observations.append(build_observation(record, output, messages, judge, dry_run))

    payload = {
        "version": "v1",
        "run_id": config.get("run_id") or config_path.stem,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "context_path": str(context_path),
        "dry_run": dry_run,
        "records": observations,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(observations)} observations to {output_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        raise SystemExit(run(args.config, args.dry_run, args.input, args.output))
    except (KeyError, ValueError, RuntimeError, FileNotFoundError) as error:
        print(error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
