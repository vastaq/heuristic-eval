# Eval Optimization Without Dataset Generation

Some projects do not need this toolkit to generate new datasets immediately.
They may already have a batch runner, an LLM judge, local diagnostics, and
human review. In that case, use the framework as an optimization ledger instead
of forcing dataset creation.

This mode is useful when the current goal is prompt, rubric, or variable
boundary improvement, not canonical test expansion.

## What To Capture

Capture the smallest durable evidence that explains why the next change is
reasonable:

- The input profile and variable boundary being evaluated.
- The run manifest or matrix used by the project runner.
- Raw generation outputs or links to their project-local paths.
- LLM review results, local diagnostics, or evaluator summaries.
- Short human signals that reinterpret scores or block misleading optimization.
- A decision file that states what changed, what did not change, and why.

Do not copy private prompts, API keys, large artifacts, or full product data into
this shared repository. Project-local data can stay in ignored directories while
the profile, adapter, templates, and decision pattern remain shareable.

## Thin-Slice Workflow

Use this workflow when an agent has already run project-local generation and
review scripts:

1. Create or reuse a profile document for the eval domain.
2. Create or reuse an adapter note for the project's existing output shape.
3. Run `eval_datasets/scripts/init_eval_run.py` or write a run manifest that
   points to local artifacts rather than duplicating them.
4. Normalize only the summary fields needed for comparison.
5. Capture human signals in the user's original wording.
6. Write one decision that compresses the outcome.
7. Update the next-action target without promoting new canonical cases unless
   the project explicitly needs them.

This keeps the framework lightweight while still preventing the main failure:
untracked prompt chasing after every score or judge comment.

## Decision Compression

Each optimization pass should compress into one primary outcome:

- `accept_direction`: current prompt or policy direction is good enough to
  continue or scale.
- `revise_prompt_boundary`: the prompt should change because it owns the
  failure.
- `revise_variable_injection`: the prompt is acceptable, but request variables
  or preset injection are causing conflict.
- `revise_rubric`: the evaluator is rewarding the wrong thing.
- `downgrade_metric_to_diagnostic`: a numeric metric is useful only as a
  warning, not a quality score.
- `accept_variance`: the issue is low-severity or expected variation.
- `stop_tuning`: the system is inside the acceptable band and further prompt
  edits risk stiffness.
- `create_candidate_cases`: repeated failures deserve new candidate tests.

If none of these outcomes is clear, keep the pass as an experiment and do not
mutate prompts or gates.

## Human Signal Priority

Human judgment should not be buried under numeric summaries. When a human says a
metric is misleading, record it as a signal and update the reward interpretation.

Examples:

- "Visual keyword misses should not be the main quality signal."
- "This repeated object is low frequency; do not optimize around it yet."
- "A revisit case cannot demand strong continuity without memory."
- "The atmosphere feels right; do not flatten it into executable actions only."

These signals should usually produce `revise_rubric`,
`downgrade_metric_to_diagnostic`, `accept_variance`, or
`revise_variable_injection` before they produce a prompt rewrite.

## Dataset Boundary

Dataset generation is optional in this mode.

Generate new candidate records only when:

- a failure repeats across runs, maps, roles, or prompts;
- the failure is judgeable and not only taste drift;
- the current eval pack lacks a countercase;
- adding the case will not reward keyword stuffing or prompt bloat;
- the project needs regression protection after a durable fix.

Otherwise, keep the evidence as run intake, human signals, and a decision.

## Minimal Artifact Set

A project using this mode can keep only:

```text
eval_datasets/runs/<adapter>/<run_id>/manifest.json
eval_datasets/runs/<adapter>/<run_id>/summary.json
eval_datasets/runs/<adapter>/<run_id>/human_signals.jsonl
eval_datasets/runs/<adapter>/<run_id>/decision.json
```

The raw product outputs may remain in project-local folders referenced by the
manifest.

Quick start:

```bash
python3 eval_datasets/scripts/init_eval_run.py \
  --run-id story_eval_001 \
  --project example_project \
  --profile generative_content \
  --adapter batch_story_generation \
  --profile-ref eval_datasets/profiles/generative_content/README.md \
  --adapter-ref eval_datasets/adapters/batch_story_generation/README.md \
  --source-root path/to/project/local/output \
  --source-file summary=path/to/project/local/output/summary.json \
  --source-file llm_review=path/to/project/local/output/review.json
```

Then validate that the run intake is bound to concrete profile and adapter
notes before using it as learning evidence:

```bash
python3 eval_datasets/scripts/validate_run_intake.py \
  eval_datasets/runs/batch_story_generation/story_eval_001 \
  --require-module-refs \
  --validate-module-notes
```

## Common Mistakes

- Treating a heuristic number as the final quality score.
- Letting lexical coverage metrics force keyword-stuffed prompts.
- Losing the user's actual judgment after summarizing scores.
- Rewriting prompts before checking whether the evaluator is biased.
- Creating canonical records when a run decision is enough.
- Importing private product data into a shared framework repository.
