---
name: heuristic-eval-dataset
description: Use when creating, updating, importing, exporting, auditing, or evolving heuristic evaluation datasets, especially conversation role evals, evaluator feedback absorption, Promptfoo adapters/examples, canonical test JSON, candidate/accepted review status, prompt-bloat control, case-by-case prompt patching, abstraction drift, eval reward-shape bias, or legacy test*.yaml migration.
---

# Heuristic Evaluation Dataset

## Overview

Use this skill to turn evaluation feedback into maintainable datasets. The
agent should import old tests, curate canonical records, generate candidate
cases, absorb evaluator results, and decide whether to revise, retire, accept
variance, stop tuning, or create a new regression case.

Treat `eval_datasets` as a file-backed dataset system for heuristic prompt and
agent-behavior evaluation. Canonical JSON is the editable source of truth.
Evaluator-specific exports, such as Promptfoo YAML, are generated views. Legacy
evaluator files are source material, not the long-term dataset.

The bundled profile is conversation role eval. Keep that profile concrete:
preserve raw evaluation assets, distill reusable conversation-core records, and
keep role-specific failure modes traceable. For non-conversation datasets, reuse
the Raw/Intake/Core/Experiment/Gate layering and heuristic-learning controller,
but define a separate schema, rubric, and promotion policy before mixing data.

Keep three layers separate:

- Framework: controller, state, run intake, reward, compression, stop rules, and
  legacy bootstrap.
- Profile: domain schema, taxonomy, rubrics, acceptable band, and promotion
  evidence.
- Adapter: evaluator import/export and result normalization.

The bundled Python scripts are reference implementations for the current
conversation-role profile and Promptfoo adapter. For a new domain or evaluator,
create a new profile or adapter instead of forcing data into conversation-role
fields.

Use the heuristic-learning controller when evaluator failures, human review, or
cross-role signals should change the dataset over time. Do not jump directly
from an observation to adding cases or prompt rules. First inspect the current
learning state, decide the action, define replay, score reward, check
prompt-bloat risk, then compress the result.

When feedback shows a prompt accumulating local `if`/`when` exceptions, treat it
as `prompt_patch_pressure`. Ask what higher-level invariant, role axis, or
decision order should replace the local repairs. If no reusable principle
emerges, block prompt mutation and prefer rubric/case review, acceptable
variance, or a failure-pattern note.

When a high-scoring prompt has many concrete-response rules, audit whether the
eval itself over-rewards one output shape, such as actions, exact phrases, lists,
or role-flavor keywords. Treat this as `eval_reward_shape_bias` before changing
the prompt again.

When a dataset or eval pack is newly generated, imported, or rebalanced, run a
dataset traction audit before using failures as prompt-tuning pressure. If the
audit flags dominant reward shape or missing countercases, revise or supplement
the eval first.

## Dataset Layout

Use these paths:

| Path | Purpose |
| --- | --- |
| `eval_datasets/canonical/all_existing_role_tests.v1.json` | Broad legacy intake dataset across existing role test YAML files |
| `eval_datasets/canonical/*.json` | Focused canonical datasets for specific profiles, projects, or roles |
| `eval_datasets/exports/*.yaml` | Generated evaluator views, with Promptfoo YAML as the default example |
| `eval_datasets/profiles/*/` | Profile-owned schema, taxonomy, rubric, and acceptable-band notes |
| `eval_datasets/adapters/*/` | Evaluator-owned import/export/result-normalization notes |
| `eval_datasets/seeds/*.json` | Source snapshots or partial migrations |
| `eval_datasets/methodology/*.md` | Schema, taxonomy, rubric, and update guidance |
| `eval_datasets/scripts/*.py` | Import, export, and audit tools |
| `eval_datasets/evolution/events.jsonl` | Append-only event log for test asset evolution |
| `eval_datasets/evolution/failure_patterns/*.json` | Role or project failure models |
| `eval_datasets/experiments/*/learning_state*.json` | Compact state snapshots for active heuristic-learning loops |
| `eval_datasets/experiments/*/dataset_candidate_units/*.json` | Experiment-layer units for constructing candidate datasets from observations |
| `eval_datasets/experiments/*/reward_assessments/*.reward.json` | Reward assessments for replay observations and mutations |
| `eval_datasets/runs/<evaluator>/<run_id>/` | Full evaluator run intake: raw output, normalized observations, summary, and decision |
| `eval_datasets/replay/configs/*.yaml` | Lightweight HL replay executor configs |
| `eval_datasets/replay/contexts/*.yaml` | Context assembly configs for HL replay |
| `eval_datasets/replay/outputs/*.observations.json` | Structured replay observations for reward assessment |
| `eval_datasets/manifests/**/*.json` | Dataset, experiment, and release gate selections |

Do not hand-edit generated exports when the canonical record should change.

## Scope And Profiles

Default to the conversation role profile unless the user explicitly asks for a
different eval domain. Do not mix non-conversation records into the conversation
canonical schema just because the import script can parse them.

For a new profile, define its input/output shape, rubric vocabulary, promotion
evidence, acceptable band, and bloat guardrail before creating canonical data.
The heuristic-learning loop is shared; the schema and rubric are profile-local.

Do not treat `eval_datasets/scripts/*.py` as the framework's required encoding.
Those scripts are working reference implementations. If their field assumptions
do not match the task, add a profile or adapter instead of warping the task into
the bundled conversation-role Promptfoo shape.

## Core Rules

- Preserve source traceability: keep `source_path`, `source_index`, and
  `legacy_asserts`.
- Preserve evaluator compatibility. For Promptfoo imports, keep `input_var` and
  the original `vars` block so `question`, `user_input`, and extra contexts
  survive export.
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
- If several failures invite separate prompt rules, pause and name the shared
  principle before editing. A good mutation replaces many local patches with a
  smaller invariant; otherwise classify the pressure as overfit or judge noise.

## Evolution Layers

Use these layers to control context while preserving information:

| Layer | Meaning |
| --- | --- |
| Raw Asset | Original YAML, old canonical files, eval results, and human notes. Preserve rather than clean aggressively. |
| Intake | Normalized `candidate` records with source lineage and evaluator compatibility fields. |
| Core | Small balanced conversation tests reusable across projects and roles. |
| Project Extension | Role-family or project-specific tests, such as Tapdoki or Slowpoke failure modes. |
| Experiment | Trial rubrics, taxonomies, failure packs, and assertions. They must prove value before entering core or gates. |
| Gate | Accepted records selected for release or CI. |

See `eval_datasets/methodology/evolution_protocol.md` for the full
absorption workflow.
Use `eval_datasets/methodology/conversation_core_taxonomy.md` for generic
conversation-core dimensions, `eval_datasets/methodology/evolution_event_log.md`
for event logging, and `eval_datasets/methodology/experiment_modules.md`
for experiment module rules. Use
`eval_datasets/methodology/heuristic_learning_loop.md` when feedback should
drive an observe/diagnose/mutate/replay/reward/compress cycle.
Use `eval_datasets/methodology/heuristic_system_spec.md` when the task is
about the self-updating system itself: state, action space, reward model, replay
policy, and compression policy.
Use `eval_datasets/methodology/framework_profile_adapter.md` before adapting the
framework to a new eval domain or evaluator.
Use `eval_datasets/methodology/autonomous_controller.md` whenever evaluator
results, repeated failures, prompt growth, user dissatisfaction, judge noise, or
compact experiments should trigger autonomous dataset iteration.
Use `eval_datasets/methodology/hl_replay_executor.md` when a small replay
should produce structured observations for reward assessment.
Use `eval_datasets/methodology/hl_dataset_generation.md` when constructing
candidate datasets from observations or diagnosis.
Use `eval_datasets/methodology/hl_reward_assessment.md` when deciding
whether a replay mutation should be kept, revised, compressed, or retired.
Use `eval_datasets/methodology/dataset_traction_audit.md` before prompt tuning
from a newly generated, imported, or suspicious eval pack.
Use `eval_datasets/methodology/legacy_learning_import.md` when old canonical
datasets, evaluator exports, run results, summaries, or prior conclusions need
to bootstrap learning state without automatically accepting records.
Use `eval_datasets/methodology/human_signal_capture.md` when the user gives a
short judgment, preference, stop rule, or strategy note that should become
heuristic memory without creating a heavy review workflow.

## Learning Controller Workflow

When the task involves system evolution, eval feedback, dataset learning, or
core/failure-model updates, run this controller before editing assets:

1. Inspect current learning state if one exists; create a lightweight state if
   none exists and the work will make durable changes.
2. Identify the observation type: eval failure, human review, legacy asset,
   cross-project replay, rubric disagreement, coverage gap, or validator
   failure.
3. Classify the signal as generic, project-specific, both, or noisy.
4. Choose the smallest allowed action from the action space in
   `heuristic_system_spec.md`.
5. Run a dataset traction audit before prompt tuning when the dataset/eval pack
   is new, rebalanced, imported, or suspected of reward-shape bias.
6. Apply the prompt-bloat gate before any prompt or policy mutation.
7. Define the replay memory that can test the claim.
8. Decide which reward signals matter before making the mutation, including
   pass rate, naturalness, role consistency, regression risk, judge noise,
   user goal, acceptable variance, and prompt-bloat risk.
9. Mutate in the experiment layer first unless evidence justifies canonical
   change.
10. Compress into one primary outcome: accept variance, failure pattern, rubric
   revision, dataset revision, compact candidate, stop tuning, needs revision,
   retired, or gate promotion.
11. Update learning state with the outcome and next replay target, or mark
   `stop_tuning`.
12. Append an event explaining the decision.

If the task cannot answer state, action, replay, reward, compression, and next
target, keep the result as an experiment and do not promote.

Mandatory triggers include new evaluator results, repeated failures, pass rate
or user satisfaction leaving the acceptable band, prompt growth, case-by-case
`if`/`when` prompt repairs, user feedback that behavior feels unnatural or
stiff, abstraction-level feedback such as principle vs technique, judge
instability, concrete-action or exact-phrase rubrics dominating a role eval,
compact experiments beating the main version, and proposed one-case prompt
rules. Also trigger on the first generated dataset for a role or project, and
on any prompt mutation proposed before a traction audit exists.

Human feedback is an observation source. Preserve the user's wording, classify
it, and compress it into a candidate outcome such as `accept_variance`,
`stop_tuning`, `failure_pattern_candidate`, `rubric_revision`, `case_revision`,
`judge_noise`, `blocked_prompt_mutation`, or a next replay target.

When prompt behavior is already inside the acceptable band, do not continue
prompt tuning for one or two narrow failures. Classify them instead.

## Evaluator Export And Replay

The dataset is evaluator-agnostic. Promptfoo is the bundled default adapter and
example path, not the only supported evaluation surface.

1. Create or update canonical-compatible candidate records.
2. Export evaluator-specific views from canonical or experiment records.
3. Run the evaluator, such as Promptfoo, with the project config when full
   prompt/test compatibility is needed.
4. Treat evaluator results as evidence for diagnosis, reward assessment, and
   compression decisions.

Use the lightweight HL replay executor only as an optional project-local replay
path when the goal is to produce small structured observations without the full
evaluator runner.

Optional HL replay flow:

1. Select a replay batch or candidate slice.
2. Create or reuse a config in `eval_datasets/replay/configs/`.
3. Create or reuse a context config in `eval_datasets/replay/contexts/`.
4. Run `eval_datasets/scripts/run_hl_replay.py`.
5. Validate the output with
   `eval_datasets/scripts/validate_hl_observations.py`.
6. Treat the observation file as evidence for reward assessment, not as a
   promotion decision.

Useful commands:

```bash
python3 eval_datasets/scripts/run_hl_replay.py \
  eval_datasets/replay/configs/hl_pilot_core.dry_run.yaml \
  --dry-run
```

```bash
python3 eval_datasets/scripts/validate_hl_observations.py \
  eval_datasets/replay/outputs/hl_pilot_core.dry_run.observations.json
```

## Legacy Learning Import

When importing old datasets, exports, eval results, or summaries, treat them as
bootstrap memory rather than trusted conclusions.

1. Discover legacy files and classify them as old test assets, old eval results,
   or old experience summaries.
2. Preserve raw files under seeds, runs, or an experiment manifest.
3. Convert tests only into candidate records.
4. Normalize old eval results into observations before reward assessment.
5. Compress summaries into candidate failure patterns, rubric/case issues,
   acceptable variance, stop-tuning decisions, or learning-state gaps.
6. Block automatic accepted status, prompt mutation, and gate promotion.

Useful command:

```bash
python3 eval_datasets/scripts/import_legacy_learning.py \
  path/to/old/tests path/to/old/results \
  --output-dir eval_datasets/experiments/legacy_bootstrap \
  --project example_project
```

If an old canonical JSON dataset already has balanced records, normalize it
before broad YAML import:

```bash
python3 eval_datasets/scripts/normalize_legacy_canonical.py \
  path/to/character_eval_dataset.v1.json \
  eval_datasets/canonical/character_eval_dataset.candidate.json \
  --project example_project
```

If old Promptfoo results or failure summaries exist, normalize them into run
observations before creating failure patterns:

```bash
python3 eval_datasets/scripts/normalize_promptfoo_results.py \
  path/to/promptfoo_result.json path/to/failure_summary.json \
  --output eval_datasets/runs/promptfoo/example_run/observations.json \
  --project example_project \
  --run-id example_run
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
python3 eval_datasets/scripts/validate_hl_dataset_candidate_units.py \
  eval_datasets/experiments/hl_pilot/dataset_candidate_units
```

```bash
python3 eval_datasets/scripts/score_hl_mutation.py \
  eval_datasets/replay/outputs/hl_pilot_core.dry_run.observations.json \
  eval_datasets/experiments/hl_pilot/reward_assessments/hl_pilot_core_dry_run.reward.json \
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

1. Inspect comparable roles in `eval_datasets/canonical/` and the new
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
6. Export a role-specific evaluator view, such as Promptfoo YAML.
7. Run eval, inspect outputs, then update record status and rubrics.

## Eval Failure Learning

When an eval fails, do not only tune the prompt. Classify the failure:

- Prompt failure: the role should change, and the case may become a regression.
- Rubric failure: the judge rewarded or punished the wrong behavior; revise the
  rubric or mark the record `needs_revision`.
- Eval reward-shape bias: the evaluator over-rewards one response shape, such as
  concrete actions, exact phrases, lists, or role-flavor keywords; rebalance
  buckets or revise rubrics before prompt tuning.
- Case failure: the input or target behavior is unclear; revise or retire it.
- Taxonomy failure: the scenario reveals a missing generic dimension or
  role-specific failure mode.
- Acceptable variance: the answer is not ideal, but still within the role's
  usable conversation band; do not tune the prompt for this alone.
- Overfit pressure: fixing the case would require a narrow or stiff prompt rule;
  prefer revising or retiring the case unless the failure is severe and repeated.
- Abstraction drift: multiple local fixes hide a missing higher-level role
  principle; revise the principle, role axis, decision order, rubric, or failure
  model before adding more case rules.

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
python3 eval_datasets/scripts/batch_import_test_yaml.py \
  . \
  eval_datasets/canonical/all_existing_role_tests.v1.json \
  --project all_existing_roles
```

```bash
python3 eval_datasets/scripts/export_promptfoo_tests.py \
  eval_datasets/canonical/all_existing_role_tests.v1.json \
  eval_datasets/exports/all_existing_role_tests.yaml \
  --include-status candidate
```

```bash
python3 eval_datasets/scripts/audit_testset_balance.py \
  eval_datasets/canonical/all_existing_role_tests.v1.json
```

## Query Patterns

For large canonical files, do not read the whole file unless necessary. Prefer
small scripts or targeted searches.

Examples:

```bash
python3 - <<'PY'
import json
from collections import Counter
data=json.load(open("eval_datasets/canonical/all_existing_role_tests.v1.json"))
print(Counter(r["role"] for r in data["records"]).most_common())
PY
```

```bash
python3 - <<'PY'
import json
role="slowpoke"
data=json.load(open("eval_datasets/canonical/all_existing_role_tests.v1.json"))
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
- Treating many small `if` fixes as proof that the prompt needs more detail
  instead of diagnosing a missing or unclear principle.
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
