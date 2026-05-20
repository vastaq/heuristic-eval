# Role Evaluation Testset Schema

This schema is the canonical source format for reusable character evaluation
testsets. Existing evaluator files, including Promptfoo YAML, can be imported
into this shape, reviewed, updated, and exported back to runner-specific views
without replacing the original tests.

## Dataset Document

```json
{
  "version": "v1",
  "project": "slowpoke",
  "dataset_type": "character_prompt_eval",
  "source_paths": ["slowpoke/test_daily.yaml"],
  "updated_at": "2026-05-11",
  "records": []
}
```

## Canonical Record

```yaml
- id: slowpoke_context_shoes_001
  layer: context_drift
  role: slowpoke
  character_context: file://prompt.md
  scene_type: child_emotional_regulation
  difficulty: medium
  input: "Slowpoke, I have to put on my shoes fast and I feel all buzzy."
  input_var: question
  vars:
    question: "Slowpoke, I have to put on my shoes fast and I feel all buzzy."
    character_context: file://prompt.md
  target_behavior:
    - "Notice the rushed, buzzy body feeling in child-friendly words"
    - "Give one tiny concrete step without a long checklist"
  avoid_behavior:
    - "Clinical language"
    - "Rushing the child"
    - "Breathing as the default answer"
  tags:
    - child
    - body_signal
    - tiny_step
  rubric_ref: emotional_reception
  source_path: slowpoke/test_daily.yaml
  source_index: 0
  legacy_asserts:
    - type: llm-rubric
      value: "The reply should notice the child's rushed, buzzy feeling..."
  review_status: candidate
  revision: 1
  notes: "Imported from the original daily Slowpoke conversation tests."
```

## Required Fields

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable unique id. Do not reuse after retiring a sample. |
| `layer` | enum | Test layer from `scenario_taxonomy.md`. |
| `role` | string | Target role key. |
| `character_context` | string | Prompt or role context path used by the evaluator. |
| `scene_type` | string | Scenario type from the taxonomy or project extension. |
| `difficulty` | enum | `easy`, `medium`, or `hard`. |
| `input` | string | User message sent to the role. |
| `target_behavior` | string[] | Behaviors a good answer should show. |
| `avoid_behavior` | string[] | Behaviors that should fail or lower confidence. |
| `tags` | string[] | Searchable labels for balancing and filtering. |
| `rubric_ref` | string | Reusable rubric key or role-specific rubric key. |
| `source_path` | string | Original test file or dataset path. |
| `review_status` | enum | `candidate`, `accepted`, `needs_revision`, or `retired`. |

## Optional Fields

| Field | Use |
| --- | --- |
| `source_index` | Original index in the imported file. |
| `source_id` | Original metadata id, if present. |
| `source_file` | Source YAML file when generated from a batch import. |
| `input_var` | Original evaluator input variable name. For Promptfoo, this is often `question` or `user_input`. |
| `vars` | Original Promptfoo `vars` block, preserved so exports keep extra context. |
| `conversation_id` | Multi-turn or context-drift group id. |
| `turn` | Turn number inside a conversation. |
| `contrast_group` | Group id for paired contrast tests. |
| `neighbor_role` | Role this sample should not collapse into. |
| `expected_length` | `one_line`, `short`, or `medium`. |
| `risk_level` | `low`, `medium`, or `high`. |
| `source` | `human_seed`, `synthetic`, `model_assisted`, `regression`, or `legacy_import`. |
| `legacy_asserts` | Original evaluator assertions that must survive export. |
| `revision` | Integer updated when the sample changes materially. |
| `updated_at` | Date of the latest sample update. |
| `notes` | Human rationale for why this sample exists. |

## Evaluator Projection

Promptfoo is the bundled default projection. Other evaluators should use their
own projection section and scripts.

Canonical records are exported to Promptfoo tests like this:

```yaml
- vars:
    character_context: file://prompt.md
    question: "Slowpoke, I have to put on my shoes fast and I feel all buzzy."
  metadata:
    id: slowpoke_context_shoes_001
    layer: context_drift
    role: slowpoke
    scene_type: child_emotional_regulation
    difficulty: medium
    source_path: slowpoke/test_daily.yaml
    tags: [child, body_signal, tiny_step]
  assert:
    - type: llm-rubric
      value: |
        The reply should notice the child's rushed, buzzy feeling...
```

`legacy_asserts`, `input_var`, and the original `vars` block are preserved on
export. This matters because older projects do not all use the same prompt
variable names: some expect `question`, others expect `user_input`, and some
include extra context variables. When a record has no legacy assertion, the
exporter can build a default `llm-rubric` from `target_behavior` and
`avoid_behavior`.

## Quality Gates

A sample is accepted only if:

1. The input sounds like a real user message.
2. The target behavior is specific enough to judge.
3. The avoid behavior catches known risks without forcing one exact phrasing.
4. The sample can fail for a meaningful reason.
5. The sample tests the role's perception style, not only literal props.
6. The source and review status are traceable.
