# APP 页面图谱演示

这是一个用于领导演示的前端静态项目，用来展示三方应用 APP 的页面层级、跳转关系和组件入口。

## 文件结构

- `index.html`：演示入口页面。
- `src/data.js`：页面节点与跳转关系数据。
- `src/app.js`：图谱渲染、搜索、详情面板、图片降级逻辑。
- `src/styles.css`：页面布局和视觉样式。
- `app_tree_demo_left_to_right_independent_scroll.html`：原始单文件版本，保留作来源备份。

## 使用方式

直接打开 `index.html` 即可演示。图片目录 `clickable_function_imgs/` 和 `widgets/` 如果不存在，页面会自动显示占位图，不影响整体演示。

## 数据规模

- 30 个页面节点
- 29 条页面跳转关系
- 3 层页面结构
