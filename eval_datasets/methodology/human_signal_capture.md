# Human Signal Capture

Human input in this system is not a labeling queue or approval workflow. It is a
low-friction judgment signal that helps the agent notice what the evaluator
missed, when to stop tuning, or which failure pattern deserves memory.

The human is a strategy anchor, not a data-entry worker.

## When To Capture

Capture a human signal when the user says things like:

- "This is not wrong, but it feels too much like therapy."
- "The score is good enough; do not make the prompt stiffer for two cases."
- "This role should not use that image; it belongs to another role."
- "The judge is rewarding keyword stuffing."
- "This compact prompt feels more natural even if it misses one case."
- "This failure is real, but it is project-specific, not generic."
- "There are too many `if` fixes; maybe the role should hold its principle
  instead of collecting techniques."

These comments should enter the heuristic system as observations. They are not
automatic final truth.

## Capture Shape

Use this minimal shape when writing a human signal into an experiment summary,
run decision, reward assessment, or event evidence:

```json
{
  "signal_type": "human_judgment",
  "raw_signal": "This answer is not exactly wrong, but it feels like therapy.",
  "context_ref": "eval_datasets/runs/promptfoo/run_001/observations.json#case_002",
  "candidate_classification": "generic_conversation_failure",
  "candidate_failure_tags": [
    "consulting_or_therapy_tone",
    "over_questioning"
  ],
  "suggested_outcome": "failure_pattern_candidate",
  "blocked_actions": [
    "prompt_patch_without_replay"
  ],
  "source_type": "user",
  "source_ref": "current conversation or review note",
  "needs_review": true
}
```

Use `human_stop_rule` when the signal is about stopping:

```json
{
  "signal_type": "human_stop_rule",
  "raw_signal": "This is good enough; do not add more prompt rules.",
  "suggested_outcome": "stop_tuning",
  "acceptable_band": {
    "naturalness": "good_enough",
    "remaining_failures": "low_severity"
  },
  "blocked_actions": [
    "continue_prompt_tuning_for_narrow_failures"
  ],
  "source_type": "user",
  "needs_review": false
}
```

Use `human_abstraction_signal` when the user points out that eval pressure is
pushing the prompt toward local repairs instead of a clearer principle:

```json
{
  "signal_type": "human_abstraction_signal",
  "raw_signal": "if的部分太多了，是不是应当在道的方面维持而不是术的角度多修补。",
  "context_ref": "slowpoke prompt simplification, Codex agent conversation 019e4332-4717-7d71-a803-38a058bf22ba",
  "candidate_classification": "generic_conversation_failure",
  "candidate_failure_tags": [
    "prompt_patch_pressure",
    "abstraction_drift",
    "case_by_case_overfit",
    "principle_loss"
  ],
  "suggested_outcome": "blocked_prompt_mutation",
  "blocked_actions": [
    "add_case_specific_if_rule",
    "continue_prompt_tuning_for_narrow_failures",
    "promote_case_patch_as_generic_learning"
  ],
  "next_action": "revise the role principle, decision order, rubric, or failure pattern before adding prompt rules",
  "source_type": "user",
  "source_ref": "current conversation",
  "needs_review": false
}
```

## Compression Targets

A human signal should be compressed into one primary target:

- `accept_variance`
- `stop_tuning`
- `failure_pattern_candidate`
- `rubric_revision`
- `case_revision`
- `judge_noise`
- `blocked_prompt_mutation`
- `next_replay_target`

If no target is clear, keep it as an experiment note and set
`needs_review: true`.

## Agent Duties

When a human signal appears, the agent should:

1. Preserve the original wording as `raw_signal`.
2. Link the relevant case, run, prompt, or observation if available.
3. Classify the signal as generic, project-specific, role-specific, rubric
   issue, case issue, judge noise, acceptable variance, or stop rule.
4. Choose one suggested outcome.
5. Block prompt mutation when the signal is about naturalness, overfitting,
   judge noise, or acceptable variance.
6. When the signal contrasts principle with local fixes, classify it as
   `prompt_patch_pressure` or `abstraction_drift`; require a reusable invariant
   before any new prompt rule.
7. Update learning state, reward assessment, event evidence, or experiment
   summary only when the signal changes the next action.

Use `source_type: "user"` for a signal that preserves the user's judgment. If
the agent is only inferring a signal from artifacts, use
`source_type: "agent_inference"` and keep `needs_review: true`; agent inference
must not masquerade as reviewed human evidence. Any `needs_review: false` signal
must carry a non-empty `source_type` so later decisions do not treat anonymous
agent-created JSON as reviewed human judgment.

Do not ask humans to fill large review forms unless the project explicitly
chooses that workflow. The default interaction should be a short judgment that
the agent turns into structured memory.

## Relationship To Reward

Human signals can override pass-rate pressure by changing reward interpretation.

Examples:

- A high pass rate plus "too stiff" human signal should increase
  `prompt_bloat_risk` and `naturalness_preservation` weight.
- A low pass rate plus "good enough" human signal may produce `accept_variance`
  or `stop_tuning`.
- A judge failure plus "this is actually fine" should trigger `judge_noise` or
  `revise_rubric`, not prompt mutation.

Human signal is evidence for reward assessment, not a shortcut around replay
when promotion or gate changes are involved.
