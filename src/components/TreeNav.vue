<script setup>
import { computed, ref, watch } from "vue";
import TreeItem from "./TreeItem.vue";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getOutgoingEdges } from "../data/graph.js";

const props = defineProps({
  graph: {
    type: Object,
    required: true
  },
  keyword: {
    type: String,
    default: ""
  },
  selected: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  floatingAiState: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits([
  "update:keyword",
  "select-node",
  "explore-floating-node",
  "merge-floating-node",
  "manual-merge-floating-node",
  "move-tree-node"
]);

const collapsed = ref(new Set());
const draggingFloatingId = ref("");
const draggingTreeId = ref("");
const dragMode = ref(false);
const treeEditMode = ref(false);

const tree = computed(() => props.graph.roots.map((rootId) => buildNode(rootId)));
const floatingTree = computed(() => props.graph.floatingRoots.map((rootId) => buildNode(rootId)));
const searchResults = computed(() => {
  const normalized = props.keyword.trim().toLowerCase();
  if (!normalized) return [];
  return props.graph.pages
    .filter((page) => searchableText(page).includes(normalized))
    .slice(0, 12);
});

watch(() => props.graph, () => {
  collapsed.value = new Set();
  draggingFloatingId.value = "";
  draggingTreeId.value = "";
  dragMode.value = false;
  treeEditMode.value = false;
});

function buildNode(nodeId) {
  const page = props.graph.pageMap.get(nodeId);
  return {
    id: nodeId,
    page,
    children: getOutgoingEdges(props.graph, nodeId).map((edge) => buildNode(edge.to))
  };
}

function toggle(nodeId) {
  const next = new Set(collapsed.value);
  if (next.has(nodeId)) next.delete(nodeId);
  else next.add(nodeId);
  collapsed.value = next;
}

function toggleDragMode() {
  dragMode.value = !dragMode.value;
  if (dragMode.value) treeEditMode.value = false;
  draggingFloatingId.value = "";
  draggingTreeId.value = "";
}

function toggleTreeEditMode() {
  treeEditMode.value = !treeEditMode.value;
  if (treeEditMode.value) dragMode.value = false;
  draggingFloatingId.value = "";
  draggingTreeId.value = "";
}

function isMuted(node) {
  const normalized = props.keyword.trim().toLowerCase();
  if (!normalized) return false;
  return !searchableText(node.page).includes(normalized);
}

function searchableText(page) {
  if (!page) return "";
  return [
    page.page_title,
    page.displayTitle,
    page.page_text,
    page.page_url,
    page.aiInference?.label,
    page.aiInference?.reason,
    JSON.stringify(page.page_info || {})
  ].join(" ").toLowerCase();
}

function handleFloatingDragStart(event, nodeId) {
  if (!dragMode.value) {
    event.preventDefault();
    return;
  }
  draggingFloatingId.value = nodeId;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("application/x-floating-node-id", nodeId);
  event.dataTransfer.setData("text/plain", nodeId);
}

function handleFloatingDragEnd() {
  draggingFloatingId.value = "";
}

function handleDropOnTree(payload) {
  const nodeId = payload?.nodeId || draggingFloatingId.value;
  const targetParentId = payload?.targetParentId || payload;
  if (!nodeId || nodeId === targetParentId) return;
  emit("manual-merge-floating-node", { nodeId, targetParentId });
  draggingFloatingId.value = "";
  dragMode.value = false;
}

function handleTreeDragStart(nodeId) {
  draggingTreeId.value = nodeId;
}

function handleTreeDragEnd() {
  draggingTreeId.value = "";
}

function handleMoveTreeNode(payload) {
  if (!payload?.nodeId || !payload?.targetParentId) return;
  emit("move-tree-node", payload);
  draggingTreeId.value = "";
  treeEditMode.value = false;
}
</script>

<template>
  <aside class="sidebar">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Navigation</p>
        <h2>页面层级</h2>
      </div>
      <span class="panel-chip">Graph</span>
    </div>

    <div class="search-box">
      <Input
        :value="keyword"
        type="search"
        placeholder="搜索页面、URL、AI 文本"
        @input="emit('update:keyword', $event.target.value)"
      />
    </div>

    <div v-if="searchResults.length" class="search-results">
      <button
        v-for="page in searchResults"
        :key="page.nodeId"
        type="button"
        @click="emit('select-node', page.nodeId)"
      >
        <strong>{{ page.displayTitle }}</strong>
        <span>{{ page.page_url || "no url" }}</span>
      </button>
    </div>

    <section class="sidebar-section main-tree-section" :class="{ 'drop-mode': dragMode || treeEditMode }">
      <div class="sidebar-section-head">
        <strong>主图谱树</strong>
        <div class="floating-head-actions">
          <button
            class="drag-mode-toggle"
            :class="{ active: treeEditMode }"
            type="button"
            :disabled="!graph.roots.length"
            @click="toggleTreeEditMode"
          >
            {{ treeEditMode ? "关闭编辑" : "编辑结构" }}
          </button>
          <Badge variant="secondary">{{ graph.roots.length }}</Badge>
        </div>
      </div>
      <ScrollArea class="tree-scroll module-scroll">
        <div v-if="loading" class="empty-state">图谱加载中...</div>
        <div v-else-if="!tree.length" class="empty-state">暂无主树数据</div>
        <div v-else>
          <p v-if="treeEditMode" class="manual-merge-hint active">
            拖动主树节点到另一个节点上，可调整父子关系。系统会阻止拖到自身或子节点下。
          </p>
          <nav class="tree-nav" aria-label="主图谱树">
            <TreeItem
              v-for="node in tree"
              :key="node.id"
              :node="node"
              :collapsed="collapsed"
              :selected="selected"
              :is-muted="isMuted"
              :can-drop-floating="dragMode || Boolean(draggingFloatingId)"
              :tree-edit-mode="treeEditMode"
              @toggle="toggle"
              @drop-floating-node="handleDropOnTree"
              @move-tree-node="handleMoveTreeNode"
              @tree-drag-start="handleTreeDragStart"
              @tree-drag-end="handleTreeDragEnd"
              @select-node="emit('select-node', $event)"
            />
          </nav>
        </div>
      </ScrollArea>
    </section>

    <section class="sidebar-section floating-section">
      <div class="sidebar-section-head">
        <strong>游离 URL 页面</strong>
        <div class="floating-head-actions">
          <button
            class="drag-mode-toggle"
            :class="{ active: dragMode }"
            type="button"
            :disabled="!graph.floatingPages.length"
            @click="toggleDragMode"
          >
            {{ dragMode ? "关闭拖拽" : "开启拖拽" }}
          </button>
          <Badge variant="secondary">{{ graph.floatingPages.length }}</Badge>
        </div>
      </div>
      <ScrollArea class="floating-scroll module-scroll">
        <div v-if="loading" class="empty-state">等待图谱数据...</div>
        <div v-else-if="!floatingTree.length" class="empty-state">暂无游离页面</div>
        <div v-else class="floating-list">
          <p class="manual-merge-hint" :class="{ active: dragMode }">
            {{ dragMode ? "拖住卡片或拖拽按钮，放到主树节点上完成归类。" : "点击“开启拖拽”后，可把游离页面拖到主树节点下。" }}
          </p>
          <div
            v-for="node in floatingTree"
            :key="node.id"
            class="floating-page-card"
            :class="{
              active: selected.type === 'node' && selected.id === node.id,
              muted: isMuted(node),
              dragging: draggingFloatingId === node.id,
              'drag-enabled': dragMode
            }"
            :draggable="dragMode"
            role="button"
            tabindex="0"
            @click="emit('select-node', node.id)"
            @dragend="handleFloatingDragEnd"
            @dragstart="handleFloatingDragStart($event, node.id)"
            @keyup.enter="emit('select-node', node.id)"
          >
            <div class="floating-card-head">
              <span>{{ node.page.displayTitle }}</span>
              <button
                v-if="dragMode"
                class="drag-handle"
                draggable="true"
                title="拖拽到主树节点并入"
                type="button"
                @click.stop
                @dragend="handleFloatingDragEnd"
                @dragstart.stop="handleFloatingDragStart($event, node.id)"
              >
                拖拽
              </button>
            </div>
            <strong>{{ node.page.aiInference.label }}</strong>
            <em>{{ node.page.aiInference.reason }}</em>
            <small>{{ node.page.page_url || "no page url" }}</small>
            <span
              v-if="floatingAiState[node.id]"
              class="floating-ai-status"
              :class="`status-${floatingAiState[node.id].status}`"
            >
              {{ floatingAiState[node.id].message }}
            </span>
            <span class="floating-actions" @click.stop>
              <button
                type="button"
                :disabled="floatingAiState[node.id]?.status === 'running' || floatingAiState[node.id]?.status === 'merging'"
                @click="emit('explore-floating-node', node.id)"
              >
                {{ floatingAiState[node.id]?.status === "running" ? "探索中" : "AI 探索" }}
              </button>
              <button
                v-if="floatingAiState[node.id]?.status === 'mergeable'"
                type="button"
                class="merge"
                @click="emit('merge-floating-node', node.id)"
              >
                并入
              </button>
            </span>
          </div>
        </div>
      </ScrollArea>
    </section>
  </aside>
</template>
