# AI Exploration And Incremental Traversal

## 1. Core Objective

This project should not rebuild the whole app graph every time.

The correct long-term model is:

```text
existing stable graph
+ new screenshots
+ new AI observations
+ new uncertain/orphan pages
+ human or AI merge decisions
= continuously growing app graph
```

The most important rule:

```text
Do not mutate the original graph structure directly during exploration.
Exploration creates evidence first. Merge only after confidence or human confirmation.
```

## 2. AI Exploration Flow

AI exploration starts from an orphan/floating URL page.

Example:

```text
floating page: /payment/face-verify
status: not_in_tree
reason: page requires face verification, original crawler could not cover it
```

Recommended flow:

```text
1. User clicks "AI Explore" on a floating page.
2. Backend creates an exploration task.
3. Backend calls HDC automation script.
4. Script checks device connection and app state.
5. Script opens the URL/deeplink if possible.
6. Script captures screenshot, OCR, current URL/activity, widget info.
7. AI analyzes whether the page belongs to an existing graph partition.
8. Backend stores the result as exploration evidence.
9. Frontend shows one of:
   - mergeable
   - needs human drag-to-merge
   - blocked
   - failed
```

## 3. What Happens After Backend Calls HDC Script

The backend should not run AI logic directly inside the HTTP request if the task may take time.

Recommended architecture:

```text
POST /api/ai/explorations
  -> create exploration task
  -> enqueue script job
  -> return task_id

GET /api/ai/explorations/{task_id}
  -> return task status and evidence
```

Execution sequence:

```text
backend API
-> task table: status = pending
-> worker process
-> hdc device check
-> launch app / open URL
-> wait for page stable
-> screenshot
-> OCR / UI dump / activity capture
-> AI page analysis
-> save PageObservation
-> save Asset
-> save ExplorationResult
-> task table: status = mergeable / needs_review / blocked / failed
```

## 4. Backend API Design

### 4.1 Start AI Exploration

```http
POST /api/ai/explorations
```

Request:

```json
{
  "app_name": "demo",
  "floating_page_id": 123,
  "node_id": "page-123",
  "page_url": "/payment/face-verify",
  "page_title": "扫脸支付",
  "page_text": "支付链路中的人脸验证页面",
  "image_url": "s3://bucket/path.png",
  "strategy": {
    "mode": "open_url",
    "max_depth": 2,
    "max_steps": 8,
    "timeout_ms": 30000
  }
}
```

Response:

```json
{
  "task_id": "explore_20260709_001",
  "status": "pending"
}
```

### 4.2 Query Exploration Task

```http
GET /api/ai/explorations/{task_id}
```

Response:

```json
{
  "task_id": "explore_20260709_001",
  "status": "mergeable",
  "result": {
    "can_merge": true,
    "confidence": 0.86,
    "target_parent_id": 45,
    "target_parent_title": "支付中心",
    "widget_description": "扫脸验证入口",
    "reason": "URL, OCR, page layout and payment widgets match the existing payment partition.",
    "evidence": {
      "screenshot_asset_id": "asset_001",
      "activity": "com.demo.PaymentActivity",
      "current_url": "/payment/face-verify",
      "ocr_keywords": ["支付", "人脸验证", "确认"],
      "structure_hash": "abc123",
      "similar_pages": [
        { "page_id": 45, "score": 0.82, "reason": "same payment layout family" }
      ]
    }
  }
}
```

### 4.3 One-click Merge

```http
POST /api/ai/explorations/{task_id}/merge
```

Request:

```json
{
  "target_parent_id": 45,
  "widget_description": "扫脸验证入口",
  "merge_mode": "append_child"
}
```

Response:

```json
{
  "status": "merged",
  "page_id": 123,
  "parent_id": 45,
  "edge_id": "edge_789"
}
```

### 4.4 Manual Drag Merge

If AI cannot confidently merge, frontend should allow human drag operation.

```http
POST /api/graph/manual-merge
```

Request:

```json
{
  "page_id": 123,
  "target_parent_id": 45,
  "widget_description": "人工归类：支付验证入口",
  "operator_note": "页面属于支付中心下的人脸验证分支",
  "source": "human_drag"
}
```

Response:

```json
{
  "status": "merged",
  "edge_id": "edge_790",
  "ai_recursive": true,
  "review_status": "human_confirmed"
}
```

## 5. Frontend Interaction Design

### 5.1 Floating Page States

Each floating page should have a state:

```text
not_explored
exploring
mergeable
needs_review
blocked
failed
merged
```

UI behavior:

```text
not_explored -> show "AI Explore"
exploring -> show progress and task status
mergeable -> show "Merge" button
needs_review -> enable drag-to-tree
blocked -> show reason
failed -> show retry
merged -> remove from floating list and show in main tree
```

### 5.2 Drag-to-Merge

When AI cannot one-click merge:

```text
1. User drags floating page card.
2. User drops it onto a normal tree node.
3. Frontend opens a small confirmation dialog.
4. User fills or confirms widget_description.
5. Backend creates PageEdge.
6. Page becomes child node under target parent.
7. Page gets ai_recursive = true and review_status = human_confirmed.
```

Drop confirmation fields:

```json
{
  "target_parent": "支付中心",
  "child_page": "扫脸支付",
  "widget_description": "扫脸验证入口",
  "operator_note": "人工拖拽归类"
}
```

## 6. HDC Script Interaction

The backend should call HDC through a worker script.

Recommended command:

```powershell
python scripts/hdc_explore.py --task-id explore_001 --app com.demo.app --url "/payment/face-verify" --out ./runs/explore_001
```

Recommended script output folder:

```text
runs/explore_001/
  result.json
  screenshots/
    before.png
    after.png
  logs/
    hdc.log
    device.log
```

Recommended `result.json`:

```json
{
  "task_id": "explore_001",
  "status": "success",
  "device": {
    "serial": "ABC123",
    "connected": true
  },
  "app": {
    "package_name": "com.demo.app",
    "activity": "com.demo.PaymentActivity"
  },
  "navigation": {
    "input_url": "/payment/face-verify",
    "current_url": "/payment/face-verify",
    "opened": true
  },
  "screenshots": [
    {
      "type": "after_open",
      "path": "screenshots/after.png",
      "sha256": "..."
    }
  ],
  "ocr": {
    "text": "支付 人脸验证 确认",
    "keywords": ["支付", "人脸验证", "确认"]
  },
  "ui": {
    "widgets": [
      {
        "text": "确认",
        "widget_type": "button",
        "bbox": { "x": 120, "y": 1500, "width": 840, "height": 96 }
      }
    ]
  },
  "errors": []
}
```

## 7. HDC Script Code Recommendation

Recommended Python structure:

```text
scripts/
  hdc_client.py
  hdc_explore.py
  screenshot.py
  ui_dump.py
  page_stability.py
```

Pseudo code:

```python
def run_exploration(task):
    device = hdc.check_device()
    if not device.connected:
        return failed("device_not_connected")

    hdc.wake_screen()
    hdc.unlock_if_needed()
    hdc.start_app(task.package_name)

    before = hdc.screenshot("before.png")

    opened = hdc.open_url(task.package_name, task.page_url)
    if not opened:
        return blocked("url_open_failed")

    wait_page_stable(timeout_ms=task.timeout_ms)

    after = hdc.screenshot("after.png")
    activity = hdc.current_activity()
    ui_xml = hdc.dump_ui()
    ocr_text = run_ocr(after)

    result = {
        "status": "success",
        "activity": activity,
        "screenshots": [before, after],
        "ocr": ocr_text,
        "ui": parse_widgets(ui_xml),
    }
    write_json(result)
```

Backend worker then sends the script result to AI analysis:

```text
script result
-> normalize page structure
-> compute screenshot_hash / structure_hash
-> compare with canonical_pages
-> vector search page_text + OCR
-> generate merge recommendation
```

## 8. Incremental Traversal

This is the most important part of the project.

Incremental traversal means:

```text
Start from known graph.
Only explore unknown or low-confidence areas.
Add new evidence without damaging existing canonical structure.
Promote new pages only after confidence/human confirmation.
```

### 8.1 Data Layers

Separate these layers:

```text
CanonicalPage
  stable functional page node

PageInstance
  actual screenshot/AI observation from one run

PageObservation
  temporary evidence from AI/HDC exploration

PageEdge
  confirmed transition relationship

CandidateEdge
  AI-suggested edge, not confirmed yet
```

Never directly overwrite `CanonicalPage` during exploration.

### 8.2 Incremental Algorithm

For every new screenshot:

```text
1. Save asset and compute screenshot_hash.
2. Run OCR and widget detection.
3. Normalize layout and compute structure_hash.
4. Search existing canonical pages:
   - exact structure_hash
   - similar visual_hash
   - vector similarity of page_text/OCR
   - route/page_url match
5. If high confidence:
   - create PageInstance under existing CanonicalPage
   - increase evidence count
6. If medium confidence:
   - create PageObservation
   - mark as review_required
7. If low confidence:
   - create floating page
   - allow AI exploration or human drag merge
```

### 8.3 Do Not Change Original Structure

Original graph should be stable.

When adding new information:

```text
new screenshot -> PageInstance
new uncertain page -> FloatingPage/PageObservation
new possible edge -> CandidateEdge
confirmed merge -> PageEdge
```

This prevents one bad AI inference from destroying the graph.

### 8.4 Continuous Image Growth

A canonical page can have many screenshots:

```text
CanonicalPage: 视频详情页
  PageInstance 1: video A
  PageInstance 2: video B
  PageInstance 3: video C
```

For feed apps:

```text
different content
same structure
same canonical page
many screenshots
```

Recommended policy:

```text
Keep all screenshots as evidence.
Select one representative screenshot for graph display.
Use newest/highest-quality screenshot for UI preview.
Never create a new CanonicalPage only because screenshot content changed.
```

## 9. Suggested Tables

```text
ai_exploration_tasks
- task_id
- app_id
- page_id
- page_url
- status
- strategy_json
- result_json
- created_at
- finished_at

page_observations
- observation_id
- task_id
- app_id
- screenshot_asset_id
- page_url
- activity
- ocr_text
- structure_hash
- visual_hash
- widgets_json
- ai_summary
- confidence

candidate_edges
- candidate_edge_id
- from_page_id
- to_page_id
- widget_description
- confidence
- reason
- status

manual_merge_events
- merge_event_id
- page_id
- target_parent_id
- widget_description
- operator_note
- created_at
```

## 10. Product Principle

The system should be conservative with graph structure and aggressive with evidence collection.

In short:

```text
Explore freely.
Store evidence generously.
Merge carefully.
Never destroy the old graph.
```

