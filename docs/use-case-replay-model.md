# Use Case Replay Model

## Why Use Cases Sit Above The Graph

The app graph describes what pages and actions exist. A replay use case describes how to execute a real user journey under specific conditions.

The graph answers:

```text
Which pages exist?
Which actions may connect them?
Which actions change state, open overlays, or leave the app?
```

The use case answers:

```text
Under what state should we start?
Which action should the script perform?
What should we wait for?
How do we know the transition succeeded?
What metrics should be collected?
What should we do if the path branches?
```

Recommended hierarchy:

```text
App Graph
└── Page Node
    ├── Navigation Action
    ├── State Action
    ├── Overlay Action
    └── External Action

Use Case
└── Scenario
    ├── Preconditions
    ├── Replay Steps
    ├── Wait Conditions
    ├── Assertions
    ├── Fallbacks
    └── Metrics Collection
```

## Page Transition Considerations

Page transitions are not just edges. A reliable replay step needs:

| Dimension | Meaning | Examples |
|---|---|---|
| Preconditions | Required app/user/device state before the step | logged in, address exists, location granted, coupon available |
| Action | What the script does | tap, long_press, swipe, input, drag, back |
| Target | Where the action happens | widget id, text, bbox, region, image anchor |
| Parameters | How the action is performed | duration, direction, distance, velocity, repeat |
| Expected Result | What should happen after the action | target page, overlay, state change, external SDK |
| Wait Condition | When the script can continue | page stable, text visible, OCR keywords, network idle |
| Match Strategy | How to identify current page | page_text, page_url, structure_hash, OCR, widget set, screenshot similarity |
| Fallback | What to do if the result differs | close modal, back, relaunch, skip, branch |
| Metrics Window | When to collect performance/power data | before action to page stable, fixed duration, after animation |

The key rule:

```text
Graph edges are knowledge. Use case steps are executable instructions.
```

## Action Type vs Effect Type

Long press and swipe should be represented as `action_type`, not as page levels.

Whether an action becomes a graph edge depends on `effect_type`.

| action_type | effect_type | Meaning | Graph Representation |
|---|---|---|---|
| tap | navigate | Click opens another page | Page -> Page edge |
| tap | state_change | Like/favorite/follow | Page internal action |
| tap | overlay | Open modal/sheet/drawer | Page internal action, optional virtual overlay |
| long_press | overlay | Open context menu | Page internal action |
| swipe | state_change | Feed scroll or next video under same structure | Page internal action |
| swipe | navigate | Swipe to another functional page/tab | Page -> Page edge |
| input | state_change | Search text typed, suggestions refresh | Page internal action |
| back | navigate | Return to previous page | Page -> Page edge or system action |
| drag | state_change | Map viewport moves, slider changes | Page internal action |
| pinch | state_change | Image/map zoom changes | Page internal action |
| tap | external | Payment SDK, camera, system share | External boundary action |

## Long Press Model

Long press needs duration and expected result.

```json
{
  "step_no": 3,
  "from_page": "商品详情页",
  "action": {
    "action_type": "long_press",
    "effect_type": "overlay",
    "target": {
      "type": "widget",
      "label": "商品图片",
      "bbox": { "x": 40, "y": 220, "width": 300, "height": 300 }
    },
    "params": {
      "duration_ms": 800
    }
  },
  "expected": {
    "overlay_type": "context_menu",
    "ocr_keywords": ["保存图片", "分享", "收藏"],
    "timeout_ms": 5000
  }
}
```

Use case meaning:

```text
The user remains on the same functional page, but a local overlay is opened.
```

## Swipe Model

Swipe needs direction, distance, duration, and repeat count.

```json
{
  "step_no": 4,
  "from_page": "视频详情页",
  "action": {
    "action_type": "swipe",
    "effect_type": "state_change",
    "target": {
      "type": "region",
      "region": "content_area",
      "bbox": { "x": 0, "y": 120, "width": 1080, "height": 1700 }
    },
    "params": {
      "direction": "up",
      "distance_ratio": 0.82,
      "duration_ms": 350,
      "repeat": 1
    }
  },
  "expected": {
    "state_key": "current_video",
    "state_change": "next_video",
    "page_structure_should_same": true,
    "timeout_ms": 5000
  },
  "metrics": {
    "start": "before_action",
    "stop": "page_stable",
    "collect": ["cpu", "fps", "battery_current", "network"]
  }
}
```

If swipe changes a functional page or tab, use `effect_type = navigate`:

```json
{
  "action_type": "swipe",
  "effect_type": "navigate",
  "from_page": "首页推荐 Tab",
  "to_page": "附近 Tab",
  "params": {
    "direction": "left",
    "distance_ratio": 0.7,
    "duration_ms": 420
  }
}
```

## Use Case JSON Shape

Recommended first version:

```json
{
  "use_case_name": "外卖点单链路",
  "app_name": "meituan",
  "goal": "复现用户从首页进入商家并加购商品的路径，采集功耗和页面稳定时间",
  "preconditions": {
    "login_status": "logged_in",
    "location_permission": "granted",
    "default_address": true,
    "coupon_available": "optional",
    "network_type": "wifi"
  },
  "steps": [
    {
      "step_no": 1,
      "from_page": "首页",
      "action": {
        "action_type": "tap",
        "effect_type": "navigate",
        "target": {
          "type": "widget",
          "label": "外卖入口"
        }
      },
      "expected": {
        "target_pages": ["外卖首页"],
        "match_by": ["page_text", "structure_hash", "ocr_keywords"],
        "ocr_keywords": ["外卖", "附近商家"],
        "timeout_ms": 8000
      },
      "wait": {
        "type": "page_stable",
        "timeout_ms": 8000
      },
      "fallback": {
        "branches": ["登录页", "定位授权弹窗", "地址选择页"],
        "recover_strategy": "handle_branch_or_stop"
      },
      "metrics": {
        "start": "before_action",
        "stop": "page_stable",
        "collect": ["cpu", "memory", "fps", "battery_current", "network"]
      }
    }
  ]
}
```

## Branching And Failure Recovery

A single action may lead to multiple outcomes:

```text
tap checkout
├── checkout page
├── login page
├── address page
├── coupon page
└── stock unavailable modal
```

Therefore a replay step should allow:

```json
{
  "expected_targets": ["结算页"],
  "allowed_branches": ["登录页", "地址选择页", "库存不足弹窗"],
  "recover_strategy": {
    "登录页": "login_then_retry",
    "地址选择页": "select_default_address_then_retry",
    "库存不足弹窗": "close_modal_and_skip"
  }
}
```

## Page Matching Strategy

Do not rely on `page_title` alone. The same title may correspond to multiple screenshots or states.

Recommended matching signals:

```text
page_text
page_url
structure_hash
OCR keywords
widget set
activity/deeplink
screenshot similarity
page_info.page_type
```

For replay, each step should define `match_by` explicitly.

## Metrics Collection

For power/performance testing, each step needs metric boundaries:

```json
{
  "metrics": {
    "start": "before_action",
    "stop": "page_stable",
    "max_duration_ms": 12000,
    "collect": [
      "cpu",
      "memory",
      "fps",
      "temperature",
      "battery_current",
      "network",
      "jank"
    ]
  }
}
```

Common windows:

| Window | Meaning |
|---|---|
| before_action -> page_stable | Best for page transition cost |
| after_action -> fixed_duration | Best for animation/feed playback cost |
| page_visible -> network_idle | Best for loading cost |
| action_start -> action_end | Best for gesture interaction cost |

## Database Direction

Later backend can model use cases with these tables:

```text
use_cases
- use_case_id
- app_id
- name
- goal
- status
- created_at

use_case_preconditions
- precondition_id
- use_case_id
- key
- value

use_case_steps
- step_id
- use_case_id
- step_no
- from_page_id
- action_type
- effect_type
- target_selector_json
- params_json
- expected_json
- wait_json
- fallback_json
- metrics_json

use_case_runs
- run_id
- use_case_id
- device_id
- app_version
- started_at
- finished_at
- result

use_case_step_results
- result_id
- run_id
- step_id
- actual_page_id
- success
- metrics_json
- screenshot_asset_id
- error_message
```

## Product Conclusion

The graph gives the replay engine possible routes. The use case turns those routes into executable, measurable steps.

The most important separation is:

```text
Page graph = possible structure
Action model = possible interactions
Use case = executable replay plan
Run result = measured evidence
```

