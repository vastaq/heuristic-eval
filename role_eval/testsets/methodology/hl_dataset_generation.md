# HL Dataset Generation

New evaluation data should be generated as dataset construction actions, not
isolated test samples. A dataset candidate unit records why a group of
canonical-compatible records exists, what observation triggered it, how it
should be exported to Promptfoo tests, and where it may be compressed after
reward assessment.

## Dataset Candidate Unit Shape

Dataset candidate units live under an experiment directory:

```text
role_eval/testsets/experiments/<experiment>/dataset_candidate_units/*.json
```

Minimal shape:

```json
{
  "unit_id": "tapdoki_dreamer_exact_help_001",
  "version": "v1",
  "trigger": {
    "type": "human_review",
    "summary": "Dreamer becomes poetic before completing exact-help requests."
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
  "records": []
}
```

## Generation Flow

1. Observe a failure, gap, replay result, or human review.
2. Diagnose the learning type before writing records.
3. Specify the dataset intent in one sentence.
4. Generate a small contrast set, usually 2-4 candidate records.
5. Keep the unit in the experiment layer until Promptfoo export, eval, and
   reward assessment.
6. Compress into core candidate, project extension, failure pattern, rubric
   revision, needs revision, or retired.

## Relationship To Canonical

Dataset candidate unit records should be canonical-compatible, but the unit file
itself is not a canonical dataset. When a record earns promotion into canonical,
preserve the unit link through `source_path`, `notes`, tags, and an event log
entry.

Do not add dataset candidate units directly to release gates.
