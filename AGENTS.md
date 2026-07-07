# AGENTS.md

## Project Purpose

This repository is a continuously evolving project for third-party mobile app graph analysis.

The goal is to build an engineering-grade system that can:

- collect screenshots and AI recognition results from mobile automation scripts
- normalize app pages into reusable functional page nodes
- deduplicate pages by structure instead of dynamic content
- store graph, screenshot, OCR, widget, route, and embedding data
- visualize app page relationships in a Vue 3 frontend
- support replay-path analysis from user URL traces
- prepare for top-market app coverage at scale

## Knowledge Base

The long-term project notes are maintained in the user's Obsidian vault:

```text
D:\storage\obsidianwill\will
```

When adding important architecture, database, API, deployment, or business-process documentation, prefer creating readable Markdown documents that can be copied or saved into this vault.

Existing operational documentation:

```text
D:\storage\obsidianwill\will\App Relation 后端与 PostgreSQL 运行规则.md
```

## Current Stack

Frontend:

- Vue 3
- Vite
- shadcn-vue style components
- graph visualization for application page maps

Backend:

- Python
- FastAPI
- PostgreSQL
- pgvector
- local file ingestion for screenshots and AI JSON

Storage model:

- screenshots are stored locally first
- PostgreSQL stores metadata, graph entities, hashes, and vector records
- `structure_hash` is the primary functional page dedupe signal
- `screenshot_hash` is only for raw image identity

## Engineering Direction

Keep the project demo-ready and incrementally production-oriented.

Prefer changes that improve:

- clear UI interaction
- reliable graph layout
- readable backend APIs
- traceable import flow
- database schema clarity
- local reproducibility
- documentation for future continuation

Avoid large unrelated rewrites unless they directly support the next milestone.

## Backend Import Contract

Mobile scripts should save AI recognition output into a local folder. The backend reads JSON files from that folder.

Recommended folder shape:

```text
backend/inbox/{scan-name}/
  ai_result.json
  screenshots/
    home.png
    detail.png
```

AI JSON should include:

- `app`: package name, app name, platform, app version, market rank
- `scan`: device, script, AI model, runtime metadata
- `pages`: page instances, screenshots, OCR, AI summaries, widgets, normalized layout
- `edges`: transitions between pages caused by tap, swipe, long press, back, or deeplink

## Page Deduplication Rule

Do not treat every screenshot as a new page.

For content-feed apps, the same functional page may show different content. For example:

- different video content
- same video detail page structure
- different raw screenshot hash
- same or similar structure hash

The canonical graph node should represent the functional page, not the specific content item.

## API Debug Flow

Preferred local debug flow:

```text
1. Start PostgreSQL
2. Start FastAPI backend
3. Open http://127.0.0.1:8000/docs
4. Call GET /health
5. Call POST /api/imports/init-db
6. Put AI JSON and screenshots into backend/inbox
7. Call POST /api/imports/scan-folder
8. Call GET /api/graph/{app_id}
```

## Git Rules

Commit messages should use the requested format:

```text
feat: describe the change
fix: describe the fix
docs: describe documentation changes
```

Do not commit local runtime artifacts:

- Python virtual environments
- frontend build outputs
- node_modules
- local screenshot batches
- PostgreSQL data files
- generated caches

## Collaboration Notes

When continuing this project, first inspect:

- `README.md`
- `backend/README.md`
- `backend/examples/ai_result_example.json`
- frontend graph components under `src/`
- current git status

The project is intended to keep evolving through repeated product, frontend, backend, database, and AI-analysis iterations.

