# voice_clone_asset Schema

This profile uses small JSON artifacts rather than one large database. Real
audio files should stay in local storage and be referenced by URI.

Use `local://...` or project-local relative paths for private audio during
development. Do not commit real audio, transcripts, speaker identities, or clone
outputs to the public framework repo unless they are intentionally licensed and
scrubbed.

## Source Clip Report

```json
{
  "schema_version": "voice_clone_asset.source_clip.v0",
  "clip_id": "raw_0001",
  "character_id": "sample_character",
  "audio_uri": "local://raw_bank/sample_character/raw_0001.wav",
  "transcript": "We can take this one step at a time.",
  "duration_sec": 4.82,
  "auto_metrics": {
    "sample_rate": 48000,
    "channels": 1,
    "clipping_ratio": 0.001,
    "silence_ratio": 0.14,
    "rms_mean": 0.061,
    "chars_per_second": 4.15,
    "f0_median_hz": 178.2
  },
  "auto_gate": {
    "technical_quality": "pass",
    "noise": "pass",
    "duration": "pass",
    "speed": "pass",
    "speaker_consistency": "unknown"
  },
  "review": {
    "required": true,
    "reason": "candidate_anchor_selection",
    "status": "pending"
  }
}
```

## Human Review Result

```json
{
  "schema_version": "voice_clone_asset.human_review.v0",
  "review_id": "review_0001",
  "task_type": "source_clip_review",
  "reviewer_role": "voice_director",
  "target_id": "raw_0001",
  "decision": "anchor_bank",
  "tags": ["clear", "in_character", "normal_pacing"],
  "confidence": "high",
  "notes": "Usable as a normal speaking anchor."
}
```

## Clone Version Card

```json
{
  "schema_version": "voice_clone_asset.clone_version.v0",
  "voice_model_version": "sample_character_v2",
  "character_id": "sample_character",
  "source_pack_id": "sample_character_source_pack_v2",
  "created_at": "2026-06-10",
  "source_pack_summary": {
    "anchor_clip_count": 24,
    "candidate_clip_count": 96,
    "negative_excluded_count": 12,
    "total_duration_min": 43.5
  },
  "preprocessing": {
    "denoise": "light",
    "loudness_normalization": "-23_lufs",
    "segment_duration_range_sec": [3, 12],
    "transcript_checked": true,
    "multi_speaker_removed": true
  },
  "change_note": "Removed fast outliers and added calm anchors."
}
```

## Regression Result

```json
{
  "schema_version": "voice_clone_asset.regression_result.v0",
  "result_id": "sample_character_v2_reg_001",
  "character_id": "sample_character",
  "voice_model_version": "sample_character_v2",
  "previous_version": "sample_character_v1",
  "test_item_id": "neutral_short_001",
  "text": "We can take this one step at a time.",
  "output_audio_uri": "local://outputs/sample_character_v2/reg_001.wav",
  "auto_metrics": {
    "asr_cer": 0.03,
    "speaker_similarity_to_anchor_centroid": 0.72,
    "chars_per_second": 5.92,
    "pause_ratio": 0.05,
    "f0_median_hz": 181.4
  },
  "profile_expectation": {
    "speaker_similarity_min": 0.75,
    "chars_per_second_range": [3.4, 4.8],
    "pause_ratio_range": [0.1, 0.24]
  },
  "auto_gate": {
    "technical_quality": "pass",
    "intelligibility": "pass",
    "speaker_identity": "borderline",
    "speed": "fail",
    "pause": "fail"
  },
  "human_review": {
    "required": true,
    "reason": "speed_fail_and_identity_borderline",
    "status": "pending"
  }
}
```

## Route Decision

```json
{
  "schema_version": "voice_clone_asset.route_decision.v0",
  "decision_id": "decision_sample_character_v2_reg_001",
  "input_result_id": "sample_character_v2_reg_001",
  "status": "fail",
  "primary_failure": "speed_regression",
  "secondary_failures": ["pause_regression", "speaker_identity_drift"],
  "blocked_actions": [
    "do_not_replace_clone_model_blindly",
    "do_not_add_random_source_audio"
  ],
  "next_actions": [
    "compare_source_pack_speed_distribution_v1_vs_v2",
    "inspect_fast_clips_added_in_v2",
    "move_confirmed_fast_style_mismatch_clips_to_negative_bank"
  ],
  "human_review_required": true,
  "create_regression_case": true,
  "notes": "Output is technically clean but too fast."
}
```
