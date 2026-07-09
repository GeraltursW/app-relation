# 20260710 Page Review Editing Iteration

## Goal

Add a human double-check workflow for AI-inferred graph data.

AI analysis can propose page meaning and graph placement, but the project needs a review surface where a human can correct the evidence before the result is treated as reliable.

## Completed

### Right Inspector Edit Mode

The right inspector now supports an explicit edit mode for graph nodes.

Editable fields:

- page title
- page URL
- parent widget description
- AI page description
- AI inference label
- AI inference reason
- `ai_recursive`
- review note
- image evidence list

The reviewer can:

- add image keys/URLs
- delete image keys/URLs
- modify AI reasoning text
- save the review

### Graph Area Update

After saving, the frontend updates the local graph model.

This means the graph node display can immediately reflect edited values such as:

- page title
- page text
- primary image
- AI inference state

This supports demo and review continuity even when backend persistence is not available.

### Backend Save API

Added backend endpoint:

```http
POST /api/graph/pages/review
POST /api/graph/page-review
```

If the request maps to a persisted `canonical_pages` UUID, the backend updates PostgreSQL fields. If the page is a demo numeric node, the backend returns normalized review data with `persisted: false`.

### API Documentation

Added:

```text
docs/page-review-editing-api.md
```

The document describes request body, response body, persistence behavior, frontend flow, and recommended audit table.

## Design Decision

This iteration keeps editing behind an explicit `开启编辑` button.

Reason:

- normal graph browsing should remain safe
- accidental edits should be avoided
- human review should feel intentional
- later audit logs can treat every save as a deliberate review event

## Remaining Work

Recommended next step:

- add `graph_change_events`
- persist every edit as an immutable audit record
- support reviewer identity
- support reject/accept states for AI inference
- add undo/revert from the review history
