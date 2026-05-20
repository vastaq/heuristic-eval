# Testset Evolution Protocol

This protocol treats `eval_datasets` as an evolving memory system for
user-facing conversation roles. Raw evaluation assets are preserved for
traceability, while a smaller reviewed core is continuously distilled from
legacy tests, eval failures, prompt work, and human feedback.

## Layer Model

Use separate asset layers so the system can retain information without forcing
every record into the same quality tier.

| Layer | Purpose | Typical contents |
| --- | --- | --- |
| Raw Asset Layer | Preserve original material without cleanup pressure. | Legacy evaluator files, Promptfoo YAML, old canonical snapshots, eval result files, human notes. |
| Intake Layer | Normalize raw material into traceable candidates. | Canonical records with `source_path`, `source_index`, `legacy_asserts`, `input_var`, and `vars`. |
| Core Layer | Keep a small, high-signal balanced conversation core. | Cross-project tests for emotional reception, lightweight help, identity boundary, context carryover, and natural style. |
| Project Extension Layer | Preserve role or project-specific behavior. | Tapdoki, Slowpoke, Ultraman, and other project-specific failure cases. |
| Experiment Layer | Trial new taxonomies, rubrics, or failure packs without polluting gates. | Candidate rubrics, role failure models, hard assertions, generated scenario packs. |
| Gate Layer | Run stable release checks. | Accepted records selected by release manifests. |

## Classification Decision

Every new or reused asset should first answer two questions:

1. Is this a generic conversation-quality issue?
2. Is this a role- or project-specific failure mode?

Classify outcomes this way:

| Outcome | Destination |
| --- | --- |
| Generic and reusable across roles | Core Layer as `candidate`. |
| Specific to one role or project | Project Extension Layer or role failure model. |
| Both generic and role-specific | Add a generic core record and a project-specific variant, linked by notes or tags. |
| Valuable but noisy | Keep as `needs_revision`. |
| Obsolete, duplicate, or misleading | Mark `retired`; do not delete lineage. |

## Absorption Workflow

Use this workflow when reusing previous evaluation assets:

1. Preserve the raw source unchanged.
2. Normalize into canonical shape only if it has reusable signal.
3. Preserve source traceability and evaluator compatibility fields.
4. Map the sample to conversation-core dimensions or project-specific failure
   modes.
5. Check for semantic duplication before adding another record.
6. Keep the first version as `candidate`.
7. Promote only with evidence from review, eval runs, or repeated failures.

## Evidence Requirements

Promotion should explain why a record matters. Evidence can include:

- Human review that the input is realistic and the rubric is fair.
- Eval output showing the record catches a meaningful regression.
- Repeated failures across prompt versions or roles.
- A clear link to a known role failure model.
- A migrated legacy assertion that still protects real behavior.

Avoid promoting a record only because it improves pass rate or because it came
from an old test file.

## Context Control

Do not load entire legacy datasets into working context by default. Prefer:

- Querying by role, layer, scene, status, or tags.
- Reviewing small batches selected for coverage gaps.
- Summarizing raw pools into failure patterns before writing new cases.
- Keeping stable release gates small enough to inspect manually.

## First-Stage Boundaries

The first implementation stage should not rewrite every canonical record. Keep
the current flat schema and add evolution metadata only when it earns its keep.
The goal is to make asset flow explicit before changing storage format.
