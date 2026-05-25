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
- human signal capture
- skill workflow rules
- validation scripts
- full evaluator run intake under `eval_datasets/runs/`

Out of scope:

- automatic prompt promotion without inspected evidence
- changing canonical review status from a single run
- treating pass rate as the only reward
- deleting raw assets to make the core look cleaner
- continuing prompt tuning after the acceptable band is reached

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
- `last_primary_outcome`
- `acceptable_band`
- `prompt_or_policy_complexity`

State should be stored as an experiment artifact first. It can later become a
stable manifest if repeated loops prove the shape useful.

## Observation Inputs

Valid observations include:

- human review
- human signal or stop-rule judgment
- promptfoo eval output
- full evaluator run summary
- repeated model failure
- legacy test asset
- cross-project replay result
- rubric disagreement
- coverage gap
- validator failure
- dataset traction audit result
- prompt growth or policy complexity increase
- user feedback that behavior is unnatural, mechanical, verbose, or stiff
- user feedback that local `if`/`when` repairs are replacing a clearer principle
- judge instability
- compact experiment outperforming the main version

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
- `audit_dataset_traction`
- `revise_eval_balance`
- `score_mutation_reward`
- `append_event`
- `update_skill_workflow`
- `accept_variance`
- `capture_human_signal`
- `mark_noisy_eval`
- `create_compact_experiment`
- `stop_tuning`

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
4. Apply the prompt-bloat gate before prompt or policy mutation.
5. Run a dataset traction audit before prompt mutation when the eval pack is
   new, imported, rebalanced, or suspected of reward-shape bias.
6. Replay against at least one relevant memory set when generality is claimed.
7. Score reward using multiple signals, not pass rate alone.
8. Compress into one primary destination: accept variance, failure pattern,
   rubric revision, dataset revision, compact candidate, stop tuning, needs
   revision, retired, or gate promotion.
9. Update state with the primary outcome and next replay target.

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
| `naturalness_preservation` | The mutation keeps ordinary interaction natural. |
| `abstraction_level` | The mutation preserves a clear principle or decision order instead of adding case rules. |
| `prompt_bloat_risk` | The mutation adds narrow rules, stiffness, or duplicated policy. |
| `overfit_risk` | The mutation serves one narrow failure at broader cost. |
| `judge_noise` | The result may be evaluator-specific or unstable. |
| `human_goal_alignment` | The mutation follows the user's actual preference rather than evaluator pressure. |

Pass rate can be evidence, but not the reward itself.

## Replay Policy

Replay must match the claim:

- Generic core claim -> replay at least two projects or role families.
- Role-specific failure claim -> replay within the role or close variants.
- Rubric claim -> inspect outputs that should pass and outputs that should fail.
- Promotion claim -> include existing accepted records or release gate samples.

If replay is unavailable, keep the result in experiment state.

## Prompt-Bloat Gate

Prompt or policy changes are allowed only after cheaper actions have been
considered. Before adding a rule, verify that the failure is repeated,
user-visible, severe enough, not better handled by rubric/case revision, and
not likely to make ordinary interaction rigid.

If several proposed rules are local `if`/`when` exceptions, stop and ask for the
shared invariant. Allow a prompt mutation only if it compresses those exceptions
into a smaller role principle, decision order, or boundary. Otherwise classify
the signal as `abstraction_drift`, `overfit_pressure`, `judge_noise`, or
`accept_variance`.

If the prompt or behavior is already inside the acceptable band, classify the
remaining narrow failures instead of tuning for them.

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
- Accept variance.
- Stop tuning.

Avoid growth-only learning. A useful loop can end by refusing to add anything.

Each loop must update learning state with the primary outcome and either a next
replay target or `stop_tuning`.

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
