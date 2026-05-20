# Role-Eval Heuristic System Spec

This document defines the heuristic eval system as a heuristic learning system, not
only as a testset database. The maintained object is the whole evaluation
apparatus: records, rubrics, failure models, replay batches, event logs, skills,
and compression decisions.

The goal is to make each update behave like a small policy improvement:
observe feedback, choose the least risky mutation, replay against memory, score
the result, and compress only the useful part.

## System Boundary

The system learns by changing files and workflows, not model weights.

In scope:

- canonical and experiment test records
- role and project failure patterns
- rubric wording and reusable rubric modules
- dataset candidate units generated from observations
- replay batch selection
- lightweight replay execution and observation capture
- reward assessments for replay mutations
- event log decisions
- skill workflow rules
- validation scripts

Out of scope:

- automatic prompt promotion without inspected evidence
- changing canonical review status from a single run
- treating pass rate as the only reward
- deleting raw assets to make the core look cleaner

## State

State is the compact representation the agent should inspect before mutating
the system.

Minimum state fields:

- `system_id`
- `version`
- `updated_at`
- `active_loop`
- `core_dimensions`
- `memory_layers`
- `known_failure_patterns`
- `open_gaps`
- `reward_weights`
- `allowed_actions`
- `blocked_actions`
- `next_replay_targets`

State should be stored as an experiment artifact first. It can later become a
stable manifest if repeated loops prove the shape useful.

## Observation Inputs

Valid observations include:

- human review
- promptfoo eval output
- repeated model failure
- legacy test asset
- cross-project replay result
- rubric disagreement
- coverage gap
- validator failure

An observation is not automatically a mutation. The controller must first decide
what kind of learning signal it is.

## Action Space

Allowed actions:

- `add_candidate_case`
- `add_dataset_candidate_unit`
- `revise_case`
- `retire_case`
- `add_failure_pattern`
- `revise_failure_pattern`
- `revise_rubric`
- `create_replay_batch`
- `create_candidate_slice`
- `score_mutation_reward`
- `append_event`
- `update_skill_workflow`

High-risk actions:

- `promote_to_accepted`
- `add_release_gate`
- `rewrite_schema`
- `delete_raw_asset`

High-risk actions require explicit evidence from replay plus human review.

## Policy

Use this policy before writing files:

1. Classify the observation as generic, project-specific, both, or noisy.
2. Pick the smallest action that preserves traceability.
3. Prefer experiment-layer mutation before canonical mutation.
4. Replay against at least one relevant memory set when generality is claimed.
5. Score reward using multiple signals, not pass rate alone.
6. Compress into one primary destination: core candidate, project extension,
   failure pattern, rubric revision, needs revision, or retired.

## Reward Model

Reward is a weighted judgment over signals:

| Signal | Meaning |
| --- | --- |
| `user_facing_relevance` | The mutation catches behavior users would notice. |
| `diagnostic_clarity` | The mutation makes future failures easier to classify. |
| `cross_project_generality` | The signal appears outside one role or project. |
| `replay_stability` | The mutation does not break existing trusted cases. |
| `noise_reduction` | The mutation prevents weak or ambiguous assets from entering gates. |
| `compression_value` | The mutation replaces many local patches with one reusable model. |

Pass rate can be evidence, but not the reward itself.

## Replay Policy

Replay must match the claim:

- Generic core claim -> replay at least two projects or role families.
- Role-specific failure claim -> replay within the role or close variants.
- Rubric claim -> inspect outputs that should pass and outputs that should fail.
- Promotion claim -> include existing accepted records or release gate samples.

If replay is unavailable, keep the result in experiment state.

Evaluator export is the primary execution path for project datasets; Promptfoo
is the bundled default adapter. The lightweight HL replay executor is an
optional project-local runner for small structured observation loops when full
evaluator compatibility is unnecessary.
See `eval_datasets/methodology/hl_replay_executor.md`.

## Compression Policy

Compression is the point where the system actually learns.

After replay, choose one:

- Keep as experiment.
- Compress into `conversation_core` candidate.
- Compress into project extension or role failure model.
- Revise rubric or taxonomy.
- Mark noisy asset `needs_revision`.
- Retire obsolete or misleading asset.

Avoid growth-only learning. A useful loop can end by refusing to add anything.

## Dataset Generation Policy

New tests should start as dataset candidate units when they are generated from a
feedback signal. A candidate unit preserves the trigger, diagnosis, dataset
intent, candidate destination, reward expectation, replay requirements, and a
small set of canonical-compatible records. See
`eval_datasets/methodology/hl_dataset_generation.md`.

After replay, create a reward assessment before compressing the unit into core
candidate records, project extension records, failure patterns, rubric revision,
needs revision, or retirement. See
`eval_datasets/methodology/hl_reward_assessment.md`.

## Controller Checklist

Before each heuristic eval update:

1. What is the observation?
2. What state does it affect?
3. What is the smallest allowed action?
4. What replay memory checks the claim?
5. What reward signals will decide success?
6. Where will the result be compressed?
7. What event will record the decision?

If these cannot be answered, do not promote or expand the core.
