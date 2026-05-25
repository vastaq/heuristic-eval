# Framework, Profiles, And Adapters

This repository should not force every project to use the bundled
conversation-role schema or Promptfoo file shape. The reusable part is the
heuristic maintenance framework. The encoding belongs to profiles and adapters.

## Three Layers

### Framework

The framework is shared across eval domains:

- Raw / Intake / Core / Experiment / Gate layers.
- Autonomous controller.
- Learning state.
- Run intake.
- Reward and compression decisions.
- Prompt-bloat or policy-bloat gates.
- Stop rules.
- Legacy learning bootstrap.

Framework documents should avoid project-specific field assumptions whenever
possible.

### Profile

A profile defines the meaning of data for one eval domain.

Examples:

- `conversation_role`
- `coding_eval`
- `support_agent`
- `retrieval_eval`
- `tool_use_eval`

A profile owns:

- canonical record schema
- required and optional fields
- taxonomy and coverage dimensions
- rubric vocabulary
- acceptable-band definition
- promotion evidence
- bloat guardrail

Profiles may reuse framework terms, but they should not force other profiles to
inherit their fields. For example, `role`, `character_context`, and `scene_type`
belong to the current conversation-role profile. They are not universal fields.

### Adapter

An adapter maps an evaluator or external file format into and out of a profile.

Examples:

- Promptfoo YAML import/export for conversation-role tests.
- A coding benchmark result importer.
- A support-ticket review exporter.
- A custom judge result normalizer.

Adapters own:

- parser assumptions
- evaluator-specific variables
- assertion or judge-result mapping
- export file shape
- result normalization

For Promptfoo, fields such as `vars`, `assert`, `input_var`, and
`legacy_asserts` are adapter compatibility fields, not framework requirements.

## Agent Rule

When a new project does not fit the bundled conversation-role profile, the agent
should create a new profile and adapter rather than bending the existing schema.

Decision order:

1. Does the existing profile describe the domain accurately?
2. If not, create or update a profile document first.
3. Does an adapter exist for the evaluator or file format?
4. If not, create an adapter script or mapping note.
5. Only then import records, normalize results, or create canonical data.

Do not modify the shared framework just to satisfy one evaluator's file shape.
Do not stuff non-conversation data into conversation-role fields.

## Bundled Python Scripts

The Python scripts in `eval_datasets/scripts/` are reference implementations for
the bundled setup:

- the current conversation-role profile
- the Promptfoo adapter
- lightweight HL replay and validation utilities
- legacy bootstrap scaffolding

They are useful examples and working tools, but they are not the universal
encoding of this framework. New domains should add new profile/adapter logic
instead of pretending their data is conversation-role Promptfoo data.
