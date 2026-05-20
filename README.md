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

Use this as a shared base when you want to:

- Import legacy `test*.yaml` promptfoo cases into traceable canonical JSON.
- Curate role conversation tests through `candidate`, `accepted`,
  `needs_revision`, and `retired` states.
- Export canonical records back into promptfoo YAML.
- Learn from promptfoo failures without automatically adding more prompt rules.
- Track reusable failure patterns, replay observations, and reward assessments.

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
