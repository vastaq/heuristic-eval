# Autonomous Agent Controller

This controller makes the heuristic eval dataset usable by an agent without
turning the work into a rigid pipeline. It defines mandatory checkpoints. The
agent still chooses the concrete action based on the project, evaluator, role,
and user goal.

## Trigger Conditions

Run this controller before changing prompts, rubrics, canonical records, gates,
or failure patterns when any of these signals appear:

- A new evaluator result, Promptfoo run, replay output, or human review arrives.
- Pass rate, judge score, or user satisfaction leaves the acceptable band.
- The same failure type repeats across runs, roles, prompts, or judges.
- The prompt grows longer, more specific, or harder to maintain.
- The user reports that behavior feels unnatural, mechanical, verbose, or stiff.
- The user gives a short judgment, preference, stop request, or strategy note
  that should become heuristic memory.
- Judge outputs disagree, fluctuate, or reward obvious bad behavior.
- A compact experiment looks better than the current main version.
- A proposed fix would add a new prompt rule for one narrow case.

## State Is Required

Before mutation, inspect the active learning state if it exists. If none exists
for the experiment, create a lightweight one before making durable changes.

Minimum state responsibilities:

- Record the active loop and current acceptable band.
- List known failure patterns, open gaps, blocked actions, and allowed actions.
- Name the current replay memory and next replay targets.
- Track prompt length or policy complexity when prompt edits are in scope.
- Record the last primary outcome so the next loop does not repeat stale work.

Do not promote records, revise gates, or add prompt constraints when state,
action, replay, reward, and compression cannot be named.

## Controller Loop

Each autonomous iteration must produce one primary outcome.

1. **Observe**: preserve the raw result under `eval_datasets/runs/` or the
   relevant experiment directory. For user judgment, preserve the original
   wording as a human signal.
2. **Read state**: inspect or create `learning_state*.json`.
3. **Classify**: mark the signal as prompt issue, rubric issue, case issue,
   taxonomy gap, failure-model gap, noisy eval, acceptable variance, or overfit
   pressure.
4. **Choose the smallest action**: prefer classification, rubric/case revision,
   failure pattern, targeted replay, or compact experiment before prompt edits.
5. **Run the prompt-bloat gate** if any prompt or policy change is considered.
6. **Replay**: choose the smallest memory set that can test the claim.
7. **Assess reward**: evaluate pass rate, naturalness, role consistency,
   prompt/policy complexity, regression risk, judge noise, user goal, and human
   signals.
8. **Compress**: write exactly one primary outcome and update state.
9. **Set next target or stop**: name the next replay target, or mark
   `stop_tuning`.

## Smallest-Action Order

When evidence is ambiguous, choose actions in this order:

1. `accept_variance`
2. `capture_human_signal`
3. `mark_noisy_eval`
4. `mark_case_failure`
5. `mark_rubric_failure`
6. `revise_case`
7. `revise_rubric`
8. `add_or_update_failure_pattern`
9. `create_targeted_replay`
10. `create_dataset_candidate_unit`
11. `create_compact_experiment`
12. `mutate_prompt_or_policy`
13. `promote_to_gate`

Prompt or policy mutation is late in the order because it increases system
complexity and can make ordinary interactions worse.

## Prompt-Bloat Gate

Before adding prompt constraints, answer all of these:

- Does the rule protect a repeated, user-visible, severe failure?
- Does it serve more than one case, role, judge, or replay batch?
- Would a failure pattern, rubric revision, or case revision solve it better?
- Does it duplicate an existing principle in different words?
- Would it make ordinary conversation more rigid, verbose, or overperformed?
- Can it be removed later if the failure disappears?

If the answer is weak, choose `accept_variance`, `revise_rubric`,
`needs_revision`, `retired`, or `failure_pattern` instead.

## Stop Rules

Stop prompt tuning when the prompt or behavior is inside the acceptable band and
remaining failures are low-severity, judge-specific, or narrow.

Stop or escalate to human review when:

- Two consecutive iterations do not improve reward.
- Prompt length or policy complexity grows without meaningful user-facing gain.
- A new fix replaces old failures with comparable new failures.
- Judge noise dominates the failure set.
- The only remaining failures require unnatural or over-specific behavior.

Stopping is a valid learning outcome. Record `stop_tuning` and move remaining
items into classification, experiment, or retirement.

## Run Intake

Full evaluator runs should be stored separately from lightweight replay outputs:

```text
eval_datasets/runs/<evaluator>/<run_id>/
  raw/                 # Original evaluator output, logs, or copied report.
  observations.json    # Normalized observations when available.
  summary.md           # Agent-readable run summary and diagnosis.
  decision.json        # Primary outcome and next target.
```

`eval_datasets/replay/outputs/` remains for lightweight HL replay observations.

## Experiment Archive

Use this shape for compact experiments, prompt variants, rubric experiments, or
candidate dataset trials:

```text
eval_datasets/experiments/<experiment_id>/
  candidates/
  exports/
  results/
  reward_assessments/
  learning_state.v1.json
  summary.md
  decision.json
```

Keep experiment artifacts local unless they are intentionally scrubbed and
useful as examples.
