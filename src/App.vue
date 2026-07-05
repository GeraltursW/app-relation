<script setup>
import { computed, ref } from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import InspectorPanel from "./components/InspectorPanel.vue";
import TreeNav from "./components/TreeNav.vue";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { appEdges, appPages, pageMap } from "./data/graph.js";

const selected = ref({ type: "node", id: "root" });
const keyword = ref("");
const layoutMode = ref("horizontal");
const graphRef = ref(null);
const layoutRevision = ref(0);
const showReplayPanel = ref(false);
const replayTraceText = ref([
  "2026-07-05 10:00:01,/product/detail?id=123,18000",
  "2026-07-05 10:00:19,/cart,6000",
  "2026-07-05 10:00:26,/order/list,9000"
].join("\n"));
const replayAnalysis = ref(null);
const layoutModes = [
  { value: "horizontal", label: "左右排列" },
  { value: "vertical", label: "上下排列" },
  { value: "radial", label: "自由排列" }
];

const selectedPayload = computed(() => {
  if (selected.value.type === "edge") {
    return appEdges.find((edge) => edge.id === selected.value.id) || null;
  }
  return pageMap.get(selected.value.id) || null;
});

const edgeMap = new Map(appEdges.map((edge) => [`${edge.from}->${edge.to}`, edge]));
const adjacencyMap = appEdges.reduce((map, edge) => {
  if (!map.has(edge.from)) map.set(edge.from, []);
  map.get(edge.from).push(edge);
  return map;
}, new Map());

const urlMatchRules = [
  { pattern: /product|goods|item|detail|sku/i, pages: ["商品详情页", "商品频道"], reason: "URL 包含商品详情语义" },
  { pattern: /cart|basket/i, pages: ["购物车"], reason: "URL 包含购物车语义" },
  { pattern: /order\/?list|orders|order-list/i, pages: ["全部订单页", "订单中心"], reason: "URL 包含订单列表语义" },
  { pattern: /pay|payment/i, pages: ["待付款页", "订单中心"], reason: "URL 包含支付语义" },
  { pattern: /search|query|keyword/i, pages: ["搜索结果页", "搜索中心"], reason: "URL 包含搜索语义" },
  { pattern: /shop|store/i, pages: ["店铺主页"], reason: "URL 包含店铺语义" },
  { pattern: /review|comment|evaluate/i, pages: ["商品评价页"], reason: "URL 包含评价语义" },
  { pattern: /message|notice|inbox/i, pages: ["消息中心", "站内信详情页"], reason: "URL 包含消息语义" },
  { pattern: /profile|user|account|member/i, pages: ["我的账户", "个人资料页", "会员中心页"], reason: "URL 包含账户语义" },
  { pattern: /address/i, pages: ["地址管理页"], reason: "URL 包含地址语义" },
  { pattern: /setting/i, pages: ["设置页"], reason: "URL 包含设置语义" },
  { pattern: /campaign|activity|banner|promo/i, pages: ["Banner活动页", "活动消息页"], reason: "URL 包含活动语义" }
];

function selectNode(title) {
  selected.value = { type: "node", id: title };
}

function selectEdge(edgeId) {
  selected.value = { type: "edge", id: edgeId };
}

function fitGraph() {
  graphRef.value?.fitGraph();
}

function expandGraph() {
  graphRef.value?.expandAll();
}

function collapseGraph() {
  graphRef.value?.collapseAll();
}

function resetGraph() {
  layoutRevision.value += 1;
  graphRef.value?.resetLayout();
}

function exportGraph() {
  graphRef.value?.exportImage();
}

function parseReplayTrace(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const parts = line.split(",").map((item) => item.trim());
      if (parts.length >= 3) {
        return { index, timestamp: parts[0], url: parts[1], durationMs: Number(parts[2]) || 0 };
      }
      return { index, timestamp: "", url: parts[0], durationMs: 0 };
    });
}

function matchUrlToPages(url) {
  const matches = [];
  urlMatchRules.forEach((rule) => {
    if (!rule.pattern.test(url)) return;
    rule.pages.forEach((title, index) => {
      const page = pageMap.get(title);
      if (!page) return;
      matches.push({
        pageId: title,
        score: Math.max(0.55, 0.92 - index * 0.12),
        reason: rule.reason
      });
    });
  });

  if (!matches.length) {
    ["应用首页", "搜索中心", "商品频道"].forEach((title, index) => {
      matches.push({
        pageId: title,
        score: 0.42 - index * 0.05,
        reason: "未命中特定规则，作为入口候选"
      });
    });
  }

  return matches
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
}

function findShortestPath(from, to) {
  if (from === to) return { nodes: [from], edges: [] };
  const queue = [{ node: from, nodes: [from], edges: [] }];
  const visited = new Set([from]);

  while (queue.length) {
    const current = queue.shift();
    if (current.nodes.length > 5) continue;
    const outgoing = adjacencyMap.get(current.node) || [];
    for (const edge of outgoing) {
      if (visited.has(edge.to)) continue;
      const next = {
        node: edge.to,
        nodes: [...current.nodes, edge.to],
        edges: [...current.edges, edge.id]
      };
      if (edge.to === to) return next;
      visited.add(edge.to);
      queue.push(next);
    }
  }
  return null;
}

function buildReplayPath(events, candidatesByUrl) {
  const selectedPages = candidatesByUrl.map((item) => item.candidates[0]?.pageId).filter(Boolean);
  const pathNodes = [];
  const pathEdges = [];
  const explanations = [];

  selectedPages.forEach((pageId, index) => {
    if (!pathNodes.length) {
      pathNodes.push(pageId);
      explanations.push(`URL ${index + 1} 优先匹配「${pageId}」。`);
      return;
    }

    const previous = pathNodes[pathNodes.length - 1];
    const segment = findShortestPath(previous, pageId);
    if (segment) {
      segment.nodes.slice(1).forEach((node) => pathNodes.push(node));
      segment.edges.forEach((edge) => pathEdges.push(edge));
      explanations.push(`从「${previous}」到「${pageId}」在图谱中存在 ${segment.edges.length} 跳可达路径。`);
    } else {
      pathNodes.push(pageId);
      explanations.push(`「${previous}」到「${pageId}」暂无直接图谱路径，保留为候选跳转断点。`);
    }
  });

  const directnessScore = pathEdges.length ? Math.min(0.95, selectedPages.length / Math.max(selectedPages.length, pathEdges.length)) : 0.52;
  const matchScore = candidatesByUrl.reduce((sum, item) => sum + (item.candidates[0]?.score || 0), 0) / Math.max(1, candidatesByUrl.length);
  const confidence = Math.round((matchScore * 0.62 + directnessScore * 0.38) * 100);

  return {
    pathId: "path-primary",
    confidence,
    nodes: [...new Set(pathNodes)],
    edges: [...new Set(pathEdges)],
    explanation: explanations
  };
}

function analyzeReplayTrace() {
  const inputUrls = parseReplayTrace(replayTraceText.value);
  const matched = inputUrls.map((event) => ({
    ...event,
    candidates: matchUrlToPages(event.url)
  }));
  const primaryPath = buildReplayPath(inputUrls, matched);
  const matchedNodes = matched.flatMap((item) => item.candidates.map((candidate) => ({
    ...candidate,
    url: item.url,
    eventIndex: item.index
  })));

  replayAnalysis.value = {
    inputUrls,
    matchedNodes,
    highlightedNodeIds: [...new Set([...primaryPath.nodes, ...matchedNodes.map((item) => item.pageId)])],
    primaryNodeIds: primaryPath.nodes,
    highlightedEdgeIds: primaryPath.edges,
    replayPaths: [primaryPath],
    summary: `共解析 ${inputUrls.length} 条 URL 事件，生成 1 条主要候选复现路径，置信度 ${primaryPath.confidence}%。`
  };

  if (primaryPath.nodes[0]) {
    selectNode(primaryPath.nodes[0]);
  }
  graphRef.value?.expandAll();
  window.setTimeout(() => graphRef.value?.fitGraph(), 80);
}

function clearReplayTrace() {
  replayAnalysis.value = null;
}
</script>

<template>
  <div class="app-shell">
    <TreeNav
      v-model:keyword="keyword"
      :selected="selected"
      @select-node="selectNode"
    />

    <main class="workspace">
      <header class="topbar">
        <div class="product-title">
          <div class="brand-mark">AR</div>
          <div>
            <p class="eyebrow">Application Map</p>
            <h1>三方应用 APP 页面跳转图谱</h1>
          </div>
        </div>
        <div class="topbar-actions">
          <div class="layout-switch button-group" data-slot="button-group" aria-label="图谱布局切换">
            <Button
              v-for="mode in layoutModes"
              :key="mode.value"
              variant="ghost"
              size="sm"
              type="button"
              :class="{ active: layoutMode === mode.value }"
              @click="layoutMode = mode.value"
            >
              {{ mode.label }}
            </Button>
          </div>

          <div class="graph-tools button-group" data-slot="button-group" aria-label="图谱操作">
            <Button variant="ghost" size="sm" @click="fitGraph">适配视图</Button>
            <Button variant="ghost" size="sm" @click="expandGraph">全部展开</Button>
            <Button variant="ghost" size="sm" @click="collapseGraph">全部收起</Button>
            <Button variant="ghost" size="sm" @click="resetGraph">重置布局</Button>
            <Button variant="ghost" size="sm" @click="exportGraph">导出图片</Button>
          </div>

          <div class="stats">
            <div class="stat">
              <span>节点</span>
              <strong>{{ appPages.length }}</strong>
            </div>
            <div class="stat">
              <span>跳转</span>
              <strong>{{ appEdges.length }}</strong>
            </div>
            <div class="stat">
              <span>层级</span>
              <strong>3</strong>
            </div>
            <div class="stat">
              <span>状态</span>
              <strong>演示版</strong>
            </div>
          </div>
        </div>
      </header>

      <Dialog v-model:open="showReplayPanel">
        <DialogContent class="replay-dialog">
          <DialogHeader>
            <p class="eyebrow">User Journey Replay</p>
            <DialogTitle>导入 URL 轨迹并高亮可能路径</DialogTitle>
            <DialogDescription>
              每行输入一条用户 URL 事件，格式为 timestamp,url,duration_ms。系统会匹配图谱节点并生成 possible replay path。
            </DialogDescription>
          </DialogHeader>
          <Textarea
            v-model="replayTraceText"
            class="replay-textarea"
            spellcheck="false"
            placeholder="每行一条：timestamp,url,duration_ms"
          />
          <DialogFooter>
            <Button variant="outline" @click="clearReplayTrace">清除高亮</Button>
            <Button @click="analyzeReplayTrace">AI 分析路径</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <GraphCanvas
        ref="graphRef"
        :layout-mode="layoutMode"
        :layout-revision="layoutRevision"
        :keyword="keyword"
        :replay-analysis="replayAnalysis"
        :selected="selected"
        @select-node="selectNode"
        @select-edge="selectEdge"
      />

      <Button class="replay-floating-trigger" size="sm" @click="showReplayPanel = true">
        导入 URL 轨迹
      </Button>
    </main>

    <InspectorPanel
      :selected="selected"
      :payload="selectedPayload"
      :replay-analysis="replayAnalysis"
    />
  </div>
</template>
