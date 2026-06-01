# Generative Content Profile

This profile covers eval loops where a generator produces user-facing content:
stories, scenes, summaries, marketing drafts, educational explanations, or other
multi-paragraph creative outputs.

It is intentionally separate from `conversation_role`. A generated story or
batch output should not be forced into fields such as `role`,
`character_context`, or `scene_type`.

## Profile Goal

Keep generated content inside an acceptable experience band while avoiding two
failure modes:

- Prompt bloat: adding narrow instructions for every weak sample.
- Eval reward-shape bias: optimizing for visible tokens, exact phrases, or
  judge-friendly structure instead of actual output quality.

The profile can be used even when no new canonical dataset is generated. In that
case, it serves as a run-intake and decision framework for prompt optimization.

## Core Objects

Use these concepts when adapting a project:

- `content_unit`: one generated artifact or one coherent generated flow.
- `source_prompt`: stable prompt or context supplied to the generator.
- `variable_set`: controlled inputs for the run, such as time, count, audience,
  style, persona, or scenario.
- `event_or_preset`: optional event anchor injected for a specific run.
- `generation_result`: raw model output or structured generation result.
- `structural_diagnostics`: local rule checks that find mechanical issues but
  do not claim final quality.
- `llm_review`: external or internal judge review, ideally with reasons.
- `human_signal`: short human judgment that interprets or overrides evaluator
  pressure.
- `decision`: compressed outcome for the next optimization step.

## Required Fields

Use these fields when this profile produces dataset candidate records. Do not
invent conversation-role fields for generated-content records.

- `id`: stable candidate record id.
- `layer`: intake, experiment, project extension, core, or gate.
- `content_unit`: generated artifact or coherent generated flow under review.
- `source_prompt`: stable prompt, policy, or context that produced the content.
- `variable_set`: controlled input variables for the run.
- `generation_result`: raw or normalized generated output under evaluation.
- `target_behavior`: quality behavior the candidate should preserve or test.
- `avoid_behavior`: failure behavior the candidate should catch.
- `quality_signals`: rubric, LLM review, diagnostic, or human signal refs.
- `rubric_ref`: profile-local rubric or quality dimension reference.
- `source_path`: source run, output, or review file path.
- `review_status`: candidate, needs_revision, accepted, or retired.

## List Fields

These fields should be lists when present:

- `variable_set`
- `target_behavior`
- `avoid_behavior`
- `quality_signals`
- `tags`
- `evidence_refs`

## Suggested Run Dimensions

For creative generation, keep controlled variables explicit and small. Examples:

- content length or turn count
- time, season, or temporal context
- participant count or audience
- preset events or required anchors
- style intensity
- repetition or revisit mode

Avoid changing unrelated variables while trying to diagnose one issue.

## Rubric Vocabulary

Recommended quality dimensions:

- `coherence`: the output reads as one connected flow.
- `variable_alignment`: controlled variables are respected without conflict.
- `style_fit`: tone, pacing, and language match the intended experience.
- `source_fidelity`: stable source prompt elements are reflected naturally.
- `event_integration`: presets appear as story movement, not pasted keywords.
- `character_or_actor_balance`: participants are not collapsed or forgotten.
- `novelty_without_drift`: output has variation without losing the brief.
- `naturalness`: the result does not feel like a checklist or judge bait.
- `safety_or_boundary_fit`: domain boundaries are respected.

Recommended diagnostic-only dimensions:

- exact keyword coverage
- motif mentions
- preset term coverage
- length ratio
- simple banned-term checks

Diagnostic-only dimensions may warn about issues, but should not dominate the
overall decision without human or LLM review support.

## Acceptable Band

A generated-content prompt is usually inside the acceptable band when:

- generation succeeds consistently enough for the product stage;
- most outputs are coherent and readable;
- controlled variables do not visibly conflict;
- recurring severe failures are known and tracked;
- remaining weak samples are low severity or acceptable variance;
- prompt edits are not making ordinary outputs stiffer or more keyword-stuffed.

The acceptable band should be project-specific. Do not use one universal score
threshold for every creative domain.

## Promotion Evidence

Use a mix of evidence rather than one score:

- representative raw outputs;
- LLM review with reasons;
- local structural diagnostics;
- human signals;
- comparison against the previous prompt or policy;
- decision notes explaining accepted variance or blocked tuning.

Only create canonical candidate cases when the project needs replayable
regression protection. Many prompt optimization loops only need run intake and
decision records.

## Bloat Guardrail

Before changing a prompt, ask:

1. Is the issue repeated and meaningful?
2. Does the prompt own the failure, or do variables/presets/rubrics own it?
3. Would fixing this sample make average outputs more rigid?
4. Is a metric rewarding token presence rather than output quality?
5. Can a smaller boundary change solve several failures?

If the answer is unclear, classify the issue as experiment evidence instead of
adding a prompt rule.

## Example Human Signals

Useful signals include:

- "This metric is looking for visual words, but that is not how quality should
  be judged."
- "The atmosphere is good; do not remove it just because it is not action-like."
- "This continuity expectation is impossible without memory."
- "This conflict belongs to preset injection, not the stable prompt."
- "The score is fine, but the result feels like a checklist."

Capture these as first-class evidence. They are often more important than a
small score movement.
