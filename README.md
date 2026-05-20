# Role Evaluation Dataset

`role-eval-dataset` is a lightweight toolkit for maintaining promptfoo-based
role evaluation datasets.

The name is intentionally about **datasets**, not a database product:

- **role**: the main target is character / persona / conversational role prompts.
- **eval**: records are used to inspect whether a role behaves naturally,
  usefully, and consistently.
- **dataset**: JSON records are the editable source of truth; promptfoo YAML
  files are generated views.

The goal is not to maximize pass rate at all costs. The goal is to keep a role
inside an acceptable experience band while avoiding prompt bloat and overfitting.

It includes:

- `skills/role-eval-dataset/SKILL.md`: an agent-readable workflow skill.
- `role_eval/testsets/methodology/`: schema, taxonomy, heuristic-learning, and
  review guidance.
- `role_eval/testsets/scripts/`: generic import, export, audit, replay, reward,
  and validation tools.
- `role_eval/testsets/tests/`: script-level regression tests.

It intentionally does not include project data:

- no canonical role datasets
- no promptfoo exports
- no eval results
- no replay outputs
- no private prompts or environment files

## What This Is For

Use this as a shared base for four jobs:

1. Feed old tests and references into a traceable dataset.
2. Maintain existing role evaluation records.
3. Generate new candidate testsets from feedback or coverage gaps.
4. Absorb returned evaluation results, such as promptfoo outputs, without
   blindly adding more prompt rules.

It is currently scoped to role conversation evaluation. Non-role datasets can
reuse some scripts and layering ideas, but should use separate schemas, rubrics,
and promotion rules.

## Repository Layout

```text
skills/role-eval-dataset/
  SKILL.md                 # Agent-readable workflow skill

role_eval/testsets/
  methodology/             # Shared schema, taxonomy, HL, and review guidance
  scripts/                 # Import/export/audit/replay/validation tools
  tests/                   # Regression tests for the scripts
  canonical/               # Local canonical JSON datasets; intentionally empty
  exports/                 # Generated promptfoo YAML views; intentionally empty
  seeds/                   # Imported source snapshots; intentionally empty
  experiments/             # HL candidate units and assessments; intentionally empty
  replay/                  # Replay configs, contexts, and outputs
  evolution/               # Event logs and failure patterns
```

### About `skills/`

The `skills/` directory is intentionally tool-agnostic. It stores the workflow
instructions as plain Markdown so Cursor, Codex, Claude, or a human maintainer
can read or adapt them.

It is not where dataset records live. The actual dataset system lives under
`role_eval/testsets/`. If a specific editor or agent runtime needs a different
skill location, copy or symlink `skills/role-eval-dataset/SKILL.md` into that
runtime's expected path.

## Installation

This is an agent-native toolkit. Install the skill folder into the skill
directory used by your agent runtime.

```bash
mkdir -p .agents/skills
cp -R skills/role-eval-dataset .agents/skills/
```

For Cursor, Codex, Claude, or another agent runtime, use that tool's expected
skill directory and keep the same folder shape:

```text
<tool-skill-root>/role-eval-dataset/SKILL.md
```

The skill is plain Markdown. It gives the agent operating rules for role eval
dataset work, but it does not install data by itself. The bundled methodology
and scripts are tools the agent can use after the repository is present in a
project.

## Basic Workflow

1. Keep raw promptfoo YAML unchanged.
2. Import or author canonical JSON records under `role_eval/testsets/canonical/`.
3. Review records before promotion; broad imports are intake pools, not gates.
4. Export promptfoo YAML views into `role_eval/testsets/exports/`.
5. Run promptfoo with your project config.
6. Convert failures into observations, candidate units, rubric revisions, or
   retirements.
7. Stop tuning when the role is inside the acceptable band; do not add prompt
   constraints just to satisfy low-value failures.

## Capabilities

### Feed Old Tests And References

Use this when you have existing promptfoo YAML, legacy `test*.yaml`, old
canonical files, human notes, or eval results that should become structured
dataset material.

Typical actions:

- Import legacy promptfoo tests into JSON while preserving `vars`,
  `input_var`, `source_path`, `source_index`, and `legacy_asserts`.
- Keep broad imports as intake pools. Do not treat them as reviewed gates.
- Mark unclear, empty, or mismatched records as `candidate` or
  `needs_revision`, not `accepted`.

Useful scripts:

```bash
python3 role_eval/testsets/scripts/import_promptfoo_tests.py \
  path/to/test.yaml \
  role_eval/testsets/seeds/example.from_legacy.json \
  --project example_project \
  --role example_role

python3 role_eval/testsets/scripts/batch_import_test_yaml.py \
  . \
  role_eval/testsets/canonical/all_existing_role_tests.v1.json \
  --project all_existing_roles
```

### Maintain Existing Datasets

Use this when editing canonical records, changing review status, cleaning
metadata, retiring noisy cases, or regenerating promptfoo views.

Typical actions:

- Edit canonical JSON, not generated exports.
- Keep record IDs stable unless the sample becomes a different test.
- Promote to `accepted` only with role fit, judgeable behavior, source
  traceability, and evidence.
- Use `retired` instead of deleting records that should not run anymore.

Useful scripts:

```bash
python3 role_eval/testsets/scripts/audit_testset_balance.py \
  role_eval/testsets/canonical/example.v1.json

python3 role_eval/testsets/scripts/export_promptfoo_tests.py \
  role_eval/testsets/canonical/example.v1.json \
  role_eval/testsets/exports/example.yaml \
  --include-status accepted
```

### Generate New Candidate Testsets

Use this when promptfoo failures, human review, or coverage gaps suggest new
tests. Do not jump straight from a failure to a prompt rule. Create a small,
reviewable candidate unit first.

Typical actions:

- Diagnose whether the signal is generic, role-specific, both, or noisy.
- Generate a small contrast set rather than one isolated case.
- Validate candidate units before replay.
- Keep generation in the experiment layer until evidence justifies canonical
  changes.

Useful scripts:

```bash
python3 role_eval/testsets/scripts/validate_hl_dataset_candidate_units.py \
  role_eval/testsets/experiments/example/dataset_candidate_units

python3 role_eval/testsets/scripts/select_hl_pilot_candidates.py \
  role_eval/testsets/canonical/example.v1.json \
  role_eval/testsets/experiments/example/review_batch.json \
  --limit 20
```

### Absorb Returned Evaluations

Use this after running promptfoo or another evaluator. The goal is to convert
results into dataset decisions, not to chase every failed assertion.

Typical actions:

- Treat promptfoo results as evidence for diagnosis, reward assessment, rubric
  revision, candidate generation, retirement, or `accept_variance`.
- Distinguish prompt failures from rubric failures, case failures, noisy evals,
  acceptable variance, and overfit pressure.
- Stop tuning when the role is inside the acceptable band.
- Do not use dry-run replay as promotion evidence.

Useful scripts:

```bash
python3 role_eval/testsets/scripts/validate_hl_observations.py \
  role_eval/testsets/replay/outputs/example.observations.json

python3 role_eval/testsets/scripts/score_hl_mutation.py \
  role_eval/testsets/replay/outputs/example.observations.json \
  role_eval/testsets/experiments/example/reward_assessments/example.reward.json \
  --mutation-id example_mutation
```

### Other Supporting Tasks

- Validate failure pattern files.
- Keep an append-only evolution event log.
- Maintain role-specific failure models.
- Use lightweight replay only when full promptfoo execution is too heavy.
- Keep private datasets, prompts, and large eval outputs outside this shared
  repository.

## Quick Checks

```bash
npm install
python3 -m py_compile role_eval/testsets/scripts/*.py
python3 -m unittest role_eval.testsets.tests.test_scripts
```

## Data Policy

This repository is meant to share protocol and tooling first. Keep private or
large project data outside the repo, or in ignored local directories.

The `.gitignore` keeps these data directories empty by default:

- `role_eval/testsets/canonical/`
- `role_eval/testsets/exports/`
- `role_eval/testsets/results/`
- `role_eval/testsets/seeds/`
- `role_eval/testsets/experiments/`
- `role_eval/testsets/replay/outputs/`
- `role_eval/testsets/evolution/events.jsonl`

## Data Boundary

Raw and intake data may be incomplete, but must remain traceable. Core, gate,
and accepted records should require usable input, judgeable behavior, source
traceability, and promotion evidence.

Dry-run replay validates wiring only. It is not reward evidence and should not
be used to promote records.

## Prompt Bloat Guardrail

A failed test is not automatically a reason to add prompt constraints. Before
tuning a role prompt, decide whether the failure is meaningful, repeated,
natural, and worth the added stiffness.

Prefer `accept_variance`, `revise_rubric`, `needs_revision`, or `retired` when a
case pressures the prompt toward rigid, over-specific behavior.
