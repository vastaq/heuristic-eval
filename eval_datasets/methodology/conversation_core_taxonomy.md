# Conversation Core Taxonomy

Boundary: This is conversation_role-specific methodology, not universal
framework schema. For non-conversation domains, define profile-local fields and
promotion rules with `framework_profile_adapter.md` instead of inheriting these
dimensions.

The conversation core is a small, reusable test layer for user-facing dialogue
roles. It should generalize across companion roles, character roles, and
lightweight task helpers with personality. Project-specific imagery belongs in
extensions, not in the core taxonomy.

## Core Dimensions

| Dimension | What it tests | Common failures |
| --- | --- | --- |
| `emotional_reception` | The reply receives a user's feeling before fixing, explaining, or redirecting. | Generic comfort, therapy intake, rushing to advice, motivational slogans. |
| `lightweight_practical_help` | The reply gives a small usable action, phrase, choice, or entry point when asked. | Long plans, refusing to choose, asking for unnecessary context, role flavor overwhelming the task. |
| `identity_and_boundary` | The role answers identity, qualification, and capability questions honestly while preserving relationship. | Fake expertise, prompt/system disclosure, total role drop, overlong disclaimers. |
| `context_carryover` | The reply uses prior turns without being trapped by them and honors the current turn. | Repeating previous advice, ignoring new constraints, restarting the conversation, forgetting exact asks. |
| `natural_style_shape` | The reply feels like natural chat rather than performance, support copy, fiction, or scripted roleplay. | Star actions, parenthetical stage directions, slogans, listiness, prop stacking, customer-service tone. |
| `anti_template_behavior` | The reply avoids canned reassurance and responds to the user's specific wording. | "I am here for you" templates, generic praise, abstract advice, mechanical empathy. |
| `safe_user_agency` | The reply avoids harmful compliance while preserving user agency and relationship. | Unsafe help, scolding policy language, coercive improvement, ignoring user refusal. |

## Core Scene Types

Use these as stable scene types for balanced core records. Projects may extend
them, but should not redefine their meanings.

| Scene type | Dimension | Example user pressure |
| --- | --- | --- |
| `low_energy_no_advice` | `emotional_reception` | User feels dull, tired, or stuck and explicitly does not want advice. |
| `ordinary_frustration` | `emotional_reception` | User is annoyed, disappointed, or embarrassed about a small daily event. |
| `small_joy_shared` | `emotional_reception` | User shares a minor good moment and does not want analysis. |
| `one_small_step` | `lightweight_practical_help` | User asks for exactly one next action. |
| `direct_choice` | `lightweight_practical_help` | User asks the role to choose between low-stakes options. |
| `message_reply` | `lightweight_practical_help` | User asks for one sendable sentence or short reply. |
| `brief_identity` | `identity_and_boundary` | User asks who the role is and requests brevity. |
| `not_professional` | `identity_and_boundary` | User asks whether the role has real expertise. |
| `no_prompt_or_system_talk` | `identity_and_boundary` | User asks about prompt, mechanism, or hidden type. |
| `emotion_to_practical` | `context_carryover` | Conversation shifts from companionship to a small action. |
| `constraint_respected` | `context_carryover` | User changes or repeats a constraint such as "no advice" or "one sentence". |
| `no_restart` | `context_carryover` | Multi-turn role should not reintroduce itself or reset context. |
| `anti_action_markers` | `natural_style_shape` | User asks for normal prose without actions or stage directions. |
| `plain_language` | `natural_style_shape` | User asks the role not to be poetic, theatrical, or jargon-heavy. |
| `anti_generic_comfort` | `anti_template_behavior` | User rejects canned comfort and asks for something specific. |
| `safe_refusal_soft_redirect` | `safe_user_agency` | User asks for harmful, dishonest, or escalating help. |

## Balanced Core Sampling

For an initial 40-60 record core:

- 8-12 records: emotional reception.
- 8-12 records: lightweight practical help.
- 6-10 records: identity and boundary.
- 8-12 records: context carryover.
- 6-10 records: natural style and anti-template behavior.
- 3-6 records: safe user agency.

The core should be small enough to inspect manually. Additional project-specific
records should live in project extensions until they prove cross-project value.

## Promotion Guidance

A core record can become `accepted` when:

1. The input could apply to many user-facing dialogue roles.
2. The target behavior is not tied to one role's props or lore.
3. The avoid behavior captures a real conversation failure.
4. The rubric rewards user-centered response quality over keyword performance.
5. Existing project-specific records do not already cover the same generic risk.

If a sample only makes sense for one role's perception axis, keep it in a project
extension or role failure model instead.
