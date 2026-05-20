# Updating Reusable Role Testsets

Use this workflow when adding or improving role tests. The goal is to keep old
tests available while building a reviewed, reusable canonical dataset.

## Import Existing Tests

1. Keep the original evaluator files unchanged.
2. Import it into `seeds/` with `source_path`, `source_index`, `input_var`,
   the original `vars` block, and `legacy_asserts`.
3. Promote useful records into `canonical/` as `candidate`.
4. Fill missing fields: `layer`, `scene_type`, `difficulty`, `target_behavior`,
   `avoid_behavior`, `tags`, and `rubric_ref`.

## Review A Candidate

A candidate can become `accepted` when:

- The input sounds like a real user message.
- It tests a specific role behavior or known failure mode.
- The rubric does not require one exact sentence.
- It keeps source traceability.
- It is not a duplicate of an existing accepted sample.

Use `needs_revision` when the idea is useful but the wording or rubric is noisy.
Use `retired` when the sample should not run but the history is still useful.

## Prompt Tuning Discipline

Do not treat every failed case as a reason to add prompt constraints. Before
tuning a role prompt, decide whether the failure is:

- A meaningful repeated failure that affects user experience.
- A rubric or case problem that should be revised instead.
- Acceptable variance inside the role's usable conversation band.
- Overfit pressure from a narrow test that would make the prompt stiffer.

Prefer accepting variance, revising the rubric, marking `needs_revision`, or
retiring a case when passing it would require an overly specific prompt rule.
Stop tuning when identity, boundaries, usefulness, and naturalness are stable and
remaining failures are low-severity style disagreements.

## Add A New Role

Start with a small profile:

```yaml
role: slowpoke
perception_axis: slow body signals, safe pauses, and one tiny next step
literal_props_to_avoid: leaves, branches, sleepiness, hugs
known_failures:
  - clinical advice
  - breathing as default answer
  - too many questions
neighbor_roles: []
```

Then add 5-10 `core_smoke` records before expanding into full coverage.

## Export For Evaluators

Promptfoo is the bundled default adapter, so current examples export Promptfoo
YAML. Other evaluators should get their own projection scripts instead of
changing canonical records to match a runner.

Export only `accepted` records by default. Include `candidate` records for local
exploration when tuning a prompt, but do not treat them as release gates.

Generated exports should go under `eval_datasets/exports/` and should be
treated as build artifacts. Edit canonical records instead of editing exports.

For broad legacy coverage, use the batch importer:

```bash
python3 eval_datasets/scripts/batch_import_test_yaml.py \
  . \
  eval_datasets/canonical/all_existing_role_tests.v1.json \
  --project all_existing_roles

python3 eval_datasets/scripts/export_promptfoo_tests.py \
  eval_datasets/canonical/all_existing_role_tests.v1.json \
  eval_datasets/exports/all_existing_role_tests.yaml \
  --include-status candidate
```

Batch-imported records remain `candidate` until someone reviews and classifies
their layer, scene type, difficulty, and role-specific target behavior.

## Preserve Legacy Assertions

Old tests may contain `icontains`, `icontains-any`, or JavaScript checks. Keep
them in `legacy_asserts` so migration does not weaken hard requirements. Add
canonical `target_behavior` and `avoid_behavior` around them instead of replacing
them blindly.
