# Scenario Taxonomy for Reusable Role Testsets

Use separate layers so a role can be tested cheaply during prompt edits and more
deeply before release.

## Dataset Layers

| Layer | Purpose | Run Frequency |
| --- | --- | --- |
| `core_smoke` | Verify identity, basic tone, and obvious safety boundaries. | Every prompt edit |
| `micro_narrative` | Everyday scenes that reveal product feel and role perception. | Major prompt edits |
| `tiny_practical` | User asks for one small action, phrase, or entry point. | Major prompt edits |
| `boundary_regression` | Known failures: unsafe advice, fake expertise, over-questioning, action markers. | Before release |
| `identity_boundary` | User asks who the role is or whether it is professional/real. | Before release |
| `contrast_pairs` | Similar roles receive similar inputs to detect role collapse. | After role tuning |
| `context_drift` | Multi-turn conversations with mode changes and prior-context pressure. | Before release |
| `small_joy` | Positive or ordinary moments, not only sadness and failure. | Dataset balance checks |

## Scenario Types

### Everyday Emotion

Small daily moments that carry a feeling without directly asking for therapy.

Measured qualities: emotional reception, naturalness, role-specific perception.

Common failures: generic comfort, over-literary monologue, interrogation.

### Tiny Practical Help

The user asks for a very small next step, sentence, or question.

Measured qualities: one actionable step, low pressure, retained role flavor.

Common failures: long plans, coaching pressure, ignoring exact-count requests.

### Boundary and Identity

The user asks who the role is, whether it is qualified, or whether it is real.

Measured qualities: honest boundary, preserved immersion, no fake expertise.

Common failures: pretending to be a professional, system disclaimers, role drop.

### Safety Boundary

The user asks for dangerous, dishonest, or escalating behavior.

Measured qualities: clear refusal of harm, child-safe or user-safe alternative,
and tone that still fits the role.

Common failures: unsafe compliance, scolding, too much abstract policy language.

### Style Shape

Inputs pressure bad output shapes such as stage directions, listiness, slogans,
or role-prop pileups.

Measured qualities: natural chat, compactness, no mechanical performance.

Common failures: `*action*`, parenthetical action, scene directions, prop stacking.

### Role Contrast

The same or similar input is sent to neighboring roles.

Measured qualities: the answer belongs to the target role's perception axis.

Common failures: generic warmth, borrowed imagery, keyword-only role markers.

### Context Drift

Multi-turn sequences change mode, such as emotion to boundary to practical help.

Measured qualities: using context without being trapped by it.

Common failures: staying in comfort mode, repeated tools, losing exact user asks.

## Difficulty Levels

| Difficulty | Definition |
| --- | --- |
| `easy` | Clear role cue, low emotional or safety risk. |
| `medium` | Natural ambiguity, mild boundary pressure, or context carryover. |
| `hard` | Conflicting instruction, safety risk, exact-count request, or neighboring-role trap. |

## Sampling Guidance

For a 50-100 record role dataset:

- 35-45% should be everyday emotion or micro-narrative samples.
- 15-25% should be tiny practical help.
- 15-20% should be boundary, identity, or safety regression.
- 10-15% should be context drift or contrast cases.
- Include a few small-joy samples so the role is not tuned only for sadness.

Do not reuse another role's nouns blindly. Reuse scenario structure, not props.
