# Experiment Modules

Experiment modules let the testset system try new ideas without treating them as
finished design. Use them for new rubrics, taxonomies, role failure packs,
assertions, scenario generators, and evaluation strategies.

## Module Types

| Module type | Examples | Default destination |
| --- | --- | --- |
| `taxonomy_experiment` | New dimensions, scene types, tag namespaces. | Candidate reports or methodology drafts. |
| `rubric_experiment` | New judge wording, scoring thresholds, role-specific rubric modules. | Candidate-only evaluator exports. |
| `failure_pack_experiment` | A set of cases targeting a generic or role-specific failure pattern. | Project extension or experiment dataset. |
| `hard_assertion_experiment` | Length checks, no-action-marker checks, no-prompt-leak checks. | Small accepted-bank trial before gate use. |
| `oracle_strategy_experiment` | Hybrid judge plus hard checks, repeated runs, alternate judge providers. | Eval run manifest or experiment notes. |

## Entry Criteria

Start an experiment when at least one is true:

- A repeated failure does not fit the current taxonomy.
- A rubric rewards the wrong behavior or misses a meaningful failure.
- A project-specific failure appears often enough to deserve a named model.
- A hard assertion may protect a clear boundary but could over-filter natural
  conversation.
- Legacy assets contain a pattern worth testing before promotion.

Do not start an experiment only because a field or abstraction seems elegant.

## Minimal Module Record

Track experiments with a small JSON or markdown note before building scripts:

```json
{
  "id": "exp_conversation_anti_template_v1",
  "type": "failure_pack_experiment",
  "status": "active",
  "hypothesis": "Anti-template failures appear across companion roles and should become part of conversation core.",
  "scope": "candidate records only",
  "evidence_needed": [
    "At least two projects or role families show the failure",
    "Human review confirms the rubric does not punish plain good answers"
  ],
  "promotion_target": "conversation_core",
  "retirement_trigger": "Mostly duplicates existing natural_style_shape records"
}
```

## Validation Loop

Use this loop for each experiment:

1. State the hypothesis and promotion target.
2. Run on a small candidate batch or selected legacy subset.
3. Inspect representative passes and failures.
4. Check whether the module catches real failures without overfitting.
5. Record evidence in the evolution event log.
6. Decide: continue, revise, promote, or retire.

## Promotion Criteria

Promote an experiment only when:

- It catches a real user-facing conversation failure.
- It does not mainly reward keywords, props, or project lore.
- It improves coverage or diagnosis beyond existing core dimensions.
- It has evidence from human review, eval failure, or cross-project reuse.
- It has a clear owner layer: conversation core, project extension, release gate,
  or methodology.

Promotion targets:

| Target | Required evidence |
| --- | --- |
| Conversation core | Reusable across multiple roles or projects. |
| Project extension | Valuable for one role family but not generic. |
| Release gate | Stable, accepted, low-noise, and manually inspectable. |
| Methodology | Improves future skill decisions or data governance. |

## Retirement Criteria

Retire or archive an experiment when:

- It duplicates existing core coverage.
- It overfits to one prompt wording or project.
- It punishes natural, user-centered replies.
- It creates noisy eval failures without clear diagnosis.
- It lacks evidence after a reasonable trial.

Retirement is not failure. It prevents half-proven ideas from hardening into
the system.

## Guardrails

- Experiments must not enter release gates by default.
- Generated packs remain `candidate` until reviewed.
- Do not rewrite canonical schema to support one experiment.
- Prefer small batches that can be inspected manually.
- Keep raw source and experiment evidence separate from stable core records.
