# voice_clone_asset Review Protocol

Human review is part of the first version of this profile. The first version is
not a labeling platform; it is a structured listening window that turns human
judgment into routeable evidence.

## Review Task Types

### source_clip_review

Use this to decide whether a source clip belongs in `anchor_bank`,
`candidate_bank`, `negative_bank`, `discard`, or `uncertain`.

Minimum decision fields:

- `task_type`: source_clip_review
- `target_id`: source clip id
- `decision`: anchor_bank, candidate_bank, negative_bank, discard, or uncertain
- `tags`: compact reasons such as clear, noisy, fast, in_character, wrong_style
- `confidence`: low, medium, or high
- `notes`: short reviewer note

### clone_ab_review

Use this to compare two clone versions on the same regression text.

Minimum decision fields:

- `task_type`: clone_ab_review
- `character_id`
- `test_item_id`
- `version_a`
- `version_b`
- `preference`: A, B, similar, neither, or uncertain
- `main_difference`: speed, identity, character_style, quality, pause,
  prosody, or other compact tags
- `confidence`
- `notes`

### output_issue_review

Use this to confirm the main failure reason for one generated output.

Minimum decision fields:

- `task_type`: output_issue_review
- `output_id`
- `usable`: boolean
- `main_issue`
- `secondary_issue`
- `should_create_regression_case`: boolean
- `notes`

## What Review Should Not Do

Do not make the first review protocol into a full listening-test platform.
Avoid accounts, reviewer reputation, crowdsourcing controls, and large scoring
matrices in the first version.

The first version only needs to:

1. play or point to audio;
2. show a small amount of context and metrics;
3. capture one compact decision;
4. export JSONL for routing.
