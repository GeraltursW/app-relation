# Page Action Layering

## Background

In the app graph, many controls clearly navigate from one page to another. These controls should form graph edges:

```text
Page A --tap control--> Page B
```

However, actions such as like, favorite, collect, follow, add to cart, select coupon, or open a SKU selector often do not switch the page. If we model these as child pages, the graph will become noisy and semantically wrong.

## Core Rule

Do not force every control into the page tree.

The page tree should describe page-to-page structure. Non-navigation actions should live inside the page node as page capabilities or state transitions.

Recommended hierarchy:

```text
App
└── Page
    ├── Navigation Actions
    │   └── Target Page
    ├── State Actions
    │   └── Page State
    ├── Overlay Actions
    │   └── Modal / Sheet / Local Panel
    └── External Actions
        └── System / SDK / OS Capability
```

## Action Types

### Navigation Action

The action switches to another functional page.

Examples:

- tap author avatar -> author profile page
- tap comment area -> comment page
- tap cart -> cart page
- tap order detail -> order detail page

Graph representation:

```text
page_edges
from_page_id
to_page_id
action_type = tap
effect_type = navigate
```

Frontend representation:

- draw an edge in Vue Flow
- include it in the page tree
- show it under "跳转控件" in the inspector

### State Action

The action changes current page state but does not switch page.

Examples:

- like
- favorite / collect
- follow
- add to cart
- receive coupon
- select option

Graph representation:

```text
page_actions
page_id
action_type = tap
effect_type = state_change
state_key = liked / collected / followed / cart_added
state_value = true / false / object
```

Frontend representation:

- do not create a child page
- show as action chips inside the page node
- show detailed rows under "状态动作" in the inspector

### Overlay Action

The action opens an overlay but keeps the user in the same functional page context.

Examples:

- open share sheet
- open SKU modal
- open coupon drawer
- open comment half-screen panel
- open filter panel

Graph representation:

```text
page_actions
page_id
action_type = tap
effect_type = overlay
overlay_type = modal / drawer / sheet / popup
```

Frontend representation:

- do not place it in the main page tree
- show as page action
- optionally show overlay state in the right inspector

If an overlay is complex enough to behave like a page, it can later be promoted to a pseudo page:

```text
effect_type = overlay
target_virtual_page = sku_selector_modal
```

### External Action

The action leaves the app page model or delegates to a system/third-party capability.

Examples:

- system share panel
- camera
- face verification
- payment SDK
- map app

Graph representation:

```text
page_actions
page_id
action_type = tap
effect_type = external
external_target = camera / payment_sdk / system_share
```

Frontend representation:

- do not force it into the tree
- display it as an external action
- for replay, mark it as a boundary requiring special script support

## Why This Matters

For performance replay and power testing, non-navigation actions are still important. They can trigger:

- network requests
- local cache writes
- animation cost
- recommendation refresh
- buried-point events
- SDK calls

But they should not change the current page node unless the visual/functional page actually changes.

## Recommended Backend Shape

The current backend page node can keep `children` for navigation pages and add `page_info.actions` or top-level `actions` for internal controls.

Example:

```json
{
  "id": 101,
  "page_title": "视频详情",
  "page_text": "短视频播放页，包含作者、点赞、收藏、评论和分享入口",
  "image_url": "screens/video-detail.png",
  "page_url": "app://video/detail/123",
  "page_info": {
    "page_type": "video_detail",
    "actions": [
      {
        "id": "like_btn",
        "label": "点赞",
        "action_type": "tap",
        "effect_type": "state_change",
        "state_key": "liked",
        "state_value": true,
        "confidence": 0.94
      },
      {
        "id": "favorite_btn",
        "label": "收藏",
        "action_type": "tap",
        "effect_type": "state_change",
        "state_key": "collected",
        "state_value": true,
        "confidence": 0.92
      },
      {
        "id": "share_btn",
        "label": "分享",
        "action_type": "tap",
        "effect_type": "external",
        "external_target": "system_share",
        "confidence": 0.88
      }
    ]
  },
  "children": [
    {
      "id": 102,
      "page_title": "作者主页",
      "page_text": "作者个人主页",
      "image_url": "screens/author.png",
      "page_url": "app://author/abc",
      "page_info": {},
      "children": []
    }
  ]
}
```

## Frontend Landing

The frontend now follows this rule:

- `children` creates tree nodes and Vue Flow edges.
- `page_info.actions`, `page_info.widgets`, `page_info.controls`, or top-level `actions/widgets/controls` are normalized into `pageActions`.
- `effect_type = navigate` is excluded from page action chips because navigation already belongs to graph edges.
- `state_change`, `overlay`, and `external` actions are shown inside the node and in the inspector.

## Future Upgrade

Later we can add a dedicated database table:

```text
page_actions
- action_id
- page_id
- widget_id
- action_type
- effect_type
- label
- state_key
- state_value
- overlay_type
- external_target
- confidence
- raw_ai_payload
```

This will make replay generation more accurate:

```text
URL path -> page node -> available actions -> replay script steps -> power/performance metrics
```

