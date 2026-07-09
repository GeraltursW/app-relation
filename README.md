# APP 页面图谱演示

基于 Vue 3、Vite 和 Vue Flow 的第三方应用页面关系图谱系统，用于展示和探索 APP 内部的页面层级、跳转关系和组件入口。

## 项目架构

```
图谱/
├── src/                          # 前端（Vue 3 + Vite）
│   ├── App.vue                   # 主应用布局与全局状态协调
│   ├── main.js                   # Vue 应用入口，注册全局样式与插件
│   ├── components/
│   │   ├── GraphCanvas.vue       # Vue Flow 图谱画布（核心）
│   │   ├── TreeNav.vue           # 左侧页面树导航
│   │   ├── TreeItem.vue          # 树节点递归组件
│   │   ├── InspectorPanel.vue    # 右侧节点/跳转详情面板
│   │   ├── nodes/
│   │   │   └── AppNode.vue       # 自定义图谱节点卡片
│   │   ├── shared/
│   │   │   └── SmartImage.vue    # 智能图片组件（多候选 URL 自动回退）
│   │   └── ui/                   # shadcn-vue UI 基础组件
│   ├── data/
│   │   └── graph.js              # 图谱数据层（API 请求、数据归一化、树构建）
│   ├── utils/
│   │   └── images.js             # 图片工具（占位 SVG 生成）
│   └── lib/
│       └── utils.js              # 通用工具（cn() CSS 类名合并）
├── backend/                      # 后端（Python / FastAPI）
│   └── app/
│       ├── main.py               # FastAPI 应用入口，注册所有路由
│       ├── core/
│       │   ├── config.py         # 全局配置（数据库 URL、存储路径、embedding 维度）
│       │   └── database.py       # PostgreSQL 连接池与 Session 工厂
│       ├── models/               # SQLAlchemy ORM 数据模型
│       │   ├── scan.py           # App（三方应用）、Scan（扫描任务）
│       │   ├── graph.py          # CanonicalPage、PageInstance、PageWidget、PageEdge
│       │   ├── asset.py          # Asset（截图/裁剪图等资源文件）
│       │   ├── embedding.py      # EmbeddingRecord（pgvector 向量嵌入记录）
│       │   └── types.py          # 通用类型工具（uuid 主键、时间戳列）
│       ├── schemas/              # Pydantic 请求/响应 Schema
│       │   ├── graph.py          # GraphNode、GraphEdge、AppGraphResponse
│       │   ├── imports.py        # FolderImportRequest、FolderImportResult、InitDbResult
│       │   └── replay.py         # ReplayAnalyzeRequest、ReplayStep、ReplayAnalyzeResponse
│       ├── api/routes/           # REST API 路由
│       │   ├── graph.py          # GET /api/graph/{app_id} — 获取应用图谱
│       │   ├── imports.py        # POST /api/imports/init-db、POST /api/imports/scan-folder
│       │   ├── assets.py         # GET /api/assets/{asset_id} — 获取资源文件
│       │   └── replay.py         # POST /api/replay/analyze — URL 路径回放分析
│       └── services/             # 业务逻辑层
│           ├── importer.py       # AI JSON 文件夹导入，页面去重归并
│           ├── replay.py         # URL 关键词匹配与页面类型推断
│           └── hash.py           # 截图/结构哈希、页面结构归一化
├── docs/                         # 设计文档
│   ├── backend-data-model.md     # 数据库设计、Page Hash 指纹体系、向量库方案
│   ├── page-deduplication-flow.md # 页面去重流程、structure_hash 生成与归并评分
│   ├── page-action-layering.md    # 页面动作分层：跳转、状态、弹层、外部动作
│   ├── use-case-replay-model.md   # 用例复现、长按滑动、性能采集窗口
│   └── ai-exploration-incremental-traversal.md # AI 探索、HDC 脚本、增量遍历
├── dist/                         # 前端构建产物
├── vite.config.js                # Vite 构建配置（含 @ 路径别名）
├── tailwind.config.js            # Tailwind CSS 配置
└── postcss.config.js             # PostCSS 配置
```

## 各组件职责说明

### 前端核心组件

| 组件 | 职责 |
|---|---|
| `App.vue` | **主应用布局**。管理全局状态：应用名称输入、选中节点/边、搜索关键词、布局模式。负责调用 API 加载图谱数据，协调左侧树导航、中间画布、右侧详情面板三个区域的联动。 |
| `GraphCanvas.vue` | **图谱画布核心**。基于 Vue Flow 渲染节点与边。实现三种布局算法：左右排列（树形递归）、上下排列（树形递归）、力导向自由排列（d3-force 模拟）。支持节点拖拽、画布平移/缩放、展开/收起子节点、全部展开/收起、适配视图、重置布局、PNG 导出。内嵌 MiniMap 和 Controls 控件。搜索关键词会使非匹配节点半透明蒙版。 |
| `AppNode.vue` | **自定义节点卡片**。每条卡片展示：页面标题（含重复序号）、分类标签（颜色编码）、层级与子节点数、截图缩略图（SmartImage）、AI 文本描述（截断 46 字）、页面 URL。顶部 Handle 接收入边，底部 Handle 发出边。支持点击选中和高亮状态。 |
| `TreeNav.vue` | **左侧页面树导航**。将图谱数据构建为树形结构通过 TreeItem 递归渲染。顶部搜索框支持按标题/URL/文本过滤，搜索结果以列表展示并支持点击跳转。 |
| `TreeItem.vue` | **树节点递归组件**。每个节点展示页面标题和层级。有子节点时显示 +/- 展开/收起按钮。支持选中高亮、搜索时非匹配节点弱化显示。 |
| `InspectorPanel.vue` | **右侧详情面板**。选中节点时展示：后端 ID、页面标题、URL、层级、上下游数量、截图（SmartImage）、page_text 语义描述、页面路径链路、上下游关系列表、原始 JSON 数据。选中边时展示跳转关系详情。 |
| `SmartImage.vue` | **智能图片组件**。接收多候选 URL 数组，逐个尝试加载；全部失败后自动降级为 SVG 占位图（模拟手机截图样式）。 |
| `graph.js` | **图谱数据层**。提供 `queryAppGraph(appName)` 调用后端接口获取原始树状数据；`normalizeBackendGraph(payload)` 将树状数据展平为 nodes + edges + pageMap 结构；`createEmptyGraph()` 返回空图谱初始值；以及 `getOutgoingEdges`、`getIncomingEdges`、`getAncestorPath`、`getPageCategory` 等查询辅助函数。 |

### 后端核心模块

| 模块 | 职责 |
|---|---|
| `main.py` | **FastAPI 应用入口**。创建 FastAPI 实例，注册 `/health` 健康检查端点，挂载 imports / graph / assets / replay 四个路由模块。 |
| `core/config.py` | **全局配置**。从环境变量 / `.env` 文件加载：数据库连接串、本地存储根路径、导入收件箱目录、embedding 向量维度。 |
| `core/database.py` | **数据库层**。创建 SQLAlchemy engine 和 SessionLocal 工厂，提供 `get_db()` FastAPI 依赖注入生成器。 |
| `models/scan.py` | **应用与扫描模型**。`App` 存储三方应用的包名、名称、市场排名、平台等信息。`Scan` 记录每次自动化探索的设备、脚本版本、AI 模型等上下文。 |
| `models/graph.py` | **图谱核心模型**。`CanonicalPage` 是跨扫描归并后的标准功能页面（以 structure_hash 为主去重依据）；`PageInstance` 是单次扫描中真实遇到的页面实例（证据层）；`PageWidget` 记录 AI 识别的可交互组件；`PageEdge` 记录页面间的跳转边。 |
| `models/asset.py` | **资源文件模型**。统一管理截图、组件裁剪图等文件的本地路径和 SHA256，支持去重和直接通过 API 返回图片。 |
| `models/embedding.py` | **向量嵌入模型**。基于 pgvector 存储页面/组件的 embedding 向量，支持语义相似度检索。 |
| `services/importer.py` | **导入服务**。扫描 inbox 目录中的 AI JSON 文件，创建 App / Scan 记录，逐页面导入并计算 structure_hash 去重归并到 CanonicalPage，同时导入 widgets 和 edges。 |
| `services/hash.py` | **哈希与归一化**。提供 SHA256 文件/字节哈希、JSON 规范序列化（canonical_json）、页面结构归一化（过滤动态内容、widget 按语义槽位归一化、bbox 分桶）、structure_hash 生成。 |
| `services/replay.py` | **回放分析**。基于预定义 URL 规则（关键词→页面类型映射）将用户 URL 列表匹配到图谱候选页面类型。 |
| `api/routes/graph.py` | **图谱查询接口**。`GET /api/graph/{app_id}` 查询指定应用的所有 CanonicalPage 节点和 PageEdge 边，返回 GraphNode + GraphEdge 列表。 |
| `api/routes/imports.py` | **数据导入接口**。`POST /api/imports/init-db` 初始化数据库（创建 pgvector 扩展和表结构）；`POST /api/imports/scan-folder` 扫描指定目录导入 AI JSON 文件。 |
| `api/routes/assets.py` | **资源服务接口**。`GET /api/assets/{asset_id}` 根据资源 ID 返回图片文件（FileResponse）。 |
| `api/routes/replay.py` | **回放分析接口**。`POST /api/replay/analyze` 接收 URL 列表，返回每一步的匹配关键词、可能页面类型和置信度。 |

### 设计文档

| 文档 | 内容 |
|---|---|
| `docs/backend-data-model.md` | 完整数据库表设计（apps、scans、assets、page_instances、canonical_pages、page_widgets、page_edges、embeddings），Page Hash 四维指纹体系（screenshot_hash / visual_hash / structure_hash / route_hash），向量库方案，归并评分模型，入库流程。 |
| `docs/page-deduplication-flow.md` | 页面去重核心流程：asset 保存 → 哈希计算 → AI/OCR 识别 → 归一化 → structure_hash 生成 → 候选 canonical_page 查询 → 归并评分 → 创建或归并。含抖音视频 Feed 完整示例和动态区域过滤规则。 |
| `docs/page-action-layering.md` | 页面控件动作分层，说明跳转动作、状态动作、弹层动作、外部动作如何进入图谱和右侧详情。 |
| `docs/use-case-replay-model.md` | 用例层设计，说明页面间转换、长按、滑动、等待条件、失败兜底和功耗/性能采集窗口。 |
| `docs/ai-exploration-incremental-traversal.md` | AI 自由探索与增量遍历方案，包含后端接口、HDC 脚本交互、拖拽并入、候选边和持续增加图片的策略。 |

## 技术栈

**前端：**
- Vue 3（Composition API）
- Vite（构建工具）
- Vue Flow（图谱可视化）
- d3-force（力导向布局引擎）
- shadcn-vue / Radix Vue（UI 组件）
- Tailwind CSS（样式）
- html-to-image（PNG 导出）

**后端：**
- Python 3
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy（ORM）
- Pydantic v2（数据校验）

## 功能

- 页面节点拖拽
- 画布拖动、滚轮缩放、适配视图
- 清晰连线、箭头和边标签
- 节点展开 / 收起
- 全部展开、全部收起、适配视图、重置布局
- 图谱 PNG 导出
- 左右排列、上下排列、力导向自由排列
- 左侧页面树导航
- 搜索结果定位
- 右侧节点 / 跳转详情面板
- 页面业务标签、上下游、路径链路、组件入口分析
- 图片缺失时自动显示占位图
- Mini Map 和缩放控制器

## API 接口

### GET /queryAppGraph/{app_Name}

根据应用名称查询页面关系图谱，返回树状结构数据。

**请求参数：**

| 参数 | 位置 | 类型 | 说明 |
|---|---|---|---|
| `app_Name` | path | string | 应用名称（如 `demo`、`tiktok`），需 URL 编码 |

**响应结构：** JSON 树状数组，每个节点包含：

```json
[
  {
    "id": 1,
    "page_title": "首页",
    "page_text": "应用主页面，包含推荐内容流和底部导航栏",
    "image_url": "https://s3.xxx.com/screenshots/home.png",
    "page_url": "/main/home",
    "page_info": {
      "page_type": "home",
      "layout_type": "feed_with_tabs",
      "regions": ["top_search_bar", "content_feed", "bottom_tab_bar"],
      "widgets": [
        {
          "widget_type": "tab",
          "semantic_name": "首页",
          "relative_position": "bottom"
        },
        {
          "widget_type": "tab",
          "semantic_name": "我的",
          "relative_position": "bottom"
        }
      ]
    },
    "children": [
      {
        "id": 2,
        "page_title": "搜索页",
        "page_text": "搜索页面，包含搜索输入框和历史搜索记录",
        "image_url": "https://s3.xxx.com/screenshots/search.png",
        "page_url": "/search",
        "page_info": {},
        "children": []
      }
    ]
  }
]
```

**字段说明：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | number | 页面唯一标识（后端 ID） |
| `page_title` | string | AI 精简后的页面标题，10 字以内 |
| `page_text` | string | AI 对页面功能和结构的自然语言描述 |
| `image_url` | string | S3 对象存储保存的页面截图链接，用于接口获取图片 |
| `page_url` | string | 自动化脚本采集到的大数据平台返回的页面 URL / 路由 |
| `page_info` | object | 页面节点信息，由 AI 识别记录（包含 page_type、layout_type、regions、widgets 等） |
| `children` | array | 子节点数组，每个子节点数据结构与父节点相同（递归） |

**调用示例：**

```bash
curl http://127.0.0.1:8000/queryAppGraph/demo
```

## 后端调试流程

```text
1. 启动 PostgreSQL（确保 pgvector 扩展可用）
2. 启动 FastAPI 后端：
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
3. 打开 http://127.0.0.1:8000/docs 查看 Swagger 文档
4. 调用 GET /health 确认服务正常
5. 调用 POST /api/imports/init-db 初始化数据库表结构
6. 将 AI JSON 和截图放入 backend/inbox 目录
7. 调用 POST /api/imports/scan-folder 导入数据
8. 调用 GET /api/graph/{app_id} 查询图谱
```

## 前端使用方式

```bash
npm install
npm run dev
```

构建生产版本：

```bash
npm run build
```

## 环境变量（前端）

| 变量 | 说明 | 默认值 |
|---|---|---|
| `VITE_API_BASE_URL` | 后端 API 基础地址 | `http://127.0.0.1:8000` |
| `VITE_DEFAULT_APP_NAME` | 默认加载的应用名称 | `demo` |
