# Evolution Event Log

Use an append-only event log to explain how test assets evolve. The log should
record decisions without forcing every detail into canonical records. This keeps
records compact while preserving traceability for future skill runs.

Recommended path:

```text
eval_datasets/evolution/events.jsonl
```

The path may not exist until the first event is written. Do not backfill every
historical change before using it; start logging new decisions.

## Event Shape

Each line is one JSON object:

```json
{
  "event_id": "evt_2026_05_19_001",
  "timestamp": "2026-05-19T15:30:00+08:00",
  "event_type": "case_added",
  "record_id": "conversation_core_low_energy_no_advice_001",
  "dataset_path": "eval_datasets/canonical/conversation_core.v1.json",
  "actor": "heuristic-eval-dataset-skill",
  "source": {
    "type": "legacy_asset",
    "path": "tapdoki/test.roles_ordinary.yaml",
    "source_index": 3
  },
  "decision": {
    "from": null,
    "to": "candidate",
    "reason": "Legacy case captures a generic no-advice emotional reception failure."
  },
  "evidence": {
    "kind": "human_review",
    "summary": "Input is reusable across companion roles and not tied to Tapdoki lore."
  }
}
```

## Event Types

| Event type | Use when |
| --- | --- |
| `case_added` | A new canonical record is created from legacy material, eval failure, human feedback, or generation. |
| `case_revised` | Input, target behavior, avoid behavior, rubric meaning, or metadata changes materially. |
| `case_promoted` | A record moves from `candidate` to `accepted` or into a release gate manifest. |
| `case_retired` | A record is marked `retired` because it is obsolete, duplicate, misleading, or too noisy. |
| `case_marked_needs_revision` | A useful idea is kept but not trusted as-is. |
| `rubric_revised` | A rubric changes because it was too broad, too narrow, or rewarded the wrong behavior. |
| `failure_pattern_added` | A generic or role-specific failure mode is created or updated. |
| `human_signal_captured` | A user judgment, preference, stop rule, or strategy note becomes structured memory. |
| `experiment_started` | A new module starts in the experiment layer. |
| `experiment_promoted` | An experiment proves value and enters core, project extension, or gate. |
| `experiment_retired` | An experiment is dropped due to noise, low reuse, or overfitting. |

## Evidence Kinds

Use one or more evidence kinds:

- `human_review`: A reviewer inspected role fit, realism, and rubric fairness.
- `human_signal`: A lightweight user judgment, preference, stop rule, or
  strategy note was captured.
- `eval_failure`: A model output failed in a meaningful way.
- `repeated_regression`: The same failure appeared across runs, prompts, or roles.
- `legacy_assertion`: An old hard assertion still protects behavior.
- `coverage_gap`: The case fills a known role, layer, scene, or dimension gap.
- `cross_project_reuse`: The case or failure pattern applies to more than one
  project or role family.

## Logging Rules

- Log decision events, not every script run.
- Prefer short evidence summaries over dumping full model outputs.
- Link to result files when the full evidence already exists elsewhere.
- Never include secrets, API keys, or raw private user data.
- If a decision reverses an earlier event, append a new event instead of editing
  the old line.

## Relationship To Canonical Records

Canonical records should stay readable and compact. Store durable fields in the
record, such as `review_status`, `revision`, `source_path`, and `notes`. Store
decision history and evidence summaries in the event log.

When a record is promoted or retired, update the canonical record and append an
event in the same working change.
