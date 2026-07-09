# 20260709 AI Graph Editing Iteration

## Summary

This iteration improves the graph curation workflow around AI-discovered pages and uncertain graph structure.

The frontend now separates two risky operations into explicit modes:

- Floating URL merge mode: manually drag orphan/floating pages into the main graph tree.
- Tree structure edit mode: drag existing main-tree nodes to adjust parent-child relationships.

This design prevents accidental graph mutation during normal browsing and makes AI output reviewable before it becomes canonical graph structure.

## Implemented Changes

### Floating URL Manual Merge

The left sidebar now supports a dedicated floating-page drag mode.

Flow:

```text
Floating URL page -> enable drag -> drag to main tree node -> merge as child node
```

Frontend behavior:

- The floating URL section has an explicit enable/disable drag button.
- Floating cards become visually highlighted when drag mode is active.
- Dropping a floating page onto a main-tree node merges it into that node.
- The merged page is marked as AI-derived/review-required evidence through the existing `ai_recursive` path.
- If the backend is unavailable, the frontend performs a local merge for demo/review continuity.

Backend contract:

```http
POST /ai/manualMergeFloatingPage
POST /ai/manual-merge-floating-page
```

The request includes:

- floating page id/node id
- page title/text/url/image
- target parent id/node id
- widget description
- operator note

The response returns merge metadata used by the frontend to update the graph.

### Main Tree Structure Editing

The main tree now has an explicit edit mode.

Flow:

```text
Main tree -> edit structure -> drag node A onto node B -> A becomes child of B
```

Safety checks:

- Users must click `编辑结构` before tree nodes become draggable.
- The system rejects dragging a node onto itself.
- The system rejects moving a node under its own descendant, preventing graph cycles.
- After a valid move, graph levels and indexes are rebuilt.

This is intended for human correction when the AI-inferred structure is suspicious.

### AI Double Check Direction

AI inference should be treated as a candidate, not final truth.

Recommended review lifecycle:

```text
AI proposes structure
-> human reviews page evidence
-> human accepts, edits, or rejects
-> backend records the reviewed edge
-> graph marks the decision as reviewed
```

Recommended fields for later persistence:

```text
review_status: pending | accepted | rejected | edited
reviewer: string
review_note: string
source_edge_id: string
target_parent_id: string
updated_at: timestamp
```

For leadership demo, the current frontend already shows the most important interaction:

- AI can suggest a merge.
- Human can manually merge floating pages.
- Human can edit the main tree if the AI structure looks wrong.

## Files Changed

- `src/components/TreeNav.vue`
- `src/components/TreeItem.vue`
- `src/App.vue`
- `src/data/graph.js`
- `src/style.css`
- `backend/app/api/routes/ai.py`
- `README.md`
- `docs/ai-exploration-incremental-traversal.md`

## Validation

Validated locally with:

```powershell
npm run check
npm run build
python -m compileall backend\app
```

## Next Recommended Step

The next engineering step is to persist these edit operations.

Recommended backend APIs:

```http
POST /api/graph/edges/review
POST /api/graph/nodes/move
POST /api/graph/floating-pages/merge
GET  /api/graph/changes/{app_id}
```

This will turn frontend operations into auditable graph curation records.
