<script setup>
import { computed, onMounted, ref } from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import InspectorPanel from "./components/InspectorPanel.vue";
import TreeNav from "./components/TreeNav.vue";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  applyPageReviewToGraph,
  createEmptyGraph,
  mergeFloatingPageIntoGraph,
  moveGraphNode,
  normalizeBackendGraph,
  queryAppGraph,
  requestAiExploreFloatingPage,
  requestManualMergeFloatingPage,
  requestMergeFloatingPage,
  requestSavePageReview
} from "./data/graph.js";

const appName = ref(import.meta.env.VITE_DEFAULT_APP_NAME || "demo");
const selected = ref({ type: "node", id: "" });
const keyword = ref("");
const layoutMode = ref("horizontal");
const compactMode = ref(false);
const graphRef = ref(null);
const layoutRevision = ref(0);
const loading = ref(false);
const errorMessage = ref("");
const graph = ref(createEmptyGraph());
const floatingAiState = ref({});

const layoutModes = [
  { value: "horizontal", label: "左右排列" },
  { value: "vertical", label: "上下排列" },
  { value: "radial", label: "自由排列" }
];

const selectedPayload = computed(() => {
  if (selected.value.type === "edge") {
    return graph.value.edges.find((edge) => edge.id === selected.value.id) || null;
  }
  return graph.value.pageMap.get(selected.value.id) || null;
});

async function loadGraph() {
  if (!appName.value.trim()) {
    errorMessage.value = "请输入 App 名称";
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  try {
    const payload = await queryAppGraph(appName.value.trim());
    const normalized = normalizeBackendGraph(payload);
    graph.value = normalized;
    floatingAiState.value = {};
    selected.value = { type: "node", id: normalized.roots[0] || "" };
    layoutRevision.value += 1;
    window.setTimeout(() => graphRef.value?.fitGraph(), 80);
  } catch (error) {
    graph.value = createEmptyGraph();
    selected.value = { type: "node", id: "" };
    errorMessage.value = error instanceof Error ? error.message : "图谱加载失败";
  } finally {
    loading.value = false;
  }
}

function selectNode(nodeId) {
  selected.value = { type: "node", id: nodeId };
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

async function exploreFloatingNode(nodeId) {
  const page = graph.value.pageMap.get(nodeId);
  if (!page) return;
  floatingAiState.value = {
    ...floatingAiState.value,
    [nodeId]: { status: "running", message: "AI 正在调用 HDC 探索 URL..." }
  };
  try {
    const result = await requestAiExploreFloatingPage(page);
    const payload = result?.data || result?.result || result;
    const canMerge = Boolean(payload?.can_merge ?? payload?.mergeable ?? payload?.suitable);
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: {
        status: canMerge ? "mergeable" : "review",
        message: payload?.reason || payload?.message || (canMerge ? "AI 推断可并入主树" : "AI 未找到稳定并入位置"),
        result: payload
      }
    };
  } catch (error) {
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: {
        status: "failed",
        message: error instanceof Error ? error.message : "AI 探索失败"
      }
    };
  }
}

async function mergeFloatingNode(nodeId) {
  const page = graph.value.pageMap.get(nodeId);
  const state = floatingAiState.value[nodeId];
  if (!page || !state?.result) return;
  floatingAiState.value = {
    ...floatingAiState.value,
    [nodeId]: { ...state, status: "merging", message: "正在并入主树..." }
  };
  try {
    const response = await requestMergeFloatingPage(page, state.result);
    const payload = response?.data || response?.result || response || state.result;
    graph.value = mergeFloatingPageIntoGraph(graph.value, nodeId, payload);
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: { ...state, status: "merged", message: "已并入主树", result: payload }
    };
    selected.value = { type: "node", id: nodeId };
    layoutRevision.value += 1;
  } catch (error) {
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: {
        ...state,
        status: "failed",
        message: error instanceof Error ? error.message : "并入失败"
      }
    };
  }
}

async function manualMergeFloatingNode({ nodeId, targetParentId }) {
  const page = graph.value.pageMap.get(nodeId);
  const targetParent = graph.value.pageMap.get(targetParentId);
  if (!page || !targetParent || page.nodeId === targetParent.nodeId) return;

  const currentState = floatingAiState.value[nodeId] || {};
  floatingAiState.value = {
    ...floatingAiState.value,
    [nodeId]: {
      ...currentState,
      status: "merging",
      message: "正在人工归类并入..."
    }
  };

  try {
    const response = await requestManualMergeFloatingPage(page, targetParent);
    const payload = response?.data || response?.result || response;
    graph.value = mergeFloatingPageIntoGraph(graph.value, nodeId, payload);
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: {
        ...currentState,
        status: "merged",
        message: "已人工并入主图谱",
        result: payload
      }
    };
  } catch (error) {
    const fallbackPayload = {
      can_merge: true,
      target_parent_node_id: targetParentId,
      target_parent_id: targetParent.backendId,
      widget_description: "人工拖拽归类",
      ai_recursive: true,
      reason: error instanceof Error ? error.message : "manual merge fallback"
    };
    graph.value = mergeFloatingPageIntoGraph(graph.value, nodeId, fallbackPayload);
    floatingAiState.value = {
      ...floatingAiState.value,
      [nodeId]: {
        ...currentState,
        status: "merged",
        message: "后端暂不可用，已本地并入待复核",
        result: fallbackPayload
      }
    };
  }

  selected.value = { type: "node", id: nodeId };
  layoutRevision.value += 1;
  window.setTimeout(() => graphRef.value?.fitGraph(), 80);
}

function moveTreeNode({ nodeId, targetParentId }) {
  const beforeGraph = graph.value;
  graph.value = moveGraphNode(graph.value, nodeId, targetParentId, {
    widget_description: "人工调整归类",
    reason: "用户在左侧树结构中拖拽调整"
  });
  if (graph.value === beforeGraph) return;
  selected.value = { type: "node", id: nodeId };
  layoutRevision.value += 1;
  window.setTimeout(() => graphRef.value?.fitGraph(), 80);
}

async function savePageReview(review) {
  const page = graph.value.pageMap.get(review.nodeId);
  if (!page) return;
  let payload = review;
  try {
    const response = await requestSavePageReview(page, review);
    payload = response?.data || response?.result || response || review;
  } catch (error) {
    payload = {
      ...review,
      review_status: "edited_local",
      review_note: `${review.review_note || ""}${review.review_note ? "\n" : ""}后端暂不可用，已本地保存待同步。`
    };
  }
  graph.value = applyPageReviewToGraph(graph.value, review.nodeId, payload);
  selected.value = { type: "node", id: review.nodeId };
  layoutRevision.value += 1;
}

onMounted(loadGraph);
</script>

<template>
  <div class="app-shell">
    <TreeNav
      v-model:keyword="keyword"
      :graph="graph"
      :floating-ai-state="floatingAiState"
      :loading="loading"
      :selected="selected"
      @explore-floating-node="exploreFloatingNode"
      @manual-merge-floating-node="manualMergeFloatingNode"
      @merge-floating-node="mergeFloatingNode"
      @move-tree-node="moveTreeNode"
      @select-node="selectNode"
    />

    <main class="workspace">
      <header class="topbar">
        <div class="product-title">
          <div class="brand-mark">AR</div>
          <div>
            <p class="eyebrow">Application Map</p>
            <h1>第三方应用页面关系图谱</h1>
          </div>
        </div>

        <div class="topbar-actions">
          <div class="app-query">
            <Input
              v-model="appName"
              class="app-name-input"
              placeholder="输入 App 名称"
              @keyup.enter="loadGraph"
            />
            <Button size="sm" :disabled="loading" @click="loadGraph">
              {{ loading ? "加载中" : "查询图谱" }}
            </Button>
          </div>

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
              <strong>{{ graph.pages.length }}</strong>
            </div>
            <div class="stat">
              <span>跳转</span>
              <strong>{{ graph.edges.length }}</strong>
            </div>
            <div class="stat">
              <span>游离</span>
              <strong>{{ graph.floatingPages.length }}</strong>
            </div>
            <div class="stat">
              <span>状态</span>
              <strong>{{ loading ? "加载中" : "在线" }}</strong>
            </div>
          </div>
        </div>
      </header>

      <div v-if="errorMessage" class="graph-error">
        {{ errorMessage }}
      </div>

      <GraphCanvas
        ref="graphRef"
        :graph="graph"
        :compact-mode="compactMode"
        :layout-mode="layoutMode"
        :layout-revision="layoutRevision"
        :keyword="keyword"
        :selected="selected"
        @toggle-compact-mode="compactMode = !compactMode"
        @select-node="selectNode"
        @select-edge="selectEdge"
      />
    </main>

    <InspectorPanel
      :graph="graph"
      :selected="selected"
      :payload="selectedPayload"
      @save-page-review="savePageReview"
    />
  </div>
</template>
