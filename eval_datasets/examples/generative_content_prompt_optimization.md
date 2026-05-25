# Generative Content Prompt Optimization Case Pattern

This example captures a reusable pattern from a story-generation optimization
loop without including private product prompts, raw generated stories, API keys,
or project data.

It is meant to show how the framework can participate even when the project does
not need to generate a new dataset.

## Situation

A project has a generator that produces multi-scene content from:

- a stable source prompt;
- a small set of controlled variables;
- optional preset events or anchors;
- a batch runner;
- a local heuristic or diagnostic summary;
- an LLM review;
- human reading and product judgment.

The team wants to improve prompt quality and evaluation reliability without
turning every weak sample into a new prompt rule.

## Useful Framework Role

Use the framework as an optimization ledger:

- preserve the run manifest;
- classify local metrics as diagnostics or quality evidence;
- capture human judgment in the user's own words;
- write a decision that states which action is allowed next;
- generate candidate dataset records only if repeated, judgeable failures need
  replay protection.

This is not a mandatory dataset-generation workflow.

## Lessons To Preserve

### Keep Stable Prompt And Variable Injection Separate

If the stable prompt describes the world, role, or content source, it should not
also encode case-specific time, count, or event details. Case variables should
enter through the adapter or request layer.

When a conflict appears, first decide whether the stable prompt, variable
injection, preset wording, or evaluator owns the failure.

### Treat Lexical Coverage As Diagnostic

Keyword, motif, or visual-term coverage can catch empty or off-brief outputs, but
it can also reward keyword stuffing. If human or LLM review says the output is
good while lexical coverage is low, downgrade that metric to diagnostic-only
before changing the prompt.

### Capture Capability Boundaries

Do not judge a generator for strong continuity if the product does not provide
memory, previous-state summaries, or retrieval. Convert that into a boundary
signal such as `revisit_without_memory`, then revise the rubric or variable
definition.

### Preserve Atmosphere When It Is Working

Not every preset or prompt line must be an executable action. Atmosphere can be a
valid quality contributor. Only revise atmospheric text when it conflicts with a
controlled variable, causes repeated repetition, or makes outputs checklist-like.

### Do Not Overreact To Low-Frequency Artifacts

A repeated object, phrase, or motif in one or two samples may be acceptable
variance. Track it as a low-severity signal unless it repeats across runs or
damages readability.

## Suggested Decision Outcomes

Common outcomes for this pattern:

- `accept_direction`: the prompt direction is better; scale cautiously.
- `revise_variable_injection`: presets or variables conflict with the stable
  prompt.
- `downgrade_metric_to_diagnostic`: a numeric metric is useful but misleading as
  a quality score.
- `revise_rubric`: the evaluator is judging something the product does not
  value.
- `accept_variance`: the artifact is low frequency and not worth prompt bloat.
- `create_candidate_cases`: repeated failures deserve replayable coverage.

## Minimal Files

Use templates from:

```text
eval_datasets/templates/generative_content/run_manifest.template.json
eval_datasets/templates/generative_content/human_signals.template.jsonl
eval_datasets/templates/generative_content/decision.template.json
```

The raw project output can remain outside the shared framework repository.
