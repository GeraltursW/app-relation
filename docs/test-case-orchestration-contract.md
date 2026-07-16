# 图谱用例编排后端与脚本契约

## 1. 系统职责

建议将能力拆成四层：

```text
图谱层：页面、边、动作、截图和结构版本
用例层：起点、路径、操作步骤、断言和采集策略
执行层：设备调度、脚本状态、重试和错误恢复
结果层：步骤事件、截图、性能采样、聚合指标和报告
```

用例不能直接修改图谱。它通过 `page_id / edge_id / action_id` 引用已确认图谱，并保存创建时的 `graph_version`，从而判断图谱变化后用例是否需要重新校验。

## 2. 后端需要准备

### 2.1 建议数据表

#### test_cases

```text
id                  uuid primary key
app_id              uuid
name                varchar
case_type           path | scenario
graph_version       varchar
start_page_id       varchar
target_page_id      varchar nullable
collection_config   jsonb
status              draft | active | archived
created_at          timestamptz
updated_at          timestamptz
```

#### test_case_steps

```text
id                  uuid primary key
case_id             uuid
step_no             integer
step_type           navigate | tap | swipe | long_press | wait | input | back | collect
page_id             varchar
edge_id             varchar nullable
action_id           varchar nullable
locator_snapshot    jsonb
parameters          jsonb
assertion            jsonb
```

#### test_runs

```text
id                  uuid primary key
case_id             uuid
device_id           varchar
graph_version       varchar
status              queued | running | passed | failed | stopped
current_step        integer
started_at          timestamptz
finished_at         timestamptz
summary             jsonb
```

#### test_run_events

```text
id                  bigserial primary key
run_id              uuid
step_no             integer
event_type          step_started | action_done | page_verified | sample | step_failed
payload             jsonb
created_at          timestamptz
```

#### performance_samples

```text
id                  bigserial primary key
run_id              uuid
step_no             integer nullable
timestamp_ms        bigint
cpu_percent         numeric
memory_mb           numeric
fps                 numeric
jank_percent        numeric
power_mw            numeric
temperature_c       numeric
raw_metrics         jsonb
```

### 2.2 建议接口

```http
GET    /test_cases?app_name=QQ
POST   /test_cases
PUT    /test_cases/{case_id}
DELETE /test_cases/{case_id}

POST   /test_cases/{case_id}/validate
POST   /test_cases/{case_id}/dispatch

GET    /test_runs/{run_id}
POST   /test_runs/{run_id}/stop
POST   /test_runs/{run_id}/events
POST   /test_runs/{run_id}/samples
GET    /test_runs/{run_id}/report

GET    /test_runs/{run_id}/stream
```

`/stream` 推荐使用 SSE；如果后续需要网页向脚本发送暂停、继续、人工确认等双向命令，再升级为 WebSocket。

### 2.3 下发请求示例

```json
{
  "device_id": "HDC_DEVICE_001",
  "case_id": "qq-path-chat-performance",
  "graph_version": "qq-20260717-01",
  "options": {
    "retry_count": 2,
    "capture_step_screenshot": true,
    "restore_app_before_run": true
  }
}
```

后端响应：

```json
{
  "status": "success",
  "run_id": "run-20260717-0001",
  "state": "queued"
}
```

## 3. 脚本需要准备

### 3.1 标准输入

脚本接收一个完整且不可变的执行快照：

```json
{
  "run_id": "run-20260717-0001",
  "app": {
    "package_name": "com.tencent.mobileqq",
    "launch_activity": "..."
  },
  "device": {
    "device_id": "HDC_DEVICE_001"
  },
  "steps": [],
  "collection": {
    "trigger": "case_lifecycle",
    "sample_interval_ms": 500,
    "metrics": ["cpu", "memory", "fps", "jank", "power", "temperature"]
  },
  "callback": {
    "event_url": "/test_runs/run-20260717-0001/events",
    "sample_url": "/test_runs/run-20260717-0001/samples"
  }
}
```

### 3.2 操作执行器

至少实现：

- `tap`
- `swipe`
- `long_press`
- `wait`
- `input`
- `back`
- `deeplink`
- `collect`

滑动和长按不要只保存绝对坐标。推荐使用屏幕比例坐标和语义目标：

```json
{
  "type": "swipe",
  "target": "feed_area",
  "start_ratio": [0.5, 0.78],
  "end_ratio": [0.5, 0.28],
  "duration_ms": 420,
  "repeat": 5
}
```

### 3.3 控件定位降级顺序

```text
resource_id
  -> accessibility / content description
  -> text + class
  -> 页面内相对区域
  -> bbox_ratio
  -> 图像模板
  -> AI 视觉定位
```

脚本每次操作都应记录最终使用的定位方式、命中控件、置信度和实际坐标，便于人工复核 AI 动作。

### 3.4 页面校验

每个跳转步骤完成后校验：

- 当前 URL 或路由标识
- `structure_hash`
- OCR 关键文本
- 关键控件集合
- 截图相似度
- AI 页面分类结果

单一 URL 可能对应多个图谱页面，因此 URL 只能作为候选召回条件，最终确认应结合结构特征。

### 3.5 性能采集

脚本侧需要统一采集适配器，屏蔽 HDC、Perfetto、dumpsys 或厂商接口差异。每条采样必须携带：

```json
{
  "run_id": "run-20260717-0001",
  "step_no": 3,
  "timestamp_ms": 1784212345000,
  "metrics": {
    "cpu_percent": 32.4,
    "memory_mb": 612,
    "fps": 56.8,
    "jank_percent": 4.1,
    "power_mw": 824,
    "temperature_c": 39.4
  }
}
```

使用统一时钟将操作事件、截图和性能样本对齐，网页才能准确指出“第几次滑动导致功耗峰值”。

### 3.6 失败恢复

脚本应支持：

- 操作超时后重新识别控件。
- 页面未命中时执行返回或重新启动应用。
- 在限定次数内重试当前步骤。
- 保存失败截图、UI 树、OCR 和日志。
- 可从最近成功步骤断点续跑。
- 收到后端停止指令后安全结束采集。

## 4. 后端校验规则

下发前必须校验：

1. `graph_version` 与当前图谱兼容。
2. 所有 `page_id` 存在且未删除。
3. 路径型用例中的 `edge_id` 连续，前一页目标等于后一页起点。
4. `action_id` 属于对应页面或边。
5. 设备在线且未被其他任务占用。
6. 采集指标被目标设备支持。

## 5. 推荐实施顺序

1. 先实现测试用例 CRUD 和 `validate`。
2. 实现单设备串行任务队列及 `dispatch`。
3. 脚本先支持 tap、swipe、long_press、wait 和页面校验。
4. 打通事件回传和 SSE 实时状态。
5. 接入性能采样与报告聚合。
6. 最后增加多设备调度、失败恢复和历史趋势分析。
