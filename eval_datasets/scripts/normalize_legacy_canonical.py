#!/usr/bin/env python3
"""Normalize legacy canonical JSON into candidate records with traceability."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def normalize_record(record: dict[str, Any], source_path: Path, index: int) -> dict[str, Any]:
    normalized = dict(record)
    original_status = str(normalized.get("review_status", "candidate"))
    normalized.setdefault("source_path", str(source_path))
    normalized.setdefault("source_index", index)
    normalized.setdefault("source_id", normalized.get("id", ""))
    normalized.setdefault("source", "legacy_canonical_import")
    normalized["review_status"] = "candidate"
    normalized.setdefault("revision", 1)
    notes = normalized.get("notes", "")
    boundary = f"Legacy status was {original_status}; imported as candidate pending review."
    normalized["notes"] = f"{notes} {boundary}".strip()
    return normalized


def normalize(source: Path, output: Path, project: str) -> int:
    payload = json.loads(source.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Expected top-level records list.")

    normalized = [normalize_record(record, source, index) for index, record in enumerate(records)]
    output_payload = {
        "version": payload.get("version", "v1"),
        "project": project or payload.get("project", "legacy_canonical_import"),
        "dataset_type": payload.get("dataset_type", "legacy_canonical_candidate"),
        "source_paths": [str(source)],
        "updated_at": date.today().isoformat(),
        "records": normalized,
        "import_boundary": {
            "legacy_import_is_not_accepted": True,
            "legacy_status_preserved_in_notes": True,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Normalized {len(normalized)} records to {output}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project", default="")
    args = parser.parse_args()
    raise SystemExit(normalize(args.source, args.output, args.project))


if __name__ == "__main__":
    main()
