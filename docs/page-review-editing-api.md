# Page Review Editing API

## Purpose

The page review editing flow lets a human reviewer double check AI-inferred graph content before treating it as reliable graph knowledge.

The frontend right inspector supports editing:

- page title
- page URL
- AI page description
- AI inference label
- AI inference reason
- whether the page was AI recursively discovered
- parent widget description
- screenshot/image evidence list
- human review note

The graph canvas updates immediately after saving so the reviewer can see the edited page content in the graph area.

## Endpoint

```http
POST /api/graph/pages/review
POST /api/graph/page-review
```

## Request Body

```json
{
  "backend_id": "optional canonical page uuid or demo id",
  "node_id": "page-xxx",
  "page_title": "消息详情页",
  "page_text": "AI 或人工复核后的页面描述",
  "page_url": "/message/detail",
  "image_url": "screenshots/message-detail.png",
  "image_urls": [
    "screenshots/message-detail.png",
    "screenshots/message-detail-state-2.png"
  ],
  "ai_inference": {
    "label": "AI 推断: 消息链路页面",
    "reason": "页面结构包含消息标题、正文、回复入口，因此应归入消息分区。"
  },
  "ai_recursive": true,
  "widget_description": "消息列表项",
  "review_status": "edited",
  "review_note": "人工确认该页面应挂在消息列表下。"
}
```

## Response Body

```json
{
  "nodeId": "page-xxx",
  "backend_id": "optional canonical page uuid or demo id",
  "page_title": "消息详情页",
  "page_text": "AI 或人工复核后的页面描述",
  "page_url": "/message/detail",
  "image_url": "screenshots/message-detail.png",
  "image_urls": [
    "screenshots/message-detail.png",
    "screenshots/message-detail-state-2.png"
  ],
  "ai_inference": {
    "label": "AI 推断: 消息链路页面",
    "reason": "页面结构包含消息标题、正文、回复入口，因此应归入消息分区。"
  },
  "ai_recursive": true,
  "widget_description": "消息列表项",
  "review_status": "edited",
  "review_note": "人工确认该页面应挂在消息列表下。",
  "persisted": true
}
```

`persisted` indicates whether the backend found a persisted `canonical_pages` record and wrote the review result into PostgreSQL. If the frontend is using demo numeric ids, the endpoint still returns a normalized response with `persisted: false`; the frontend can still update the local graph for demo and review continuity.

## Persistence Behavior

When the request resolves to a real `canonical_pages.canonical_page_id`:

- `canonical_pages.display_name` is updated from `page_title`.
- `canonical_pages.review_status` is updated from `review_status`.
- the latest related `page_instances` record receives:
  - `page_title`
  - `ai_summary`
  - `inferred_purpose`
  - `ai_recursive`
  - `raw_ai_payload.human_review`

The current implementation intentionally avoids creating new screenshot asset rows from arbitrary image keys. Image keys are returned to the frontend and should later be normalized into an asset-management endpoint.

## Recommended Next Tables

For production auditability, add a dedicated review/change table:

```text
graph_change_events
  change_id
  app_id
  node_id
  canonical_page_id
  change_type
  before_payload
  after_payload
  reviewer
  review_note
  created_at
```

This separates human review history from the current canonical page state.

## Frontend Flow

```text
select node
-> right inspector
-> 开启编辑
-> edit AI reasoning / image evidence / page fields
-> 保存复核
-> POST /api/graph/pages/review
-> update local graph node
-> graph canvas reflects edited title/text/image
```
