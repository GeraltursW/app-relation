# AI 全场景用户行为用例生成方案

## 1. 目标

本方案解决三个问题：

1. AI 如何从截图、UI 树、OCR、URL、前后页面和系统状态中识别动作。
2. AI 如何将动作稳定归入四层结构：`popupAction`、`stateAction`、`externalAction`、`pageNaviAction`。
3. AI 如何基于应用图谱和四层动作生成覆盖应用内行为、应用切换和返回链路的可执行用例。

系统最终形成四个相互独立但可追溯的层次：

```text
页面图谱：有哪些功能页面、页面之间如何到达
动作模型：每个页面上可以执行什么动作、动作产生什么效果
测试用例：在什么前置条件下，按什么顺序执行动作
运行证据：实际页面、截图、性能数据、失败原因和恢复过程
```

关键原则：

- 图谱描述“可能性”，用例描述“一次确定执行计划”。
- `action_type` 描述用户如何操作，四层结构描述操作造成什么效果。
- 不因点赞、滑动、弹窗等局部变化创建错误的页面子节点。
- 应用内图谱保持独立；跨应用行为由用例层的应用上下文和交接记录连接。
- AI 结果必须可解释、可复核、可版本化，不能只保存最终标签。

## 2. 四层动作结构

后端与前端继续使用固定顶层对象：

```json
{
  "action": {
    "popupAction": [],
    "stateAction": [],
    "externalAction": [],
    "pageNaviAction": []
  }
}
```

### 2.1 popupAction

动作打开弹窗、抽屉、半屏面板、浮层或上下文菜单，但用户仍处于同一个功能页面上下文。

典型动作：

- 点击筛选按钮打开筛选抽屉
- 点击评论打开半屏评论面板
- 长按图片打开上下文菜单
- 点击商品规格打开 SKU 面板

判定信号：

- 前后 `page_id` 或 `structure_hash` 基本不变。
- 前景应用包名不变。
- 页面出现新的高层级窗口、遮罩或局部面板。
- 返回键或关闭按钮通常可以恢复原页面。

### 2.2 stateAction

动作只改变当前页面状态、内容或业务数据，不切换功能页面，也不打开独立浮层。

典型动作：

- 点赞、收藏、关注
- 加入购物车、领取优惠券
- 切换开关、选择 Tab
- 信息流滑动到下一条相同结构内容
- 输入搜索词后刷新建议

判定信号：

- `structure_hash` 保持相同或变化低于阈值。
- URL/路由和前景包名不变。
- 某个控件属性、文本、计数、选中态或内容实例发生变化。
- 变化可以描述成 `state_key: before -> after`。

### 2.3 externalAction

动作把控制权交给系统组件、SDK、浏览器或另一个应用。

典型动作：

- 打开系统相机、系统分享、文件选择器
- 进入支付 SDK、人脸识别或权限授权页
- 从外卖应用打开地图导航
- 从社交应用跳转浏览器或小程序宿主

判定信号：

- 前景包名、Activity、窗口所有者或进程发生变化。
- 出现系统 UI、第三方 SDK 容器或另一个已知应用。
- 原应用进入后台，之后可能通过返回、回调或 Deep Link 恢复。

### 2.4 pageNaviAction

动作在当前应用内进入另一个功能页面，是应用图谱边的动作来源。

典型动作：

- 首页点击消息进入消息中心
- 商品列表点击商品进入详情页
- 左右滑动切换到不同功能 Tab
- 返回上一级页面

判定信号：

- 前景应用包名不变。
- 目标 canonical page 与源页面不同。
- URL、Activity、关键控件集合或 `structure_hash` 明显变化。
- 可以确定 `target_page_id`，并形成 `source_page -> target_page` 图谱边。

## 3. action_type 与动作分层不能混淆

`action_type` 是操作方式，四层结构是效果类型。同一种操作可以落入不同层：

| action_type | 动作层 | 示例 |
| --- | --- | --- |
| tap | pageNaviAction | 点击商品进入详情页 |
| tap | stateAction | 点赞 |
| tap | popupAction | 打开筛选抽屉 |
| tap | externalAction | 打开系统相机 |
| swipe | stateAction | 刷下一条相同结构视频 |
| swipe | pageNaviAction | 左滑切换到附近功能页 |
| long_press | popupAction | 长按图片打开菜单 |
| long_press | stateAction | 长按录音并持续更新录音状态 |
| back | pageNaviAction | 返回应用内上一页 |
| back | externalAction | 从外部应用返回源应用 |

建议支持的 `action_type`：

```text
tap / double_tap / long_press / swipe / drag / pinch
input / clear / submit / back / home / deeplink / wait
```

## 4. 动作字段设计

### 4.1 通用字段

四层数组中的每个动作统一使用以下结构：

```json
{
  "id": "act_video_like_001",
  "label": "点赞",
  "description": "点击右侧点赞按钮，切换当前视频点赞状态",
  "action_type": "tap",
  "source_page_id": "page_hash_video_detail",
  "target": {
    "resource_id": "com.demo:id/like",
    "text": "点赞",
    "accessibility": "点赞",
    "role": "button",
    "region": "right_action_bar",
    "bbox_ratio": [0.86, 0.42, 0.96, 0.52],
    "image_anchor": "like_icon"
  },
  "params": {
    "duration_ms": 120,
    "repeat": 1
  },
  "preconditions": [],
  "expected": {},
  "wait": {
    "type": "ui_stable",
    "timeout_ms": 5000
  },
  "fallback": {
    "retry": 2,
    "strategies": ["refresh_ui_tree", "visual_relocate"]
  },
  "confidence": 0.94,
  "evidence": {
    "ocr": ["点赞"],
    "widget_path": "/FrameLayout/.../ImageButton[2]",
    "before_screenshot_id": "asset_before",
    "after_screenshot_id": "asset_after",
    "before_structure_hash": "hash_a",
    "after_structure_hash": "hash_a",
    "foreground_package_before": "com.demo.app",
    "foreground_package_after": "com.demo.app",
    "reason": "页面结构不变，点赞图标由未选中变为选中"
  },
  "source": "ai_probe",
  "review_status": "ai_generated",
  "model_version": "vision-action-v1",
  "schema_version": "action-v1"
}
```

定位字段采用降级链：

```text
resource_id
  -> accessibility
  -> text + role
  -> UI 树路径
  -> 相对区域 + bbox_ratio
  -> image_anchor
  -> AI 视觉定位
```

不要只保存绝对像素坐标。不同设备分辨率、字体和系统缩放会导致绝对坐标失效。

### 4.2 popupAction 专属字段

```json
{
  "popup_name": "评论半屏面板",
  "popup_type": "bottom_sheet",
  "expected": {
    "popup_visible": true,
    "ocr_keywords": ["评论", "发送"],
    "dismiss_actions": ["back", "tap_mask", "close_button"],
    "source_page_should_remain": true
  }
}
```

### 4.3 stateAction 专属字段

```json
{
  "state_key": "liked",
  "state_before": false,
  "state_value": true,
  "reversible": true,
  "expected": {
    "page_structure_should_same": true,
    "changed_widgets": ["like_button", "like_count"]
  }
}
```

对于信息流滑动，动态内容标识可以变化，但 canonical page 不变：

```json
{
  "state_key": "content_instance",
  "state_before": "video_A",
  "state_value": "next_item",
  "page_structure_should_same": true
}
```

### 4.4 externalAction 专属字段

```json
{
  "target_type": "application",
  "target_app": {
    "app_name": "地图",
    "package_name": "com.map.app"
  },
  "handoff": {
    "method": "intent",
    "uri_pattern": "map://navigation/*",
    "expected_foreground_package": "com.map.app"
  },
  "return_policy": {
    "required": true,
    "method": "back_or_callback",
    "expected_source_page_id": "page_hash_order_detail"
  }
}
```

### 4.5 pageNaviAction 专属字段

```json
{
  "target_page_id": "page_hash_product_detail",
  "target_page_title": "商品详情",
  "edge_id": "edge_list_to_detail",
  "expected": {
    "target_page_ids": ["page_hash_product_detail"],
    "match_by": ["structure_hash", "page_url", "widget_set", "ocr_keywords"]
  }
}
```

`pageNaviAction` 与 `page_edges` 必须能相互校验。未人工复核时可以从已确认边生成；一旦用户通过 `/update_node` 保存完整 `action`，人工版本成为权威数据。

## 5. AI 如何推断动作分层

### 5.1 输入数据

每次动作探测至少保存：

```text
动作前截图、UI 树、OCR、URL、Activity、前景包名
候选控件语义、位置、可点击性和父子结构
执行的 action_type 与参数
动作后截图、UI 树、OCR、URL、Activity、前景包名
系统窗口、权限窗口、SDK 容器和应用生命周期事件
页面匹配结果与 structure_hash
```

只有静态截图时，AI只能生成“候选动作”；拥有动作前后证据后，才能生成“已验证动作”。

### 5.2 推断流水线

```text
1. 控件候选检测
2. 控件语义理解
3. 风险过滤
4. 安全探测执行
5. 前后状态对比
6. 效果层分类
7. 目标页面或状态绑定
8. 置信度与证据保存
9. 人工复核或自动确认
```

### 5.3 分类决策

推荐先使用确定性规则，再让模型处理模糊场景：

```text
if foreground_package changed or system_window appeared:
    externalAction
else if canonical_page_id changed:
    pageNaviAction
else if overlay_window_added or mask_added:
    popupAction
else if widget_state_changed or content_instance_changed:
    stateAction
else:
    unresolvedAction
```

模型输出四层概率，而不是只输出一个标签：

```json
{
  "classification": {
    "selected": "popupAction",
    "probabilities": {
      "popupAction": 0.78,
      "stateAction": 0.16,
      "externalAction": 0.01,
      "pageNaviAction": 0.05
    },
    "reason": "出现遮罩和底部面板，页面结构与前景包名保持不变"
  }
}
```

建议阈值：

- `confidence >= 0.90` 且规则证据一致：自动确认。
- `0.70 <= confidence < 0.90`：保留为 AI 结果，进入抽样复核。
- `confidence < 0.70` 或规则与模型冲突：必须人工复核。
- 支付、删除、发消息、下单、关注等高风险动作无论置信度多高都需要策略许可。

### 5.4 模糊场景处理

同一控件可能产生多种结果：

```text
点击支付
├── 应用内收银台：pageNaviAction
├── 支付 SDK：externalAction
├── 登录弹窗：popupAction
└── 余额变化：stateAction
```

因此动作定义允许多个 outcome：

```json
{
  "outcomes": [
    { "layer": "pageNaviAction", "target_page_id": "cashier", "probability": 0.45 },
    { "layer": "externalAction", "target": "payment_sdk", "probability": 0.35 },
    { "layer": "popupAction", "popup_name": "登录提示", "probability": 0.20 }
  ]
}
```

生成用例时，每个重要 outcome 应形成独立分支，不强行压成一个确定结果。

## 6. 应用内动作与应用间切换

### 6.1 应用内动作

应用内保持当前 `app_id` 和 `package_name`：

- `pageNaviAction` 更新当前 `page_id`。
- `popupAction` 更新 overlay stack，不改变当前 canonical page。
- `stateAction` 更新 page state，不改变当前 canonical page。
- 页面返回时同时校验 page stack。

运行上下文：

```json
{
  "app_context": {
    "current_app_id": "qq",
    "current_package": "com.tencent.mobileqq",
    "current_page_id": "message_list",
    "page_stack": ["home", "message_center", "message_list"],
    "overlay_stack": [],
    "state": {}
  }
}
```

### 6.2 应用间切换

不建议把两个应用的全部页面强行混成一棵树。采用两层图：

```text
应用内 Page Graph
  +
跨应用 App Transition Graph
```

跨应用边保存：

```text
source_app_id
source_page_id
source_action_id
target_app_id / target_package
target_entry_page_id（已覆盖时）
handoff_method
uri_pattern
return_policy
```

用例执行状态机：

```text
SOURCE_APP_ACTIVE
  -> EXTERNAL_HANDOFF
  -> TARGET_APP_ACTIVE
  -> TARGET_APP_ACTIONS
  -> RETURN_HANDOFF
  -> SOURCE_APP_RESUMED
```

如果目标应用也在 Top 225 覆盖范围内，脚本切换到目标应用图谱继续规划；如果目标应用未覆盖，则把它当作 external boundary，只验证包名、系统窗口和返回结果。

跨应用用例示例：

```json
{
  "case_name": "订单地址打开地图并返回",
  "steps": [
    {
      "app_id": "delivery_app",
      "page_id": "order_detail",
      "action_id": "open_map",
      "layer": "externalAction",
      "expected_app": "map_app"
    },
    {
      "app_id": "map_app",
      "page_id": "route_preview",
      "action_type": "swipe",
      "layer": "stateAction",
      "expected_state": "map_viewport_changed"
    },
    {
      "app_id": "map_app",
      "action_type": "back",
      "layer": "externalAction",
      "expected_app": "delivery_app",
      "expected_page_id": "order_detail"
    }
  ]
}
```

## 7. AI 全场景用例生成流程

### 7.1 生成输入

```text
已确认页面图谱及 graph_version
四层动作及 action_version
应用列表与跨应用交接关系
官方 Function Tree
用户画像与业务目标
账号、权限、地址、网络、地区等前置状态
设备支持的操作与性能指标
历史运行结果和线上 URL/埋点分布
风险动作策略
```

### 7.2 用例生成阶段

#### 阶段 A：基础覆盖

1. 每条根到叶简单路径生成一个终点采集用例。
2. 每个 `stateAction` 至少生成正向动作；可逆动作增加恢复动作。
3. 每个 `popupAction` 生成打开、面板内操作和关闭用例。
4. 每个 `externalAction` 生成成功交接、取消和返回用例。
5. 每个 `pageNaviAction` 校验存在可执行边和目标页面断言。

#### 阶段 B：场景组合

AI 按用户目标把四层动作组合成行为链：

```text
进入页面
  -> 局部状态准备
  -> 打开弹层并操作
  -> 页面跳转
  -> 连续滑动/长按/输入
  -> 外部应用交接（可选）
  -> 返回源应用
  -> 结果断言与性能采集
```

推荐行为语法：

```ebnf
Scenario = Precondition, Navigation*, Interaction+, ExternalFlow?, Assertion;
Interaction = StateAction | PopupFlow | NavigationAction;
PopupFlow = OpenPopup, PopupInteraction*, ClosePopup;
ExternalFlow = Handoff, TargetAppAction*, ReturnToSource;
```

#### 阶段 C：组合降维

不能对页面、动作、状态和设备做笛卡尔积。采用：

- 单动作覆盖：每个动作至少出现一次。
- 动作对覆盖：覆盖重要的前后动作组合。
- Pairwise/正交组合：覆盖权限、网络、账号、主题等参数。
- 风险加权：支付、登录、视频、直播、跨应用获得更高权重。
- 线上频率加权：URL/埋点高频路径优先。
- 历史缺陷加权：失败率和性能退化高的动作优先。
- 长度约束：默认 3 到 12 步，超过后拆分。
- 状态约束：过滤不满足前置条件或互相矛盾的组合。

### 7.3 场景覆盖矩阵

生成器至少计算以下覆盖率：

| 覆盖维度 | 目标 |
| --- | --- |
| 页面路径 | 每条目标路径有用例 |
| 动作层 | 四层动作均被覆盖 |
| action_type | tap、swipe、long_press、input、back 等 |
| 状态 | 登录/未登录、选中/未选中、首次/非首次 |
| 弹层 | 打开、操作、关闭、异常关闭 |
| 外部边界 | 成功、取消、授权拒绝、返回 |
| 应用切换 | 源应用 -> 目标应用 -> 源应用 |
| 参数 | 方向、次数、时长、输入类型 |
| 性能窗口 | 页面跳转、连续交互、外部交接 |

## 8. AI 生成用例的数据结构

```json
{
  "case_id": "case_ai_001",
  "case_name": "视频浏览、点赞、评论并分享返回",
  "case_type": "ai_scenario",
  "source": "ai_generated",
  "app_id": "short_video_app",
  "graph_version": "graph-20260722-01",
  "action_version": "action-20260722-01",
  "goal": "模拟用户浏览视频并完成互动和系统分享",
  "generation": {
    "model": "scenario-planner-v1",
    "prompt_version": "prompt-v3",
    "strategy": "risk_weighted_pairwise",
    "reason": "覆盖高频视频路径、状态动作、弹层动作和外部分享边界",
    "confidence": 0.88
  },
  "preconditions": {
    "login_status": "logged_in",
    "network": "wifi",
    "permissions": ["notifications_optional"]
  },
  "steps": [
    {
      "step_no": 1,
      "app_id": "short_video_app",
      "page_id": "home",
      "action_id": "open_video",
      "layer": "pageNaviAction",
      "expected": { "target_page_id": "video_detail" }
    },
    {
      "step_no": 2,
      "app_id": "short_video_app",
      "page_id": "video_detail",
      "action_id": "swipe_next",
      "layer": "stateAction",
      "params": { "repeat": 5, "direction": "up" },
      "expected": { "page_structure_should_same": true }
    },
    {
      "step_no": 3,
      "app_id": "short_video_app",
      "page_id": "video_detail",
      "action_id": "like",
      "layer": "stateAction",
      "expected": { "state_key": "liked", "state_value": true }
    },
    {
      "step_no": 4,
      "app_id": "short_video_app",
      "page_id": "video_detail",
      "action_id": "open_comments",
      "layer": "popupAction",
      "expected": { "popup_name": "评论半屏面板" }
    },
    {
      "step_no": 5,
      "app_id": "short_video_app",
      "page_id": "video_detail",
      "action_id": "system_share",
      "layer": "externalAction",
      "expected_app": "system_share",
      "return_policy": { "required": true }
    }
  ],
  "metrics": {
    "start": "case_started",
    "stop": "case_finished",
    "collect": ["cpu", "memory", "fps", "jank", "power", "temperature"]
  },
  "review_status": "pending_review"
}
```

## 9. 生成器实现建议

### 9.1 不让大模型直接操作数据库

推荐三段式架构：

```text
Deterministic Collector
  -> 生成候选动作与前后证据

AI Action Classifier
  -> 输出严格 JSON 的四层动作、概率和理由

Deterministic Scenario Compiler
  -> 校验引用、展开模板、去重并生成可执行用例
```

大模型负责语义推断和规划；程序负责 ID、图遍历、约束、去重、安全和持久化。

### 9.2 生成伪代码

```python
def generate_cases(graph, actions, app_transitions, policies):
    cases = []
    cases += generate_root_to_leaf_cases(graph)

    for page in graph.pages:
        cases += generate_state_cases(page, actions.stateAction)
        cases += generate_popup_cases(page, actions.popupAction)
        cases += generate_external_cases(page, actions.externalAction, app_transitions)

    candidates = ai_plan_user_scenarios(
        graph=graph,
        actions=actions,
        goals=policies.goals,
        max_steps=policies.max_steps,
    )
    candidates = constraint_filter(candidates, policies)
    candidates = pairwise_reduce(candidates)
    candidates = deduplicate_by_fingerprint(candidates)
    return validate_and_version(cases + candidates)
```

### 9.3 用例指纹

```text
case_fingerprint = hash(
  graph_version
  + ordered(app_id, page_id, action_id, layer, normalized_params)
  + normalized_preconditions
)
```

相同指纹不重复创建。图谱或动作版本变化时重新校验；无法解析的动作标记 `stale`，保留历史运行记录。

## 10. 后端存储建议

### 10.1 page_actions

```text
action_id
app_id
page_id
action_layer
action_type
label
description
target_json
params_json
preconditions_json
expected_json
wait_json
fallback_json
evidence_json
confidence
source
review_status
model_version
schema_version
created_at / updated_at
```

当前阶段可以继续将四层 `action` JSON 保存在 PageInstance 中；进入规模化和统计阶段后，应迁移到独立表，并保留节点接口的聚合输出格式。

### 10.2 app_transitions

```text
transition_id
source_app_id
source_page_id
source_action_id
target_app_id nullable
target_package
target_entry_page_id nullable
handoff_method
uri_pattern
return_policy_json
evidence_json
confidence
review_status
```

### 10.3 ai_generation_jobs

```text
job_id
app_id
graph_version
action_version
strategy
config_json
model_version
prompt_version
status
generated_count
accepted_count
rejected_count
error_json
created_at / finished_at
```

## 11. 推荐接口

```http
POST /ai/actions/infer
POST /ai/actions/probe
POST /ai/actions/{action_id}/review
GET  /apps/{app_id}/actions

POST /ai/test-cases/generate
GET  /ai/test-cases/jobs/{job_id}
POST /test-cases/{case_id}/validate
POST /test-cases/{case_id}/review
POST /test-cases/{case_id}/dispatch

GET  /app-transitions
POST /app-transitions/{transition_id}/review
```

生成请求：

```json
{
  "app_ids": ["qq", "map_app"],
  "graph_versions": {
    "qq": "graph-v12",
    "map_app": "graph-v7"
  },
  "strategies": [
    "root_to_leaf",
    "single_action",
    "pairwise_action",
    "cross_app_return"
  ],
  "max_steps": 12,
  "max_cases": 1000,
  "risk_policy": "demo_safe",
  "metrics": ["cpu", "memory", "fps", "jank", "power"]
}
```

## 12. 校验与人工复核

生成后必须经过确定性校验：

1. `page_id`、`action_id` 和 `edge_id` 均存在于指定版本。
2. 每一步动作属于当前页面。
3. `pageNaviAction` 的目标与图谱边一致。
4. popup 打开后必须存在关闭或恢复策略。
5. external 切换必须声明目标包名和返回策略。
6. stateAction 的前后状态不能自相矛盾。
7. 定位信息至少有一种非 AI-only 方案，或明确标记视觉定位。
8. 高风险动作符合账号、环境和安全策略。
9. 用例总时长、重试次数和循环次数不超过上限。
10. 指纹去重后再入库。

人工复核界面需要展示：

- 动作前后截图对比。
- AI 分类概率与推断理由。
- UI 树定位和实际点击区域。
- 四层动作对象的可编辑字段。
- 生成用例中引用该动作的步骤。
- 修改后重新校验和影响范围。

人工复核状态：

```text
ai_generated -> pending_review -> confirmed
                              -> rejected
confirmed -> edited -> confirmed
```

## 13. 增量演进

图谱持续新增页面时，不需要全量重建所有用例：

1. 根据新增/变化的 `page_id` 和 `action_id` 找到影响子图。
2. 只生成新增根到叶路径和新增动作覆盖用例。
3. 对引用变化动作的旧用例执行重新校验。
4. 保留稳定用例及历史运行结果。
5. 使用线上频率、失败率和性能异常持续调整优先级。

建议保存：

```text
graph_version
action_version
case_version
generator_version
model_version
prompt_version
```

这样每一次 AI 结论和用例变化都有可追溯依据。

## 14. 实施顺序

### 第一阶段：动作标准化

- 固定四层 action JSON Schema。
- 脚本保存动作前后证据。
- 实现规则分类器和 AI 分类器。
- 接入右侧人工复核编辑。

### 第二阶段：单应用生成

- 根到叶路径全量生成。
- 四层动作单动作覆盖。
- 模板化滑动、长按、输入和弹层用例。
- 接入用例校验、执行和结果回传。

### 第三阶段：组合与跨应用

- Pairwise 场景组合。
- 建立 `app_transitions`。
- 支持目标应用继续执行和返回源应用。
- 增加权限、登录、网络和账号状态组合。

### 第四阶段：数据驱动优化

- 按线上 URL/埋点频率排序。
- 按性能异常和历史失败动态加权。
- AI 根据运行证据修正动作分类和定位器。
- 对 Top 225 应用持续增量生成与回归。

## 15. 最终结论

完整方案不是让 AI 随机点击，而是：

```text
AI 理解控件语义
  + 前后证据确定动作效果层
  + 图算法保证路径合法
  + 组合算法控制场景规模
  + 应用上下文保持跨应用连续性
  + 人工复核保证高风险动作可信
```

四层动作是图谱与用例之间的关键契约。页面图谱提供可达结构，动作层提供可操作能力，AI 规划器把它们编译成可执行、可验证、可度量、可追踪的全场景用户行为用例。
