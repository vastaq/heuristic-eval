# voice_clone_asset Calibration

Do not use one fixed threshold for every character, speaker, language, vendor,
or speaking style.

Calibrate gates from:

- anchor bank distributions;
- negative bank distributions;
- historical regression results;
- human review results;
- known constraints of the clone vendor or model.

## Example Character Calibration

```yaml
character_id: sample_character

quality_gate:
  clipping_ratio_max: 0.01
  silence_ratio_max: 0.35

intelligibility_gate:
  asr_cer_max: 0.08

speaker_identity_gate:
  similarity_pass_min: 0.76
  similarity_fail_max: 0.68
  borderline_range: [0.68, 0.76]

speed_gate:
  chars_per_second_pass_range: [3.4, 4.8]
  chars_per_second_borderline_range: [4.8, 5.3]
  chars_per_second_fail_above: 5.3

pause_gate:
  pause_ratio_pass_range: [0.1, 0.24]
  pause_ratio_fail_below: 0.06
```

## Calibration Rules

- Treat technical metrics as screening and regression evidence.
- Treat speaker embeddings as identity evidence, not character-style proof.
- Treat human A/B review as required for borderline identity or style decisions.
- Do not update thresholds from one output.
- Do not tune thresholds to make the current clone version pass.
