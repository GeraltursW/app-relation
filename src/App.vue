<script setup>
import { computed, ref } from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import InspectorPanel from "./components/InspectorPanel.vue";
import TreeNav from "./components/TreeNav.vue";
import { appEdges, appPages, pageMap } from "./data/graph.js";

const selected = ref({ type: "node", id: "root" });
const keyword = ref("");
const layoutMode = ref("horizontal");
const graphRef = ref(null);
const layoutRevision = ref(0);
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
        <div>
          <p class="eyebrow">Application Map</p>
          <h1>三方应用 APP 页面跳转图谱</h1>
        </div>
        <div class="topbar-actions">
          <div class="layout-switch" aria-label="图谱布局切换">
            <button
              v-for="mode in layoutModes"
              :key="mode.value"
              type="button"
              :class="{ active: layoutMode === mode.value }"
              @click="layoutMode = mode.value"
            >
              {{ mode.label }}
            </button>
          </div>

          <div class="graph-tools" aria-label="图谱操作">
            <button type="button" @click="fitGraph">适配视图</button>
            <button type="button" @click="expandGraph">全部展开</button>
            <button type="button" @click="collapseGraph">全部收起</button>
            <button type="button" @click="resetGraph">重置布局</button>
            <button type="button" @click="exportGraph">导出图片</button>
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

      <GraphCanvas
        ref="graphRef"
        :layout-mode="layoutMode"
        :layout-revision="layoutRevision"
        :keyword="keyword"
        :selected="selected"
        @select-node="selectNode"
        @select-edge="selectEdge"
      />
    </main>

    <InspectorPanel
      :selected="selected"
      :payload="selectedPayload"
    />
  </div>
</template>
