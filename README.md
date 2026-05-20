# Role Evaluation Dataset

This package contains the shareable protocol and tools for maintaining
promptfoo-based role evaluation datasets.

It includes:

- `.cursor/skills/role-eval-dataset/SKILL.md`: the agent workflow skill.
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

## Intended Use

Use this as a lightweight shared base for role prompt evaluation datasets. Keep
local or private data in the empty `role_eval/testsets/*` data directories, then
use the scripts to import legacy promptfoo YAML, export generated promptfoo
views, audit records, and validate heuristic-learning artifacts.

## Quick Checks

```bash
npm install
python3 -m py_compile role_eval/testsets/scripts/*.py
python3 -m unittest role_eval.testsets.tests.test_scripts
```

## Data Boundary

Raw and intake data may be incomplete, but must remain traceable. Core, gate,
and accepted records should require usable input, judgeable behavior, source
traceability, and promotion evidence.

Dry-run replay validates wiring only. It is not reward evidence and should not
be used to promote records.
