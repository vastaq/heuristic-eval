# Dataset Traction Audit

A dataset traction audit asks whether a new eval pack is safe to use as
pressure for prompt or policy tuning. It runs after dataset generation, import,
or rebalance, and before prompt mutation.

The audit is not a quality score. It checks the shape of the measuring stick:
what behavior the rubrics repeatedly reward, which counterbehaviors are missing,
and whether pass-rate pressure would likely pull the prompt toward local
patches.

## When To Run

Run the audit when:

- A dataset is generated or imported for the first time.
- A prompt is about to be tuned from eval failures.
- A high-scoring prompt feels unnatural, rigid, over-helpful, or too literal.
- A compact or principle-first prompt loses heavily to a longer prompt.
- The user flags local `if`/`when` patching, abstraction drift, or "technique
  over principle."

## Checks

Minimum checks:

- Reward-shape distribution: action, exact response shape, presence/restraint,
  identity boundary, and anti-action counterpressure.
- Dominant-shape pressure: one response shape should not silently define the
  whole role.
- Countercase coverage: if the role values restraint, quiet presence, or not
  doing more, the dataset needs cases that reward those behaviors.
- Judge noise suspects: contradictory reasons, exact wording preferences, or
  failures that still satisfy the user's visible intent.
- Prompt-bloat pressure: whether failed cases invite many local rules instead
  of one reusable invariant.

## Recommended Actions

Use one primary action:

| Action | Use when |
| --- | --- |
| `revise_or_supplement_eval_first` | The eval over-rewards one shape or lacks countercases. |
| `inspect_before_prompt_tuning` | The eval has medium warnings that need human or output review. |
| `prompt_tuning_allowed_with_bloat_gate` | The eval is balanced enough to tune, but prompt-bloat checks still apply. |
| `accept_variance` | The failure is low-severity and tuning would add stiffness. |
| `mark_judge_noise` | The judge reason conflicts with the output or rubric. |
| `stop_tuning` | The prompt is inside the acceptable band and remaining failures are narrow. |

## Script

Use:

```bash
python3 eval_datasets/scripts/audit_dataset_traction.py DATASET.yaml \
  --output EXPERIMENT/traction_audit.json \
  --markdown EXPERIMENT/traction_audit.md
```

The script accepts Promptfoo YAML, Promptfoo-style JSON lists, or canonical JSON
with `records`. It writes a compact JSON artifact and an optional Markdown
summary. Keep these under the experiment that owns the eval pack.

## Decision Rule

If the audit says `revise_or_supplement_eval_first`, block prompt mutation until
the eval has been revised, supplemented with countercases, or explicitly marked
as a biased stress test. Pass rate from a biased eval may still be useful, but
it should not decide the next prompt shape by itself.
