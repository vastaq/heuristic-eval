# HL Dataset Generation

New evaluation data should be generated as dataset construction actions, not
isolated test samples. A dataset candidate unit records why a group of
canonical-compatible records exists, what observation triggered it, how it
should be exported to evaluator tests, and where it may be compressed after
reward assessment.

## Dataset Candidate Unit Shape

Dataset candidate units live under an experiment directory:

```text
eval_datasets/experiments/<experiment>/dataset_candidate_units/*.json
```

Minimal shape:

```json
{
  "unit_id": "tapdoki_dreamer_exact_help_001",
  "version": "v1",
  "profile": "conversation_role",
  "trigger": {
    "type": "human_review",
    "summary": "Dreamer becomes poetic before completing exact-help requests.",
    "evidence_refs": ["observations.json#dreamer_exact_help_1"]
  },
  "diagnosis": "both_generic_and_role_specific",
  "dataset_intent": "Build candidate records that check whether the role completes exact small help before adding flavor.",
  "candidate_destination": [
    "conversation_core_candidate",
    "project_failure_pattern"
  ],
  "reward_expectation": [
    "diagnostic_clarity",
    "noise_reduction"
  ],
  "replay_requirements": [
    "same role",
    "nearby exact-help scenes"
  ],
  "source_route_ref": "route.json",
  "records": [
    {
      "id": "dreamer_exact_help_candidate_001",
      "source_record_id": "dreamer_exact_help_1",
      "evidence_ref": "observations.json#dreamer_exact_help_1",
      "review_status": "candidate"
    }
  ]
}
```

For route-backed candidate units, `route.json` is evidence for the action, not
the learning outcome by itself. Preserve `source_route_ref`,
`trigger.evidence_refs`, `records[].evidence_ref`, and the profile-required
fields for every candidate record. Non-conversation profiles should pass
`--profile-ref` to the candidate-unit validator so profile-required fields come
from the profile module instead of the default conversation-role shape.

## Generation Flow

1. Observe a failure, gap, replay result, or human review.
2. Diagnose the learning type before writing records.
3. Specify the dataset intent in one sentence.
4. Generate a small contrast set, usually 2-4 candidate records.
5. Keep the unit in the experiment layer until evaluator export, eval, and
   reward assessment.
6. Compress into core candidate, project extension, failure pattern, rubric
   revision, needs revision, or retired.

Route-backed candidate units use the same flow with a stricter order:

1. Run `route_hl_observations.py`.
2. Bind the decision to `observation_route_ref`.
3. Run `validate_learning_action_plan.py`.
4. Create the candidate unit.
5. Run `validate_hl_dataset_candidate_units.py`.
6. Run `record_learning_outcome.py` only after the candidate unit validates,
   passing `--evidence-ref` for both the candidate unit and the validation
   result. Candidate-unit outcomes must also pass `--profile` and `--adapter`
   so the learning state cannot be reused across domains by accident.

## Relationship To Canonical

Dataset candidate unit records should be canonical-compatible, but the unit file
itself is not a canonical dataset. Every unit must declare its `profile`; do not
let a CLI default decide whether a unit is conversation-role, tool-use,
generative-content, or another domain. When a record earns promotion into
canonical, preserve the unit link through `source_path`, `notes`, tags, and an
event log entry.

Do not add dataset candidate units directly to release gates.

## Action-Plan Guard

Creating candidate units is a durable learning action, even when the records
remain outside canonical. Before a run decision sets
`dataset_generation.needed: true` or `decision_type:
create_dataset_candidate_unit`, run `validate_learning_action_plan.py`.

The decision should include reviewed `human_signal_refs`, concrete
`replay_targets`, and either `learning_state_ref` or
`learning_state_not_needed_reason`. This prevents one weak failed case from
becoming new eval pressure before the agent has named the reusable failure,
next replay target, and state boundary.
