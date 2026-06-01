# Batch Story Generation Adapter

This adapter note describes how to connect an existing story-generation batch
runner to the heuristic eval framework without replacing the runner or forcing
canonical dataset generation.

Use it for projects that already produce:

- a story or content catalog;
- an explicit test matrix;
- raw run JSON files;
- a readable CSV or report;
- local structural diagnostics;
- LLM review outputs;
- human review comments.

## Adapter Boundary

The adapter should map project-local files into framework evidence. It should
not require the project to rename its runner, change API clients, or store
private story content in this repository.

Keep raw product artifacts in the project workspace. Store references, summaries,
human signals, and decisions in `eval_datasets/runs/<adapter>/<run_id>/` when the
project wants durable learning.

## Suggested Source Files

Typical project files:

```text
story-catalog.json
story-test-matrix.json
summary.json
csv/story-results.csv
runs/<content_unit>/<case_name>/run-xx.json
llm-review/review-results.json
llm-review/eval-flow-report.json
heuristic-summary.json
heuristic-results.json
```

These names are examples, not requirements. The manifest should record the
actual paths.

## Normalized Evidence Shape

For each run, preserve:

- `run_id`
- `project`
- `profile`
- `adapter`
- `source_artifact_root`
- `content_units`
- `case_count`
- `success_count`
- `failure_count`
- `controlled_variables`
- `generation_model`
- `review_model`
- `diagnostic_summary_ref`
- `llm_review_ref`
- `human_signals_ref`
- `decision_ref`

For each generated row, preserve enough identifiers to reconnect evidence:

- `content_unit`
- `case_name`
- `run_index`
- `variable_set`
- `result_ref`
- `story_text_ref` or `content_ref`
- `diagnostic_ref`
- `llm_review_ref`
- `status`

Do not flatten all information into one score.

## Recommended Interpretation

Use local heuristics as `structural_diagnostics`, not as a final quality score.
They are good at finding mechanical issues such as empty output, failed variable
alignment, truncation, severe repetition, or missing required anchors.

Use LLM review as quality evidence, but check whether the judge is rewarding a
shape that the human does not want.

Use human signals to reinterpret both. If a human says a metric is misleading,
record that as `downgrade_metric_to_diagnostic` or `revise_rubric` before
changing the generator prompt.

## Common Failure Tags

Useful tags for story or scene generation:

- `time_variable_leak`
- `preset_prompt_boundary_conflict`
- `keyword_coverage_bias`
- `event_as_keyword_paste`
- `participant_collapse`
- `flow_fragmentation`
- `truncation_or_early_stop`
- `revisit_without_memory`
- `overfit_to_judge`
- `atmosphere_flattening`
- `object_repetition_low_severity`

Tags are not automatic prompt changes. They are observations for decisions.

## Thin-Slice Decision Example

A prompt-optimization run may produce this decision without generating new
dataset records. If it accepts a direction, keep the decision evidence-bound:

```json
{
  "decision_id": "story_run_001_decision",
  "run_id": "story_run_001",
  "profile": "generative_content",
  "adapter": "batch_story_generation",
  "decision_type": "revise_variable_injection",
  "accepted_direction": true,
  "primary_reason": "Stable map prompt improved atmosphere, but time-specific preset text caused variable conflicts.",
  "human_signal_refs": ["human_signals.jsonl#1"],
  "event_refs": ["events.jsonl#evt_story_run_001_decision"],
  "learning_state_ref": "eval_datasets/experiments/story_run_001/learning_state.v1.json",
  "blocked_actions": [
    "rewrite_stable_prompt_for_single_case",
    "optimize_for_visual_keyword_coverage"
  ],
  "next_actions": [
    "make reusable preset descriptions time-neutral",
    "keep visual keyword checks as diagnostics only",
    "rerun a small time-conflict smoke test"
  ]
}
```

This is useful framework participation even though no canonical dataset was
created. Before treating the accepted direction as controlled, run
`eval_datasets/scripts/validate_learning_action_plan.py` on the run directory so
the human-signal refs, event refs, learning-state ref, prompt-bloat gate, and
replay or audit targets are checked.
