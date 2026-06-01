---
name: heuristic-eval
description: Use when working with the heuristic-eval repository or its eval_datasets workspace: importing, maintaining, auditing, generating, or evolving heuristic evaluation assets; absorbing evaluator feedback; maintaining profiles/adapters/templates; handling Promptfoo examples, canonical JSON, candidate/accepted review status, prompt-bloat control, acceptable variance, stop-tuning decisions, or legacy test migration.
---

# heuristic-eval

Use this skill as the short agent entrypoint into the
`heuristic-eval` repository. The repository is not only a skill package:
`eval_datasets/` is the real file-backed workspace for methodology, profiles,
adapters, templates, scripts, run intake, canonical records, experiments, and
evolution memory.

If this repository is not present in the current workspace, locate, clone,
vendor, or reference it before relying on its scripts, profiles, adapters, or
templates.

The job is to turn eval feedback into maintainable evidence and decisions. A
failed eval can become a candidate case, rubric revision, failure pattern,
retirement, acceptable variance, or stop-tuning decision. It is not
automatically a prompt rule.

## First Routing Decision

Before changing data, prompts, rubrics, or scripts, decide the active route:

1. **Old content intake**: legacy tests, YAML, old JSON, eval summaries, or
   prior conclusions need to become traceable evidence.
2. **Dataset maintenance**: canonical records, review status, exports, balance,
   or retirement need updates.
3. **New candidate generation**: repeated, judgeable failures or coverage gaps
   need small candidate testsets.
4. **Returned eval absorption**: Promptfoo or another evaluator produced results
   that need normalization, routing, reward interpretation, or compression.
5. **Optimization without dataset generation**: a project already has local
   outputs, diagnostics, LLM review, or human judgment, and only needs run
   evidence and a decision.

Use the lightest route that preserves evidence.

## Framework / Profile / Adapter

Keep three layers separate:

- **Framework**: shared concepts such as run intake, learning state, reward
  interpretation, prompt-bloat gates, stop rules, and legacy bootstrap.
- **Profile**: domain schema, rubric vocabulary, acceptable band, promotion
  evidence, and bloat guardrail.
- **Adapter**: evaluator import/export and result normalization.

Default to `conversation_role` and `promptfoo` only when the artifacts really
are conversation-role Promptfoo-shaped. For TTS, coding, retrieval, tool use,
generative content, or another domain, create or update a profile and adapter.

Do not invent `role`, `scene_type`, `vars`, `input_var`, or `legacy_asserts`
for non-role or non-Promptfoo data. Define local schema and mapping instead.

The Python scripts are primitives and examples, not the universal encoding of
the framework. Compose, adapt, or add profile/adapter tools when the local
runner or evidence shape is different.

## New-Domain Checklist

When the task is not clearly conversation-role Promptfoo work:

1. Inspect the task domain, existing outputs, evaluator shape, and user goal.
2. Inspect or create `eval_datasets/profiles/<profile>/README.md`.
3. Inspect or create `eval_datasets/adapters/<adapter>/README.md`.
4. Initialize run intake with `profile_ref` and `adapter_ref`.
5. Validate module refs before using the run to drive prompt, policy, or
   dataset work.

Useful commands:

```bash
python3 eval_datasets/scripts/init_profile_adapter.py \
  --profile-id example_eval \
  --adapter-id example_runner \
  --domain "example eval domain" \
  --evaluator "example runner"
```

```bash
python3 eval_datasets/scripts/init_eval_run.py \
  --run-id example_run \
  --project example_project \
  --profile example_eval \
  --adapter example_runner \
  --profile-ref eval_datasets/profiles/example_eval/README.md \
  --adapter-ref eval_datasets/adapters/example_runner/README.md \
  --source-file summary=path/to/summary.json
```

```bash
python3 eval_datasets/scripts/validate_run_intake.py \
  eval_datasets/runs/example_runner/example_run \
  --require-module-refs \
  --validate-module-notes \
  --validate-adapter-boundaries
```

## Universal Rules

- Preserve source traceability with fields that belong to the active profile and
  adapter.
- New or imported records start as `candidate`.
- Promote to `accepted` only with review evidence.
- Use `needs_revision` for useful but noisy tests.
- Use `retired` instead of deleting obsolete tests.
- Do not optimize only for maximum pass rate.
- Treat dry-run replay as wiring evidence, not reward or promotion evidence.
- Stop prompt tuning when behavior is inside the acceptable band and remaining
  failures are low-severity, judge-specific, or narrow.

## Prompt-Bloat Gate

Before adding prompt or policy constraints, answer:

- Is the failure repeated, user-visible, and severe?
- Does the rule serve more than one narrow case?
- Would a failure pattern, rubric revision, case revision, or retirement solve
  it better?
- Would the rule make ordinary interaction more rigid, verbose, or
  overperformed?
- Can the rule be removed later if the failure disappears?

If the answer is weak, prefer `accept_variance`, `mark_noisy_eval`,
`mark_case_failure`, `mark_rubric_failure`, `needs_revision`, `retired`, or
`failure_pattern_candidate`.

## Controller Trigger

Use the autonomous controller when evaluator results, repeated failures, prompt
growth, user dissatisfaction, judge noise, compact experiments, or proposed
one-case prompt rules should change durable assets.

Controller shape:

```text
observe -> read state -> classify -> choose smallest action -> bloat gate
-> replay -> reward -> compress -> update state -> next target or stop
```

Do not run the full controller for typo fixes, routine exports, or metadata
cleanup that do not change prompts, rubrics, canonical records, gates, or
failure patterns.

## Old Content Intake

Old content is evidence, not truth.

- Old tests become seeds or candidate records.
- Old eval results become run intake and normalized observations.
- Old summaries become candidate failure patterns, state gaps, events, or stop
  rules.
- Legacy import must not automatically accept records, mutate prompts, or
  promote gates.

Useful commands:

```bash
python3 eval_datasets/scripts/import_legacy_learning.py \
  path/to/legacy/tests path/to/legacy/results \
  --output-dir eval_datasets/experiments/legacy_bootstrap \
  --project example_project
```

```bash
python3 eval_datasets/scripts/import_promptfoo_tests.py \
  path/to/test.yaml \
  eval_datasets/seeds/example.from_legacy.json \
  --project example_project \
  --role example_role
```

## Dataset Maintenance

When adding or revising records:

1. Edit canonical JSON, not generated exports.
2. Keep IDs stable when only wording or rubric changes.
3. Add revision context when meaning changes materially.
4. Preserve legacy assertions unless proven wrong.
5. Audit and export targeted evaluator views.

Useful commands:

```bash
python3 eval_datasets/scripts/audit_testset_balance.py \
  eval_datasets/canonical/example.v1.json
```

```bash
python3 eval_datasets/scripts/export_promptfoo_tests.py \
  eval_datasets/canonical/example.v1.json \
  eval_datasets/exports/example.yaml \
  --include-status accepted
```

## Returned Eval Absorption

When evaluator results arrive:

1. Preserve or reference raw output under `eval_datasets/runs/<adapter>/<run_id>/`.
2. Normalize observations when possible.
3. Route observations before prompt mutation, canonical promotion, or dataset
   generation.
4. Classify failures as prompt issue, rubric issue, case issue, taxonomy gap,
   noisy eval, acceptable variance, overfit pressure, or failure-pattern gap.
5. Compress into one primary outcome and update state only when that outcome
   should affect the next loop.

Promptfoo example:

```bash
python3 eval_datasets/scripts/normalize_promptfoo_results.py \
  path/to/promptfoo_result.json \
  --output eval_datasets/runs/promptfoo/example_run/observations.json \
  --project example_project \
  --run-id example_run
```

```bash
python3 eval_datasets/scripts/route_hl_observations.py \
  eval_datasets/runs/promptfoo/example_run/observations.json \
  eval_datasets/runs/promptfoo/example_run/route.json
```

## Candidate Generation

Create new testsets only when the signal is repeated, judgeable, useful, and
not better handled by rubric/case revision or acceptable variance.

Generate small candidate units in the experiment layer. Validate them before
recording successful learning outcomes.

```bash
python3 eval_datasets/scripts/validate_hl_dataset_candidate_units.py \
  eval_datasets/experiments/example/dataset_candidate_units
```

For non-conversation units, pass the active profile and preferably
`--profile-ref`; do not let the conversation-role default stand in for another
domain.

## Optimization Without Dataset Generation

When a project already has local outputs, review summaries, diagnostics, and
human judgment, do not force immediate dataset creation.

Use:

- `eval_datasets/runs/<adapter>/<run_id>/manifest.json`
- `human_signals.jsonl`
- `decision.json`
- optional `observations.json` and `route.json`

Capture user judgment in the user's wording. If the agent is only inferring a
signal from artifacts, use `source_type=agent_inference` and
`needs_review=true`.

## Doc Routing

- Start with `README.md` for project orientation.
- Use `eval_datasets/methodology/README.md` to choose deeper reference docs.
- Use `eval_datasets/scripts/README.md` to understand script support levels.
- Use `eval_datasets/profiles/<profile>/README.md` for profile-specific schema
  and rubric terms.
- Use `eval_datasets/adapters/<adapter>/README.md` for evaluator-specific file
  assumptions.

## Quick Checks

```bash
npm test
npm run py-compile
git diff --check
```
