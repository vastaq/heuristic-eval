# Conversation Role Profile

This is the bundled default profile. It is intentionally concrete and should
not be treated as the universal schema for every eval domain.

It covers user-facing conversation roles where the evaluator checks naturalness,
role consistency, lightweight help, identity boundaries, context carryover, and
prompt-bloat risk.

Profile-owned concepts include:

- `role`
- `character_context`
- `scene_type`
- `conversation_id`
- `turn`
- conversation-core taxonomy
- role-specific failure patterns
- acceptable band for natural conversation quality

Relevant reference files currently live in `eval_datasets/methodology/`:

- `dataset.schema.md`
- `conversation_core_taxonomy.md`
- `scenario_taxonomy.md`
- `rubric_templates.md`
- `update_guide.md`

Other domains should create their own profile rather than reusing these fields
by default.

## Legacy Canonical Import

When importing old conversation-role canonical JSON, use
`normalize_legacy_canonical.py` first. It adds traceability fields and resets
records to `candidate` so old accepted statuses do not become new gate evidence
without review.
