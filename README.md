# APP 页面图谱演示

这是一个基于 Vue 3、Vite 和 Vue Flow 的 APP 页面关系图谱演示项目，用来展示三方应用的页面层级、跳转关系和组件入口。

## 技术栈

- Vue 3
- Vite
- Vue Flow
- 原生 CSS

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

## 文件结构

- `src/App.vue`：整体页面布局和选择状态。
- `src/components/GraphCanvas.vue`：Vue Flow 图谱画布。
- `src/components/nodes/AppNode.vue`：自定义页面节点卡片。
- `src/components/TreeNav.vue`：左侧页面树。
- `src/components/InspectorPanel.vue`：右侧详情面板。
- `src/data/graph.js`：页面节点与跳转关系数据。
- `src/utils/images.js`：图片候选路径和占位图逻辑。

## 使用方式

```bash
npm install
npm run dev
```

构建生产版本：

```bash
npm run build
```
