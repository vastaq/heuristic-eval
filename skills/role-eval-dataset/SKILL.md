---
name: role-eval-dataset
description: Use when creating, updating, importing, exporting, auditing, or evolving reusable character role evaluation datasets in this project, especially work involving role_eval/testsets, canonical test JSON, promptfoo YAML tests, new role coverage, candidate/accepted review status, or legacy test*.yaml migration.
---

# Role Evaluation Dataset

## Overview

Treat `role_eval/testsets` as a file-backed dataset system for role prompt
evaluation in promptfoo workflows. Canonical JSON is the editable source of
truth. Promptfoo YAML exports are generated views. Legacy `test*.yaml` files are
source material, not the long-term dataset.

This skill also acts as the evolution protocol for user-facing conversation role
tests. Its job is to preserve raw evaluation assets, distill reusable
conversation-core records, and keep role-specific failure modes traceable.

Use the heuristic-learning controller when promptfoo failures, human review, or
cross-role signals should change the dataset over time. Do not jump directly
from an observation to adding cases or prompt rules. First inspect the current
learning state, decide the action, define replay, score reward, check
prompt-bloat risk, then compress the result.

## Dataset Layout

Use these paths:

| Path | Purpose |
| --- | --- |
| `role_eval/testsets/canonical/all_existing_role_tests.v1.json` | Broad legacy intake dataset across existing role test YAML files |
| `role_eval/testsets/canonical/*.json` | Focused canonical datasets for specific projects or roles |
| `role_eval/testsets/exports/*.yaml` | Generated promptfoo test views |
| `role_eval/testsets/seeds/*.json` | Source snapshots or partial migrations |
| `role_eval/testsets/methodology/*.md` | Schema, taxonomy, rubric, and update guidance |
| `role_eval/testsets/scripts/*.py` | Import, export, and audit tools |
| `role_eval/testsets/evolution/events.jsonl` | Append-only event log for test asset evolution |
| `role_eval/testsets/evolution/failure_patterns/*.json` | Role or project failure models |
| `role_eval/testsets/experiments/*/learning_state*.json` | Compact state snapshots for active heuristic-learning loops |
| `role_eval/testsets/experiments/*/dataset_candidate_units/*.json` | Experiment-layer units for constructing candidate datasets from observations |
| `role_eval/testsets/experiments/*/reward_assessments/*.reward.json` | Reward assessments for replay observations and mutations |
| `role_eval/testsets/replay/configs/*.yaml` | Lightweight HL replay executor configs |
| `role_eval/testsets/replay/contexts/*.yaml` | Context assembly configs for HL replay |
| `role_eval/testsets/replay/outputs/*.observations.json` | Structured replay observations for reward assessment |
| `role_eval/testsets/manifests/**/*.json` | Dataset, experiment, and release gate selections |

Do not hand-edit generated exports when the canonical record should change.

## Core Rules

- Preserve source traceability: keep `source_path`, `source_index`, and
  `legacy_asserts`.
- Preserve promptfoo compatibility: keep `input_var` and the original `vars`
  block so `question`, `user_input`, and extra contexts survive export.
- New or imported records start as `candidate`.
- Promote to `accepted` only after reviewing role fit, scenario quality, and
  rubric fairness.
- Use `needs_revision` for useful but noisy tests. Use `retired` instead of
  deleting obsolete tests.
- Do not copy another role's props blindly. Reuse scenario structure, not nouns.
- Before adding or promoting a record, decide whether it tests a generic
  conversation behavior or a role/project-specific failure mode.
- Keep raw assets traceable. Do not compress away `vars`, legacy assertions, or
  source links just because the current export does not need them.
- Do not optimize only for maximum pass rate. Optimize for a stable acceptable
  band: natural, useful, role-consistent, and not over-constrained.
- A failed case is not automatically a prompt change. Before adding prompt
  constraints, decide whether the failure is meaningful, reusable, severe, and
  worth the added stiffness.
- Prefer revising, lowering confidence on, or retiring narrow tests over adding
  prompt rules that make simple conversations rigid.

## Evolution Layers

Use these layers to control context while preserving information:

| Layer | Meaning |
| --- | --- |
| Raw Asset | Original YAML, old canonical files, eval results, and human notes. Preserve rather than clean aggressively. |
| Intake | Normalized `candidate` records with source lineage and promptfoo compatibility fields. |
| Core | Small balanced conversation tests reusable across projects and roles. |
| Project Extension | Role-family or project-specific tests, such as Tapdoki or Slowpoke failure modes. |
| Experiment | Trial rubrics, taxonomies, failure packs, and assertions. They must prove value before entering core or gates. |
| Gate | Accepted records selected for release or CI. |

See `role_eval/testsets/methodology/evolution_protocol.md` for the full
absorption workflow.
Use `role_eval/testsets/methodology/conversation_core_taxonomy.md` for generic
conversation-core dimensions, `role_eval/testsets/methodology/evolution_event_log.md`
for event logging, and `role_eval/testsets/methodology/experiment_modules.md`
for experiment module rules. Use
`role_eval/testsets/methodology/heuristic_learning_loop.md` when feedback should
drive an observe/diagnose/mutate/replay/reward/compress cycle.
Use `role_eval/testsets/methodology/heuristic_system_spec.md` when the task is
about the self-updating system itself: state, action space, reward model, replay
policy, and compression policy.
Use `role_eval/testsets/methodology/hl_replay_executor.md` when a small replay
should produce structured observations for reward assessment.
Use `role_eval/testsets/methodology/hl_dataset_generation.md` when constructing
candidate datasets from observations or diagnosis.
Use `role_eval/testsets/methodology/hl_reward_assessment.md` when deciding
whether a replay mutation should be kept, revised, compressed, or retired.

## Learning Controller Workflow

When the task involves system evolution, eval feedback, role-test learning, or
core/failure-model updates, run this controller before editing assets:

1. Inspect current learning state if one exists, such as
   `role_eval/testsets/experiments/hl_pilot/learning_state.v1.json`.
2. Identify the observation type: eval failure, human review, legacy asset,
   cross-project replay, rubric disagreement, coverage gap, or validator
   failure.
3. Classify the signal as generic, project-specific, both, or noisy.
4. Choose the smallest allowed action from the action space in
   `heuristic_system_spec.md`.
5. Define the replay memory that can test the claim.
6. Decide which reward signals matter before making the mutation, including
   naturalness, acceptable variance, and prompt-bloat risk.
7. Mutate in the experiment layer first unless evidence justifies canonical
   change.
8. Compress into one primary outcome: core candidate, project extension, failure
   pattern, rubric revision, accept variance, stop tuning, needs revision, or
   retired.
9. Append an event explaining the decision.

If the task cannot answer state, action, replay, reward, and compression, keep
the result as an experiment and do not promote.

## Promptfoo Test Generation And Replay

The primary execution path is Promptfoo test generation:

1. Create or update canonical-compatible candidate records.
2. Export Promptfoo YAML views from canonical or experiment records.
3. Run Promptfoo with the project config when full prompt/test compatibility is
   needed.
4. Treat Promptfoo results as evidence for diagnosis, reward assessment, and
   compression decisions.

Use the lightweight HL replay executor only as an optional project-local replay
path when the goal is to produce small structured observations without the full
Promptfoo runner.

Optional HL replay flow:

1. Select a replay batch or candidate slice.
2. Create or reuse a config in `role_eval/testsets/replay/configs/`.
3. Create or reuse a context config in `role_eval/testsets/replay/contexts/`.
4. Run `role_eval/testsets/scripts/run_hl_replay.py`.
5. Validate the output with
   `role_eval/testsets/scripts/validate_hl_observations.py`.
6. Treat the observation file as evidence for reward assessment, not as a
   promotion decision.

Useful commands:

```bash
python3 role_eval/testsets/scripts/run_hl_replay.py \
  role_eval/testsets/replay/configs/hl_pilot_core.dry_run.yaml \
  --dry-run
```

```bash
python3 role_eval/testsets/scripts/validate_hl_observations.py \
  role_eval/testsets/replay/outputs/hl_pilot_core.dry_run.observations.json
```

## Dataset Generation

Do not create new tests as isolated records when the task is part of the HL
system. Create a dataset candidate unit first:

1. Record the trigger observation or review.
2. Diagnose whether the signal is generic, project-specific, both, or noisy.
3. Write the `dataset_intent`.
4. Generate a small contrast set of canonical-compatible candidate records.
5. Validate with `validate_hl_dataset_candidate_units.py`.
6. Replay the unit or a derived batch.
7. Score replay observations with `score_hl_mutation.py`.
8. Compress only after reward assessment and human review.

Useful commands:

```bash
python3 role_eval/testsets/scripts/validate_hl_dataset_candidate_units.py \
  role_eval/testsets/experiments/hl_pilot/dataset_candidate_units
```

```bash
python3 role_eval/testsets/scripts/score_hl_mutation.py \
  role_eval/testsets/replay/outputs/hl_pilot_core.dry_run.observations.json \
  role_eval/testsets/experiments/hl_pilot/reward_assessments/hl_pilot_core_dry_run.reward.json \
  --mutation-id hl_pilot_core_dry_run
```

## Generic vs Role-Specific Decision

For every new case, eval failure, or legacy asset, ask:

1. Would this failure matter for many user-facing conversation roles?
2. Or does it only make sense for this role's perception axis, style, or lore?

Route the asset this way:

- Generic conversation issue -> `conversation_core` candidate.
- Role-specific issue -> project dataset or role failure model.
- Both -> add a generic core record and a linked project-specific variant.
- Noisy but promising -> `needs_revision`.
- Duplicative, obsolete, or misleading -> `retired`.

Common generic dimensions include emotional reception, lightweight practical
help, identity boundary, context carryover, natural style, anti-template
behavior, and safe refusal. Role-specific dimensions include perception-axis
collapse, prop stuffing, borrowed imagery, project lore drift, and known failure
modes unique to one role family.

## New Role Workflow

1. Inspect comparable roles in `role_eval/testsets/canonical/` and the new
   role's prompt files.
2. Define the role axis:

   ```text
   This role understands human experience through [perception axis], not through [literal props].
   ```

3. Query existing records for similar scenes, boundaries, and risks before
   writing new tests.
4. Create 5-10 `candidate` smoke records first.
5. Cover these buckets before expanding:
   - `core_smoke`
   - `micro_narrative`
   - `tiny_practical`
   - `boundary_regression`
   - `identity_boundary`
   - `context_drift`
   - `small_joy`
6. Export a role-specific promptfoo YAML view.
7. Run eval, inspect outputs, then update record status and rubrics.

## Eval Failure Learning

When an eval fails, do not only tune the prompt. Classify the failure:

- Prompt failure: the role should change, and the case may become a regression.
- Rubric failure: the judge rewarded or punished the wrong behavior; revise the
  rubric or mark the record `needs_revision`.
- Case failure: the input or target behavior is unclear; revise or retire it.
- Taxonomy failure: the scenario reveals a missing generic dimension or
  role-specific failure mode.
- Acceptable variance: the answer is not ideal, but still within the role's
  usable conversation band; do not tune the prompt for this alone.
- Overfit pressure: fixing the case would require a narrow or stiff prompt rule;
  prefer revising or retiring the case unless the failure is severe and repeated.

If the failure is reusable, add or update a canonical candidate and record the
reason in notes or the evolution event log. Do not promote based on a single
uninspected model output.

For repeated or ambiguous feedback, follow the heuristic-learning loop:
observe the failure, diagnose the layer, mutate the smallest useful asset,
replay against a small batch, inspect reward quality, then compress the result
into core, project extension, failure model, rubric revision, or retirement.

If an active learning state exists, update it after meaningful compression so
the next loop sees what changed, what remains blocked, and which replay target
should come next.

Stop tuning when core identity, boundary, and naturalness are stable and the
remaining failures are low-severity style disagreements. Do not make the prompt
more rigid just to pass a few more narrow tests.

## Updating Existing Testsets

When adding or revising tests:

1. Edit canonical JSON, not `exports/*.yaml`.
2. Keep IDs stable when only wording or rubric changes.
3. Add `revision` when a sample changes materially.
4. Keep old hard checks in `legacy_asserts` unless they are proven wrong.
5. Re-export the YAML view.
6. Run audit and targeted eval.

When updating because of an eval or user feedback, preserve the reason:

- Add `revision` when wording, target behavior, avoid behavior, or rubric
  meaning changes materially.
- Keep old hard checks in `legacy_asserts` unless proven wrong.
- Prefer appending an evolution event over overwriting history in-place.

Useful commands:

```bash
python3 role_eval/testsets/scripts/batch_import_test_yaml.py \
  . \
  role_eval/testsets/canonical/all_existing_role_tests.v1.json \
  --project all_existing_roles
```

```bash
python3 role_eval/testsets/scripts/export_promptfoo_tests.py \
  role_eval/testsets/canonical/all_existing_role_tests.v1.json \
  role_eval/testsets/exports/all_existing_role_tests.yaml \
  --include-status candidate
```

```bash
python3 role_eval/testsets/scripts/audit_testset_balance.py \
  role_eval/testsets/canonical/all_existing_role_tests.v1.json
```

## Query Patterns

For large canonical files, do not read the whole file unless necessary. Prefer
small scripts or targeted searches.

Examples:

```bash
python3 - <<'PY'
import json
from collections import Counter
data=json.load(open("role_eval/testsets/canonical/all_existing_role_tests.v1.json"))
print(Counter(r["role"] for r in data["records"]).most_common())
PY
```

```bash
python3 - <<'PY'
import json
role="slowpoke"
data=json.load(open("role_eval/testsets/canonical/all_existing_role_tests.v1.json"))
for r in data["records"]:
    if r["role"] == role and r["review_status"] == "candidate":
        print(r["id"], r["source_path"], r["input"][:80])
PY
```

## Review Checklist

Before marking a record `accepted`, verify:

- The input sounds like a real user message.
- The sample tests role perception, not costume props.
- The target behavior is judgeable.
- The avoid behavior catches real failure modes.
- The original hard assertions still make sense.
- The record has useful `layer`, `scene_type`, `difficulty`, and `tags`.
- Similar accepted records are not duplicates.
- There is evidence for promotion: human review, repeated eval failure, a stable
  regression signal, or a link to a known failure model.
- The record is not an experiment-only module being promoted prematurely.
- Passing or failing the record would not push the prompt toward excessive
  constraints, keyword stuffing, or over-performed role flavor.

## Experiment Module Rules

New rubrics, taxonomies, hard assertions, and failure packs start as experiments.
Use them against candidate pools first. Promote them only when they:

- Catch a meaningful failure without rewarding keyword stuffing.
- Do not overfit to one project unless intentionally project-specific.
- Produce inspectable evidence from eval runs or human review.
- Have a clear retirement path if they create noise.

## Common Mistakes

- Editing `exports/*.yaml` and forgetting to update canonical.
- Re-importing legacy YAML and overwriting reviewed statuses.
- Flattening all inputs into `question` when a prompt expects `user_input`.
- Dropping extra `vars` such as shared context files.
- Treating `legacy_import` as finished classification.
- Optimizing pass rate before inspecting representative outputs.
- Adding prompt rules for every failed case instead of accepting reasonable
  variance or revising noisy tests.
- Overfitting a prompt to pass a narrow case while making ordinary conversation
  stiffer.
- Letting project-specific datasets redefine the generic conversation core.
- Promoting experiment records into release gates without evidence.
- Losing raw source details while trying to make records cleaner.
- Adding local test assets when the real missing piece is state, policy, reward,
  replay, or compression.
- Treating the event log as learning by itself; it is memory, not the controller.

## Output Summary Format

When reporting work on this dataset system, include:

```markdown
## Coverage
- Source files:
- Records:
- Roles:
- Accepted / candidate / needs_revision / retired:

## Changes
- ...

## Verification
- ...

## Remaining Classification Work
- ...
```
