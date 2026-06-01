# Script Support Levels

The scripts in this directory are working tools and reference implementations.
They are not the universal encoding of the framework.

Agents should use them when they match the active profile and adapter, and add
or adapt profile/adapter tools when the project has a different evidence shape.

## Stable Primitives

These scripts are intended as reusable project primitives:

- `init_eval_run.py`: create a run-intake skeleton with manifest and optional
  decision/template files.
- `init_profile_adapter.py`: scaffold minimal profile and adapter notes.
- `validate_run_intake.py`: check run structure, module refs, and structural
  readiness boundaries.
- `record_human_signal.py`: append preserved user or agent-inferred signals to
  a run.
- `record_learning_outcome.py`: write scoped learning-state outcomes after
  meaningful compression.
- `validate_learning_action_plan.py`: guard prompt/policy mutation, dataset
  generation, acceptance, route refs, reward refs, and learning-state carryover.
- `validate_evolution_events.py`: validate append-only event logs.
- `validate_hl_learning_state.py`: validate learning-state shape and scoped
  evidence refs.
- `validate_hl_dataset_candidate_units.py`: validate experiment-layer candidate
  dataset units.
- `validate_hl_observations.py`: validate normalized observation payloads.
- `validate_failure_patterns.py`: validate failure-pattern files.

## Bundled Adapter Examples

These scripts encode the bundled conversation-role and Promptfoo assumptions:

- `import_promptfoo_tests.py`
- `batch_import_test_yaml.py`
- `export_promptfoo_tests.py`
- `normalize_promptfoo_results.py`
- `normalize_legacy_canonical.py`
- `audit_testset_balance.py`
- `yaml_bridge.py`

Use them for Promptfoo-shaped conversation role work. For other evaluators,
create an adapter-specific normalizer, importer, or exporter.

## Heuristic Loop Helpers

These scripts help with lightweight replay, reward interpretation, routing, and
dataset traction. Treat their output as evidence or suggestions, not final
promotion:

- `route_hl_observations.py`
- `score_hl_mutation.py`
- `run_hl_replay.py`
- `select_hl_pilot_candidates.py`
- `audit_dataset_traction.py`
- `validate_hl_pilot_outputs.py`

Dry-run replay validates wiring only. It is not reward or promotion evidence.

## Custom Adapter Example

- `normalize_custom_tool_results.py`

This is an example of how a non-Promptfoo runner can normalize traces into the
shared observation shape. Treat its `tool_use_eval` and `custom_tool_runner`
examples as placeholders that should be replaced or calibrated in real
projects.

## Legacy Bootstrap

- `import_legacy_learning.py`

Use this for broad scans of old tests, old results, and old summaries. It should
produce bootstrap evidence and learning-state gaps, not accepted records or
prompt mutations.
