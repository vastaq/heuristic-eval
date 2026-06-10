# Review Window Protocol

`review_window` is a lightweight JSON protocol for human review tasks. It is
not a UI framework and not a crowdsourcing platform.

Profiles can use this protocol when automatic metrics are not enough and a
human decision must become structured evidence.

## Scope

The first version should support only:

- `source_clip_review`
- `clone_ab_review`
- `output_issue_review`

The review surface can be a local HTML file, notebook, CLI prompt, or any other
project-local tool. The public framework only defines the task and result shape.

## Task Shape

Every task should include:

- `schema_version`
- `task_id`
- `task_type`
- `profile`
- `target_id`
- `audio_refs`
- `context`
- `choices`
- `evidence_refs`

Audio refs should point to local or private project paths. Do not commit real
audio assets to the public framework repo.

## Result Shape

Every result should include:

- `schema_version`
- `review_id`
- `task_id`
- `task_type`
- `reviewer_role`
- `decision`
- `confidence`
- `tags`
- `notes`

Human review results are evidence for routing. They are not automatic promotion
unless the active profile explicitly says so.
