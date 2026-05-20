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
	    "prompt_bloat_risk": 1,
	    "overfit_risk": 1
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
	    "has_real_model_output": true
	  },
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

## Bloat And Overfit Checks

Reward assessment must explicitly check whether a proposed mutation makes the
role prompt more rigid. Penalize mutations that:

- Add narrow wording rules for one case.
- Force role flavor into simple practical replies.
- Improve pass rate while lowering naturalness.
- Depend on one judge's style preference.
- Create prompt rules that are hard to remember, test, or retire.

If the current prompt is already in the acceptable band, prefer `accept_variance`
or `stop_tuning` over more prompt edits. A small number of low-severity failures
is healthier than a prompt that passes more tests by becoming stiff.
