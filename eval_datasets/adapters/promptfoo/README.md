# Promptfoo Adapter

Promptfoo is the bundled default evaluator adapter. It is an example and a
working path, not a framework requirement.

Adapter-owned concepts include:

- Promptfoo YAML test lists.
- `vars`
- `assert`
- `metadata`
- `input_var`
- `legacy_asserts`
- Promptfoo result normalization.

Current reference scripts:

- `eval_datasets/scripts/import_promptfoo_tests.py`
- `eval_datasets/scripts/export_promptfoo_tests.py`
- `eval_datasets/scripts/batch_import_test_yaml.py`
- `eval_datasets/scripts/normalize_promptfoo_results.py`

When adding a different evaluator, create a separate adapter instead of forcing
its file shape into Promptfoo fields.

## Import Notes

Broad YAML import should use `--include-role` or `--exclude-role` when a source
tree contains experiments, non-target roles, or unrelated test fixtures.

The Promptfoo test importer maps common metadata aliases:

- `scene_type`, `scene`, `dimension`, `category`, `task_type` -> `scene_type`
- `rubric_ref`, `rubric`, `dimension` -> `rubric_ref`
- `question`, `user_input`, `input`, `message`, `text` -> record input

If these mappings do not describe a project, create a project adapter rather
than overloading the bundled one.

## Result Normalization

Use `normalize_promptfoo_results.py` to turn full Promptfoo JSON exports or
failure summary JSON into observations under `eval_datasets/runs/`.

The normalizer is intentionally conservative. It summarizes pass/fail by role,
scene, and prompt variant, but does not create failure patterns or prompt
mutations by itself.
