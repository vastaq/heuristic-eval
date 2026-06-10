# voice_clone_asset Minimal Example

This example shows the public shape of a voice clone asset loop without shipping
real audio, real transcripts, speaker identities, or private project data.

All audio paths are placeholders using `local://...`. They are meant to point to
project-local files in a downstream workspace.

## Flow

```text
source_clip_report.sample.json
-> human_source_review.sample.json
-> clone_version_card.sample.json
-> regression_result.sample.json
-> human_ab_review.sample.json
-> route_decision.expected.json
```

The route decision shows the key behavior: a technically clean output can still
route to `speed_regression`, while blocking random source-pack changes.
