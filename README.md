# Heuristic Evaluation Dataset

`heuristic-eval-dataset` is a small file-backed toolkit for turning evaluation
feedback into maintainable evidence, decisions, and datasets. It gives agents a
shared workflow for importing old tests, curating canonical records, generating
new candidate cases, absorbing evaluator results, and deciding when to revise,
retire, accept variance, or stop tuning.

This repository is not only a skill package. The skill under `skills/` is one
agent-readable entrypoint into a larger project structure:

- `eval_datasets/` is the actual dataset, run-intake, methodology, template, and
  script workspace.
- `skills/heuristic-eval-dataset/SKILL.md` tells an agent how to use that
  workspace.
- `README.md` is the human and repository-level orientation.

It is designed for prompt and agent behavior evaluation where failures should
improve the dataset and rubric over time, not simply add more prompt
constraints.

The name is intentionally about **datasets**, not a database product:

- **heuristic**: agents use feedback to update datasets, rubrics, replay plans,
  and compression decisions rather than only chasing pass rate.
- **eval**: records inspect whether a prompt, role, or agent behavior stays
  inside an acceptable experience band.
- **dataset**: JSON records are the editable source of truth; evaluator-specific
  files, such as Promptfoo YAML, are generated views.

The toolkit is evaluator-agnostic. Promptfoo is the bundled default adapter,
example path, and currently implemented import/export surface.

The current default profile is **conversation role eval**. That is intentional:
it keeps the schema and rubrics concrete while the heuristic-learning loop
stabilizes. Non-conversation evals should reuse the layering and feedback loop,
but should define their own schema, rubrics, and promotion rules before sharing
canonical data.

The goal is not to maximize pass rate at all costs. The goal is to keep a prompt
or role inside an acceptable experience band while avoiding prompt bloat and
overfitting.

It includes:

- `README.md`: repository-level orientation and quick start.
- `skills/heuristic-eval-dataset/SKILL.md`: an agent-readable workflow skill.
- `eval_datasets/methodology/`: framework guidance, heuristic-learning
  protocol, and bundled profile references.
- `eval_datasets/profiles/`: profile notes for eval-domain-specific schemas.
- `eval_datasets/adapters/`: adapter notes for evaluator-specific file shapes.
- `eval_datasets/templates/`: copyable manifests and decision templates for
  project-local eval loops.
- `eval_datasets/examples/`: non-private case patterns showing how to apply the
  framework without shipping project data.
- `eval_datasets/scripts/`: reference scripts for current adapters, replay,
  reward, validation, and bootstrap workflows.
- `eval_datasets/tests/`: script-level regression tests.

It intentionally does not include project data:

- no canonical datasets
- no evaluator exports
- no eval results
- no replay outputs
- no private prompts or environment files

## What This Is For

Use this repository as a shared base for six jobs:

1. Feed old tests and references into a traceable dataset.
2. Maintain existing evaluation records.
3. Generate new candidate testsets from feedback or coverage gaps.
4. Absorb returned evaluation results, such as Promptfoo outputs, without
   blindly adding more prompt rules.
5. Bootstrap learning state from legacy datasets, results, summaries, and prior
   decisions without treating them as accepted truth.
6. Capture short human judgments as heuristic memory without creating a heavy
   review workflow.

The bundled profile is currently conversation-first. Treat other domains as new
profiles, not as records mixed into the same canonical schema.

## Scope And Profiles

This repository has a generic name because the maintenance loop is generic:
preserve raw assets, normalize intake records, run evals, absorb feedback,
generate candidates, and compress decisions.

The included schema, rubrics, and most Python scripts are still intentionally
narrow. They are for conversation role evaluation first, with Promptfoo as the
bundled adapter. That prevents the project from pretending a TTS test, tool-use
benchmark, coding task, or retrieval eval has the same meaning as a user-facing
dialogue case.

Add a new profile only when it has its own:

- input and output shape
- rubric vocabulary
- promotion evidence
- acceptable-band definition
- prompt-bloat or policy-bloat guardrail

## Framework / Profile / Adapter

Use the repository in three layers:

- **Framework**: shared controller, state, run intake, reward, compression,
  stop rules, and legacy bootstrap.
- **Profile**: domain-specific schema, taxonomy, rubrics, promotion evidence,
  and acceptable band.
- **Adapter**: evaluator-specific import, export, and result normalization.

The current profile is `conversation_role`. The current adapter is `promptfoo`.
The bundled Python scripts are reference implementations for that setup, not the
universal encoding of the framework.

For a new eval domain, create a profile and adapter instead of forcing data into
conversation-role fields such as `role`, `character_context`, or `scene_type`.

See `eval_datasets/methodology/framework_profile_adapter.md`.

The repository also includes a lightweight `generative_content` profile and a
`batch_story_generation` adapter note for projects that already have their own
batch runner, LLM review, local diagnostics, and human review. That path is meant
to participate in prompt optimization without requiring immediate dataset
generation. See
`eval_datasets/methodology/eval_optimization_without_dataset_generation.md`.

## Human Signals

The project does not require a labeling queue or heavy reviewer workflow.
Instead, short human judgments can be captured as heuristic signals:

- "This feels too much like therapy."
- "The score is good enough; stop tuning."
- "This is a role-specific failure, not a generic one."

The agent should preserve the original wording, classify it, and compress it
into `accept_variance`, `stop_tuning`, `failure_pattern_candidate`,
`rubric_revision`, `case_revision`, `judge_noise`, or a next replay target.

See `eval_datasets/methodology/human_signal_capture.md`.

## Heuristic Learning Inspiration

This toolkit is inspired by
[Learning Beyond Gradients](https://trinkle23897.github.io/learning-beyond-gradients/#zh)
and the accompanying
[Trinkle23897/learning-beyond-gradients](https://github.com/Trinkle23897/learning-beyond-gradients)
repository. The useful lesson is not to optimize every score locally; it is to
keep an explicit heuristic system that can observe feedback, mutate small
assets, replay evidence, and compress the lesson into a smaller maintainable
state.

For prompt and role evals, that means a failed test can become a new candidate
case, a rubric revision, a failure pattern, a retired noisy sample, or an
`accept_variance` decision. Not every failure should become a prompt constraint.

## Repository Layout

```text
README.md
package.json

skills/heuristic-eval-dataset/
  SKILL.md                 # Optional agent-readable entrypoint

eval_datasets/
  methodology/             # Shared framework and bundled profile guidance
  profiles/                # Eval-domain-specific schema notes
  adapters/                # Evaluator-specific adapter notes
  templates/               # Copyable run/decision/human-signal templates
  examples/                # Public case patterns without private data
  scripts/                 # Reference scripts and current adapters
  tests/                   # Regression tests for the scripts
  canonical/               # Local canonical JSON datasets; intentionally empty
  exports/                 # Generated evaluator views; intentionally empty
  seeds/                   # Imported source snapshots; intentionally empty
  experiments/             # HL candidate units and assessments; intentionally empty
  runs/                    # Full evaluator run intake; intentionally empty
  replay/                  # Replay configs, contexts, and outputs
  evolution/               # Event logs and failure patterns
```

### About `skills/`

The `skills/` directory is intentionally tool-agnostic. It stores the workflow
instructions as plain Markdown so Cursor, Codex, Claude, or a human maintainer
can read or adapt them.

It is not the whole project and it is not where dataset records live. The actual
dataset system lives under `eval_datasets/`. If a specific editor or agent
runtime needs a different skill location, copy or symlink
`skills/heuristic-eval-dataset/SKILL.md` into that runtime's expected path while
keeping the repository available as the working toolkit.

## Quick Start

Clone or vendor the repository into the project that needs eval maintenance:

```bash
git clone https://github.com/vastaq/heuristic-eval-dataset.git
cd heuristic-eval-dataset
npm install
npm test
```

Then use `eval_datasets/` as the local place for run intake, profiles, adapter
notes, canonical records, templates, and scripts. Project data can stay in
ignored local directories or in the project that references this toolkit.

For an existing project that already has generated outputs or evaluator
summaries, start by creating a thin run-intake skeleton:

```bash
python3 eval_datasets/scripts/init_eval_run.py \
  --run-id example_run_001 \
  --project example_project \
  --source-root path/to/project/local/output \
  --source-file summary=path/to/project/local/output/summary.json
```

By default, this writes under `eval_datasets/runs/`, which is ignored by Git so
project-specific evidence stays local unless you choose another `--output-dir`.

## Optional Agent Skill

For agent runtimes that support skills, install the skill folder as an entrypoint
into the repository workflow:

```bash
mkdir -p .agents/skills
cp -R skills/heuristic-eval-dataset .agents/skills/
```

For Cursor, Codex, Claude, or another agent runtime, use that tool's expected
skill directory and keep the same folder shape:

```text
<tool-skill-root>/heuristic-eval-dataset/SKILL.md
```

The skill is plain Markdown. It gives the agent operating rules for heuristic eval
dataset work, but it does not install the toolkit or data by itself. The bundled
methodology and scripts are tools the agent can use after the repository is
present in a project.

## Basic Workflow

1. Keep raw evaluator inputs unchanged.
2. Import or author canonical JSON records under `eval_datasets/canonical/`.
3. Review records before promotion; broad imports are intake pools, not gates.
4. Export evaluator-specific views into `eval_datasets/exports/`.
5. Run the evaluator, such as Promptfoo, with your project config.
6. Convert failures into observations, candidate units, rubric revisions, or
   retirements.
7. Stop tuning when the role is inside the acceptable band; do not add prompt
   constraints just to satisfy low-value failures.

## Capabilities

### Feed Old Tests And References

Use this when you have existing evaluator files, Promptfoo YAML, legacy
`test*.yaml`, old canonical files, human notes, or eval results that should
become structured dataset material.

Typical actions:

- Import legacy Promptfoo tests into JSON while preserving `vars`,
  `input_var`, `source_path`, `source_index`, and `legacy_asserts`.
- Keep broad imports as intake pools. Do not treat them as reviewed gates.
- Mark unclear, empty, or mismatched records as `candidate` or
  `needs_revision`, not `accepted`.

Useful scripts:

```bash
python3 eval_datasets/scripts/import_promptfoo_tests.py \
  path/to/test.yaml \
  eval_datasets/seeds/example.from_legacy.json \
  --project example_project \
  --role example_role

python3 eval_datasets/scripts/batch_import_test_yaml.py \
  . \
  eval_datasets/canonical/all_existing_role_tests.v1.json \
  --project all_existing_roles
```

For mixed legacy folders that contain tests, eval results, and summaries, use
the bootstrap importer first:

```bash
python3 eval_datasets/scripts/import_legacy_learning.py \
  path/to/legacy/tests path/to/legacy/results \
  --output-dir eval_datasets/experiments/legacy_bootstrap \
  --project example_project
```

This writes a manifest, learning state, summary, and decision. It does not
accept records, mutate prompts, or promote gates.

When a structured old canonical JSON is available, normalize it before broad
YAML import:

```bash
python3 eval_datasets/scripts/normalize_legacy_canonical.py \
  path/to/character_eval_dataset.v1.json \
  eval_datasets/canonical/character_eval_dataset.candidate.json \
  --project example_project
```

### Maintain Existing Datasets

Use this when editing canonical records, changing review status, cleaning
metadata, retiring noisy cases, or regenerating evaluator views.

Typical actions:

- Edit canonical JSON, not generated exports.
- Keep record IDs stable unless the sample becomes a different test.
- Promote to `accepted` only with role fit, judgeable behavior, source
  traceability, and evidence.
- Use `retired` instead of deleting records that should not run anymore.

Useful scripts:

```bash
python3 eval_datasets/scripts/audit_testset_balance.py \
  eval_datasets/canonical/example.v1.json

python3 eval_datasets/scripts/export_promptfoo_tests.py \
  eval_datasets/canonical/example.v1.json \
  eval_datasets/exports/example.yaml \
  --include-status accepted
```

### Generate New Candidate Testsets

Use this when evaluator failures, human review, or coverage gaps suggest new
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
python3 eval_datasets/scripts/validate_hl_dataset_candidate_units.py \
  eval_datasets/experiments/example/dataset_candidate_units

python3 eval_datasets/scripts/select_hl_pilot_candidates.py \
  eval_datasets/canonical/example.v1.json \
  eval_datasets/experiments/example/review_batch.json \
  --limit 20
```

### Absorb Returned Evaluations

Use this after running Promptfoo or another evaluator. The goal is to convert
results into dataset decisions, not to chase every failed assertion.

Typical actions:

- Treat evaluator results as evidence for diagnosis, reward assessment, rubric
  revision, candidate generation, retirement, or `accept_variance`.
- Distinguish prompt failures from rubric failures, case failures, noisy evals,
  acceptable variance, and overfit pressure.
- Store full evaluator runs under `eval_datasets/runs/<evaluator>/<run_id>/`
  before compressing them into durable dataset changes.
- Stop tuning when the role is inside the acceptable band.
- Do not use dry-run replay as promotion evidence.

Useful scripts:

```bash
python3 eval_datasets/scripts/validate_hl_observations.py \
  eval_datasets/replay/outputs/example.observations.json

python3 eval_datasets/scripts/normalize_promptfoo_results.py \
  path/to/promptfoo_result.json \
  --output eval_datasets/runs/promptfoo/example_run/observations.json \
  --project example_project \
  --run-id example_run

python3 eval_datasets/scripts/score_hl_mutation.py \
  eval_datasets/replay/outputs/example.observations.json \
  eval_datasets/experiments/example/reward_assessments/example.reward.json \
  --mutation-id example_mutation
```

### Optimize Without Generating A Dataset

Use this when a project already has generated outputs, review summaries, and
human judgment, but does not yet need new canonical records.

Typical actions:

- Pick or create a profile, such as `generative_content`.
- Pick or create an adapter note for the project output shape.
- Store a small run manifest and decision record that point to local artifacts.
- Capture human signals that reinterpret scores or block misleading tuning.
- Keep local diagnostics as warnings unless they are supported by human or LLM
  review.

Useful starting templates:

```text
eval_datasets/templates/generative_content/run_manifest.template.json
eval_datasets/templates/generative_content/decision.template.json
eval_datasets/templates/generative_content/human_signals.template.jsonl
```

Or create a run skeleton directly:

```bash
python3 eval_datasets/scripts/init_eval_run.py \
  --run-id story_eval_001 \
  --project example_project \
  --profile generative_content \
  --adapter batch_story_generation \
  --source-root path/to/project/local/output \
  --source-file llm_review=path/to/review.json \
  --controlled-variable season \
  --content-unit example_map
```

See `eval_datasets/profiles/generative_content/README.md` and
`eval_datasets/adapters/batch_story_generation/README.md`. For a concrete
non-private pattern, see
`eval_datasets/examples/generative_content_prompt_optimization.md`.

### Other Supporting Tasks

- Validate failure pattern files.
- Keep an append-only evolution event log.
- Maintain role-specific failure models.
- Use lightweight replay only when full evaluator execution is too heavy.
- Keep private datasets, prompts, and large eval outputs outside this shared
  repository.

## Quick Checks

```bash
npm install
python3 -m py_compile eval_datasets/scripts/*.py
python3 -m unittest eval_datasets.tests.test_scripts
```

## Data Policy

This repository is meant to share protocol and tooling first. Keep private or
large project data outside the repo, or in ignored local directories.

The `.gitignore` keeps these data directories empty by default:

- `eval_datasets/canonical/`
- `eval_datasets/exports/`
- `eval_datasets/runs/`
- `eval_datasets/seeds/`
- `eval_datasets/experiments/`
- `eval_datasets/replay/outputs/`
- `eval_datasets/evolution/events.jsonl`

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

## Autonomous Controller

When new evaluator results, repeated failures, prompt growth, judge noise, user
feedback, or compact experiments appear, the agent should run the autonomous
controller before changing prompts or canonical data:

```text
observe -> read state -> classify -> choose smallest action -> bloat gate
-> replay -> reward -> compress -> update state -> next target or stop
```

See `eval_datasets/methodology/autonomous_controller.md`.

## Legacy Import Boundary

Old content enters as evidence and memory, not final truth:

- old tests -> candidate records or seeds
- old eval results -> run intake and normalized observations
- old summaries -> candidate failure patterns, state gaps, events, or stop rules

See `eval_datasets/methodology/legacy_learning_import.md`.
