# HL Reward Assessment

Reward assessment converts replay observations into a conservative system-level
decision. It does not judge whether one output is beautiful. It judges whether a
mutation improved the heuristic eval system.

## Input

Reward assessment reads observation files produced from project test runs. The
main path is evaluator export plus result conversion, with Promptfoo as the
bundled default adapter. The lightweight HL replay executor can also produce the
same observation shape for small focused replays:

```text
eval_datasets/replay/outputs/*.observations.json
```

## Output

Reward assessments should live under the experiment that owns the mutation:

```text
eval_datasets/experiments/<experiment>/reward_assessments/*.reward.json
```

Minimal shape:

```json
{
  "version": "v1",
  "mutation_id": "tapdoki_dreamer_exact_help.v1",
  "observation_path": "eval_datasets/replay/outputs/example.observations.json",
	  "scores": {
	    "user_facing_relevance": 3,
	    "diagnostic_clarity": 4,
	    "cross_project_generality": 2,
	    "replay_stability": 3,
	    "noise_reduction": 3,
	    "compression_value": 2,
	    "naturalness_preservation": 3,
	    "abstraction_level": 3,
	    "rubric_shape_balance": 3,
	    "prompt_bloat_risk": 1,
	    "overfit_risk": 1,
	    "human_goal_alignment": 3
	  },
	  "acceptable_band": {
	    "identity": "stable",
	    "naturalness": "good",
	    "user_intent": "good_enough",
	    "role_flavor": "present_but_not_forced",
	    "constraint_bloat": "low"
	  },
	  "hard_gates": {
	    "has_replay": true,
	    "has_source_trace": true,
	    "has_judge_or_dry_run": true,
	    "has_real_model_output": true,
	    "has_real_judge_score": true,
	    "risk_signals_clear": true
	  },
	  "assessment_level": "judged_replay",
	  "risk_flags": [],
	  "decision": "keep_experiment"
	}
```

## Decisions

- `compress_candidate`: Strong enough to consider compression, but still needs
  human review before canonical promotion.
- `keep_experiment`: Useful signal, but not enough for stable memory.
- `needs_revision`: The mutation may be useful but needs clearer records,
  replay, or rubric.
- `retire_or_noop`: Too weak or noisy to keep expanding.
- `accept_variance`: The output is imperfect but inside the acceptable role
  experience band; do not tune for it.
- `revise_rubric`: The case is useful but the judge/rubric is too narrow.
- `stop_tuning`: Core behavior is stable and remaining failures are low-value or
  would increase prompt bloat.
- `not_assessed`: Dry-run or missing evidence; useful for wiring checks only.

Pass rate is evidence, not the reward. Promotion still requires replay and human
review.

Dry-run observations and replay outputs without real judge scores are not formal
reward evidence. They should produce `assessment_level: dry_run` or
`assessment_level: unjudged_replay` with `decision: not_assessed`, even when the
file shape is otherwise valid.

When a run decision includes `reward_assessment_refs`, the action-plan validator
should accept only `assessment_level: judged_replay` rewards with real model
output and real judge scores. Judged replay rewards must carry
`observation_run_id` for the current `run_id`; a reward without that run context
is not formal decision evidence. A `not_assessed` reward file can document
wiring, but cannot support prompt mutation, dataset generation, acceptance, or
compression. For prompt mutation decisions, referenced rewards should support
the mutation path (`compress_candidate` or `keep_experiment`); `needs_revision`
and `retire_or_noop` are evidence to revise, stop, or discard rather than push
the mutation forward. Prefer run-directory-relative refs for portable run
archives, for example `reward_assessments/compact_v1.reward.json`.

Human signals can change reward interpretation. If the user says a passing
answer feels stiff, increase prompt-bloat concern. If the user says remaining
failures are acceptable, prefer `accept_variance` or `stop_tuning` over prompt
edits.

High pass rate is not enough for compression. If observations carry risk flags
such as `naturalness_low`, `prompt_bloat_risk`, `overfit_risk`, or
`regression_risk_high`, the automatic assessment should keep the mutation out of
`compress_candidate` until those risks are reviewed or replayed away.

## Bloat And Overfit Checks

Reward assessment must explicitly check whether a proposed mutation makes the
role prompt more rigid. Penalize mutations that:

- Add narrow wording rules for one case.
- Add several `if`/`when` exceptions without naming the shared principle they
  preserve.
- Improve pass rate by satisfying a dominant eval shape, such as always adding a
  concrete action, while weakening the role's natural response range.
- Force role flavor into simple practical replies.
- Improve pass rate while lowering naturalness.
- Depend on one judge's style preference.
- Create prompt rules that are hard to remember, test, or retire.

If the current prompt is already in the acceptable band, prefer `accept_variance`
or `stop_tuning` over more prompt edits. A small number of low-severity failures
is healthier than a prompt that passes more tests by becoming stiff.

Reward useful compression. A prompt mutation should score higher only when it
turns repeated local failures into a clearer role invariant, decision order, or
rubric distinction. If the mutation merely adds local exceptions, treat the
pass-rate gain as overfit pressure rather than durable learning.

Before accepting a prompt mutation, check rubric shape balance. If the eval
mostly rewards one shape, such as actions or exact phrases, the next mutation
should usually revise or supplement the eval instead of making the prompt better
at that single shape.

For a newly generated, imported, or rebalanced eval pack, require a dataset
traction audit before treating pass rate as prompt-tuning pressure. If the audit
recommends `revise_or_supplement_eval_first`, the reward decision should usually
be `revise_rubric`, `needs_revision`, `accept_variance`, or `stop_tuning`, not a
prompt mutation. When that recommendation becomes the primary decision, record
`decision_type: revise_or_supplement_eval_first` with `traction_audit_ref`,
`eval_revision_targets` or `replay_targets`, plus state and event refs.
If the audit recommends `inspect_before_prompt_tuning`, treat prompt mutation as
blocked for the current decision and record an inspection or review target first.
Use `decision_type: inspect_before_prompt_tuning` with a `traction_audit_ref`,
`next_review_targets` or `replay_targets`, plus state and event refs, so the
medium-warning review becomes the next task rather than an unowned warning.
