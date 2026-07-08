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

const emit = defineEmits(["update:keyword", "select-node", "explore-floating-node", "merge-floating-node"]);
const collapsed = ref(new Set());

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

    <section class="sidebar-section main-tree-section">
      <div class="sidebar-section-head">
        <strong>主图谱树</strong>
        <Badge variant="secondary">{{ graph.roots.length }}</Badge>
      </div>
      <ScrollArea class="tree-scroll module-scroll">
        <div v-if="loading" class="empty-state">图谱加载中...</div>
        <div v-else-if="!tree.length" class="empty-state">暂无主树数据</div>
        <nav v-else class="tree-nav" aria-label="主图谱树">
          <TreeItem
            v-for="node in tree"
            :key="node.id"
            :node="node"
            :collapsed="collapsed"
            :selected="selected"
            :is-muted="isMuted"
            @toggle="toggle"
            @select-node="emit('select-node', $event)"
          />
        </nav>
      </ScrollArea>
    </section>

    <section class="sidebar-section floating-section">
      <div class="sidebar-section-head">
        <strong>游离 URL 页面</strong>
        <Badge variant="secondary">{{ graph.floatingPages.length }}</Badge>
      </div>
      <ScrollArea class="floating-scroll module-scroll">
        <div v-if="loading" class="empty-state">等待图谱数据...</div>
        <div v-else-if="!floatingTree.length" class="empty-state">暂无游离页面</div>
        <div v-else class="floating-list">
          <div
            v-for="node in floatingTree"
            :key="node.id"
            class="floating-page-card"
            :class="{ active: selected.type === 'node' && selected.id === node.id, muted: isMuted(node) }"
            role="button"
            tabindex="0"
            @click="emit('select-node', node.id)"
            @keyup.enter="emit('select-node', node.id)"
          >
            <span>{{ node.page.displayTitle }}</span>
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
