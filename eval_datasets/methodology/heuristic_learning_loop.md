# Heuristic Learning Loop for Role Evaluation

Role-eval heuristic learning treats the testset system as software that can
learn from feedback without updating model weights. The maintained object is not
one prompt or one dataset. It is the connected system of canonical records,
rubrics, failure patterns, event logs, replay batches, and skill workflows.

## Role-Eval Mapping

| HL concept | Role-eval equivalent |
| --- | --- |
| State | Current role prompt, canonical records, taxonomy, failure models, eval history, and active experiment notes. |
| Action | Add, revise, retire, or promote a case; update a rubric; add a failure pattern; change a skill workflow; build a replay batch. |
| Feedback | Eval failure, human review, legacy replay, pass-rate change, noisy judge behavior, or regression evidence. |
| Replay | Accepted bank, release gates, targeted legacy records, previous eval outputs, and multi-turn conversation groups. |
| Memory | Canonical datasets, `evolution/events.jsonl`, failure pattern files, methodology docs, and experiment outputs. |
| Compression | Fold repeated local cases into a core taxonomy, role failure model, rubric module, or retirement decision. |

## Loop

Use this loop when an eval fails, a human gives feedback, a prompt changes, or a
legacy asset appears useful:

1. Observe: collect the concrete failure, feedback, or legacy case.
2. Diagnose: decide which layer needs attention.
3. Mutate: make the smallest useful change to a test asset or workflow.
4. Replay: check the change against a small relevant batch.
5. Reward: judge whether the mutation improved signal without adding noise or
   prompt bloat.
6. Compress: keep, generalize, project-scope, accept variance, stop tuning,
   revise, or retire the asset.

## Diagnosis Categories

| Category | Meaning | Typical mutation |
| --- | --- | --- |
| `prompt_issue` | The role response is bad and the case/rubric are fair. | Tune prompt and consider adding a regression case. |
| `rubric_issue` | The judge rewards or punishes the wrong behavior. | Revise rubric wording or mark the record `needs_revision`. |
| `eval_reward_shape_bias` | The eval repeatedly rewards one output shape, such as concrete actions, exact phrases, lists, or role keywords. | Rebalance buckets or revise rubrics before prompt tuning. |
| `dataset_traction_audit_missing` | A new or suspicious eval pack is being used to tune a prompt before checking reward-shape pressure and countercase coverage. | Run a traction audit and block prompt mutation if the measuring stick is biased. |
| `case_issue` | The input, target behavior, or avoid behavior is unclear. | Revise, split, or retire the record. |
| `taxonomy_gap` | The failure does not fit existing dimensions. | Start a taxonomy experiment or add a core scene type after evidence. |
| `failure_model_gap` | A repeated role-specific failure has no named model. | Add or update a role/project failure pattern. |
| `noisy_eval` | The evidence is unstable, judge-dependent, or too prompt-specific. | Keep in experiment layer; do not promote. |
| `acceptable_variance` | The output is imperfect but still inside the acceptable role experience band. | Accept variance, record the rationale, and do not tune. |
| `overfit_pressure` | Fixing the case would require a narrow rule that makes simple conversation rigid. | Revise or retire the case; only tune after repeated severe evidence. |
| `abstraction_drift` | Several local fixes point to a missing or unclear higher-level role principle. | Revise the role invariant, decision order, rubric, or failure model before adding more prompt rules. |

## Reward Signals

Reward is not just pass rate. A useful mutation should improve at least one of:

- It catches a real user-facing failure.
- It reduces ambiguity in diagnosis.
- It preserves old behavior in replay.
- It generalizes beyond one role, prompt wording, or judge output.
- It compresses several local patches into a simpler pattern.
- It identifies noise and prevents bad records from entering gates.
- It keeps the role in an acceptable band without making the prompt more rigid.
- It identifies cases where stopping is better than adding another constraint.

## Prompt Bloat Guardrail

Role prompts often fail by accumulating too many local fixes. A simple
conversation should not need a dense contract of hard constraints to feel right.
Before changing a prompt because of a failed case, ask:

1. Is the failure severe enough to affect real user experience?
2. Is it repeated across outputs, roles, judges, or replay batches?
3. Is the case fair, natural, and worth preserving?
4. Would the fix add a narrow rule, keyword requirement, or role-flavor
   overperformance?
5. Are several fixes trying to say the same higher-level rule in local `if`
   form?
6. Is the eval rewarding one output shape too often, such as always requiring a
   concrete action when presence or restraint may be better?
7. Has a dataset traction audit been run for this eval pack if it is new,
   imported, rebalanced, or suspected of bias?
8. Would revising the rubric, accepting variance, or retiring the case produce a
   healthier system?

Prefer `accept_variance`, `revise_rubric`, `needs_revision`, or `retired` when a
case pressures the prompt toward stiffness. Prompt changes should pay for their
complexity by protecting a meaningful, reusable behavior.

If several failures share a root cause, do not patch them separately. Compress
them into one role principle, decision order, or named failure pattern, then
replay a small batch to check that the principle handles the cases naturally.

## Acceptable Band

Do not tune toward perfect pass rate. Tune toward a stable band:

- The role identity and boundaries are recognizable.
- The answer is natural in ordinary conversation.
- The user's immediate intent is handled.
- Role flavor appears when useful, but is not forced into every turn.
- Remaining failures are low-severity style disagreements or judge preference.

When this band is stable, choose `stop_tuning` rather than adding more prompt
constraints.

## Forgetting Control

Heuristic systems can forget in engineering-shaped ways: a new case can overfit,
a new rubric can punish good answers, or a new failure pack can make the system
too heavy. Control this by:

- Keeping release gates small and inspectable.
- Running targeted replay before promotion.
- Logging decisions in `evolution/events.jsonl`.
- Retiring noisy experiments instead of preserving everything.
- Compressing repeated cases into failure patterns or taxonomy updates.

## Compression Outcomes

After replay and reward inspection, choose exactly one primary outcome:

| Outcome | Use when |
| --- | --- |
| Core candidate | The lesson is generic across user-facing conversation roles. |
| Project extension | The lesson is valuable but role-family specific. |
| Failure pattern | The lesson names a repeated generic or role-specific failure. |
| Rubric revision | The lesson changes how outputs should be judged. |
| Accept variance | The output is acceptable enough and further tuning would overfit. |
| Stop tuning | The current prompt is inside the acceptable band and remaining issues are low-value. |
| Needs revision | The idea is useful but the case is not trusted yet. |
| Retired | The asset is obsolete, duplicate, misleading, or too noisy. |

Do not let the system only grow. Learning requires both absorbing feedback and
compressing history into maintainable representations.
