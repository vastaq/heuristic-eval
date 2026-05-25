# Legacy Learning Import

Legacy content should enter the heuristic eval system as evidence and memory,
not as final truth. Importing old files must never directly accept records,
mutate prompts, or promote release gates.

## Three Import Streams

### Old Test Assets

Typical sources:

- Old canonical JSON datasets.
- Promptfoo YAML exports.
- Project-local dataset JSON files.

Default destination:

- `eval_datasets/seeds/` for source snapshots or partial migrations.
- `eval_datasets/canonical/` only after conversion into candidate records.
- `eval_datasets/exports/` only for generated evaluator views.

Rules:

- Converted records start as `candidate`.
- Preserve `source_path`, `source_id`, `source_index`, `legacy_asserts`, and
  evaluator variables such as Promptfoo `vars`.
- Do not mark records `accepted` during import.

### Old Evaluation Results

Typical sources:

- Promptfoo result JSON or JSONL.
- Full run result folders.
- Retest outputs.
- Prompt simplification experiment results.

Default destination:

```text
eval_datasets/runs/<evaluator>/<run_id>/
  raw/
  observations.json
  summary.md
  decision.json
```

Rules:

- Raw files may be copied or referenced by manifest if too large or private.
- Normalize pass/fail, role, scene, reason, output, judge score, and prompt
  variant when available.
- Summarize pass rate by role, failure rate by scene, repeated failure types,
  judge noise, and prompt variant comparisons.
- Do not convert one failed run directly into prompt constraints.

### Old Experience And Summaries

Typical sources:

- `eval_summary.md`
- audit notes
- failure summaries
- decisions formed in conversations

Default destination:

- `eval_datasets/evolution/failure_patterns/`
- `eval_datasets/experiments/<id>/learning_state.v1.json`
- `eval_datasets/evolution/events.jsonl`

Rules:

- Compress summaries into failure pattern candidates, rubric/case issues,
  acceptable variance decisions, stop-tuning decisions, or compact candidates.
- Do not import prose line by line.
- Keep conclusions as `needs_human_review` unless evidence is linked.

## Bootstrap Importer

Use `eval_datasets/scripts/import_legacy_learning.py` to discover old assets and
create a conservative bootstrap package:

```bash
python3 eval_datasets/scripts/import_legacy_learning.py \
  path/to/old/results path/to/old/tests \
  --output-dir eval_datasets/experiments/legacy_bootstrap \
  --project example_project
```

The script writes:

```text
manifest.json
learning_state.v1.json
summary.md
decision.json
```

The default decision is `needs_human_review`. The learning state points the next
agent toward normalization, replay, candidate review, or failure-pattern
compression.

## Recommended Tapdoki-Style Sequence

Prefer high-signal structured assets before broad YAML imports:

1. Normalize an old canonical JSON dataset into candidate records with
   `source_path`, `source_index`, and `source_id`.
2. Normalize full evaluator result JSON or failure summary JSON into
   observations under `eval_datasets/runs/<evaluator>/<run_id>/`.
3. Use observations to create candidate failure patterns or stop-tuning
   decisions.
4. Only then revisit broad legacy YAML imports, using role include/exclude
   filters and metadata mapping.

Useful commands:

```bash
python3 eval_datasets/scripts/normalize_legacy_canonical.py \
  path/to/character_eval_dataset.v1.json \
  eval_datasets/canonical/character_eval_dataset.candidate.json \
  --project example_project
```

```bash
python3 eval_datasets/scripts/normalize_promptfoo_results.py \
  path/to/full_result.json path/to/failure_summary.json \
  --output eval_datasets/runs/promptfoo/example_run/observations.json \
  --project example_project \
  --run-id example_run
```

Use broad YAML import with role filters when the source tree contains unrelated
experiments or non-target roles:

```bash
python3 eval_datasets/scripts/batch_import_test_yaml.py \
  path/to/project \
  eval_datasets/seeds/project_yaml_import.json \
  --project example_project \
  --include-role star \
  --include-role dreamer
```

## Hard Boundary

Legacy import is not:

- `accepted`
- prompt mutation
- gate promotion
- proof that an old judge was correct

Default imported state:

- Test records: `candidate`.
- Failure patterns: candidate pattern or `needs_human_review`.
- Experiment conclusion: `needs_human_review`, `accept_variance`, or
  `stop_tuning` only with linked evidence.
- Next action: replay, human review, rubric revision, case revision, or
  failure-pattern compression.
