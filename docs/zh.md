# AI 探索与增量遍历

## 1. 核心目标

本项目不应每次都重建整个应用图谱。

正确的长期模型是：

```text
已有的稳定图谱
+ 新截图
+ 新 AI 观察结果
+ 新的不确定/游离页面
+ 人工或 AI 归并决策
= 持续增长的应用图谱
```

最重要的规则：

```text
探索过程中不要直接修改原始图谱结构。
探索先产生证据。仅在置信度足够或人工确认后才执行归并。
```

## 2. AI 探索流程

AI 探索从一个游离/浮动 URL 页面开始。

示例：

```text
游离页面: /payment/face-verify
状态: not_in_tree
原因: 页面需要人脸验证，原始爬虫无法覆盖
```

推荐流程：

```text
1. 用户在游离页面上点击"AI 探索"。
2. 后端创建探索任务。
3. 后端调用 HDC 自动化脚本。
4. 脚本检查设备连接和应用状态。
5. 脚本尽可能打开 URL/deeplink。
6. 脚本采集截图、OCR、当前 URL/Activity、组件信息。
7. AI 分析此页面是否属于已有图谱分区。
8. 后端将结果存储为探索证据。
9. 前端展示以下状态之一：
   - 可归并 (mergeable)
   - 需人工拖拽归并 (needs human drag-to-merge)
   - 受阻 (blocked)
   - 失败 (failed)
```

## 3. 后端调用 HDC 脚本后发生什么

如果任务可能耗时较长，后端不应在 HTTP 请求内直接执行 AI 逻辑。

推荐架构：

```text
POST /api/ai/explorations
  -> 创建探索任务
  -> 将脚本作业入队
  -> 返回 task_id

GET /api/ai/explorations/{task_id}
  -> 返回任务状态和证据
```

执行序列：

```text
后端 API
-> 任务表: status = pending
-> Worker 进程
-> HDC 设备检查
-> 启动应用 / 打开 URL
-> 等待页面稳定
-> 截图
-> OCR / UI dump / Activity 采集
-> AI 页面分析
-> 保存 PageObservation
-> 保存 Asset
-> 保存 ExplorationResult
-> 任务表: status = mergeable / needs_review / blocked / failed
```

## 4. 后端 API 设计

### 4.1 启动 AI 探索

```http
POST /api/ai/explorations
```

请求：

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

响应：

```json
{
  "task_id": "explore_20260709_001",
  "status": "pending"
}
```

### 4.2 查询探索任务

```http
GET /api/ai/explorations/{task_id}
```

响应：

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
    "reason": "URL、OCR、页面布局和支付组件与已有支付分区匹配。",
    "evidence": {
      "screenshot_asset_id": "asset_001",
      "activity": "com.demo.PaymentActivity",
      "current_url": "/payment/face-verify",
      "ocr_keywords": ["支付", "人脸验证", "确认"],
      "structure_hash": "abc123",
      "similar_pages": [
        { "page_id": 45, "score": 0.82, "reason": "同属支付布局家族" }
      ]
    }
  }
}
```

### 4.3 一键归并

```http
POST /api/ai/explorations/{task_id}/merge
```

请求：

```json
{
  "target_parent_id": 45,
  "widget_description": "扫脸验证入口",
  "merge_mode": "append_child"
}
```

响应：

```json
{
  "status": "merged",
  "page_id": 123,
  "parent_id": 45,
  "edge_id": "edge_789"
}
```

### 4.4 人工拖拽归并

如果 AI 无法自信归并，前端应允许人工拖拽操作。

```http
POST /api/graph/manual-merge
```

请求：

```json
{
  "page_id": 123,
  "target_parent_id": 45,
  "widget_description": "人工归类：支付验证入口",
  "operator_note": "页面属于支付中心下的人脸验证分支",
  "source": "human_drag"
}
```

响应：

```json
{
  "status": "merged",
  "edge_id": "edge_790",
  "ai_recursive": true,
  "review_status": "human_confirmed"
}
```

## 5. 前端交互设计

### 5.1 游离页面状态

每个游离页面应有一个状态：

```text
not_explored   未探索
exploring      探索中
mergeable      可归并
needs_review   需审核
blocked        受阻
failed         失败
merged         已归并
```

UI 行为：

```text
not_explored  -> 显示"AI 探索"
exploring     -> 显示进度和任务状态
mergeable     -> 显示"归并"按钮
needs_review  -> 启用拖拽到树
blocked       -> 显示原因
failed        -> 显示重试
merged        -> 从游离列表移除，显示在主树中
```

### 5.2 拖拽归并

当 AI 无法一键归并时：

```text
1. 用户拖拽游离页面卡片。
2. 用户将其放到普通树节点上。
3. 前端弹出小型确认对话框。
4. 用户填写或确认 widget_description。
5. 后端创建 PageEdge。
6. 页面成为目标父节点下的子节点。
7. 页面获得 ai_recursive = true 且 review_status = human_confirmed。
```

放置确认字段：

```json
{
  "target_parent": "支付中心",
  "child_page": "扫脸支付",
  "widget_description": "扫脸验证入口",
  "operator_note": "人工拖拽归类"
}
```

## 6. HDC 脚本交互

后端应通过 Worker 脚本调用 HDC。

推荐命令：

```powershell
python scripts/hdc_explore.py --task-id explore_001 --app com.demo.app --url "/payment/face-verify" --out ./runs/explore_001
```

推荐脚本输出目录：

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

推荐 `result.json`：

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

## 7. HDC 脚本代码建议

推荐 Python 结构：

```text
scripts/
  hdc_client.py
  hdc_explore.py
  screenshot.py
  ui_dump.py
  page_stability.py
```

伪代码：

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

后端 Worker 随后将脚本结果送入 AI 分析：

```text
脚本结果
-> 归一化页面结构
-> 计算 screenshot_hash / structure_hash
-> 与 canonical_pages 比对
-> 向量搜索 page_text + OCR
-> 生成归并建议
```

## 8. 增量遍历

这是项目最重要的部分。

增量遍历意味着：

```text
从已知图谱出发。
仅探索未知或低置信度区域。
在不破坏已有规范结构的前提下添加新证据。
仅在置信度足够或人工确认后才提升新页面。
```

### 8.1 数据分层

分离以下层级：

```text
CanonicalPage
  稳定的功能页面节点

PageInstance
  单次运行中真实的截图/AI 观察结果

PageObservation
  AI/HDC 探索产生的临时证据

PageEdge
  已确认的跳转关系

CandidateEdge
  AI 建议的边，尚未确认
```

探索期间永远不要直接覆盖 `CanonicalPage`。

### 8.2 增量算法

对每一张新截图：

```text
1. 保存 Asset 并计算 screenshot_hash。
2. 执行 OCR 和组件检测。
3. 归一化布局并计算 structure_hash。
4. 搜索已有规范页面：
   - 精确匹配 structure_hash
   - 相似 visual_hash
   - page_text/OCR 的向量相似度
   - 路由/page_url 匹配
5. 如果高置信度：
   - 在已有 CanonicalPage 下创建 PageInstance
   - 增加证据计数
6. 如果中等置信度：
   - 创建 PageObservation
   - 标记为 review_required
7. 如果低置信度：
   - 创建游离页面
   - 允许 AI 探索或人工拖拽归并
```

### 8.3 不要改变原始结构

原始图谱应保持稳定。

添加新信息时：

```text
新截图     -> PageInstance
新的不确定页面 -> FloatingPage/PageObservation
新的可能边   -> CandidateEdge
已确认归并   -> PageEdge
```

这样可以防止一次错误的 AI 推断破坏整个图谱。

### 8.4 持续图像增长

一个规范页面可以拥有多张截图：

```text
CanonicalPage: 视频详情页
  PageInstance 1: 视频 A
  PageInstance 2: 视频 B
  PageInstance 3: 视频 C
```

对于信息流应用：

```text
不同内容
相同结构
相同规范页面
多张截图
```

推荐策略：

```text
保留所有截图作为证据。
选择一张代表性截图用于图谱展示。
使用最新/最高质量的截图用于 UI 预览。
永远不要仅因截图内容变化就创建新的 CanonicalPage。
```

## 9. 建议表结构

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

## 10. 产品原则

系统对图谱结构应持保守态度，对证据收集应持积极态度。

简而言之：

```text
自由探索。
慷慨存储证据。
谨慎归并。
永远不破坏旧图谱。
```
