# voice_clone_asset Failure Taxonomy

Use failure tags to route work to the right layer. A failure tag is evidence for
diagnosis; it is not automatically a source-pack or clone-version change.

## Source Failures

- `source_noise_contamination`: background noise, hum, compression, or room
  sound makes the clip unsafe for anchors or training.
- `source_multi_speaker_contamination`: more than one speaker is present.
- `source_transcript_mismatch`: transcript does not match the clip closely
  enough for source-pack use.
- `source_clipping_or_distortion`: clipping, distortion, or overload is present.
- `source_reverb_too_high`: room reverb dominates voice quality.
- `source_speed_outlier`: speaking rate is outside the intended voice style.
- `source_emotion_outlier`: emotion is too intense or mismatched for the target
  asset.
- `source_style_mismatch`: delivery is technically clean but not in character.
- `source_character_mismatch`: clip does not represent the intended character.
- `insufficient_anchor_coverage`: anchor bank does not cover enough normal,
  expressive, or regression-relevant speech.

## Clone Output Failures

- `output_noise_or_artifact`: generated output has audible artifacts.
- `output_discontinuity`: generated output has jumps, glitches, or unstable
  cuts.
- `output_loudness_failure`: generated output is too quiet, too loud, or
  unstable.
- `output_intelligibility_failure`: generated output is hard to understand.
- `pronunciation_failure`: words are pronounced incorrectly.
- `speaker_identity_drift`: voice identity moved away from anchors.
- `character_style_drift`: identity may be close, but style or performance no
  longer fits the character.
- `speed_regression`: output is too fast or too slow compared with calibrated
  anchor behavior.
- `pause_regression`: pauses are missing, excessive, or unlike the character.
- `prosody_regression`: pitch, rhythm, or emphasis changed in a harmful way.
- `long_text_instability`: long text exposes quality or style instability.
- `version_regression`: new version is worse than a previous version.

## Review Failures

- `reviewer_disagreement`: reviewers do not agree enough to route the case.
- `unclear_character_definition`: the target voice is not defined clearly
  enough.
- `insufficient_reference_examples`: not enough anchors or negatives exist to
  judge the case.
- `requires_voice_director_review`: a human voice director or owner must decide.

## Decision Outcomes

- `accept`
- `reject`
- `accept_with_note`
- `needs_human_review`
- `accept_variance`
- `stop_tuning`
- `create_regression_case`
- `update_anchor_bank`
- `update_negative_bank`
- `rebuild_source_pack`
